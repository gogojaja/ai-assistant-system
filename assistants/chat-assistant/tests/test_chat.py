#!/usr/bin/env python3
"""
模块名称：test_chat
功能描述：1号AI 完整测试脚本，包含对话历史保存/加载、清空历史、本地知识库检索共3组测试用例
对外接口：
    - cleanup(): 测试前清理对话历史
    - test1_chat_history(): 测试对话历史保存与加载
    - test2_clear_history(): 测试清空对话历史
    - test3_local_search(): 测试本地知识库检索
依赖：
    - 标准库：json, os, sys
    - 第三方：无
    - 项目内：chat (load_history, save_history, clear_history, format_history), search (search_archive, format_results, archive_search)
版本：v1.0
更新记录：
    - 2026-05-23: 自动添加统一注释头
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from chat import load_history, save_history, clear_history, format_history
from search import search_archive, format_results, archive_search
import json

def cleanup():
    """测试前清理"""
    clear_history()

def test1_chat_history():
    """测试1：对话历史保存与加载"""
    print("测试1：对话历史保存与加载")
    cleanup()
    
    messages = [
        {"role": "user", "content": "你好"},
        {"role": "assistant", "content": "你好！有什么可以帮助你的？"}
    ]
    save_history(messages)
    
    loaded = load_history()
    assert len(loaded) == 2, f"历史长度应为2，实际为{len(loaded)}"
    assert loaded[0]["content"] == "你好"
    assert loaded[1]["role"] == "assistant"
    
    print(f"✅ 测试1通过：保存并加载了 {len(loaded)} 条消息")
    return True

def test2_clear_history():
    """测试2：清空对话历史"""
    print("测试2：清空对话历史")
    
    # 先保存一些内容
    save_history([{"role": "user", "content": "测试消息"}])
    assert len(load_history()) == 1
    
    # 清空
    result = clear_history()
    assert "已清空" in result
    assert len(load_history()) == 0
    
    print("✅ 测试2通过：历史清空正常")
    return True

def test3_local_search():
    """测试3：本地知识库检索"""
    print("测试3：本地知识库检索")
    
    # 确保有归档数据
    archive_search("验收测试", [
        {"title": "测试条目", "url": "", "snippet": "这是验收测试的内容"}
    ])
    
    result = search_archive("验收测试")
    assert result["found"], "应找到匹配记录"
    assert len(result["results"]) >= 1
    
    print(f"✅ 测试3通过：检索到 {len(result['results'])} 条匹配（共 {result['total_archived']} 条归档）")
    return True

if __name__ == "__main__":
    print("🔧 1号AI 完整测试\n")
    
    all_pass = True
    for test_func in [test1_chat_history, test2_clear_history, test3_local_search]:
        try:
            test_func()
        except Exception as e:
            print(f"❌ 测试失败：{e}")
            all_pass = False
        print()
    
    cleanup()
    
    if all_pass:
        print("🎉 全部测试通过！1号AI 阶段1验收合格。")
    else:
        print("⚠️ 存在失败项，请检查。")