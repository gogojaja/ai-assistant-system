#!/usr/bin/env python3
"""
模块名称：test_search
功能描述：搜索模块测试脚本，包含联网搜索、格式化结果、本地归档与检索共3组测试用例
对外接口：
    - test1(): 测试联网搜索已知关键词
    - test2(): 测试格式化搜索结果
    - test3(): 测试本地归档和检索
依赖：
    - 标准库：os, sys
    - 第三方：无
    - 项目内：search (search_web, search_archive, format_results, archive_search)
版本：v1.0
更新记录：
    - 2026-05-23: 自动添加统一注释头
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from search import search_web, search_archive, format_results, archive_search

def test1():
    """测试1：搜索已知关键词"""
    print("测试1：搜索 Python")
    result = search_web("Python")
    assert result["success"], f"搜索失败：{result.get('error')}"
    assert len(result["results"]) > 0, "搜索结果为空"
    print(f"✅ 测试1通过：获取到 {len(result['results'])} 条结果")

def test2():
    """测试2：格式化搜索结果"""
    print("测试2：格式化搜索结果")
    sample = {
        "success": True,
        "results": [
            {"title": "测试标题", "url": "https://example.com", "snippet": "这是测试摘要"}
        ]
    }
    formatted = format_results(sample)
    assert "测试标题" in formatted
    assert "测试摘要" in formatted
    print(f"✅ 测试2通过：格式化正常")

def test3():
    """测试3：本地归档和检索"""
    print("测试3：本地归档和检索")
    archive_search("测试查询词", [
        {"title": "测试", "url": "", "snippet": "测试内容"}
    ])
    result = search_archive("测试查询词")
    assert result["found"], "本地检索失败"
    print(f"✅ 测试3通过：找到 {len(result['results'])} 条匹配")

if __name__ == "__main__":
    print("运行搜索模块测试...\n")
    test1()
    test2()
    test3()
    print("\n🎉 全部测试通过")