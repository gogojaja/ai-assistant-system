#!/usr/bin/env python3
"""
模块名称：feishu_bot
功能描述：飞书 Bot 模块，通过 REST API 获取 tenant_access_token、发送消息，通过 WebSocket 长连接实时监听并处理消息
对外接口：
    - get_tenant_access_token(): 获取企业访问令牌，返回 token 字符串或 None
    - send_message(receive_id, msg_type, content): 发送消息给指定用户，返回发送结果字典
    - listen_messages(callback): 启动 WebSocket 长连接，收到消息时调用 callback 并可选回复
依赖：
    - 标准库：json, logging, os
    - 第三方：requests, python-dotenv, websocket-client
    - 项目内：无
版本：v1.0
更新记录：
    - 2026-05-23: 自动添加统一注释头，补充功能描述
"""

import os
import json
import logging
import requests
from dotenv import load_dotenv

logging.basicConfig(level=logging.DEBUG, format='[%(levelname)s] %(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

# 显式加载 .env 文件
env_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(env_path)
logger.debug(f"加载 .env 文件: {env_path}")

APP_ID = os.environ.get("FEISHU_APP_ID", "")
APP_SECRET = os.environ.get("FEISHU_APP_SECRET", "")
logger.debug(f"APP_ID: {APP_ID[:10]}...")
logger.debug(f"APP_SECRET 长度: {len(APP_SECRET)}")

BASE_URL = "https://open.feishu.cn/open-apis"


def get_tenant_access_token():
    """获取企业访问令牌"""
    url = f"{BASE_URL}/auth/v3/tenant_access_token/internal"
    body = {"app_id": APP_ID, "app_secret": APP_SECRET}
    
    logger.debug(f"请求 token，body: app_id={APP_ID[:10]}...")
    resp = requests.post(url, json=body, timeout=10)
    data = resp.json()
    
    if data.get("code") != 0:
        logger.error(f"获取 token 失败：{data}")
        return None
    
    token = data["tenant_access_token"]
    logger.debug(f"token 获取成功: {token[:10]}...")
    return token


def send_message(receive_id, msg_type, content, receive_id_type="open_id"):
    """发送消息给用户或群聊"""
    token = get_tenant_access_token()
    if not token:
        return {"success": False, "message_id": None}
    
    url = f"{BASE_URL}/im/v1/messages"
    url += f"?receive_id_type={receive_id_type}"
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    if msg_type == "text":
        body = {
            "receive_id": receive_id,
            "msg_type": "text",
            "content": json.dumps({"text": content})
        }
    else:
        return {"success": False, "message_id": None}
    
    logger.debug(f"发送消息给 {receive_id}({receive_id_type}): {content[:50]}...")
    resp = requests.post(url, headers=headers, json=body, timeout=10)
    data = resp.json()
    
    if data.get("code") != 0:
        logger.error(f"发送失败：{data}")
        return {"success": False, "message_id": None}
    
    message_id = data.get("data", {}).get("message_id", "")
    logger.debug(f"发送成功，message_id: {message_id}")
    return {"success": True, "message_id": message_id}


def listen_messages(callback):
    """启动 WebSocket 长连接，监听收到的消息"""
    token = get_tenant_access_token()
    if not token:
        logger.error("无法获取 token，长连接启动失败")
        return
    
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.post(
        f"{BASE_URL}/event/v1/ws/open",
        headers=headers,
        json={"ping_interval": 30},
        timeout=10
    )
    data = resp.json()
    
    if data.get("code") != 0:
        logger.error(f"获取 WS 地址失败：{data}")
        return
    
    ws_url = data.get("data", {}).get("url", "")
    ws_token = data.get("data", {}).get("token", "")
    logger.debug(f"WS 地址获取成功")
    
    import websocket
    
    def on_open(ws):
        logger.debug("WebSocket 连接已建立")
    
    def on_message(ws, message):
        try:
            event = json.loads(message)
            event_type = event.get("header", {}).get("event_type", "")
            
            if event_type == "im.message.receive_v1":
                msg_data = event.get("event", {}).get("message", {})
                sender_data = event.get("event", {}).get("sender", {})
                sender_id = sender_data.get("sender_id", {}).get("open_id", "")
                msg_type = msg_data.get("message_type", "")
                
                logger.debug(f"收到消息: type={msg_type}, sender={sender_id}")
                
                if msg_type == "text":
                    content = json.loads(msg_data.get("content", "{}"))
                    text = content.get("text", "")
                    
                    if text and callback:
                        reply = callback(event_type, sender_id, text, {})
                        if reply:
                            send_message(sender_id, "text", reply)
                            
        except Exception as e:
            logger.error(f"处理消息出错：{e}")
    
    def on_close(ws, status, msg):
        logger.debug(f"WebSocket 断开: {status}")
    
    ws_app = websocket.WebSocketApp(
        f"{ws_url}?token={ws_token}",
        on_open=on_open,
        on_message=on_message,
        on_close=on_close
    )
    
    logger.info("飞书 Bot 开始监听消息...")
    ws_app.run_forever()


if __name__ == "__main__":
    print("飞书 Bot 模块测试")
    token = get_tenant_access_token()
    if token:
        print("✅ token 获取成功")
    else:
        print("❌ token 获取失败，请检查 App ID 和 Secret")