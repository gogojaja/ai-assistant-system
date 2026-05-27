#!/usr/bin/env python3

"""
模块名称：feishu_api
功能描述：飞书开放平台 API 封装（获取 token、发送消息、下载/上传文件）
对外接口：
    - get_tenant_access_token(): 获取并缓存 tenant_access_token
    - send_message(open_id, text): 发送文本消息到指定用户
    - send_file_message(receive_id, file_path, file_name, receive_id_type): 发送文件消息
    - download_file(message_id, file_key, save_path): 下载飞书文件到本地
依赖：
    - 标准库：os, json, logging, time, pathlib
    - 第三方：requests, python-dotenv
    - 项目内：无
版本：v2.0
更新记录：
    - 2026-05-26: 新增 send_file_message，支持上传并发送文件到飞书
    - 2026-05-23: 初始创建，从 callback_server.py 剥离飞书 API 相关函数
"""
import os
import json
import logging
import time
from pathlib import Path

import requests
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

def _load_feishu_env():
    """尝试加载项目中常见的 Feishu 环境变量文件。"""
    env_paths = [
        os.path.join(os.getcwd(), '.env'),
        os.path.join(os.path.dirname(__file__), '.env'),
        os.path.join(os.getcwd(), 'shared', 'feishu-bot', '.env')
    ]
    for env_path in env_paths:
        if os.path.exists(env_path):
            load_dotenv(env_path, override=False)
            logger.debug(f"加载 Feishu 环境变量文件: {env_path}")

_load_feishu_env()

_token_cache = {"token": None, "expires_at": 0}


def get_tenant_access_token():
    """获取飞书 tenant_access_token，自动缓存并刷新"""
    _load_feishu_env()
    now = time.time()
    if _token_cache["token"] and _token_cache["expires_at"] > now + 60:
        return _token_cache["token"]
    app_id = os.getenv("FEISHU_APP_ID")
    app_secret = os.getenv("FEISHU_APP_SECRET")
    if not app_id or not app_secret:
        logger.error("缺少 FEISHU_APP_ID 或 FEISHU_APP_SECRET，无法获取 token")
        return None
    url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
    try:
        resp = requests.post(url, json={"app_id": app_id, "app_secret": app_secret}, timeout=10)
        if resp.status_code != 200:
            logger.error(f"获取 token 失败: {resp.text}")
            return None
        data = resp.json()
        if data.get("code") != 0:
            logger.error(f"获取 token 错误: {data}")
            return None
        token = data["tenant_access_token"]
        expire = data["expire"]
        _token_cache["token"] = token
        _token_cache["expires_at"] = now + expire
        logger.info("获取 token 成功")
        return token
    except Exception as e:
        logger.error(f"获取 token 异常: {e}")
        return None


def send_message(receive_id: str, text: str, receive_id_type: str = "open_id"):
    """
    发送消息到指定飞书目标。
    支持纯文本和飞书互动卡片（传入 dict 含 type='card'）。
    receive_id_type 可以是 open_id 或 chat_id。
    返回 message_id (str) 或 None。
    """
    if not text or (isinstance(text, str) and not text.strip()):
        logger.warning("拒绝发送空消息")
        return None
    token = get_tenant_access_token()
    if not token:
        return None
    url = "https://open.feishu.cn/open-apis/im/v1/messages"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json; charset=utf-8"
    }
    params = {"receive_id_type": receive_id_type}

    safe_text = str(text) if not isinstance(text, dict) else ""
    if isinstance(text, dict) and text.get("type") == "card":
        msg_type = "interactive"
        content_json = json.dumps(text["card"], ensure_ascii=False)
    else:
        msg_type = "text"
        if len(safe_text) > 4900:
            safe_text = safe_text[:4900] + "…"
        content_json = json.dumps({"text": safe_text}, ensure_ascii=False)

    payload = {
        "receive_id": receive_id,
        "msg_type": msg_type,
        "content": content_json
    }
    try:
        resp = requests.post(
            url,
            headers=headers,
            params=params,
            data=json.dumps(payload, ensure_ascii=False).encode('utf-8'),
            timeout=10
        )
        if resp.status_code != 200:
            logger.error(f"发送消息 HTTP 错误: {resp.status_code}")
            return None
        data = resp.json()
        if data.get("code") != 0:
            logger.error(f"发送消息 API 错误: {data}")
            return None
        msg_id = data.get("data", {}).get("message_id")
        preview = safe_text[:50] if safe_text else "(card)"
        logger.info(f"回复成功: {preview} (msg_id={msg_id})")
        return msg_id
    except Exception as e:
        logger.error(f"发送消息异常: {e}")
        return None


def update_message(message_id: str, text: str) -> bool:
    """
    更新已发送的飞书消息（替换内容，用于"正在思考"→真正回复）。
    返回 True/False。
    """
    if not message_id or not text:
        return False
    token = get_tenant_access_token()
    if not token:
        return False
    url = f"https://open.feishu.cn/open-apis/im/v1/messages/{message_id}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    safe_text = str(text)
    if len(safe_text) > 4900:
        safe_text = safe_text[:4900] + "…"
    payload = {
        "content": json.dumps({"text": safe_text}, ensure_ascii=False),
        "msg_type": "text"
    }
    try:
        resp = requests.patch(url, headers=headers, json=payload, timeout=10)
        if resp.status_code == 200:
            logger.info(f"更新消息成功: {message_id}")
            return True
        logger.warning(f"更新消息失败: {resp.status_code} - {resp.text}")
        return False
    except Exception as e:
        logger.error(f"更新消息异常: {e}")
        return False


def send_card_message(receive_id: str, card: dict, receive_id_type: str = "open_id"):
    """发送飞书互动卡片消息"""
    if not card or not isinstance(card, dict):
        logger.warning("拒绝发送空卡片消息")
        return False
    token = get_tenant_access_token()
    if not token:
        return False
    url = "https://open.feishu.cn/open-apis/im/v1/messages"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json; charset=utf-8"
    }
    params = {"receive_id_type": receive_id_type}
    payload = {
        "receive_id": receive_id,
        "msg_type": "interactive",
        "content": json.dumps({"card": card}, ensure_ascii=False)
    }
    try:
        resp = requests.post(
            url,
            headers=headers,
            params=params,
            json=payload,
            timeout=10
        )
        if resp.status_code != 200:
            logger.error(f"发送卡片消息 HTTP 错误: {resp.status_code} - {resp.text}")
            return False
        data = resp.json()
        if data.get("code") != 0:
            logger.error(f"发送卡片消息 API 错误: {data}")
            return False
        logger.info("卡片消息发送成功")
        return True
    except Exception as e:
        logger.error(f"发送卡片消息异常: {e}")
        return False


def send_file_message(receive_id: str, file_path: str, file_name: str = "", receive_id_type: str = "open_id") -> bool:
    """上传本地文件到飞书并发送文件消息，返回是否成功"""
    token = get_tenant_access_token()
    if not token:
        return False
    if not file_name:
        file_name = Path(file_path).name

    # 步骤1：上传文件
    upload_url = "https://open.feishu.cn/open-apis/im/v1/files"
    headers = {"Authorization": f"Bearer {token}"}
    try:
        with open(file_path, 'rb') as f:
            resp = requests.post(
                upload_url,
                headers=headers,
                files={'file': (file_name, f, 'application/octet-stream')},
                data={'file_type': 'stream', 'file_name': file_name},
                timeout=60
            )
        if resp.status_code != 200:
            logger.error(f"上传文件失败: {resp.status_code} - {resp.text}")
            return False
        data = resp.json()
        if data.get("code") != 0:
            logger.error(f"上传文件 API 错误: {data}")
            return False
        file_key = data.get("data", {}).get("file_key")
        if not file_key:
            logger.error("上传文件未返回 file_key")
            return False
        logger.info(f"文件上传成功: {file_name} -> file_key={file_key}")
    except Exception as e:
        logger.error(f"上传文件异常: {e}")
        return False

    # 步骤2：发送文件消息
    msg_url = "https://open.feishu.cn/open-apis/im/v1/messages"
    params = {"receive_id_type": receive_id_type}
    content_json = json.dumps({"file_key": file_key, "file_name": file_name}, ensure_ascii=False)
    payload = {
        "receive_id": receive_id,
        "msg_type": "file",
        "content": content_json
    }
    try:
        resp = requests.post(
            msg_url,
            headers={**headers, "Content-Type": "application/json; charset=utf-8"},
            params=params,
            data=json.dumps(payload, ensure_ascii=False).encode('utf-8'),
            timeout=30
        )
        if resp.status_code != 200:
            logger.error(f"发送文件消息 HTTP 错误: {resp.status_code} - {resp.text}")
            return False
        data = resp.json()
        if data.get("code") != 0:
            logger.error(f"发送文件消息 API 错误: {data}")
            return False
        logger.info(f"文件消息发送成功: {file_name}")
        return True
    except Exception as e:
        logger.error(f"发送文件消息异常: {e}")
        return False


def download_file(message_id: str, file_key: str, save_path: str) -> bool:
    """下载飞书文件到本地，返回是否成功"""
    token = get_tenant_access_token()
    if not token:
        return False
    url = f"https://open.feishu.cn/open-apis/im/v1/messages/{message_id}/resources/{file_key}"
    headers = {"Authorization": f"Bearer {token}"}
    params = {"type": "file"}
    try:
        resp = requests.get(url, headers=headers, params=params, stream=True)
        if resp.status_code != 200:
            logger.error(f"下载文件失败: {resp.status_code} - {resp.text}")
            return False
        with open(save_path, 'wb') as f:
            for chunk in resp.iter_content(chunk_size=8192):
                f.write(chunk)
        logger.info(f"文件已保存: {save_path}")
        return True
    except Exception as e:
        logger.error(f"下载文件异常: {e}")
        return False
