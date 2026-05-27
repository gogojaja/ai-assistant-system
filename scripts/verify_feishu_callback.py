#!/usr/bin/env python3
"""
模块名称：verify_feishu_callback
功能描述：验证飞书回调服务本地健康和公网隧道连通性
对外接口：
    - 直接运行，输出本地 /health 和公网 /webhook 验证结果
依赖：
    - 标准库：os, json, logging, subprocess, re, time
    - 第三方：requests
版本：v1.0
更新记录：
    - 2026-05-25: 初始创建，新增回调连通性自动验证
"""

import json
import logging
import re
import subprocess
import time
from pathlib import Path

import requests

logging.basicConfig(level=logging.INFO, format='[FEISHU VERIFY] %(message)s')
logger = logging.getLogger(__name__)

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent


def get_local_health() -> bool:
    url = "http://127.0.0.1:5001/health"
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200 and resp.json().get("status") == "ok":
            logger.info("本地回调服务 /health 可达")
            return True
        logger.warning(f"本地 /health 返回异常: {resp.status_code} {resp.text}")
        return False
    except Exception as e:
        logger.error(f"本地 /health 连接失败: {e}")
        return False


def get_public_webhook_url() -> str | None:
    script = PROJECT_ROOT / "scripts" / "get_tunnel_url.sh"
    if not script.exists():
        logger.error("未找到 get_tunnel_url.sh，请先检查隧道配置")
        return None
    try:
        result = subprocess.run(["bash", str(script)], capture_output=True, text=True, timeout=10)
        output = result.stdout.strip()
        if result.returncode != 0:
            logger.warning(f"获取隧道地址脚本返回非零: {result.returncode}")
        match = re.search(r"https://[a-z0-9-]+\.trycloudflare\.com", output)
        if match:
            webhook_url = f"{match.group(0)}/webhook"
            logger.info(f"检测到公网回调地址: {webhook_url}")
            return webhook_url
        logger.error("未从隧道日志中解析到公网地址，请确认 cloudflared 已正常运行")
        return None
    except Exception as e:
        logger.error(f"执行 get_tunnel_url.sh 失败: {e}")
        return None


def verify_public_webhook(webhook_url: str) -> bool:
    payload = {
        "schema": "2.0",
        "header": {
            "event_type": "im.message.receive_v1",
            "event_id": f"verify-public-{int(time.time())}",
            "create_time": str(int(time.time() * 1000)),
            "token": "verify-token"
        },
        "event": {
            "message": {
                "message_id": "msg_verify_001",
                "message_type": "text",
                "content": json.dumps({"text": "【回调验证】公网 /webhook 可达测试"})
            },
            "sender": {
                "sender_id": {
                    "open_id": "ou_84b0c82ab02e6aa3c78d42741710ee91"
                }
            }
        }
    }
    try:
        resp = requests.post(webhook_url, json=payload, headers={"Content-Type": "application/json"}, timeout=20)
        if resp.status_code == 200:
            logger.info("公网 /webhook 请求成功返回 200")
            logger.info(f"响应内容: {resp.text}")
            return True
        logger.warning(f"公网 /webhook 返回异常: {resp.status_code} {resp.text}")
        return False
    except Exception as e:
        logger.error(f"公网 /webhook 请求失败: {e}")
        return False


if __name__ == "__main__":
    logger.info("开始飞书回调连通性验证")
    local_ok = get_local_health()
    public_url = get_public_webhook_url()
    if public_url:
        public_ok = verify_public_webhook(public_url)
    else:
        public_ok = False

    logger.info("验证结果：")
    logger.info(f"  本地 /health: {'成功' if local_ok else '失败'}")
    logger.info(f"  公网 /webhook: {'成功' if public_ok else '失败'}")
    if local_ok and public_ok:
        logger.info("飞书回调本地与公网连通性验证通过")
    else:
        logger.warning("飞书回调验证未完全通过，请根据上方提示排查")
