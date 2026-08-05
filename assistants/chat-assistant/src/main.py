"""
模块名称：main
功能描述：1号AI 闲聊检索主入口，终端对话与搜索，支持上下文记忆
对外接口：
    - talk(messages): 调用模型进行对话，返回回复文本
    - handle_search(user_input): 处理搜索指令
    - handle_local_search(user_input): 本地知识库检索
    - show_help(): 返回帮助信息
依赖：
    - 标准库：sys, os, logging, json, datetime, re
    - 第三方：requests, yaml
    - 项目内：chat (load_history, save_history, clear_history), search (search_web, search_archive, format_results)
版本：v2.3
更新记录：
    - 2026-05-23: 添加流式UTF-8修复、后处理提取，统一注释头
"""
import sys
import os
import logging
import json
import requests
import re
import datetime
import yaml
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))
from chat import load_history, save_history, clear_history
from search import search_web, search_archive, format_results

logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
PROMPTS_DIR = _PROJECT_ROOT / "prompts"
MODEL_NAME = "qwen2.5:7b"
MAX_HISTORY_TURNS = 10


def _load_custom_prompt(open_id=""):
    """加载用户自定义提示词"""
    if not open_id:
        return ""
    prompt_file = PROMPTS_DIR / f"{open_id}.txt"
    if prompt_file.exists():
        try:
            return prompt_file.read_text(encoding="utf-8").strip()
        except:
            pass
    return ""


def _save_custom_prompt(open_id, text):
    """保存用户自定义提示词"""
    PROMPTS_DIR.mkdir(parents=True, exist_ok=True)
    prompt_file = PROMPTS_DIR / f"{open_id}.txt"
    if text.strip():
        prompt_file.write_text(text.strip(), encoding="utf-8")
        return True
    elif prompt_file.exists():
        prompt_file.unlink()
    return False


def _get_backend_config():
    """从 settings.yaml 读取后端配置"""
    config_path = _PROJECT_ROOT / "config" / "settings.yaml"
    try:
        if config_path.exists():
            cfg = yaml.safe_load(config_path.read_text())
            backend = cfg.get("backend", "llama.cpp")
            port = cfg.get("ollama_port", 11434) if backend == "ollama" else cfg.get("llama_port", 8080)
            return {"backend": backend, "port": port, "model": "gpt-3.5-turbo"}
    except:
        pass
    return {"backend": "llama.cpp", "port": 8080, "model": "gpt-3.5-turbo"}


def trim_history(messages):
    """裁剪历史消息，保留最近 MAX_HISTORY_TURNS 轮对话"""
    system_messages = [msg for msg in messages if msg.get("role") == "system"]
    non_system = [msg for msg in messages if msg.get("role") != "system"]
    max_non_system = 2 * MAX_HISTORY_TURNS
    if len(non_system) > max_non_system:
        non_system = non_system[-max_non_system:]
    return system_messages + non_system


def _inject_system_context(messages, open_id=""):
    """注入当前时间、城市信息、自定义提示词和格式指南"""
    tz = datetime.timezone(datetime.timedelta(hours=8))
    now = datetime.datetime.now(tz)
    weekdays = ["星期一","星期二","星期三","星期四","星期五","星期六","星期日"]
    time_str = f"{now.strftime('%Y年%m月%d日')} {weekdays[now.weekday()]} {now.strftime('%H:%M')}"
    location = "北京"
    config_path = _PROJECT_ROOT / "config" / "settings.yaml"
    try:
        if config_path.exists():
            cfg = yaml.safe_load(config_path.read_text())
            if cfg and "location" in cfg:
                location = cfg["location"]
    except:
        pass
    content = (
        f"当前时间：{time_str}\n"
        f"当前城市：{location}\n"
        "你是1号AI闲聊助理。回答问题请注意：\n"
        "1. 直接输出最终回答，不要输出推理过程。用自然的中文分段，每段不超过3句话。\n"
        "2. 根据问题灵活调整风格——解释类先概括再展开，闲聊/讲故事/笑话直接输出。列举时用数字序号（1. 2. 3.），不要用markdown符号。\n"
        "3. 不确定的信息要说明「据我所知」或「可能」，不编造。回答简洁，控制在300字以内。\n"
        "【联网搜索规则】你的训练数据截止于2025年。当用户消息中包含了【联网搜索结果】时，必须按以下步骤回答：\n"
        "① 逐条检查每个<item>的<title>和<snippet>是否直接包含用户问题的答案\n"
        "② 只有当搜索结果中明确出现答案（如具体比分、确切数值、原文引用）时，才基于搜索结果回答\n"
        "③ 如果搜索结果仅包含背景介绍、历史赛程、通用描述，而无用户追问的具体实时信息，必须回答：「搜索结果未提供相关信息」\n"
        "④ 绝对禁止使用训练数据补全、推断或编造任何实时数据\n"
        "⑤ 绝对禁止从通用描述中推导具体答案"
    )
    custom = _load_custom_prompt(open_id)
    if custom:
        content += f"\n\n用户自定义要求：{custom}"
    system_msg = {"role": "system", "content": content}
    messages[:] = [m for m in messages if m.get("role") != "system"]
    messages.insert(0, system_msg)


def get_weather(city="北京"):
    """获取实时天气（使用 wttr.in，无需 API Key）"""
    import requests
    logger_weather = logging.getLogger("weather")
    try:
        url = f"https://wttr.in/{city}?format=%C+%t+%h+%w&lang=zh"
        resp = requests.get(url, timeout=5)
        if resp.status_code == 200:
            data = resp.text.strip()
            return f"{city}当前天气：{data}"
        else:
            return f"获取{city}天气失败"
    except Exception as e:
        logger_weather.error(f"天气查询异常: {e}")
        return "天气服务暂时不可用"


def _wake_model(cfg):
    """如果模型进程被 SIGSTOP 挂起，发送 SIGCONT 唤醒"""
    import subprocess, os
    proc_name = "ollama" if cfg['backend'] == "ollama" else "llama-server"
    try:
        result = subprocess.run(
            ["pgrep", "-f", proc_name],
            capture_output=True, text=True, timeout=3
        )
        pids = [p.strip() for p in result.stdout.split("\n") if p.strip()]
        for pid in pids:
            # 检查进程状态是否含 T (stopped)
            state = subprocess.run(
                ["ps", "-o", "stat=", "-p", pid],
                capture_output=True, text=True, timeout=3
            ).stdout.strip()
            if "T" in state:
                os.kill(int(pid), 18)  # SIGCONT = 18
                logger.info(f"唤醒模型进程 PID={pid}")
    except Exception:
        pass


def _format_reply(text):
    """后处理：清理模型输出的格式问题，提升可读性"""
    if not text:
        return text
    # 去除多余的空白行（保留最多一个连续换行）
    text = re.sub(r'\n{3,}', '\n\n', text)
    # 去除行尾多余空格
    text = re.sub(r'[ \t]+\n', '\n', text)
    # 去除中文与英文/数字之间的多余空格
    text = re.sub(r'([\u4e00-\u9fff]) ([a-zA-Z0-9])', r'\1\2', text)
    text = re.sub(r'([a-zA-Z0-9]) ([\u4e00-\u9fff])', r'\1\2', text)
    # 修复中文标点前多余空格
    text = re.sub(r' +([，。！？、；：])', r'\1', text)
    # 去除非 reasoning 痕迹：行首的"我的回答是"等前缀
    text = re.sub(r'^(?:我的回答[：:]|响应是[：:]|最终回答[：:])\s*', '', text)
    # 去除开头结尾多余空白
    text = text.strip()
    # 如果文本末尾不是合理结束标点，补句号
    if text and text[-1] not in ('。', '！', '？', '）', '」', '…', '.', '!', '?', '、', '，', '；', '：'):
        text += '。'
    # 去掉结尾的残缺标点（枚举逗号后接句号: "、。")
    text = re.sub(r'[、，；：]+[。！？]?$', '。', text)
    return text


def talk(messages, open_id=""):
    """流式调用模型，强制 UTF-8 解码，拼接 content 和 reasoning_content，并后处理"""
    import requests, json
    _inject_system_context(messages, open_id)
    messages = trim_history(messages)
    cfg = _get_backend_config()
    if cfg['backend'] != 'free-api-hub':
        _wake_model(cfg)
        api_url = f"http://localhost:{cfg['port']}/v1/chat/completions"
    else:
        api_url = cfg['api_url'] + "/chat/completions"
    api_model = cfg['model']
    logger.debug(f"后端={cfg['backend']} 端口={cfg.get('port','?')} 模型={api_model} 消息数={len(messages)}")
    full_content = ""
    full_reasoning = ""

    import time as _time
    request_body = {
        "model": api_model,
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 2048,
        "stream": True
    }
    for attempt in range(3):
        try:
            resp = requests.post(api_url, json=request_body, timeout=60, stream=True)
        except requests.ConnectionError as _ce:
            logger.warning(f"llama-server 连接失败（尝试 {attempt+1}/3）: {_ce}")
            if attempt < 2:
                _time.sleep(1.5)
            continue
        if resp.status_code == 200:
            break
        resp_body = resp.text[:500] if resp.text else '(empty)'
        logger.error(f"llama-server 返回 {resp.status_code}（尝试 {attempt+1}/3）body={resp_body}")
        logger.error(f"请求体消息数={len(request_body['messages'])} 总字符={sum(len(m.get('content','')) for m in request_body['messages'])}")
        if attempt < 2:
            _time.sleep(1.5)
    else:
        logger.error(f"llama-server 连续 3 次失败")
        return "抱歉，AI 服务暂时不可用，请稍后重试。"

    try:
        resp.encoding = 'utf-8'

        for line in resp.iter_lines(decode_unicode=True):
            if not line or not line.startswith("data: "):
                continue
            data_str = line[6:]
            if data_str.strip() == "[DONE]":
                break
            try:
                chunk = json.loads(data_str)
                delta = chunk.get("choices", [{}])[0].get("delta", {})
                content_piece = delta.get("content", "")
                reasoning_piece = delta.get("reasoning_content", "")
                if content_piece:
                    full_content += content_piece
                if reasoning_piece:
                    full_reasoning += reasoning_piece
            except json.JSONDecodeError:
                logger.debug(f"JSON解析失败，原始数据: {data_str[:100]}...")
                continue

        full_content = full_content.strip()
        if full_content:
            logger.debug(f"流式拼接完成，总长度 {len(full_content)} 字符")
            return _format_reply(full_content)
        else:
            combined = full_reasoning.strip()
            if combined:
                logger.warning(f"content 为空，使用 reasoning ({len(combined)} 字符)")
                return _format_reply(_extract_from_reasoning(combined))
            logger.warning("流式未收到任何内容，尝试非流式兜底")
            return _format_reply(_fallback_with_postprocess(messages))

    except Exception as e:
        logger.error(f"流式请求异常: {e}")
        return "抱歉，AI 服务暂时不可用，请稍后重试。"


def _extract_from_reasoning(text):
    """从 reasoning_content 中提取最终回答"""
    import re
    # 策略1：查找"回应说"或"回答是"后的引号内容
    m = re.search(r'(?:回应说|回答是|答案是)[：:]\s*[“「](.+?)[”」]', text)
    if m:
        extracted = m.group(1).strip()
        logger.info("从 reasoning 回应说中提取")
        return extracted
    # 策略2：查找"最终回答"附近的引号内容
    m = re.search(r'最终回答[^。]*?[“「](.+?)[”」]', text)
    if m:
        extracted = m.group(1).strip()
        logger.info("从 reasoning 最终回答中提取")
        return extracted
    # 策略3：查找"所以我的回答是/所以我说/所以我回应"后的内容
    m = re.search(r'所以(?:我(?:的回答|说|回应))[：:]\s*(.+?)(?:[。\n]|$)', text)
    if m:
        extracted = m.group(1).strip()
        if extracted:
            logger.info("从 reasoning 所以回答中提取")
            return extracted
    # 策略4：取最后一段有完整含义的句子（优先于引号提取，避免截断）
    paragraphs = re.split(r'\n\s*\n', text)
    meaningful = [p.strip() for p in paragraphs if len(p.strip()) > 5 and '我' not in p[:5] and '用户' not in p[:5]]
    if meaningful:
        logger.info("从 reasoning 段落中提取")
        return meaningful[-1]
    # 策略5：查找最后一个引号内的内容（兜底）
    quoted = re.findall(r'[“「]([^”」]+)[”」]', text)
    if quoted:
        logger.info("从 reasoning 最后引号中提取")
        return quoted[-1].strip()
    return "抱歉，我暂时无法生成回复，请稍后再试。"


def _fallback_with_postprocess(messages):
    """
    非流式兜底，并精准提取最终回答
    优先查找“最终回答”附近第一个中文引号内的内容
    """
    import requests, re
    _cfg = _get_backend_config()
    if _cfg['backend'] != 'free-api-hub':
        _api_url = f"http://localhost:{_cfg['port']}/v1/chat/completions"
    else:
        _api_url = _cfg['api_url'] + "/chat/completions"
    _api_model = _cfg['model']
    try:
        resp = requests.post(
            _api_url,
            json={
                "model": _api_model,
                "messages": messages,
                "max_tokens": 2048,
                "temperature": 0.7
            },
            timeout=60
        )
        if resp.status_code == 200:
            data = resp.json()
            content = data["choices"][0]["message"].get("content", "").strip()
            reasoning = data["choices"][0]["message"].get("reasoning_content", "").strip()
            if content:
                text = content
            elif reasoning:
                logger.info("content 为空，从 reasoning 提取")
                return _extract_from_reasoning(reasoning)
            else:
                return "抱歉，我暂时无法生成回复，请稍后再试。"

            # 策略1：在“最终回答”附近的句子中，提取第一个中文引号内的内容
            m = re.search(r'最终回答[^。]*?[“「](.+?)[”」]', text)
            if m:
                extracted = m.group(1).strip()
                logger.info("精准提取引号内最终回答")
                return extracted

            # 策略2：其他明确指令模式
            patterns = [
                r"我的响应应该直接是中文的[“「](.+?)[”」]",
                r"直接输出[“「](.+?)[”」]",
                r"我的回答[：:]\s*(.*?)(?:[。\n]|$)",
                r"最终回答[：:]\s*(.*?)(?:[。\n]|$)",
                r"响应是[：:]\s*(.*?)(?:[。\n]|$)",
            ]
            for pat in patterns:
                m = re.search(pat, text)
                if m:
                    extracted = m.group(1).strip()
                    if extracted:
                        logger.info("从兜底文本中提取最终回答")
                        return extracted

            # 策略3：全局查找最后一个引号内的内容
            quoted = re.findall(r'[“「]([^”」]+)[”」]', text)
            if quoted:
                logger.info("使用最后一个引号内内容作为回答")
                return quoted[-1].strip()

            # 策略4：返回最后一句
            sentences = re.split(r'[。！!]', text)
            last_sentence = sentences[-1].strip() if sentences else text
            return last_sentence if last_sentence else text
        else:
            return "抱歉，AI 服务暂时不可用，请稍后重试。"
    except Exception:
        return "抱歉，AI 服务暂时不可用，请稍后重试."


def handle_search(user_input):
    """处理搜索指令"""
    keyword = user_input.replace("搜索", "", 1).strip()
    if not keyword:
        return "请指定搜索关键词，例如：搜索 Python 教程"
    print(f"\n🔍 正在联网搜索：{keyword} ...")
    result = search_web(keyword)
    return format_results(result)


def handle_local_search(user_input):
    """在本地知识库中检索"""
    keyword = user_input.replace("本地搜索", "", 1).replace("查找", "", 1).strip()
    if not keyword:
        return "请指定检索关键词"
    result = search_archive(keyword)
    if not result["found"]:
        return f"本地知识库中未找到与「{keyword}」相关的记录（共 {result['total_archived']} 条归档）"
    lines = [f"📂 本地知识库中找到 {len(result['results'])} 条匹配："]
    for r in result["results"]:
        lines.append(f"  [{r['timestamp']}] {r['query']}")
    return "\n".join(lines)


def show_help():
    return """
📋 可用指令：
  直接输入文字  → 和 AI 闲聊（支持上下文记忆）
  搜索 + 关键词  → 联网搜索（例如：搜索 今天天气）
  本地搜索 + 词  → 在本地知识库检索
  clear         → 清空对话历史
  help          → 显示此帮助
  exit          → 退出
"""


def main():
    messages = load_history()
    if not messages or messages[0].get("role") != "system":
        messages.insert(0, {"role": "system", "content": "你是一个中文AI助手，请始终使用中文回答。"})
        save_history(messages)

    print("\n🤖 1号AI · 闲聊检索助理 · 已上线（支持上下文记忆，强制中文回复）")
    print("输入 'help' 查看指令 | 'exit' 退出\n")

    while True:
        try:
            user_input = input("你：").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n👋 已退出")
            break

        if not user_input:
            continue

        if user_input.lower() == "exit":
            print("👋 已退出")
            break

        if user_input.lower() == "clear":
            print(clear_history())
            messages = [{"role": "system", "content": "你是一个中文AI助手，请始终使用中文回答。"}]
            save_history(messages)
            continue

        if user_input.lower() == "help":
            print(show_help())
            continue

        if user_input.startswith("搜索"):
            try:
                result = handle_search(user_input)
                print(f"助手：{result}")
                messages.append({"role": "user", "content": user_input})
                messages.append({"role": "assistant", "content": result})
                save_history(trim_history(messages))
            except Exception as e:
                logger.error(f"搜索出错：{e}")
                print(f"⚠️ 搜索出错：{e}")
            continue

        if user_input.startswith(("本地搜索", "查找")):
            result = handle_local_search(user_input)
            print(f"助手：{result}")
            messages.append({"role": "user", "content": user_input})
            messages.append({"role": "assistant", "content": result})
            save_history(trim_history(messages))
            continue

        # 正常对话
        messages.append({"role": "user", "content": user_input})
        trimmed_for_api = trim_history(messages)
        try:
            assistant_reply = talk(trimmed_for_api)
            print(f"助手：{assistant_reply}")
            messages.append({"role": "assistant", "content": assistant_reply})
            save_history(trim_history(messages))
        except Exception as e:
            logger.error(f"对话出错：{e}")
            print(f"⚠️ 出错了：{e}")
            messages.pop()


if __name__ == "__main__":
    main()