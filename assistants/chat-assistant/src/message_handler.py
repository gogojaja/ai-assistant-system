"""
模块名称：message_handler
功能描述：文本消息处理（闲聊、天气、翻译、搜索），整合工具调用与 1号AI，支持 per-user 上下文记忆
对外接口：
    - process_message(user_text, target_id, open_id, receive_id_type): 处理用户文本消息，调用 send_message 回复
依赖：
    - 标准库：logging, os, json
    - 第三方：requests
    - 项目内：shared.utils (get_weather, translate_text, handle_search, get_city_from_config_or_default),
               assistants.chat-assistant.src.main (talk, trim_history),
               shared.feishu_api (send_message)
版本：v2.0
更新记录：
    - 2026-05-25: 添加 per-user 对话历史管理，修复上下文记忆缺失
    - 2026-05-23: 初始创建，从 callback_server.py 剥离文本消息处理逻辑
"""
import logging
import sys
import os
import json

# 确保能导入项目内模块
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..'))
from shared.utils import get_weather, normalize_city_for_weather, translate_text, handle_search, get_city_from_config_or_default
from shared.feishu_api import send_message, update_message

logger = logging.getLogger(__name__)

def _now_str():
    """返回当前本地时间字符串"""
    import datetime
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def _quote_reply_header(user_text, reply, question_time=None):
    qtime = question_time or _now_str()
    rtime = _now_str()
    header = f"{qtime}\n{user_text[:200]}"
    return f"{header}\n\n{rtime}\n{reply}"

# 尝试导入 talk，失败时提供降级
try:
    from main import talk, trim_history
    TALK_AVAILABLE = True
except ImportError:
    TALK_AVAILABLE = False
    def talk(messages, open_id=""):
        return "AI 服务不可用"
    def trim_history(messages):
        return messages[-20:] if len(messages) > 20 else messages

MAX_HISTORY_TURNS = 10

_HELP_TEXT = """🤖 **AI 使用指南**

1️⃣ **闲聊** — 直接聊天即可
天气/翻译/搜索/查知识/提示词/clear

2️⃣ **办公** — 发 #办公 命令或直接发文件
#办公 ppt <文案> | 转PPT 转上次文档
文件自动分析(docx/xlsx/pptx)

3️⃣ **日程健康** — #3 或 #life
schedule add/list/del · health record/report

💡 文件自动分析 · help 查看完整帮助
""".strip()


def _find_user_name(history: list) -> str:
    """从对话历史中查找用户的自我介绍"""
    import re
    for msg in history:
        if msg.get("role") == "user":
            text = msg.get("content", "")
            # 匹配"我叫XXX"、"我是XXX"、"名字是XXX"
            m = re.search(r'(?:我叫|我是|名字是|姓名是|称呼我?为?)\s*([\u4e00-\u9fa5]{2,4}(?:[\u4e00-\u9fa5]*))', text)
            if m:
                return m.group(1).strip()
    return ""


def _history_path(open_id: str) -> str:
    log_dir = os.path.join(os.path.dirname(__file__), '..', 'logs')
    os.makedirs(log_dir, exist_ok=True)
    return os.path.join(log_dir, f'chat_history_{open_id}.json')


def _counter_path(open_id: str) -> str:
    log_dir = os.path.join(os.path.dirname(__file__), '..', 'logs')
    return os.path.join(log_dir, f'chat_counter_{open_id}.txt')


def _load_counter(open_id: str) -> int:
    path = _counter_path(open_id)
    try:
        if os.path.exists(path):
            return int(open(path).read().strip())
    except Exception:
        pass
    return 0


def _save_counter(open_id: str, count: int):
    path = _counter_path(open_id)
    try:
        with open(path, 'w') as f:
            f.write(str(count))
    except Exception as e:
        logger.warning(f"保存轮次计数失败: {e}")


def _load_history(open_id: str) -> list:
    path = _history_path(open_id)
    if os.path.exists(path):
        raw = open(path, 'r', encoding='utf-8').read()
        if raw.startswith("gAAAA"):
            try:
                from shared.crypto import decrypt_json
                return decrypt_json(raw)
            except Exception as e:
                logger.warning(f"解密对话历史失败，已丢弃: {e}")
                raw = ""
        return json.loads(raw) if raw else []
    return []


def _save_history(open_id: str, messages: list):
    path = _history_path(open_id)
    max_msgs = 2 * MAX_HISTORY_TURNS
    trimmed = messages[-max_msgs:] if len(messages) > max_msgs else messages
    from shared.crypto import encrypt_json
    encrypted = encrypt_json(trimmed)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(encrypted)


def _clear_history(open_id: str):
    path = _history_path(open_id)
    if os.path.exists(path):
        os.remove(path)
    cpath = _counter_path(open_id)
    if os.path.exists(cpath):
        os.remove(cpath)
        return True
    return False


def process_message(user_text: str, target_id: str, open_id: str = None, receive_id_type: str = "open_id"):
    """处理用户文本消息，根据内容分发到不同功能，并回复"""
    try:
        user_text = user_text.strip()
        uid = open_id or target_id
        question_time = _now_str()

        # 帮助指令
        help_triggers = ("帮助", "你能帮我做什么", "你能做什么", "我能做什么", "功能", "指令")
        if user_text in help_triggers or any(t in user_text for t in ("能帮我做什么", "你能做什么")):
            send_message(target_id, _HELP_TEXT, receive_id_type=receive_id_type)
            return

        # 清空指令
        if user_text.lower() == "clear":
            _clear_history(uid)
            send_message(target_id, "✅ 对话历史已清空", receive_id_type=receive_id_type)
            return

        # 自定义提示词
        if user_text.startswith("设置提示词") or user_text.startswith("设定提示词"):
            custom = user_text.replace("设置提示词", "", 1).replace("设定提示词", "", 1).lstrip(":： ")
            if custom:
                from main import _save_custom_prompt
                _save_custom_prompt(uid, custom)
                send_message(target_id, "✅ 自定义提示词已保存", receive_id_type=receive_id_type)
            else:
                send_message(target_id, "请提供提示词内容，例如：设置提示词：你是一位幽默的段子手", receive_id_type=receive_id_type)
            return

        if user_text == "查看提示词":
            from main import _load_custom_prompt
            prompt = _load_custom_prompt(uid)
            if prompt:
                send_message(target_id, f"📝 当前提示词：\n{prompt}", receive_id_type=receive_id_type)
            else:
                send_message(target_id, "📝 你尚未设置自定义提示词", receive_id_type=receive_id_type)
            return

        if user_text == "重置提示词" or user_text == "删除提示词":
            from main import _save_custom_prompt
            _save_custom_prompt(uid, "")
            send_message(target_id, "✅ 自定义提示词已删除", receive_id_type=receive_id_type)
            return

        # 知识库查询
        if user_text.startswith("查知识") or user_text.startswith("知识库"):
            query = user_text.replace("查知识", "", 1).replace("知识库", "", 1).lstrip(":： ").strip()
            if query:
                try:
                    from shared.knowledge_base import search
                    results = search(query, top_k=3, user_id=uid)
                    if results:
                        reply = "📚 相关知识：\n\n" + "\n---\n".join(
                            f"【{r['file']}】\n{r['text'][:300]}" for r in results
                        )
                    else:
                        reply = "知识库中未找到相关内容"
                except Exception as e:
                    reply = f"知识库查询失败：{e}"
            else:
                docs = __import__("shared.knowledge_base", fromlist=["list_docs"]).list_docs()
                if docs:
                    reply = "📚 知识库文档：\n" + "\n".join(f"  - {d}" for d in docs)
                else:
                    reply = "📚 知识库为空，将文件放入 data/knowledge/ 目录即可导入"
            send_message(target_id, reply, receive_id_type=receive_id_type)
            return

        # 搜索指令
        if user_text.startswith("搜索"):
            query = user_text[2:].strip()
            reply = handle_search(query) if query else "请告诉我你要搜索什么。"
            send_message(target_id, reply, receive_id_type=receive_id_type)
            return

        # 翻译指令
        if user_text.startswith("翻译"):
            to_trans = user_text.replace('翻译', '', 1).lstrip(':：').strip()
            if to_trans:
                reply = translate_text(to_trans, source="en")
            else:
                reply = "请提供要翻译的内容，例如：翻译: Hello World"
            send_message(target_id, reply, receive_id_type=receive_id_type)
            return

        # 天气查询
        weather_keywords = ["天气","气温","下雨","下雪","风力","湿度","温度","几度","气候"]
        if any(kw in user_text for kw in weather_keywords):
            import re
            # 识别时间偏移
            day_offset = 0
            if "后天" in user_text:
                day_offset = 2
            elif "明天" in user_text or "明晚" in user_text:
                day_offset = 1
            elif "今天" in user_text or "现在" in user_text or "当前" in user_text:
                day_offset = 0
            # 提取城市
            city = None
            patterns = [
                r'(.+?)今天的天气', r'(.+?)明天的天气',
                r'(.+?)后天的天气', r'(.+?)的天气',
            ]
            for pattern in patterns:
                m = re.search(pattern, user_text)
                if m:
                    city = normalize_city_for_weather(m.group(1))
                    if city:
                        break
            if not city:
                city = normalize_city_for_weather(user_text)
            if not city:
                city = get_city_from_config_or_default()
            weather_result = get_weather(city, day_offset=day_offset)
            if isinstance(weather_result, dict):
                if weather_result.get('error'):
                    reply = weather_result['error']
                else:
                    desc_cn = weather_result.get('description', '')
                    desc_en = weather_result.get('description_en', '')
                    desc_str = f"{desc_cn}（{desc_en}）" if desc_en and desc_en.lower() != desc_cn.lower() else desc_cn
                    city_cn = weather_result.get('city_cn', '') or weather_result.get('city', city)
                    city_en = weather_result.get('city_en', '')
                    city_str = f"{city_cn}（{city_en}）" if city_en and city_en.lower() != city_cn.lower() else city_cn
                    weekday = weather_result.get('weekday', '')
                    date_str = weather_result.get('date', '')
                    if weather_result.get('type') == 'forecast':
                        time_label = {0: "今天", 1: "明天", 2: "后天"}.get(day_offset, "")
                        reply = (
                            f"{city_str} {time_label}（{weekday}）{date_str}：{desc_str}，"
                            f"最高{weather_result.get('temp_max', '')}°C，最低{weather_result.get('temp_min', '')}°C"
                        )
                    else:
                        reply = (
                            f"{city_str} 当前（{weekday}）{date_str}：{desc_str}，"
                            f"温度{weather_result.get('temp_c', '')}°C，湿度{weather_result.get('humidity', '')}%，"
                            f"风速{weather_result.get('wind_speed', '')} km/h"
                        )
            else:
                reply = weather_result
            send_message(target_id, reply, receive_id_type=receive_id_type)
            return

        # 闲聊：加载历史 → 追加 → 调用 talk → 追加回复 → 保存 → 发送
        if TALK_AVAILABLE:
            history = _load_history(uid)

            # 身份类问题：从历史或当前消息中找用户自我介绍
            import re as _re
            if _re.match(r'我(是|叫|是谁|叫什么|的名字)', user_text):
                user_name = _find_user_name(history)
                if not user_name:
                    m = _re.search(r'(?:我是|我叫|名字是|姓名是|称呼我?为?)\s*([\u4e00-\u9fa5]{2,6})', user_text)
                    if m:
                        user_name = m.group(1).strip()
                if user_name:
                    reply = f"你是{user_name}，这是你之前告诉我的。"
                    history.append({"role": "user", "content": user_text})
                    history.append({"role": "assistant", "content": reply})
                    _save_history(uid, history)
                    send_message(target_id, reply, receive_id_type=receive_id_type)
                    return
                else:
                    reply = "抱歉，我还不知道你是谁。你可以说'我叫XXX'来告诉我。"
                    history.append({"role": "user", "content": user_text})
                    history.append({"role": "assistant", "content": reply})
                    _save_history(uid, history)
                    send_message(target_id, reply, receive_id_type=receive_id_type)
                    return

            history.append({"role": "user", "content": user_text})

            # 自动检索知识库，注入上下文（不修改原始 history）
            kb_context = None
            try:
                from shared.knowledge_base import search as _kb_search
                _kb_results = _kb_search(user_text, top_k=2, user_id=uid)
                if _kb_results:
                    kb_context = "\n\n相关知识：\n" + "\n".join(f"- {r['text'][:200]}" for r in _kb_results)
            except Exception:
                pass

            _thinking_msg_id = None

            chat_messages = list(history)
            if kb_context:
                chat_messages.insert(-1, {"role": "system", "content": kb_context})

            try:
                reply = talk(chat_messages, open_id=uid)
            except Exception:
                reply = "处理出错，请稍后重试。"

            if not reply or not reply.strip():
                reply = "抱歉，我暂时无法回复，请稍后再试。"

            # 对问候/身份问题追加帮助引导
            if user_text in ("你好", "你是谁"):
                reply += "\n\n💡 可以通过「帮助」来查看所有功能"

            # 在回复尾部添加记忆轮次提示（累计轮次，超过上限时单独标记）
            if reply not in ("处理出错，请稍后重试。", "抱歉，我暂时无法回复，请稍后再试。"):
                total_turns = _load_counter(uid) + 1
                if total_turns > MAX_HISTORY_TURNS:
                    total_turns = 1
                _save_counter(uid, total_turns)
                reply += f"\n⏳ 已记忆 {total_turns}/{MAX_HISTORY_TURNS} 轮"

            # 引用提问 + 时间戳头
            display_reply = _quote_reply_header(user_text, reply, question_time=question_time)

            # 分块发送/更新消息（超长回复自动分段）
            def _send_chunks(base_msg_id, text, target, rtype):
                max_chunk = 1500
                if len(text) <= max_chunk:
                    # 单条，直接更新或发送
                    if base_msg_id:
                        if not update_message(base_msg_id, text):
                            send_message(target, text, receive_id_type=rtype)
                    else:
                        send_message(target, text, receive_id_type=rtype)
                    return
                # 按段落拆分
                paragraphs = text.split('\n\n')
                chunks = []
                buf = ""
                for p in paragraphs:
                    if len(buf) + len(p) + 2 > max_chunk and buf:
                        chunks.append(buf.strip())
                        buf = p
                    else:
                        buf = (buf + '\n\n' + p).strip() if buf else p
                if buf:
                    chunks.append(buf.strip())
                # 更新 thinking 为第一段
                if base_msg_id:
                    if not update_message(base_msg_id, chunks[0]):
                        send_message(target, chunks[0], receive_id_type=rtype)
                else:
                    send_message(target, chunks[0], receive_id_type=rtype)
                # 后续段分别发送
                for ch in chunks[1:]:
                    send_message(target, ch, receive_id_type=rtype)

            _send_chunks(_thinking_msg_id, display_reply, target_id, receive_id_type)

            # 保存历史（去掉界面提示后缀，避免模型学到）
            if reply not in ("处理出错，请稍后重试。", "抱歉，我暂时无法回复，请稍后再试。"):
                try:
                    clean = reply
                    import re as _re_strip
                    clean = _re_strip.sub(r'\n\n⏳ 已记忆 \d+/\d+ 轮$', '', clean)
                    clean = _re_strip.sub(r'\n\n💡 可以通过.*$', '', clean)
                    history.append({"role": "assistant", "content": clean})
                    _save_history(uid, history)
                except Exception as e:
                    logger.warning(f"保存历史失败: {e}")
        else:
            reply = "AI 服务不可用"
            send_message(target_id, reply, receive_id_type=receive_id_type)

    except Exception as e:
        logger.error(f"处理消息异常: {e}", exc_info=True)
        send_message(target_id, "处理出错，请稍后重试。", receive_id_type=receive_id_type)
