#!/usr/bin/env python3
"""
模块名称：test_weather_query
功能描述：天气查询功能测试，验证地点提取与 wttr.in 请求是否正常。
对外接口：
    - test_normalize_city()
    - test_get_weather_location()
    - test_query_full_phrase()
依赖：
    - 标准库：sys, os
    - 项目内：shared.utils (normalize_city_for_weather, get_weather)
版本：v1.0
"""
import sys
import os
sys.path.insert(0, os.path.abspath('.'))
from shared.utils import normalize_city_for_weather, get_weather


def test_weather_reply_translation():
    print('测试天气回复翻译')
    import assistants.chat_assistant.src.message_handler as mh

    original_get_weather = mh.get_weather
    original_send_message = mh.send_message
    try:
        mh.get_weather = lambda city: {
            'city': '西安市',
            'description': 'Partly Cloudy',
            'temp_c': '21',
            'humidity': '68',
            'wind_speed': '21'
        }
        results = []
        mh.send_message = lambda open_id, text: results.append(text)
        mh.process_message('西安市今天的天气', 'test_openid')
        assert results, '未发送回复'
        assert '局部多云' in results[0], f'翻译失败: {results[0]}'
        assert '2026-' in results[0], f'日期缺失: {results[0]}'
        print('✅ 天气回复翻译通过')
    finally:
        mh.get_weather = original_get_weather
        mh.send_message = original_send_message


def test_normalize_city():
    print('测试 normalize_city_for_weather')
    assert normalize_city_for_weather('西安市雁塔区今天的天气') == '西安市雁塔区'
    assert normalize_city_for_weather('今天西安市雁塔区的天气') == '西安市雁塔区'
    assert normalize_city_for_weather('请帮我查西安市雁塔区天气') == '西安市雁塔区'
    assert normalize_city_for_weather('西安市雁塔区今天的天气') == '西安市雁塔区'
    assert normalize_city_for_weather('西安市雁塔区今天的天气。') == '西安市雁塔区'
    assert normalize_city_for_weather('请问西安市雁塔区今天的天气？') == '西安市雁塔区'
    assert normalize_city_for_weather('@三号AI 西安市雁塔区今天的天气') == '西安市雁塔区'
    assert normalize_city_for_weather('<at id="123">三号AI</at>西安市雁塔区今天的天气') == '西安市雁塔区'
    assert normalize_city_for_weather('西安天气') == '西安'
    print('✅ normalize_city_for_weather 通过')


def test_get_weather_location():
    print('测试 get_weather 对具体地点的响应')
    res = get_weather('西安市雁塔区')
    assert isinstance(res, dict), f'返回类型不正确: {type(res)}'
    assert 'description' in res and 'temp_c' in res, f'返回内容不完整: {res}'
    print(f"✅ get_weather 返回 {res['city']} 天气: {res['description']} {res['temp_c']}°C")


def test_query_full_phrase():
    print('测试 get_weather 处理完整查询短语')
    res = get_weather('西安市雁塔区今天的天气')
    assert isinstance(res, dict), f'返回类型不正确: {type(res)}'
    assert 'description' in res and 'temp_c' in res, f'返回内容不完整: {res}'
    print(f"✅ 全句测试通过: {res['city']} {res['description']} {res['temp_c']}°C")


if __name__ == '__main__':
    all_pass = True
    for func in [test_weather_reply_translation, test_normalize_city, test_get_weather_location, test_query_full_phrase]:
        try:
            func()
        except AssertionError as e:
            print(f'❌ 测试失败: {e}')
            all_pass = False
        except Exception as e:
            print(f'❌ 测试异常: {e}')
            all_pass = False
        print()
    if all_pass:
        print('🎉 天气查询功能测试全部通过')
    else:
        print('⚠️ 存在失败项，请检查')
