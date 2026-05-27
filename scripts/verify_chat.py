#!/usr/bin/env python3
"""
模块名称：verify_chat
功能描述：1号AI 回复验证脚本，发送固定测试消息并检查回复是否有效
对外接口：
    - 直接运行，输出模型回复并判断修复是否生效
依赖：
    - 标准库：sys, os, logging
    - 第三方：无
    - 项目内：assistants.chat-assistant.src.main (talk)
版本：v1.0
更新记录：
    - 2026-05-23: 初始创建，添加统一注释头
"""
import sys
import os
import logging

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.dirname(SCRIPT_DIR)
sys.path.insert(0, os.path.join(PROJECT, "assistants/chat-assistant/src"))
from main import talk

logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(asctime)s - %(message)s')
logger = logging.getLogger("verify_chat")

def verify():
    test_messages = [
        {"role": "user", "content": "你好，请用中文说“测试成功”"}
    ]
    logger.info("📤 发送测试消息: 你好，请用中文说“测试成功”")
    result = talk(test_messages)
    logger.info(f"📥 模型返回 ({len(result)} 字符):\n{result}")

    # 判断是否有效
    if not result or result.startswith("抱歉") or result.startswith("你好呀"):
        logger.error("❌ 修复可能未生效，仍返回空或降级固定话术")
    else:
        logger.info("✅ 修复生效，1号AI 正常回复")

if __name__ == "__main__":
    verify()