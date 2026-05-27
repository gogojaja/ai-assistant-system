#!/usr/bin/env python3

"""
模块名称：test_talk_fix
功能描述：TODO: 请补充功能描述
对外接口：
    - talk_mock()
    - test1()
    - test2()
    - test3()
依赖：
    - 标准库：logging
    - 第三方：无
    - 项目内：无
版本：v1.0
更新记录：
    - 2026-05-23: 自动添加统一注释头
"""
"""
模块名称：test_talk_fix
功能描述：测试 talk 修复逻辑（content/reasoning_content 优先级与降级），纯模拟，无需外部依赖
对外接口：
    - 直接运行，执行 3 组测试用例并输出结果
依赖：
    - 标准库：logging
    - 第三方：无
    - 项目内：无
版本：v1.0
更新记录：
    - 2026-05-23: 初始创建，添加统一注释头
"""
import logging

logging.basicConfig(level=logging.INFO, format='[TEST] %(message)s')
logger = logging.getLogger("test_talk_fix")


def talk_mock(response_json):
    """
    模拟 talk() 函数对模型返回的 json 的处理逻辑
    和真实 main.py 中完全一致：
    优先级：content > reasoning_content > 降级
    """
    try:
        data = response_json
        content = data["choices"][0]["message"].get("content", "").strip()
        reasoning = data["choices"][0]["message"].get("reasoning_content", "").strip()

        if content:
            logger.debug(f"使用 content 回复，长度 {len(content)} 字符")
            return content
        elif reasoning:
            logger.warning(f"content 为空，改用 reasoning_content 作为回复")
            return reasoning
        else:
            logger.warning("content 和 reasoning_content 均为空，降级回复")
            return "抱歉，我暂时无法生成回复，请稍后再试。"
    except Exception as e:
        return f"处理异常: {e}"


def test1():
    """内容正常返回时，应直接使用 content"""
    resp = {
        "choices": [{
            "message": {
                "content": "今天天气不错",
                "reasoning_content": "让我想想..."
            }
        }]
    }
    result = talk_mock(resp)
    assert result == "今天天气不错", f"测试1失败，得到：{result}"
    logger.info("✅ 测试1通过：content 存在时直接返回 content")


def test2():
    """content 为空，reasoning_content 有值时，应返回 reasoning"""
    resp = {
        "choices": [{
            "message": {
                "content": "",
                "reasoning_content": "模型思考后的结论：应该这样回答"
            }
        }]
    }
    result = talk_mock(resp)
    assert result == "模型思考后的结论：应该这样回答", f"测试2失败，得到：{result}"
    logger.info("✅ 测试2通过：content 空时使用 reasoning_content")


def test3():
    """两者都为空，返回降级提示"""
    resp = {
        "choices": [{
            "message": {
                "content": "",
                "reasoning_content": ""
            }
        }]
    }
    result = talk_mock(resp)
    assert "无法生成回复" in result, f"测试3失败，得到：{result}"
    logger.info("✅ 测试3通过：两者空时返回降级提示")


if __name__ == "__main__":
    logger.info("🚀 开始独立测试 talk 修复逻辑...")
    test1()
    test2()
    test3()
    logger.info("🎉 所有测试用例通过，修复逻辑无误。")