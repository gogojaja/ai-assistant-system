import os
import json
import logging
import tempfile
from pathlib import Path

logger = logging.getLogger(__name__)

FEISHU_UPLOAD_DIR = os.path.expanduser("~/ai-assistant-system/data/file-assistant/uploads")
os.makedirs(FEISHU_UPLOAD_DIR, exist_ok=True)

DOWNLOAD_DIR = os.path.expanduser("~/ai-assistant-system/data/file-assistant/downloads")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)


def cmd_upload(file_key: str, message_id: str, filename: str = None) -> str:
    from shared.feishu_api import download_file
    save_name = filename or f"upload_{file_key}"
    save_path = os.path.join(FEISHU_UPLOAD_DIR, save_name)
    counter = 1
    base, ext = os.path.splitext(save_path)
    while os.path.exists(save_path):
        save_path = f"{base}_{counter}{ext}"
        counter += 1
    success = download_file(message_id, file_key, save_path)
    if success:
        size = os.path.getsize(save_path)
        from file_manager import format_size
        return f"✅ 文件上传成功\n  保存位置：{save_path}\n  文件大小：{format_size(size)}"
    else:
        return "❌ 文件上传失败，请检查飞书文件是否有效"


def cmd_download(path: str, target_id: str = None, receive_id_type: str = "open_id") -> str:
    if not os.path.exists(path):
        return f"❌ 路径不存在：{path}"
    if os.path.isdir(path):
        import shutil
        import tempfile
        dir_name = os.path.basename(path.rstrip("/")) or "download"
        archive_path = os.path.join(DOWNLOAD_DIR, f"{dir_name}.zip")
        counter = 1
        base, ext = os.path.splitext(archive_path)
        while os.path.exists(archive_path):
            archive_path = f"{base}_{counter}{ext}"
            counter += 1
        try:
            shutil.make_archive(archive_path.replace(".zip", ""), "zip", path)
            file_for_send = archive_path
        except Exception as e:
            return f"❌ 目录打包失败：{str(e)}"
    else:
        file_for_send = path
    if target_id:
        return _send_file_via_feishu(file_for_send, target_id, receive_id_type)
    else:
        from file_manager import format_size
        size = format_size(os.path.getsize(file_for_send))
        return f"📥 文件已就绪：{file_for_send}（{size}）\n提示：可发送 分享 <路径> 通过飞书发送"


def cmd_share(path: str, target_id: str = None, receive_id_type: str = "open_id") -> str:
    if not os.path.exists(path):
        return f"❌ 路径不存在：{path}"
    if os.path.isdir(path):
        import shutil
        dir_name = os.path.basename(path.rstrip("/")) or "share"
        archive_path = os.path.join(DOWNLOAD_DIR, f"{dir_name}_share.zip")
        counter = 1
        base, ext = os.path.splitext(archive_path)
        while os.path.exists(archive_path):
            archive_path = f"{base}_{counter}{ext}"
            counter += 1
        try:
            shutil.make_archive(archive_path.replace(".zip", ""), "zip", path)
            file_for_send = archive_path
        except Exception as e:
            return f"❌ 目录打包失败：{str(e)}"
    else:
        file_for_send = path
    if not target_id:
        return f"📤 文件已就绪：{file_for_send}\n提示：此命令需要指定接收目标"
    return _send_file_via_feishu(file_for_send, target_id, receive_id_type)


def _send_file_via_feishu(file_path: str, target_id: str, receive_id_type: str = "open_id") -> str:
    try:
        from shared.feishu_api import get_tenant_access_token
        token = get_tenant_access_token()
        if not token:
            return "❌ 获取飞书 Token 失败，无法发送文件"
        import requests
        url = "https://open.feishu.cn/open-apis/im/v1/files"
        headers = {"Authorization": f"Bearer {token}"}
        filename = os.path.basename(file_path)
        file_type = _get_feishu_file_type(filename)
        with open(file_path, "rb") as f:
            resp = requests.post(
                url,
                headers=headers,
                data={"file_type": file_type, "file_name": filename},
                files={"file": (filename, f)},
                timeout=60
            )
        if resp.status_code != 200:
            logger.error(f"飞书文件上传失败: HTTP {resp.status_code}, body={resp.text[:500]}")
            return f"❌ 文件上传到飞书失败：HTTP {resp.status_code}"
        data = resp.json()
        if data.get("code") != 0:
            return f"❌ 飞书上传 API 错误：{data.get('msg', '')}"
        file_key = data["data"]["file_key"]
        msg_url = "https://open.feishu.cn/open-apis/im/v1/messages"
        msg_params = {"receive_id_type": receive_id_type}
        msg_payload = {
            "receive_id": target_id,
            "msg_type": "file",
            "content": json.dumps({"file_key": file_key})
        }
        msg_resp = requests.post(
            msg_url,
            headers=headers,
            params=msg_params,
            json=msg_payload,
            timeout=10
        )
        if msg_resp.status_code != 200:
            logger.error(f"发送文件消息失败: HTTP {msg_resp.status_code}, body={msg_resp.text[:500]}")
            return f"❌ 发送文件消息失败：HTTP {msg_resp.status_code}"
        msg_data = msg_resp.json()
        if msg_data.get("code") != 0:
            return f"❌ 发送文件消息 API 错误：{msg_data.get('msg', '')}"
        from file_manager import format_size
        size = format_size(os.path.getsize(file_path))
        return f"✅ 文件已发送：{filename}（{size}）"
    except Exception as e:
        logger.error(f"发送文件异常: {e}")
        return f"❌ 发送文件失败：{str(e)}"


def _get_feishu_file_type(filename):
    ext = os.path.splitext(filename)[1].lower()
    type_map = {
        ".txt": "txt", ".md": "txt",
        ".py": "txt", ".js": "txt", ".ts": "txt",
        ".json": "txt", ".yaml": "txt", ".yml": "txt",
        ".xml": "txt", ".csv": "txt",
        ".jpg": "image", ".jpeg": "image", ".png": "image",
        ".gif": "image", ".bmp": "image", ".svg": "image",
        ".mp3": "opus", ".wav": "opus", ".flac": "opus",
        ".mp4": "stream", ".mov": "stream", ".avi": "stream",
        ".pdf": "pdf", ".doc": "doc", ".docx": "doc",
        ".xls": "xls", ".xlsx": "xls",
        ".ppt": "ppt", ".pptx": "ppt",
        ".zip": "file", ".tar": "file", ".gz": "file",
        ".7z": "file", ".rar": "file",
        ".sh": "file", ".py": "file", ".js": "file", ".ts": "file",
        ".json": "file", ".yaml": "file", ".yml": "file",
        ".csv": "file", ".xml": "file", ".md": "file", ".txt": "file",
        ".jpg": "file", ".jpeg": "file", ".png": "file", ".gif": "file",
        ".bmp": "file", ".svg": "file",
        ".mp3": "file", ".wav": "file", ".flac": "file",
        ".mp4": "file", ".mov": "file", ".avi": "file",
    }
    return type_map.get(ext, "file")
