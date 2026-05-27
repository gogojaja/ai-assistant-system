#!/usr/bin/env python3

"""
模块名称：callback_server
功能描述：飞书回调服务主入口，负责接收 webhook 事件并分派给处理器
对外接口：
    - Flask 应用：/webhook (POST), /health (GET)
依赖：
    - 标准库：os, sys, json, logging, threading
    - 第三方：flask, python-dotenv
    - 项目内：shared.feishu_api (无直接调用，但被各处理器使用),
               assistants.chat-assistant.src.message_handler (process_message),
               assistants.chat-assistant.src.voice_handler (process_voice_message),
               assistants.office-assistant.src.document_handler (process_document_file)
版本：v1.0
更新记录：
    - 2026-05-23: 重构，剥离附加功能到独立模块，仅保留路由和事件分派
"""
import os
import sys
import json
import logging
import threading
from pathlib import Path

from flask import Flask, request, jsonify, Response
import requests

# 项目根路径
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "assistants/chat-assistant/src"))
sys.path.insert(0, str(PROJECT_ROOT / "assistants/office-assistant/src"))
sys.path.insert(0, str(PROJECT_ROOT / "assistants"))

# 加载环境变量（飞书凭证）
from dotenv import load_dotenv
env_path = PROJECT_ROOT / "shared/feishu-bot/.env"
load_dotenv(env_path)

# 日志配置
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 导入处理器
try:
    from assistants.chat_assistant.src.message_handler import process_message
    from assistants.chat_assistant.src.voice_handler import process_voice_message
    from assistants.office_assistant.src.document_handler import process_document_file
    logger.info("所有处理器加载成功")
except ImportError as e:
    logger.error(f"处理器导入失败: {e}")
    def process_message(*args, **kwargs): pass
    def process_voice_message(*args, **kwargs): pass
    def process_document_file(*args, **kwargs): pass

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False

# 注册看板
from dashboard import dashboard_bp
app.register_blueprint(dashboard_bp)


@app.route("/webhook_chat", methods=["POST"])
@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()
    if not data:
        return jsonify({"code": 400, "msg": "empty body"}), 400
    if "challenge" in data:
        return jsonify({"challenge": data["challenge"]})
    threading.Thread(target=handle_event, args=(data,)).start()
    return jsonify({"code": 0, "msg": "success"}), 200


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"}), 200


BACKENDS = {
    "/webhook_file": ("http://127.0.0.1:5102", "/webhook"),
    "/webhook_sys":  ("http://127.0.0.1:5103", "/webhook"),
    "/health_file":  ("http://127.0.0.1:5102", "/health"),
    "/health_sys":   ("http://127.0.0.1:5103", "/health"),
}


@app.route("/webhook_file", methods=["POST"])
@app.route("/webhook_sys", methods=["POST"])
@app.route("/health_file", methods=["GET"])
@app.route("/health_sys", methods=["GET"])
def proxy_backend():
    path = request.path
    backend, target_path = BACKENDS.get(path, (None, None))
    if not backend:
        return jsonify({"code": 404, "msg": "no route"}), 404
    target_url = f"{backend}{target_path}"
    headers = {k: v for k, v in request.headers if k.lower() not in ("host", "content-length")}
    try:
        resp = requests.request(
            method=request.method,
            url=target_url,
            headers=headers,
            data=request.get_data(),
            params=request.args,
            timeout=30,
        )
        return Response(
            resp.content,
            status=resp.status_code,
            headers={k: v for k, v in resp.headers.items() if k.lower() not in ("transfer-encoding",)},
        )
    except requests.ConnectionError:
        logger.error(f"后端连接失败: {target_url}")
        return jsonify({"code": 502, "msg": f"backend unreachable"}), 502
    except requests.Timeout:
        logger.error(f"后端超时: {target_url}")
        return jsonify({"code": 504, "msg": "backend timeout"}), 504
    except Exception as e:
        logger.error(f"代理异常: {e}")
        return jsonify({"code": 500, "msg": str(e)}), 500


def handle_event(data: dict):
    """解析飞书事件，分派到对应处理器"""
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

    if message_type == "text":
        try:
            content = json.loads(content_str)
            user_text = content.get("text", "")
        except:
            user_text = ""
        if user_text:
            chat_id = message.get("chat_id") or message.get("open_chat_id") or event.get("open_chat_id")
            target_id = chat_id if chat_id else open_id
            receive_id_type = "chat_id" if chat_id else "open_id"
            logger.info(f"📩 用户 {open_id} 在 {receive_id_type} {target_id} 说: {user_text}")
            # 2号AI 办公助理（前缀 #2 / #office）
            if user_text.startswith("#2 ") or user_text.startswith("#office ") or user_text == "#2" or user_text == "#office":
                from assistants.office_assistant.src.document_handler import process_office_text
                cmd = user_text[3:].strip() if user_text.startswith("#2") else user_text[7:].strip()
                process_office_text(cmd, open_id, target_id=target_id, receive_id_type=receive_id_type)
                return
            # 3号AI 日程健康助理（前缀 #3 / #life）
            if user_text.startswith("#3 ") or user_text.startswith("#life ") or user_text == "#3" or user_text == "#life":
                cmd = user_text
                for prefix in ["#3 ", "#life ", "#3", "#life"]:
                    if cmd.startswith(prefix):
                        cmd = cmd[len(prefix):].strip()
                        break
                from life_assistant.src import process as process_life
                import yaml
                try:
                    cfg = yaml.safe_load((PROJECT_ROOT / "config" / "settings.yaml").read_text())
                    dash_url = cfg.get("dashboard_url", "")
                except Exception:
                    dash_url = ""
                reply = process_life(cmd, dashboard_url=dash_url)
                from shared.feishu_api import send_message
                if reply:
                    send_message(target_id, reply, receive_id_type=receive_id_type)
                return
            # 默认走 1号AI 闲聊处理
            process_message(user_text, target_id, open_id=open_id, receive_id_type=receive_id_type)

    elif message_type == "audio":
        try:
            content = json.loads(content_str)
            file_key = content.get("file_key")
        except:
            file_key = None
        if file_key:
            logger.info(f"🎤 收到语音消息 from {open_id}")
            threading.Thread(target=process_voice_message, args=(file_key, message_id, open_id)).start()
        else:
            logger.warning("语音消息缺少 file_key")

    elif message_type == "file":
        try:
            content = json.loads(content_str)
            file_key = content.get("file_key")
            file_name = content.get("file_name", "file.docx")
        except:
            file_key = None
            file_name = "file.docx"
        if file_key:
            logger.info(f"📎 收到文件消息 from {open_id}, file_name={file_name}")
            threading.Thread(target=process_document_file, args=(file_key, message_id, open_id, file_name)).start()
        else:
            logger.warning("文件消息缺少 file_key")

    else:
        logger.info(f"忽略消息类型: {message_type}")


if __name__ == "__main__":
    logger.info("🚀 启动飞书回调服务（模块化重构）")
    app.run(host="0.0.0.0", port=5101, debug=False)