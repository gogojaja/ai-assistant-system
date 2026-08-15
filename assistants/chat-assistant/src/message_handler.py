"""
模块名称：message_handler
功能描述：文本消息处理（闲聊、天气、翻译、搜索），整合工具调用与 1号AI，支持 per-user 上下文记忆、跨会话记忆（REQ-034）、任务委派（REQ-035）、文档起草（REQ-036）
对外接口：
    - process_message(user_text, target_id, open_id, receive_id_type): 处理用户文本消息，调用 send_message 回复
依赖：
    - 标准库：logging, os, json
    - 第三方：requests
    - 项目内：shared.utils (get_weather, translate_text, handle_search, get_city_from_config_or_default),
               assistants.chat-assistant.src.main (talk, trim_history),
               shared.feishu_api (send_message)
版本：v2.1
更新记录：
    - 2026-08-16: 新增跨会话记忆（REQ-034）/任务委派（REQ-035）/文档起草（REQ-036）
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
        try:
            return json.loads(raw) if raw else []
        except:
            pass
    return []


def _save_history(open_id: str, messages: list):
    path = _history_path(open_id)
    max_msgs = 2 * MAX_HISTORY_TURNS
    trimmed = messages[-max_msgs:] if len(messages) > max_msgs else messages
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(trimmed, f, ensure_ascii=False, indent=2)


def _clear_history(open_id: str):
    path = _history_path(open_id)
    if os.path.exists(path):
        os.remove(path)
    cpath = _counter_path(open_id)
    if os.path.exists(cpath):
        os.remove(cpath)
        return True
    return False


# ===================== REQ-034 跨会话记忆 =====================

def _memory_path(open_id: str) -> str:
    mem_dir = os.path.join(os.path.dirname(__file__), '..', 'memory')
    os.makedirs(mem_dir, exist_ok=True)
    return os.path.join(mem_dir, f'memory_{open_id}.json')


def _load_memory(open_id: str) -> dict:
    path = _memory_path(open_id)
    if os.path.exists(path):
        try:
            raw = open(path, 'r', encoding='utf-8').read()
            data = json.loads(raw) if raw else {}
            if isinstance(data, dict):
                return data
        except Exception:
            pass
    return {"facts": [], "updated_at": ""}


def _save_memory(open_id: str, memory: dict):
    path = _memory_path(open_id)
    memory["updated_at"] = _now_str()
    try:
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(memory, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        logger.warning(f"保存跨会话记忆失败: {e}")
        return False


def _extract_facts(user_text: str) -> list:
    """从用户消息中提取可持久化的关键事实（简单规则）"""
    import re
    facts = []
    m = re.search(r'(?:我叫|我是|名字是|姓名是|称呼我?为?)\s*([\u4e00-\u9fa5]{2,6})', user_text)
    if m:
        facts.append({"type": "user_name", "value": m.group(1).strip()})
    m = re.search(r'(?:我(?:的)?(?:生日|生日是|过生日)[是为]?)\s*(\d{1,2}[月/]\d{1,2}日?)', user_text)
    if m:
        facts.append({"type": "birthday", "value": m.group(1).strip()})
    m = re.search(r'(?:我(?:的)?)?(?:邮箱|Email|email)[是:：为]?\s*([A-Za-z0-9._%+-]+@[A-Za-z0-9-]+\.[A-Za-z]{2,})', user_text)
    if m:
        facts.append({"type": "email", "value": m.group(1).strip()})
    m = re.search(r'(?:我(?:的)?(?:公司|工作单位|在|任职于)[是:：为]?)\s*([\u4e00-\u9fa5A-Za-z0-9]{2,20}公司)', user_text)
    if m:
        facts.append({"type": "company", "value": m.group(1).strip()})
    # 喜好：我喜欢/最爱/偏好
    m = re.search(r'我(?:比较)?(?:喜欢|最爱|偏好|爱喝|爱吃)\s*([\u4e00-\u9fa5A-Za-z0-9]{2,10})', user_text)
    if m:
        facts.append({"type": "preference", "value": m.group(1).strip()})
    return facts


def _remember(user_text: str, open_id: str):
    """提取并保存跨会话记忆，返回新增事实描述（无则空串）"""
    facts = _extract_facts(user_text)
    if not facts:
        return ""
    memory = _load_memory(open_id)
    new_desc = []
    for fact in facts:
        exists = any(f.get("type") == fact["type"] and f.get("value") == fact["value"] for f in memory.get("facts", []))
        if not exists:
            memory.setdefault("facts", []).append(fact)
            new_desc.append(f"{fact['type']}={fact['value']}")
    if new_desc:
        _save_memory(open_id, memory)
    return "、".join(new_desc)


def _memory_context(open_id: str) -> str:
    """生成跨会话记忆注入文本，供模型感知长期上下文"""
    memory = _load_memory(open_id)
    facts = memory.get("facts", [])
    if not facts:
        return ""
    lines = []
    for f in facts:
        if f.get("type") == "user_name":
            lines.append(f"用户的名字是{f['value']}")
        elif f.get("type") == "birthday":
            lines.append(f"用户的生日是{f['value']}")
        elif f.get("type") == "email":
            lines.append(f"用户的邮箱是{f['value']}")
        elif f.get("type") == "company":
            lines.append(f"用户在{f['value']}工作")
        elif f.get("type") == "preference":
            lines.append(f"用户偏好：{f['value']}")
        else:
            lines.append(f"{f.get('type')}:{f['value']}")
    return "【跨会话记忆】" + "；".join(lines)


# ===================== REQ-035 任务委派 =====================

_DELEGATE_HELP = (
    "🤖 **任务委派**\n"
    "将任务委派给指定 AI：\n"
    "- `#委派 办公 <内容>` — 交给 2号AI 办公处理（Word/Excel/PPT）\n"
    "- `#委派 日程 <内容>` — 交给 3号AI 生活处理（日程/健康/旅行/锻炼/工作）\n"
    "- `#委派 闲聊 <内容>` — 交给 1号AI 闲聊处理\n"
    "示例：`#委派 办公 帮我生成一份项目汇报PPT`"
)


def _delegate(user_text: str, target_id: str, open_id: str, receive_id_type: str):
    """解析 #委派 指令并转交对应角色，返回是否已处理"""
    cmd = user_text[len("#委派"):].lstrip(":： ").strip()
    if not cmd:
        return "help"
    role_name = ""
    content = cmd
    for role, aliases in {
        "办公": ("办公", "office", "2号", "#办公"),
        "日程": ("日程", "生活", "life", "3号"),
        "闲聊": ("闲聊", "chat", "1号"),
    }.items():
        for alias in aliases:
            if cmd.startswith(alias):
                role_name = role
                content = cmd[len(alias):].lstrip(":： ").strip()
                break
        if role_name:
            break
    if not role_name:
        return "help"
    if not content:
        return "help"
    try:
        if role_name == "办公":
            from assistants.office_assistant.src.document_handler import process_office_text
            process_office_text(content, open_id, target_id=target_id, receive_id_type=receive_id_type)
            return "done"
        if role_name == "日程":
            from assistants.life_assistant.src import process as process_life
            reply = process_life(content)
            if reply:
                from shared.feishu_api import send_message
                send_message(target_id, reply, receive_id_type=receive_id_type)
            return "done"
        if role_name == "闲聊":
            return "chat"
    except Exception as e:
        logger.error(f"任务委派失败: {e}")
        send_message(target_id, f"⚠️ 任务委派失败：{e}", receive_id_type=receive_id_type)
        return "done"
    return "help"


# ===================== REQ-036 文档起草 =====================

def _draft_path() -> str:
    draft_dir = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'data', 'drafts')
    os.makedirs(draft_dir, exist_ok=True)
    return draft_dir


def _draft(user_text: str, target_id: str, open_id: str, receive_id_type: str):
    """解析 起草 指令，调用模型生成文档草稿并保存"""
    topic = user_text[len("起草"):].lstrip(":： ").strip()
    if not topic:
        return "help"
    send_message(target_id, f"📝 正在起草《{topic}》，请稍候…", receive_id_type=receive_id_type)
    try:
        from main import talk
        prompt = (
            f"请以《{topic}》为题，起草一份结构完整的文档。\n"
            "要求：使用 Markdown 格式；包含标题、引言、正文若干小节、总结；"
            "内容专业、条理清晰、可直接作为初稿使用。"
        )
        draft = talk([{"role": "user", "content": prompt}], open_id=open_id)
        if not draft or "AI 服务不可用" in draft:
            send_message(target_id, "⚠️ 起草失败：AI 服务不可用", receive_id_type=receive_id_type)
            return "done"
        import datetime
        fname = datetime.datetime.now().strftime("%Y%m%d_%H%M%S") + "_" + topic[:20] + ".md"
        path = os.path.join(_draft_path(), fname)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(f"# {topic}\n\n{draft}\n")
        send_message(target_id, f"✅ 草稿已保存：\n`{path}`\n\n（内容预览）\n{draft[:500]}", receive_id_type=receive_id_type)
        return "done"
    except Exception as e:
        logger.error(f"文档起草失败: {e}")
        send_message(target_id, f"⚠️ 起草失败：{e}", receive_id_type=receive_id_type)
        return "done"


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

        # REQ-035 任务委派
        if user_text.startswith("#委派") or user_text.startswith("#delegate") or user_text.startswith("#转交"):
            result = _delegate(user_text, target_id, uid, receive_id_type)
            if result == "help":
                send_message(target_id, _DELEGATE_HELP, receive_id_type=receive_id_type)
            elif result == "chat":
                pass  # 落入下方闲聊处理
            return

        # REQ-036 文档起草
        if user_text.startswith("起草") or user_text.startswith("写文档"):
            result = _draft(user_text, target_id, uid, receive_id_type)
            if result == "help":
                send_message(target_id, "📝 请提供起草主题，例如：起草 项目周报", receive_id_type=receive_id_type)
            return

        # REQ-034 跨会话记忆：提取事实并注入上下文
        _remembered = _remember(user_text, uid)
        _mem_ctx = _memory_context(uid)

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
            # 提取城市：先去除"查一下""帮我""看看"等非城市前缀
            city = None
            clean_text = re.sub(r'^(能不能帮我|帮我查一下|帮我查|帮我看看|查一下|看一下|有没有|能帮我|查下|看下|麻烦|帮我|看看|查|看|帮|请)\s*', '', user_text)
            patterns = [
                r'(.+?)今天的天气', r'(.+?)明天的天气',
                r'(.+?)后天的天气', r'(.+?)的天气',
            ]
            for pattern in patterns:
                m = re.search(pattern, clean_text)
                if m:
                    city = normalize_city_for_weather(m.group(1))
                    if city:
                        break
            if not city:
                city = normalize_city_for_weather(clean_text)
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

        if TALK_AVAILABLE:
            history = _load_history(uid)

            # REQ-034 跨会话记忆注入（在模型上下文前置系统记忆）
            _mem_ctx = _memory_context(uid)
            if _mem_ctx:
                _mem_prompt = {
                    "role": "user",
                    "content": f"{_mem_ctx}\n\n请记住以上关于用户的信息，并在后续回答中自然运用。本条为记忆注入，无需回复。",
                }
            else:
                _mem_prompt = None

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

            _thinking_msg_id = None
            _search_mode = False

            # 自动联网搜索，结果嵌入用户消息（模型上下文有限，搜索时只保留当前轮）
            try:
                from shared.utils import search_web
                _web_results = search_web(user_text)
                if _web_results.get("success") and _web_results.get("results"):
                    items = []
                    for r in _web_results["results"][:5]:
                        snippet = r['snippet'][:300] if r.get('snippet') else ''
                        items.append(f"<item>\n<title>{r['title']}</title>\n<url>{r.get('url','')}</url>\n<snippet>{snippet}</snippet>\n</item>")
                    if items:
                        enriched = (
                            "【联网搜索结果】\n"
                            + "\n".join(items) +
                            "\n\n【指令】你的训练数据截止于2025年，你无法知道2025年之后的任何实时信息。\n"
                            "请先逐条核对每个<item>：\n"
                            "1. <title>和<snippet>是否直接包含用户问题的具体答案（如：具体比分、确切数值、原文引用）？\n"
                            "2. 是否仅为背景介绍/历史赛程/通用描述，而无用户追问的具体实时信息？\n"
                            "只有当搜索结果中明确出现答案时，才基于搜索结果回答；否则必须回答：「搜索结果未提供相关信息」。\n"
                            "严禁使用训练数据补全、推断或编造实时数据；严禁从通用描述中推导具体答案。\n\n"
                            f"用户问题：{user_text}"
                        )
                        _search_mode = True
                        chat_messages = [{"role": "user", "content": enriched}]
                    else:
                        chat_messages = list(history[-2:])
                else:
                    chat_messages = list(history[-2:])
            except Exception:
                chat_messages = list(history[-2:])

            # REQ-034 跨会话记忆注入到模型上下文
            if _mem_prompt:
                chat_messages.insert(0, _mem_prompt)

            logger.info(f"[DEBUG] 传入 talk() 消息数={len(chat_messages)} 搜索模式={_search_mode} 历史长度={len(history)}")



            try:
                reply = talk(chat_messages, open_id=uid)
            except Exception:
                reply = "处理出错，请稍后重试。"

            if not reply or not reply.strip():
                reply = "抱歉，我暂时无法回复，请稍后再试。"

            # 对问候/身份问题追加帮助引导
            if user_text in ("你好", "你是谁"):
                reply += "\n\n💡 可以通过「帮助」来查看所有功能"

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
