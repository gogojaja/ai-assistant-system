"""
1号AI 飞书连接脚本（纯 HTTP 模式）
用 requests 直接调用飞书 API，零第三方 SDK 依赖
"""
import sys
import os
import json
import logging

sys.path.insert(0, os.path.dirname(__file__))
from chat import load_history, save_history
from search import search_web, search_archive, format_results

logging.basicConfig(level=logging.DEBUG, format='[%(levelname)s] %(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

from dotenv import load_dotenv
_env_path = os.path.join(os.path.dirname(__file__), '../../../shared/feishu-bot/.env')
load_dotenv(_env_path)

APP_ID = os.getenv("FEISHU_APP_ID")
APP_SECRET = os.getenv("FEISHU_APP_SECRET")
MODEL_NAME = "qwen2.5:7b"

import requests

BASE_URL = "https://open.feishu.cn/open-apis"


def get_tenant_token():
    """获取 tenant_access_token"""
    if not APP_ID or not APP_SECRET:
        logger.error("FEISHU_APP_ID 或 FEISHU_APP_SECRET 未配置，请检查 shared/feishu-bot/.env")
        return None
    try:
        resp = requests.post(
            f"{BASE_URL}/auth/v3/tenant_access_token/internal",
            json={"app_id": APP_ID, "app_secret": APP_SECRET},
            timeout=10
        )
        data = resp.json()
        if data.get("code") == 0:
            logger.debug("token 获取成功")
            return data["tenant_access_token"]
        else:
            logger.error(f"token 失败：{data}")
            return None
    except Exception as e:
        logger.error(f"token 请求异常：{e}")
        return None


def process_message(text):
    """处理消息，调用1号AI"""
    messages = load_history()

    if text.startswith("搜索"):
        keyword = text.replace("搜索", "", 1).strip()
        if not keyword:
            return "请指定搜索关键词"
        result = search_web(keyword)
        return format_results(result)

    if text.startswith("本地搜索") or text.startswith("查找"):
        keyword = text.replace("本地搜索", "", 1).replace("查找", "", 1).strip()
        if not keyword:
            return "请指定检索关键词"
        result = search_archive(keyword)
        if not result["found"]:
            return f"本地知识库未找到「{keyword}」"
        lines = [f"📂 找到 {len(result['results'])} 条匹配："]
        for r in result["results"]:
            lines.append(f"  [{r['timestamp']}] {r['query']}")
        return "\n".join(lines)

    if text == "clear":
        from chat import clear_history
        return clear_history()

    messages.append({"role": "user", "content": text})
    import ollama
    response = ollama.chat(model=MODEL_NAME, messages=messages)
    reply = response["message"]["content"]
    messages.append({"role": "assistant", "content": reply})
    save_history(messages)
    return reply


def list_messages():
    """获取机器人最近收到的消息列表"""
    token = get_tenant_token()
    if not token:
        logger.error("无 token")
        return []

    headers = {"Authorization": f"Bearer {token}"}
    params = {"page_size": 5, "sort_type": "ByCreateTimeAsc"}
    
    try:
        resp = requests.get(
            f"{BASE_URL}/im/v1/messages",
            headers=headers,
            params=params,
            timeout=10
        )
        data = resp.json()
        if data.get("code") == 0:
            items = data.get("data", {}).get("items", [])
            logger.debug(f"获取到 {len(items)} 条消息")
            return items
        else:
            logger.error(f"获取消息失败：{data}")
            return []
    except Exception as e:
        logger.error(f"获取消息异常：{e}")
        return []


def reply_message(message_id, content):
    """回复消息"""
    token = get_tenant_token()
    if not token:
        return False

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json; charset=utf-8"
    }
    body = {
        "content": json.dumps({"text": content}),
        "msg_type": "text"
    }
    
    try:
        resp = requests.post(
            f"{BASE_URL}/im/v1/messages/{message_id}/reply",
            headers=headers,
            json=body,
            timeout=10
        )
        data = resp.json()
        if data.get("code") == 0:
            logger.info(f"回复成功: {content[:50]}...")
            return True
        else:
            logger.error(f"回复失败：{data}")
            return False
    except Exception as e:
        logger.error(f"回复异常：{e}")
        return False


def main():
    print("=" * 50)
    print("  1号AI · 飞书 Bot · HTTP轮询模式")
    print("=" * 50)
    
    token = get_tenant_token()
    if not token:
        print("❌ 获取 token 失败")
        return
    
    print("✅ token 连接正常")
    print("📱 请在飞书中给「三角色AI助理」发消息")
    print("   本程序会每 3 秒检查一次新消息")
    print("   按 Ctrl+C 停止")
    print()
    
    processed_ids = set()
    
    import time
    while True:
        try:
            messages = list_messages()
            for msg in messages:
                msg_id = msg.get("message_id")
                msg_type = msg.get("msg_type")
                
                # 只处理文本消息，且跳过已处理的
                if msg_type == "text" and msg_id and msg_id not in processed_ids:
                    content = json.loads(msg.get("body", {}).get("content", "{}"))
                    text = content.get("text", "").strip()
                    
                    if text:
                        logger.info(f"收到消息: {text[:50]}...")
                        processed_ids.add(msg_id)
                        
                        reply = process_message(text)
                        reply_message(msg_id, reply)
                        
                        # 只保留最近 100 条已处理 ID
                        if len(processed_ids) > 100:
                            processed_ids = set(list(processed_ids)[-50:])
            
            time.sleep(3)
            
        except KeyboardInterrupt:
            print("\n👋 已停止")
            break
        except Exception as e:
            logger.error(f"轮询异常：{e}")
            time.sleep(5)


if __name__ == "__main__":
    main()
