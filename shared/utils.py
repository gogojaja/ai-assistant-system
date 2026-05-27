"""
模块名称：shared/utils.py
功能描述：提供天气查询、翻译、搜索、城市获取等通用工具函数
对外接口：
 - get_weather(city): 获取城市天气
 - translate_text(text, target_lang='zh-CN'): 翻译文本
 - handle_search(user_input): 处理搜索指令（联网搜索）
 - get_city_from_config_or_default(): 从配置或默认获取城市
依赖：
 - 标准库：json, urllib.request, urllib.parse
 - 第三方：deep-translator (GoogleTranslator), requests
 - 项目内：无
版本：v2.4
更新记录：
 - 2026-05-24: 稳定版本。搜索功能因网络环境问题降级为友好提示。天气、翻译功能正常。
"""
import json
import re
import datetime
import urllib.request
import urllib.parse

# ===== 天气 =====

WEEKDAY_CN = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]

WEATHER_CN_MAP = {
    "sunny": "晴", "clear": "晴", "fair": "晴",
    "partly cloudy": "多云", "cloudy": "多云", "mostly cloudy": "多云",
    "overcast": "阴",
    "mist": "雾", "fog": "雾", "foggy": "雾",
    "haze": "霾", "hazy": "霾", "smoke": "烟霾",
    "light rain": "小雨", "light rain shower": "小雨",
    "moderate rain": "中雨", "heavy rain": "大雨",
    "torrential rain": "暴雨", "drizzle": "毛毛雨",
    "light drizzle": "毛毛雨",
    "patchy rain possible": "阵雨", "patchy rain nearby": "阵雨",
    "light rain shower": "阵雨", "rain shower": "阵雨",
    "shower": "阵雨", "showers": "阵雨",
    "thundery outbreaks possible": "雷阵雨",
    "thunderstorm": "雷阵雨", "thunder": "雷阵雨",
    "light snow": "小雪", "moderate snow": "中雪",
    "heavy snow": "大雪", "snow": "雪",
    "patchy snow possible": "阵雪", "patchy snow nearby": "阵雪",
    "blowing snow": "吹雪", "blizzard": "暴风雪",
    "sleet": "雨夹雪", "ice pellets": "冰雹",
    "freezing rain": "冻雨",
    "windy": "大风", "breezy": "微风",
    "dust": "扬尘", "dust storm": "沙尘暴",
    "sandstorm": "沙尘暴",
}

# 匹配时需忽略的修饰词（移除后提取核心天气词）
_WEATHER_NOISE_WORDS = {"nearby", "possible", "expected", "at times", "in vicinity",
                        "patches of", "with", "and", "periods of"}


def _to_cn_weather(desc_en):
    """将英文天气描述转为中文"""
    if not desc_en:
        return ""
    key = desc_en.strip().lower()
    # 精确匹配
    direct = WEATHER_CN_MAP.get(key)
    if direct:
        return direct
    # 去掉噪音词后再精确匹配
    clean_key = key
    for w in sorted(_WEATHER_NOISE_WORDS, key=len, reverse=True):
        clean_key = clean_key.replace(w, "")
    clean_key = re.sub(r'\s+', ' ', clean_key).strip()
    if clean_key != key:
        direct = WEATHER_CN_MAP.get(clean_key)
        if direct:
            return direct
    # 部分匹配（长短语优先）
    for en, cn in sorted(WEATHER_CN_MAP.items(), key=lambda x: -len(x[0])):
        if en in key or en in clean_key:
            return cn
    return desc_en

# 常见外国城市中英文别名（提高天气查询稳定性）
CITY_ALIASES = {
    "清迈": "Chiang Mai",
    "曼谷": "Bangkok",
    "东京": "Tokyo",
    "首尔": "Seoul",
    "纽约": "New York",
    "伦敦": "London",
    "巴黎": "Paris",
    "新加坡": "Singapore",
    "悉尼": "Sydney",
    "迪拜": "Dubai"
}

def normalize_city_for_weather(text):
    """从用户输入中提取和规范化地点名称，去除时间词、查询短语和 mentions。"""
    if not text or not isinstance(text, str):
        return text
    text = text.strip()
    # 飞书文本中常见 mention 格式，例如 <at id="xxx">名字</at> 或 @机器人
    text = re.sub(r'<at[^>]*?>.*?</at>', '', text)
    text = re.sub(r'[@＠][\w\u4e00-\u9fa5_]+', '', text)
    # 去掉常见关键词、时间限定词、查询填充词
    text = re.sub(r'^(?:请问|请帮我查|帮我查|请帮我|帮我|请帮我看|帮我看|查询|查一下|看一下|我想知道|能告诉我|能不能告诉我)[\s，,]*', '', text)
    text = re.sub(r'[?？!！。；，,]+$', '', text)
    text = re.sub(r'(今天|明天|后天|今晚|明晚|现在|当前|本周|未来|最近|这周)', '', text)
    text = re.sub(r'的?(?:天气|气温|气候|气象|温度|阴晴|状况)[?？!！。；，,]*$', '', text)
    text = re.sub(r'[?？!！。；，,]+$', '', text)
    return text.strip()


def _day_offset_to_weekday(offset):
    """根据 day_offset 返回中文星期几"""
    return WEEKDAY_CN[(datetime.date.today().weekday() + offset) % 7]


def _parse_forecast(data, city_name, offset):
    """从 wttr.in JSON 的第 offset 天天气预报中提取数据"""
    try:
        forecast = data['weather'][offset]
        hourly = forecast.get('hourly', [])
        desc_en = ""
        if hourly:
            mid_idx = len(hourly) // 2
            desc_en = hourly[mid_idx].get('weatherDesc', [{}])[0].get('value', '')
        return {
            'city': city_name,
            'description': _to_cn_weather(desc_en),
            'description_en': desc_en.strip(),
            'temp_max': forecast.get('maxtempC', ''),
            'temp_min': forecast.get('mintempC', ''),
            'type': 'forecast',
            'date': forecast.get('date', ''),
            'weekday': _day_offset_to_weekday(offset)
        }
    except (IndexError, KeyError, TypeError):
        return None


def _parse_current(data, city_name):
    """从 wttr.in JSON 的当前天气中提取数据"""
    try:
        current = data['current_condition'][0]
        desc_en = current['weatherDesc'][0]['value']
        return {
            'city': city_name,
            'description': _to_cn_weather(desc_en),
            'description_en': desc_en.strip(),
            'temp_c': current['temp_C'],
            'humidity': current['humidity'],
            'wind_speed': current['windspeedKmph'],
            'type': 'current',
            'date': datetime.date.today().isoformat(),
            'weekday': _day_offset_to_weekday(0)
        }
    except (IndexError, KeyError, TypeError):
        return None


def _fetch_weather_data(city):
    """通用天气数据获取，返回原始 JSON 或 None"""
    try:
        url = f"http://wttr.in/{urllib.parse.quote(city)}?format=j1"
        with urllib.request.urlopen(url, timeout=10) as resp:
            return json.loads(resp.read().decode('utf-8'))
    except Exception:
        return None


# 反向别名表：英文名 → 中文名
_CITY_ALIASES_REVERSE = {v.lower(): k for k, v in CITY_ALIASES.items()}


def _resolve_city_names(raw_city):
    """根据用户输入的城市名，返回 (city_cn, city_en) 用于显示"""
    if not raw_city:
        return raw_city, ""
    cn = _CITY_ALIASES_REVERSE.get(raw_city.strip().lower())
    if cn:
        return cn, raw_city.strip()
    en = CITY_ALIASES.get(raw_city.strip())
    if en:
        return raw_city.strip(), en
    if re.match(r'^[a-zA-Z\s]+$', raw_city):
        return raw_city.strip(), raw_city.strip()
    return raw_city.strip(), ""


def get_weather(city, day_offset=0):
    """获取指定城市的天气信息（使用 wttr.in 免费接口，支持中英文）
    day_offset: 0=当前/今天, 1=明天, 2=后天
    """
    city = normalize_city_for_weather(city)
    if not city:
        return {'error': '天气查询失败: 未识别地点'}
    # 计算显示用中英文名
    city_cn, city_en = _resolve_city_names(city)
    # 第一次尝试：直接使用原城市名
    data = _fetch_weather_data(city)
    if data is None:
        # 第二次尝试：翻译为英文后查询
        try:
            en_city = CITY_ALIASES.get(city)
            if en_city is None:
                translated = translate(city, target_lang='en')
                if translated and "失败" not in translated and "INVALID" not in translated and "ERROR" not in translated:
                    en_city = translated
                    if not city_en:
                        city_en = en_city
                else:
                    raise Exception(f"无法获取{city}的英文名称")
            else:
                city_cn = city
                city_en = en_city
            data = _fetch_weather_data(en_city)
        except Exception as e:
            return {'error': f'天气查询失败: {str(e)}'}
    if data is None:
        return {'error': f'天气查询失败: {city} 数据不可用'}
    # 根据 day_offset 决定返回当前还是预报
    if day_offset == 0:
        result = _parse_current(data, city)
        if result:
            result['city_cn'] = city_cn
            result['city_en'] = city_en
            return result
        day_offset = 1
    result = _parse_forecast(data, city, day_offset)
    if result:
        result['city_cn'] = city_cn
        result['city_en'] = city_en
        return result
    return {'error': f'天气查询失败: 无法获取{["今天","明天","后天"][day_offset if day_offset <= 2 else 0]}的预报数据'}

# ===== 翻译 =====
def translate(text, target_lang='zh', source='auto'):
    """
    使用 MyMemory 免费翻译 API（无需密钥，国内可访问）
    """
    if not text:
        return ""
    try:
        import requests
        url = "https://api.mymemory.translated.net/get"
        lang_map = {
            'zh': 'zh-CN',
            'en': 'en-US',
            'ja': 'ja-JP',
            'ko': 'ko-KR',
            'fr': 'fr-FR',
            'de': 'de-DE'
        }
        target_code = lang_map.get(target_lang, target_lang)
        if source == 'auto':
            langpair = f"|{target_code}"
        else:
            source_code = lang_map.get(source, source)
            langpair = f"{source_code}|{target_code}"
        params = {
            "q": text,
            "langpair": langpair
        }
        resp = requests.get(url, params=params, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            if data.get("responseStatus") == 200:
                return data["responseData"]["translatedText"]
            else:
                return f"翻译失败: {data.get('responseDetails', '未知错误')}"
        return f"翻译失败: HTTP {resp.status_code}"
    except Exception as e:
        return f"翻译失败: {str(e)}"

# 别名，兼容旧调用
translate_text = translate

# ===== 搜索 =====

def search_web(keyword):
    """使用 Bing 搜索并解析前几条结果。"""
    try:
        import requests
    except ImportError:
        return {"success": False, "results": [], "error": "⚠️ 搜索功能暂不可用：requests 未安装"}

    try:
        requests.get("https://www.bing.com", timeout=5)
    except requests.RequestException:
        return {"success": False, "results": [], "error": "⚠️ 无网络连接，请检查网络后重试"}

    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        }
        params = {"q": keyword, "count": 10}
        response = requests.get("https://www.bing.com/search", params=params, headers=headers, timeout=10)
        if response.status_code != 200:
            return {"success": False, "results": [], "error": f"⚠️ 搜索失败：HTTP {response.status_code}"}

        from html import unescape
        html = response.text
        items = re.findall(r'<li class="b_algo"[^>]*>(.*?)</li>', html, re.DOTALL)
        results = []
        for item in items[:5]:
            title_match = re.search(r'<h2[^>]*><a[^>]*>(.*?)</a></h2>', item, re.DOTALL)
            url_match = re.search(r'<a[^>]*href="(https?://[^"]+)"', item)
            snippet_match = re.search(r'<p[^>]*>(.*?)</p>', item, re.DOTALL)
            if title_match:
                title = unescape(re.sub(r'<[^>]+>', '', title_match.group(1)).strip())
                url = url_match.group(1) if url_match else ""
                snippet = unescape(re.sub(r'<[^>]+>', '', snippet_match.group(1)).strip()) if snippet_match else ""
                results.append({
                    "title": title,
                    "url": url,
                    "snippet": snippet[:300]
                })
        if not results:
            return {"success": True, "results": [], "message": "未找到相关结果，请尝试其他关键词"}
        return {"success": True, "results": results}
    except requests.Timeout:
        return {"success": False, "results": [], "error": "⚠️ 搜索超时，请稍后重试"}
    except Exception as e:
        return {"success": False, "results": [], "error": f"⚠️ 搜索出错：{e}"}


def format_results(search_result):
    """格式化搜索结果"""
    if not search_result.get("success"):
        return search_result.get("error", "搜索失败")
    results = search_result.get("results", [])
    if not results:
        return search_result.get("message", "未找到结果")
    lines = []
    for i, r in enumerate(results, 1):
        lines.append(f"{i}. {r['title']}")
        if r.get("snippet"):
            lines.append(f"   {r['snippet']}")
        if r.get("url"):
            lines.append(f"   🔗 {r['url']}")
        lines.append("")
    return "\n".join(lines)


def build_search_card(keyword, results):
    """构建飞书互动卡片格式的搜索结果"""
    def safe_text(text):
        if not text:
            return ""
        return text.replace("\n", " ").strip()

    elements = [
        {
            "tag": "div",
            "text": {
                "tag": "lark_md",
                "content": f"**查询词:** {safe_text(keyword)}"
            }
        }
    ]
    for i, item in enumerate(results[:3], 1):
        title = safe_text(item.get("title", ""))
        url = safe_text(item.get("url", ""))
        snippet = safe_text(item.get("snippet", ""))
        content_lines = [f"{i}. {title}"]
        if snippet:
            content_lines.append(snippet)
        if url:
            content_lines.append(url)
        elements.append({
            "tag": "div",
            "text": {
                "tag": "lark_md",
                "content": "\n".join(content_lines)
            }
        })
    return {
        "config": {"wide_screen_mode": True},
        "header": {"title": {"tag": "plain_text", "content": "搜索结果"}, "template": "blue"},
        "elements": elements
    }


def handle_search(user_input):
    """处理搜索指令"""
    keyword = user_input.replace("搜索", "", 1).strip()
    for word in ["从", "关于", "有关", "对于", "的", "信息", "怎么样", "如何", "是什么"]:
        keyword = keyword.replace(word, "")
    keyword = keyword.strip()
    if not keyword:
        return "请指定搜索关键词，例如：搜索 Python 教程"
    result = search_web(keyword)
    if not result.get("success"):
        return result.get("error", "搜索失败")
    if not result.get("results"):
        return result.get("message", "未找到结果")
    return {
        "type": "card",
        "card": build_search_card(keyword, result.get("results", [])),
        "fallback": format_results(result)
    }

# ===== 城市获取 =====
def get_city_from_config_or_default():
    """从 config/settings.yaml 读取城市，失败时返回默认值北京"""
    import os
    config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'settings.yaml')
    try:
        import yaml
        with open(config_path, 'r', encoding='utf-8') as f:
            cfg = yaml.safe_load(f)
            if cfg:
                val = cfg.get('location') or cfg.get('city')
                if val:
                    import re
                    m = re.match(r'([\u4e00-\u9fa5]{2,3}(?:市)?)', val)
                    if m:
                        return m.group(1).replace('市', '')
    except:
        pass
    return "北京"
