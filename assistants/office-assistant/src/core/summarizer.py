#!/usr/bin/env python3

"""
模块名称：summarizer
功能描述：文档摘要生成器
对外接口：
    - DocumentSummarizer(): 初始化摘要器
        - summarize(text, max_points): 生成文本摘要
依赖：
    - 标准库：logging
    - 第三方：无
    - 项目内：无
版本：v1.0
更新记录：
    - 2026-05-23: 添加统一注释头
"""

import logging
import time
from pathlib import Path
from typing import Optional
import requests

logger = logging.getLogger("Summarizer")


class DocumentSummarizer:
    """文档文本摘要器，调用推理后端生成中文摘要"""
    
    CHUNK_SIZE = 2000
    REQUEST_TIMEOUT = 30
    MAX_RETRIES = 1

    @staticmethod
    def _get_backend_config() -> dict:
        """从 settings.yaml 读取后端配置"""
        config_path = Path(__file__).parent.parent.parent.parent.parent / "config" / "settings.yaml"
        try:
            if config_path.exists():
                import yaml
                cfg = yaml.safe_load(config_path.read_text())
                backend = cfg.get("backend", "llama.cpp")
                port = cfg.get("ollama_port", 11434) if backend == "ollama" else cfg.get("llama_port", 8080)
                model = cfg.get("ollama_model", "qwen2.5:7b") if backend == "ollama" else "gpt-3.5-turbo"
                return {"backend": backend, "port": port, "model": model}
        except Exception:
            pass
        return {"backend": "llama.cpp", "port": 8080, "model": "gpt-3.5-turbo"}
    
    def __init__(self, llama_url: Optional[str] = None, model_name: Optional[str] = None):
        """
        初始化摘要器
        :param llama_url: API 地址，默认根据 settings.yaml 决定
        :param model_name: 模型名称，默认根据 settings.yaml 决定
        """
        cfg = self._get_backend_config()
        self.api_url = llama_url or f"http://localhost:{cfg['port']}/v1/chat/completions"
        self.model_name = model_name or cfg['model']
        self.backend = cfg['backend']
        
        self._check_backend_status()
    
    def _check_backend_status(self) -> bool:
        """检查推理后端服务是否可用"""
        health_url = self.api_url.replace('/v1/chat/completions', '/health')
        endpoints = [health_url]
        if self.backend == "ollama":
            endpoints.append("http://localhost:11434/api/tags")
        for endpoint in endpoints:
            try:
                logger.debug(f"检查后端状态：{endpoint}")
                resp = requests.get(endpoint, timeout=5)
                if resp.status_code == 200:
                    logger.info(f"后端服务可用: {endpoint} (model={self.model_name})")
                    return True
                else:
                    logger.warning(f"后端状态检查返回 {resp.status_code}：{endpoint}")
            except requests.exceptions.ConnectionError:
                logger.warning(f"无法连接后端服务：{endpoint}")
            except requests.exceptions.Timeout:
                logger.warning(f"后端状态检查超时：{endpoint}")
            except Exception as e:
                logger.warning(f"检查后端状态异常：{e}")
        logger.error("推理后端服务不可用，摘要功能将降级")
        return False

    def _call_llama(self, prompt: str) -> Optional[str]:
        """
        调用推理后端 API 生成回复
        :param prompt: 提示词
        :return: 生成的文本，失败返回 None
        """
        payload = {
            "model": self.model_name,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
            "max_tokens": 256,
            "temperature": 0.3
        }
        for attempt in range(self.MAX_RETRIES + 1):
            try:
                logger.debug(f"调用后端 (尝试 {attempt+1}/{self.MAX_RETRIES+1}) model={self.model_name}")
                start_time = time.time()
                resp = requests.post(
                    self.api_url,
                    json=payload,
                    timeout=self.REQUEST_TIMEOUT
                )
                resp.raise_for_status()
                elapsed = time.time() - start_time
                result = resp.json().get("choices", [{}])[0].get("message", {}).get("content", "").strip()
                logger.info(f"后端响应成功，耗时 {elapsed:.1f}s，返回 {len(result)} 字符")
                return result
            except requests.exceptions.Timeout:
                logger.warning(f"后端请求超时 (尝试 {attempt+1})")
                if attempt < self.MAX_RETRIES:
                    time.sleep(2)
            except requests.exceptions.ConnectionError:
                logger.error("推理后端连接失败")
                break
            except Exception as e:
                logger.error(f"后端请求异常: {e}")
                if attempt < self.MAX_RETRIES:
                    time.sleep(2)
        return None

    def _split_text(self, text: str) -> list:
        """
        按段落分块，每块不超过 CHUNK_SIZE 字符
        :param text: 原始文本
        :return: 文本块列表
        """
        if len(text) <= self.CHUNK_SIZE:
            return [text]
        chunks = []
        paragraphs = text.split('\n')
        current_chunk = ""
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            # 如果单个段落本身就超过限制，按句号分割
            if len(para) > self.CHUNK_SIZE:
                # 先保存当前块
                if current_chunk:
                    chunks.append(current_chunk.strip())
                    current_chunk = ""
                # 按句子分割长段落
                sentences = para.replace('。', '。\n').replace('！', '！\n').replace('？', '？\n').split('\n')
                for sent in sentences:
                    sent = sent.strip()
                    if not sent:
                        continue
                    if len(current_chunk) + len(sent) + 1 <= self.CHUNK_SIZE:
                        current_chunk += sent + '\n'
                    else:
                        if current_chunk:
                            chunks.append(current_chunk.strip())
                        current_chunk = sent + '\n'
            elif len(current_chunk) + len(para) + 1 <= self.CHUNK_SIZE:
                current_chunk += para + '\n'
            else:
                chunks.append(current_chunk.strip())
                current_chunk = para + '\n'
        if current_chunk.strip():
            chunks.append(current_chunk.strip())
        logger.info(f"文本分块完成: 原始 {len(text)} 字符 → {len(chunks)} 块")
        for i, chunk in enumerate(chunks):
            logger.debug(f"  块 {i+1}: {len(chunk)} 字符")
        return chunks

    def summarize(self, text: str, max_points: int = 5) -> dict:
        """
        对文本生成中文摘要
        :param text: 输入文本
        :param max_points: 期望的要点数量
        :return: 字典，包含 success, summary, method, error 字段
        """
        if not text or not text.strip():
            logger.warning("输入文本为空，跳过摘要")
            return {
                "success": False,
                "summary": "",
                "method": "none",
                "error": "输入文本为空"
            }
        # 处理长文本：分块摘要
        if len(text) > self.CHUNK_SIZE:
            logger.info(f"文本长度 {len(text)} 超过阈值，启用分块摘要")
            return self._chunked_summarize(text, max_points)
        # 短文本直接摘要
        prompt = f"""请用中文总结以下文档的要点，输出 {max_points} 个以内的编号列表：
---
{text}
---
要点总结："""
        result = self._call_llama(prompt)
        if result:
            return {
                "success": True,
                "summary": result,
                "method": "ollama_direct",
                "error": None
            }
        logger.warning("后端调用失败，降级为简单摘要")
        return self._fallback_summary(text, max_points)

    def _chunked_summarize(self, text: str, max_points: int) -> dict:
        """
        分块摘要：逐块生成摘要，再合并生成最终摘要
        """
        chunks = self._split_text(text)
        if len(chunks) == 1:
            # 实际只有一块，走直接摘要
            prompt = f"""请用中文总结以下文档的要点，输出 {max_points} 个以内的编号列表：
---
{chunks[0]}
---
要点总结："""
            result = self._call_llama(prompt)
            if result:
                return {"success": True, "summary": result, "method": "ollama_single", "error": None}
            return self._fallback_summary(text, max_points)
        # 逐块摘要
        chunk_summaries = []
        for i, chunk in enumerate(chunks):
            logger.info(f"正在处理第 {i+1}/{len(chunks)} 块...")
            prompt = f"请用1-2句话简洁概括以下文本片段的核心内容：\n---\n{chunk}\n---\n概括："
            summary = self._call_llama(prompt)
            if summary:
                chunk_summaries.append(summary)
            else:
                # 该块摘要失败，用原文前200字符代替
                logger.warning(f"第 {i+1} 块摘要失败，使用原文截取")
                chunk_summaries.append(chunk[:200] + "...")
        if not chunk_summaries:
            return self._fallback_summary(text, max_points)
        # 合并所有分块摘要
        merged = "\n\n".join([f"部分{i+1}: {s}" for i, s in enumerate(chunk_summaries)])
        final_prompt = f"""以下是一篇文档各部分的摘要，请整合成 {max_points} 个以内的要点总结（编号列表）：
---
{merged}
---
最终要点总结："""
        final_result = self._call_llama(final_prompt)
        if final_result:
            return {
                "success": True,
                "summary": final_result,
                "method": "ollama_chunked",
                "chunks_processed": len(chunks),
                "error": None
            }
        # 最终合并失败，返回分块摘要的拼接
        return {
            "success": True,
            "summary": merged,
            "method": "ollama_chunked_partial",
            "chunks_processed": len(chunks),
            "error": "最终合并步骤失败，返回原始分块摘要"
        }
    def _fallback_summary(self, text: str, max_points: int) -> dict:
        """
        降级方案：提取文本前 N 句作为简单摘要
        """
        sentences = text.replace('\n', ' ').split('。')
        key_sentences = []
        for s in sentences:
            s = s.strip()
            if s and len(s) > 5:
                key_sentences.append(s)
            if len(key_sentences) >= max_points * 2:
                break
        summary = "（降级摘要）\n" + '\n'.join([f"{i+1}. {s}。" for i, s in enumerate(key_sentences[:max_points])])
        logger.info("降级摘要生成完成")
        return {
            "success": True,
            "summary": summary,
            "method": "fallback",
            "error": "llama-server 服务不可用，使用简单文本截取"
        }
# 命令行入口（用于直接测试）
if __name__ == "__main__":
    import sys
    summarizer = DocumentSummarizer()
    # 测试文本
    test_text = """人工智能技术近年来取得了飞速发展。深度学习作为其核心驱动力，在图像识别、自然语言处理等领域取得了突破性进展。
大语言模型的出现标志着自然语言处理进入新纪元。这些模型通过海量文本数据的预训练，能够理解和生成人类语言，完成翻译、写作、编程等复杂任务。
在医疗领域，AI辅助诊断系统已经能够帮助医生识别早期病变，提高诊断准确率。在自动驾驶领域，计算机视觉技术让汽车能够感知周围环境并做出安全决策。
然而，AI的快速发展也带来了隐私保护、就业影响、伦理安全等挑战。各国纷纷出台相关政策法规，旨在引导AI技术健康发展。"""
    print("="*60)
    print("测试 1: 短文本摘要")
    result = summarizer.summarize(test_text, max_points=3)
    print(f"方法: {result['method']}")
    print(f"摘要:\n{result['summary']}")
    if result.get('error'):
        print(f"提示: {result['error']}")
    print("\n" + "="*60)
    print("测试 2: 空文本处理")
    result2 = summarizer.summarize("")
    print(f"成功: {result2['success']}")
    print(f"错误: {result2['error']}")
    cfg = summarizer._get_backend_config()
    print(f"\n后端配置: {cfg['backend']} port={cfg['port']} model={cfg['model']}")