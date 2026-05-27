#!/usr/bin/env python3
"""
模块名称：test_search
功能描述：验证共享搜索工具是否可用，检查搜索命令解析和结果格式化。
对外接口：
    - test_search_command()

依赖：
    - 标准库：sys, os
    - 项目内：shared.utils (handle_search)
版本：v1.0
"""
import sys
import os
sys.path.insert(0, os.path.abspath('.'))
from shared.utils import handle_search


def test_search_command():
    print('测试搜索命令')
    result = handle_search('搜索 Python')
    assert isinstance(result, dict) and result.get('type') == 'card', f'搜索结果应返回卡片格式: {result}'
    card = result.get('card')
    assert isinstance(card, dict), f'卡片内容格式错误: {card}'
    assert card.get('header') and card.get('elements'), f'卡片缺少 header 或 elements: {card}'
    assert isinstance(result.get('fallback'), str) and result.get('fallback'), f'搜索结果应包含文本回退: {result}'
    print('✅ 搜索命令执行通过')


if __name__ == '__main__':
    test_search_command()
    print('\n🎉 搜索功能测试通过')
