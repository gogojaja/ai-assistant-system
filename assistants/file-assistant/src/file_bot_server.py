import os
import sys
import json
import logging
import threading
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
FILE_SRC = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "shared"))
sys.path.insert(0, str(FILE_SRC))

BOT_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = BOT_DIR / ".env"

from dotenv import load_dotenv
load_dotenv(ENV_PATH, override=True)

os.environ.setdefault("FEISHU_APP_ID", os.getenv("FEISHU_APP_ID", ""))
os.environ.setdefault("FEISHU_APP_SECRET", os.getenv("FEISHU_APP_SECRET", ""))

from flask import Flask, request, jsonify

from feishu_api import send_message, download_file
import importlib.util
_spec = importlib.util.spec_from_file_location("file_assistant_init", str(FILE_SRC / "__init__.py"))
_file_mod = importlib.util.module_from_spec(_spec)
_file_mod.__file__ = str(FILE_SRC / "__init__.py")
_file_mod.__package__ = None
_file_mod.__name__ = "file_assistant_init"
sys.modules["file_assistant_init"] = _file_mod
_spec.loader.exec_module(_file_mod)
process_file_command = _file_mod.process
from file_manager import format_size

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(str(PROJECT_ROOT / "logs" / "file_bot.log"), encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger("file_bot")

app = Flask(__name__)
app.config["JSON_AS_ASCII"] = False

PENDING_UPLOADS = {}


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
    return jsonify({"status": "ok", "bot": "file-assistant"}), 200


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
        if text.startswith("#4 "):
            text = text[3:].strip()
        elif text.startswith("#file "):
            text = text[5:].strip()

        if text.startswith("上传"):
            context = {
                "target_id": target_id,
                "receive_id_type": receive_id_type,
                "upload_callback": _do_upload,
            }
            reply = process_file_command(text, open_id, context)
        elif text == "帮助" or text == "？" or text == "?" or not text:
            reply = process_file_command("帮助", open_id)
        else:
            reply = process_file_command(text, open_id)
        if reply:
            send_message(target_id, reply, receive_id_type=receive_id_type)

    elif message_type == "file":
        try:
            content = json.loads(content_str)
            file_key = content.get("file_key")
            file_name = content.get("file_name", "unknown_file")
        except:
            file_key = None
            file_name = "unknown_file"

        if file_key:
            logger.info(f"[FILE] {file_name} from {open_id}")
            PENDING_UPLOADS[open_id] = {
                "file_key": file_key,
                "message_id": message_id,
                "file_name": file_name,
            }
            reply = (
                f"📎 已收到文件：{file_name}\n"
                f"如需保存，请输入：\n"
                f"  上传        保存到默认目录\n"
                f"  上传 <路径>  保存到指定目录"
            )
            send_message(target_id, reply, receive_id_type=receive_id_type)
        else:
            logger.warning("文件消息缺少 file_key")

    elif message_type == "image":
        try:
            content = json.loads(content_str)
            image_key = content.get("image_key")
        except:
            image_key = None

        if image_key:
            logger.info(f"[IMAGE] from {open_id}, key={image_key}")
            PENDING_UPLOADS[open_id] = {
                "file_key": image_key,
                "message_id": message_id,
                "file_name": f"image_{image_key[:8]}.png",
                "is_image": True,
            }
            reply = (
                f"🖼️ 已收到图片\n"
                f"如需保存，请输入：\n"
                f"  上传        保存到默认目录\n"
                f"  上传 <路径>  保存到指定目录"
            )
            send_message(target_id, reply, receive_id_type=receive_id_type)
        else:
            logger.warning("图片消息缺少 image_key")

    elif message_type == "audio":
        send_message(target_id, "❌ 本助手不支持语音消息，请发送文字命令或文件。", receive_id_type=receive_id_type)

    else:
        logger.info(f"忽略消息类型: {message_type}")


def _do_upload(open_id: str, target_path: str = None) -> str:
    if open_id not in PENDING_UPLOADS:
        return "❌ 没有待处理的文件，请先发送飞书文件给我"

    info = PENDING_UPLOADS.pop(open_id)
    file_key = info["file_key"]
    message_id = info["message_id"]
    file_name = info["file_name"]
    is_image = info.get("is_image", False)

    if target_path:
        target_path = os.path.expanduser(target_path.strip().strip("'\""))
        save_path = os.path.join(target_path, file_name) if os.path.isdir(target_path) else target_path
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
    else:
        save_dir = os.path.expanduser("~/ai-assistant-system/data/file-assistant/uploads")
        os.makedirs(save_dir, exist_ok=True)
        save_path = os.path.join(save_dir, file_name)
        counter = 1
        base, ext = os.path.splitext(save_path)
        while os.path.exists(save_path):
            save_path = f"{base}_{counter}{ext}"
            counter += 1

    if is_image:
        success = _download_image(message_id, file_key, save_path)
    else:
        success = download_file(message_id, file_key, save_path)
    if success:
        size = format_size(os.path.getsize(save_path))
        return f"✅ 文件已保存\n  位置：{save_path}\n  大小：{size}"
    else:
        return "❌ 文件下载失败，请重新发送"


def _download_image(message_id: str, image_key: str, save_path: str) -> bool:
    from feishu_api import get_tenant_access_token
    import requests
    token = get_tenant_access_token()
    if not token:
        return False
    url = f"https://open.feishu.cn/open-apis/im/v1/messages/{message_id}/resources/{image_key}"
    headers = {"Authorization": f"Bearer {token}"}
    params = {"type": "image"}
    try:
        resp = requests.get(url, headers=headers, params=params, stream=True, timeout=30)
        if resp.status_code != 200:
            logger.error(f"下载图片失败: HTTP {resp.status_code}")
            return False
        with open(save_path, "wb") as f:
            for chunk in resp.iter_content(chunk_size=8192):
                f.write(chunk)
        logger.info(f"图片已保存: {save_path}")
        return True
    except Exception as e:
        logger.error(f"下载图片异常: {e}")
        return False


if __name__ == "__main__":
    port = int(os.getenv("FILE_BOT_PORT", "5002"))
    logger.info(f"启动4号文件助手服务，端口 {port}")
    app.run(host="0.0.0.0", port=port, debug=False)
