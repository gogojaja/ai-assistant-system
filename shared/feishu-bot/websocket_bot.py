#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
模块名称：websocket_bot
功能描述：飞书 WebSocket 长连接机器人，基于 lark_oapi SDK 接收用户消息并自动回复
对外接口：
    - send_message(open_id, text): 通过飞书 API 发送文本消息给指定用户
    - MyHandler: 事件处理器类，实现 on_message 和 on_error 方法
    - main(): 启动长连接机器人，保持运行直到手动停止
依赖：
    - 标准库：json, logging, os, pathlib, sys, time
    - 第三方：python-dotenv, lark-oapi
    - 项目内：无
版本：v1.0
更新记录：
    - 2026-05-23: 自动添加统一注释头，补充功能描述
"""

import os
import sys
import json
import logging
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

from dotenv import load_dotenv
env_path = Path(__file__).parent / ".env"
load_dotenv(env_path)

APP_ID = os.getenv("FEISHU_APP_ID")
APP_SECRET = os.getenv("FEISHU_APP_SECRET")
if not APP_ID or not APP_SECRET:
    logger.error("❌ 缺少 FEISHU_APP_ID 或 FEISHU_APP_SECRET")
    sys.exit(1)

# 导入飞书 SDK 的实际可用组件
from lark_oapi import Client as ApiClient
from lark_oapi.ws import Client as WsClient
from lark_oapi.api.im.v1 import CreateMessageRequest, CreateMessageRequestBody
from lark_oapi import MessageType

def send_message(open_id: str, text: str):
    client = ApiClient.builder().app_id(APP_ID).app_secret(APP_SECRET).build()
    req = CreateMessageRequest.builder() \
        .receive_id_type("open_id") \
        .request_body(CreateMessageRequestBody.builder()
                      .receive_id(open_id)
                      .msg_type(MessageType.TEXT)
                      .content(json.dumps({"text": text}))
                      .build()) \
        .build()
    resp = client.im.v1.message.create(req)
    if resp.success():
        logger.info(f"✅ 回复成功: {text[:30]}")
    else:
        logger.error(f"❌ 回复失败: {resp.msg}")

# 定义事件处理器（根据 ws.Client 要求）
class MyHandler:
    def on_message(self, message):
        """接收并处理飞书推送的消息"""
        logger.info(f"收到原始消息: {message}")
        try:
            if isinstance(message, dict):
                event = message.get("event")
                if event and event.get("type") == "p2_message_receive_v1":
                    content = json.loads(event["message"]["content"])
                    text = content.get("text", "")
                    sender_id = event["sender"]["sender_id"]["open_id"]
                    logger.info(f"用户 {sender_id} 说: {text}")
                    reply = f"收到：{text}"
                    send_message(sender_id, reply)
        except Exception as e:
            logger.error(f"处理消息异常: {e}")

    def on_error(self, error):
        logger.error(f"WebSocket 错误: {error}")

def main():
    logger.info("启动飞书长连接机器人（ws.Client 模式）...")
    handler = MyHandler()
    ws_client = WsClient(APP_ID, APP_SECRET, handler)
    ws_client.start()
    try:
        import time
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("停止机器人")
        ws_client.stop()

if __name__ == "__main__":
    main()