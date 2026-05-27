"""
模块名称：search
功能描述：联网搜索与本地知识库检索
对外接口：
    - search_web(keyword): 联网搜索
    - search_archive(keyword): 本地归档搜索
    - format_results(result): 格式化搜索结果
    - archive_search(query, result): 归档搜索结果
依赖：
    - 标准库：os, logging, json
    - 第三方：requests
    - 项目内：无
版本：v1.0
更新记录：
    - 2026-05-23: 添加统一注释头
"""
import requests
import json
import os
import logging
import re
from datetime import datetime
from html import unescape

logging.basicConfig(level=logging.DEBUG, format='[%(levelname)s] %(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

SEARCH_ARCHIVE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "knowledge_base")
SEARCH_ARCHIVE_FILE = os.path.join(SEARCH_ARCHIVE_DIR, "search_archive.json")
TIMEOUT = 10

SEARCH_URL = "https://www.bing.com/search"


def search_web(query):
    """使用 Bing 搜索，解析 HTML 结果"""
    logger.debug(f"收到搜索请求：{query}")
    
    # 检测网络连接
    try:
        test = requests.get("https://www.baidu.com", timeout=3)
        logger.debug("网络连接正常")
    except requests.RequestException:
        return {"success": False, "results": [], "error": "⚠️ 无网络连接，请检查网络后重试"}
    
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        }
        params = {"q": query, "count": 10}
        
        logger.debug(f"发送搜索请求到 Bing")
        response = requests.get(SEARCH_URL, params=params, headers=headers, timeout=TIMEOUT)
        logger.debug(f"HTTP 状态码：{response.status_code}")
        
        if response.status_code != 200:
            return {"success": False, "results": [], "error": f"⚠️ 请求失败（状态码 {response.status_code}）"}
        
        html = response.text
        
        # 提取搜索结果
        results = []
        
        # 匹配每个搜索条目
        items = re.findall(r'<li class="b_algo"[^>]*>(.*?)</li>', html, re.DOTALL)
        logger.debug(f"找到 {len(items)} 个搜索结果块")
        
        for item in items[:5]:
            # 提取标题
            title_match = re.search(r'<h2[^>]*><a[^>]*>(.*?)</a></h2>', item, re.DOTALL)
            # 提取链接
            url_match = re.search(r'<a[^>]*href="(https?://[^"]+)"', item)
            # 提取摘要
            snippet_match = re.search(r'<p[^>]*>(.*?)</p>', item, re.DOTALL)
            
            if title_match:
                title = unescape(re.sub(r'<[^>]+>', '', title_match.group(1))).strip()
                url = url_match.group(1) if url_match else ""
                snippet = unescape(re.sub(r'<[^>]+>', '', snippet_match.group(1))).strip() if snippet_match else ""
                
                results.append({
                    "title": title,
                    "url": url,
                    "snippet": snippet[:300]
                })
        
        if not results:
            return {"success": True, "results": [], "message": "未找到相关结果，请尝试其他关键词"}
        
        logger.debug(f"共解析 {len(results)} 条结果")
        archive_search(query, results)
        return {"success": True, "results": results}
        
    except requests.Timeout:
        return {"success": False, "results": [], "error": "⚠️ 搜索超时，请稍后重试"}
    except Exception as e:
        logger.error(f"搜索出错：{e}")
        return {"success": False, "results": [], "error": f"⚠️ 搜索出错：{e}"}


def archive_search(query, results):
    """将搜索结果归档到本地知识库"""
    os.makedirs(SEARCH_ARCHIVE_DIR, exist_ok=True)
    
    record = {
        "query": query,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "results": results
    }
    
    archive = []
    if os.path.exists(SEARCH_ARCHIVE_FILE):
        with open(SEARCH_ARCHIVE_FILE, "r", encoding="utf-8") as f:
            archive = json.load(f)
    
    archive.insert(0, record)
    archive = archive[:200]
    
    with open(SEARCH_ARCHIVE_FILE, "w", encoding="utf-8") as f:
        json.dump(archive, f, ensure_ascii=False, indent=2)
    
    logger.debug(f"搜索已归档，当前共 {len(archive)} 条记录")


def search_archive(query):
    """在本地知识库中检索"""
    if not os.path.exists(SEARCH_ARCHIVE_FILE):
        return {"found": False, "results": [], "message": "暂无搜索历史"}
    
    with open(SEARCH_ARCHIVE_FILE, "r", encoding="utf-8") as f:
        archive = json.load(f)
    
    matched = []
    for record in archive:
        if query.lower() in record["query"].lower():
            matched.append(record)
    
    return {
        "found": len(matched) > 0,
        "results": matched,
        "total_archived": len(archive)
    }


def format_results(search_result):
    """将搜索结果格式化为可读文本"""
    if not search_result.get("success"):
        return search_result.get("error", "搜索失败")
    
    results = search_result.get("results", [])
    if not results:
        return search_result.get("message", "未找到结果")
    
    lines = []
    for i, r in enumerate(results, 1):
        lines.append(f"{i}. {r['title']}")
        lines.append(f"   {r['snippet'][:200]}")
        if r.get("url"):
            lines.append(f"   🔗 {r['url']}")
        lines.append("")
    
    return "\n".join(lines)
