"""
模块名称：chat
功能描述：对话历史管理（加载、保存、清空）
对外接口：
    - load_history(): 加载对话历史
    - save_history(messages): 保存对话历史
    - clear_history(): 清空对话历史
依赖：
    - 标准库：os, json, logging
    - 第三方：无
    - 项目内：无
版本：v1.0
更新记录：
    - 2026-05-23: 添加统一注释头
"""
import json
import os
import logging

logging.basicConfig(level=logging.DEBUG, format='[%(levelname)s] %(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

HISTORY_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs", "chat_history.json")
MAX_HISTORY = 50  # 最多保留最近50轮对话

def load_history():
    """加载历史对话"""
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            logger.debug(f"加载历史对话，共 {len(data)} 轮")
            return data
    logger.debug("无历史对话文件，返回空列表")
    return []

def save_history(messages):
    """保存对话历史，只保留最近 MAX_HISTORY 轮"""
    trimmed = messages[-MAX_HISTORY * 2:]  # 每轮包含 user + assistant，所以乘 2
    os.makedirs(os.path.dirname(HISTORY_FILE), exist_ok=True)
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(trimmed, f, ensure_ascii=False, indent=2)
    logger.debug(f"保存历史对话，共 {len(trimmed)} 条消息")

def format_history(messages):
    """将对话历史格式化为模型可理解的上下文"""
    lines = []
    for msg in messages:
        role = "用户" if msg["role"] == "user" else "助手"
        lines.append(f"{role}：{msg['content']}")
    return "\n".join(lines)

def clear_history():
    """清空对话历史"""
    if os.path.exists(HISTORY_FILE):
        os.remove(HISTORY_FILE)
        logger.debug("对话历史已清空")
        return "对话历史已清空"
    return "暂无历史对话"
