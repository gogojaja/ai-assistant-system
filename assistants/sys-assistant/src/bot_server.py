"""
模块名称：bot_server
功能描述：5号AI 系统管理助手 — 独立飞书 Bot Webhook 服务（端口 5003）
对外接口：
    - Flask 应用：/webhook (POST), /health (GET)
依赖：
    - 标准库：os, sys, json, logging, threading, pathlib
    - 第三方：flask, python-dotenv
    - 项目内：shared.feishu_api, sys_assistant.src.__init__ (process)
版本：v1.0
更新记录：
    - 2026-05-26: 初始创建，独立 Bot 服务与主回调完全隔离
"""
import os
import sys
import json
import logging
import threading
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
SYS_SRC = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "shared"))
sys.path.insert(0, str(SYS_SRC))

BOT_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = BOT_DIR / ".env"

from dotenv import load_dotenv
load_dotenv(ENV_PATH, override=True)

os.environ.setdefault("FEISHU_APP_ID", os.getenv("FEISHU_APP_ID", ""))
os.environ.setdefault("FEISHU_APP_SECRET", os.getenv("FEISHU_APP_SECRET", ""))

from flask import Flask, request, jsonify
from feishu_api import send_message

import importlib.util
_spec = importlib.util.spec_from_file_location("sys_assistant_init", str(SYS_SRC / "__init__.py"))
_sys_mod = importlib.util.module_from_spec(_spec)
_sys_mod.__file__ = str(SYS_SRC / "__init__.py")
_sys_mod.__package__ = None
_sys_mod.__name__ = "sys_assistant_init"
sys.modules["sys_assistant_init"] = _sys_mod
_spec.loader.exec_module(_sys_mod)
process_sys_command = _sys_mod.process

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(str(PROJECT_ROOT / "logs" / "sys_bot.log"), encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger("sys_bot")

app = Flask(__name__)
app.config["JSON_AS_ASCII"] = False


@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()
    if not data:
        return jsonify({"code": 400, "msg": "empty body"}), 400

    # 飞书 URL 验证 — 兼容 schema 1.0 和 2.0
    challenge = data.get("challenge") or (data.get("event") or {}).get("challenge")
    event_type = data.get("header", {}).get("event_type", data.get("type", ""))
    if challenge or event_type == "url_verification" or event_type == "event_callback_url_verification":
        logger.info(f"URL 验证请求: type={event_type}")
        if challenge:
            return jsonify({"challenge": challenge})
        return jsonify({"challenge": "ok"})

    threading.Thread(target=handle_event, args=(data,)).start()
    return jsonify({"code": 0, "msg": "success"}), 200


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "bot": "sys-assistant"}), 200


def handle_event(data: dict):
    if data.get("schema") == "2.0":
        event_type = data.get("header", {}).get("event_type")
        event = data.get("event", {})
    else:
        event_type = data.get("type")
        event = data.get("event", {})

    if event_type != "im.message.receive_v1":
        return

    message = event.get("message", {})
    message_type = message.get("message_type")
    content_str = message.get("content", "{}")
    message_id = message.get("message_id")
    sender = event.get("sender", {})
    open_id = sender.get("sender_id", {}).get("open_id")
    if not open_id:
        open_id = message.get("sender", {}).get("sender_id", {}).get("open_id")
    if not open_id:
        logger.warning("无法获取发送者 open_id")
        return

    chat_id = message.get("chat_id") or message.get("open_chat_id") or event.get("open_chat_id")
    target_id = chat_id if chat_id else open_id
    receive_id_type = "chat_id" if chat_id else "open_id"

    if message_type == "text":
        try:
            content = json.loads(content_str)
            user_text = content.get("text", "")
        except:
            user_text = ""

        if not user_text:
            return

        logger.info(f"[TEXT] {open_id}: {user_text[:80]}")

        text = user_text.strip()
        if text.startswith("#5 "):
            text = text[3:].strip()
        elif text.startswith("#sys "):
            text = text[4:].strip()
        elif text == "#5" or text == "#sys":
            text = ""

        reply = process_sys_command(text, open_id)
        if reply:
            send_message(target_id, reply, receive_id_type=receive_id_type)

    elif message_type == "file":
        send_message(target_id, "❌ 本助手不支持文件消息，请发送文字命令。\n输入 help 查看可用命令。",
                     receive_id_type=receive_id_type)

    elif message_type == "image":
        send_message(target_id, "❌ 本助手不支持图片消息，请发送文字命令。\n输入 help 查看可用命令。",
                     receive_id_type=receive_id_type)

    elif message_type == "audio":
        send_message(target_id, "❌ 本助手不支持语音消息，请发送文字命令。",
                     receive_id_type=receive_id_type)

    else:
        logger.info(f"忽略消息类型: {message_type}")


if __name__ == "__main__":
    port = int(os.getenv("SYS_BOT_PORT", "5003"))
    logger.info(f"启动5号系统管理助手服务，端口 {port}")
    app.run(host="0.0.0.0", port=port, debug=False)
