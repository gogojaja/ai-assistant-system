"""
模块名称：backend_utils
功能描述：推理后端通用工具函数（配置读取、进程唤醒、API调用、回复清理）
对外接口：
    - get_backend_config(): 读取 settings.yaml 后端配置
    - wake_model(): 唤醒被 SIGSTOP 挂起的模型进程
    - call_api(messages, temperature, max_tokens): 流式调用推理后端 API，返回文本
    - clean_reply(text): 清理模型输出中的指令残留前缀
    - extract_from_reasoning(text): 从 reasoning_content 提取最终总结句子
依赖：
    - 标准库：os, json, logging, subprocess, pathlib, re
    - 第三方：requests, yaml
    - 项目内：无
版本：v1.0
更新记录：
    - 2026-05-26: 初始创建，从 document_handler.py 和 main.py 抽取重复代码
"""
import json
import logging
import os
import re
import subprocess
from pathlib import Path

import requests
import yaml

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def get_backend_config() -> dict:
    """从 settings.yaml 读取后端配置"""
    config_path = PROJECT_ROOT / "config" / "settings.yaml"
    try:
        if config_path.exists():
            cfg = yaml.safe_load(config_path.read_text())
            chat_api_url = cfg.get("chat_api_url", "")
            if chat_api_url:
                return {
                    "backend": "free-api-hub",
                    "api_url": chat_api_url,
                    "model": cfg.get("chat_model", "free-api-hub-chat"),
                }
            backend = cfg.get("backend", "llama.cpp")
            port = cfg.get("ollama_port", 11434) if backend == "ollama" else cfg.get("llama_port", 8080)
            model = cfg.get("ollama_model", "qwen2.5:7b") if backend == "ollama" else "gpt-3.5-turbo"
            return {"backend": backend, "port": port, "model": model}
    except Exception:
        pass
    return {"backend": "llama.cpp", "port": 8080, "model": "gpt-3.5-turbo"}


def wake_model():
    """唤醒被 SIGSTOP 挂起的模型进程 (llama-server 或 ollama)"""
    try:
        for proc_name in ("llama-server", "ollama"):
            result = subprocess.run(["pgrep", "-f", proc_name], capture_output=True, text=True, timeout=3)
            for pid in [p.strip() for p in result.stdout.split("\n") if p.strip()]:
                state = subprocess.run(["ps", "-o", "stat=", "-p", pid], capture_output=True, text=True, timeout=3).stdout.strip()
                if "T" in state:
                    os.kill(int(pid), 18)
                    logger.info(f"唤醒模型进程 PID={pid}")
    except Exception:
        pass


def call_api(messages: list, temperature: float = 0.3, max_tokens: int = 1024) -> str:
    """流式调用推理后端 API，返回回复文本"""
    cfg = get_backend_config()

    if cfg.get("backend") == "free-api-hub":
        api_url = cfg["api_url"] + "/chat/completions"
    else:
        wake_model()
        api_url = f"http://localhost:{cfg['port']}/v1/chat/completions"
    try:
        resp = requests.post(
            api_url,
            json={
                "model": cfg["model"],
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "stream": True,
            },
            timeout=60,
            stream=True,
        )
        if resp.status_code != 200:
            logger.error(f"API 返回错误: {resp.status_code}")
            return ""
        resp.encoding = 'utf-8'
        content_parts = []
        reasoning_parts = []
        for line in resp.iter_lines(decode_unicode=True):
            if not line or not line.startswith("data: "):
                continue
            data_str = line[6:]
            if data_str.strip() == "[DONE]":
                break
            try:
                chunk = json.loads(data_str)
                delta = chunk.get("choices", [{}])[0].get("delta", {})
                c = (delta.get("content") or "")
                r = (delta.get("reasoning_content") or "")
                if c:
                    content_parts.append(c)
                if r:
                    reasoning_parts.append(r)
            except json.JSONDecodeError:
                continue
        content = "".join(content_parts).strip()
        if content:
            return clean_reply(content)
        reasoning = "".join(reasoning_parts).strip()
        if reasoning:
            logger.info("content 为空，从 reasoning_content 提取")
            return extract_from_reasoning(reasoning)
        logger.warning("API 返回空内容")
        return ""
    except Exception as e:
        logger.error(f"API 调用异常: {e}")
        return ""


_REASONING_SKIP_PREFIXES = ("- ", "• ", "开头", "首先", "关键点", "然后", "接着", "最后", "用户说", "用户要求", "用户指定", "数据描述", "数据内容", "从数据", "让我", "我需要", "在总结", "可能", "这看起来", "这是", "这里")


def extract_from_reasoning(text: str) -> str:
    """从 reasoning_content 中提取最终总结句子"""
    candidates = []
    for line in text.replace("\n\n", "\n").split("\n"):
        line = line.strip()
        if not line:
            continue
        if any(line.startswith(p) for p in _REASONING_SKIP_PREFIXES):
            continue
        if "：" in line and not line.startswith("总结"):
            continue
        if len(line) < 15:
            continue
        candidates.append(line)
    if candidates:
        return candidates[-1]
    fallback = re.split(r'[。！？]', text)
    good = [s.strip() for s in fallback if len(s.strip()) > 15 and not any(p in s[:10] for p in ("用户", "要求", "关键点", "开头"))]
    if good:
        return good[-1] + "。"
    return "（摘要为空）"


_CLEAN_PATTERNS = [
    "最终输出：", "最终输出:", "最终回答：", "最终回答:",
    "我的回答：", "我的回答:", "直接输出：", "直接输出:",
    "答案是：", "答案是:", "总结：", "总结:",
    "Direct output:", "The answer is:", "Summary:",
]


def clean_reply(text: str) -> str:
    """清理模型输出中的指令残留前缀"""
    if not text:
        return text
    for pat in _CLEAN_PATTERNS:
        if text.startswith(pat):
            text = text[len(pat):].strip()
    return text
