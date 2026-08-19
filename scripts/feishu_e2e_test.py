#!/usr/bin/env python3
"""
模块名称：feishu_e2e_test
功能描述：飞书客户端模拟 — 端到端 HTTP 测试脚本
          模拟飞书 Webhook 请求，逐一测试全部路由与处理链路
对外接口：
    - 直接运行：python3 scripts/feishu_e2e_test.py
    - 筛选服务：python3 scripts/feishu_e2e_test.py --service chat
依赖：
    - 标准库：os, sys, json, time
    - 第三方：requests
版本：v2.0
更新记录：
    - 2026-05-28: 初始创建，覆盖 3 个服务 5 个角色全部路由
    - 2026-08-19: v2.0 对齐三角色基线，移除 4号文件(5082)/5号系统(5103) 服务测试段
"""
import os
import sys
import json
import time
import requests

BASE_CALLBACK = "http://127.0.0.1:5101"

TIMEOUT = 15
results = {"pass": 0, "fail": 0, "skip": 0}
filter_service = None

if "--service" in sys.argv:
    idx = sys.argv.index("--service")
    if idx + 1 < len(sys.argv):
        filter_service = sys.argv[idx + 1]


def _assert(condition, msg):
    if condition:
        results["pass"] += 1
        return True
    results["fail"] += 1
    print(f"  ❌ {msg}")
    return False


def _check(label, resp, expected_status=200):
    ok = _assert(resp.status_code == expected_status,
                 f"{label}: 期望状态 {expected_status}，实际 {resp.status_code}")
    if not ok:
        print(f"     响应体: {resp.text[:200]}")
    return ok


def _section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


def _test(label, fn):
    if results["fail"] > 0:
        results["skip"] += 1
        print(f"  ⏭️  {label} (前置失败)")
        return
    try:
        fn()
        print(f"  ✅ {label}")
    except Exception as e:
        results["fail"] += 1
        print(f"  ❌ {label}: {e}")


# =====================================================================
# 1. 回调服务 (5101) — 1号/2号/3号AI
# =====================================================================
def test_callback_service():
    if filter_service and filter_service not in ("callback", "all"):
        return
    _section("1. 回调服务 :5101（1号/2号/3号AI）")

    _test("/health", lambda: _check("health",
        requests.get(f"{BASE_CALLBACK}/health", timeout=TIMEOUT)))

    _test("challenge 验证", lambda: _check("challenge",
        requests.post(f"{BASE_CALLBACK}/webhook", json={"challenge": "e2e_test"},
                      timeout=TIMEOUT)))
    _test("challenge 返回值", lambda: _assert(
        requests.post(f"{BASE_CALLBACK}/webhook", json={"challenge": "e2e_test"},
                      timeout=TIMEOUT).json().get("challenge") == "e2e_test",
        "challenge 回显不匹配"))

    _test("空 body", lambda: _check("空body",
        requests.post(f"{BASE_CALLBACK}/webhook", json={}, timeout=TIMEOUT), 400))

    _test("空数据", lambda: _check("空数据",
        requests.post(f"{BASE_CALLBACK}/webhook", data="notjson",
                      headers={"Content-Type": "application/json"}, timeout=TIMEOUT), 400))

    # ---------- 1号AI 闲聊 ----------
    _test("1号AI 文本消息",
        lambda: _check("1号AI",
            requests.post(f"{BASE_CALLBACK}/webhook", json=_text_msg("你好"), timeout=TIMEOUT)))

    _test("1号AI clear 命令",
        lambda: _check("clear",
            requests.post(f"{BASE_CALLBACK}/webhook", json=_text_msg("clear"), timeout=TIMEOUT)))

    _test("1号AI 设置/查看提示词",
        lambda: _check("提示词",
            requests.post(f"{BASE_CALLBACK}/webhook", json=_text_msg("设置提示词：你是助手"),
                          timeout=TIMEOUT)))

    _test("1号AI 查看提示词",
        lambda: _check("查看提示词",
            requests.post(f"{BASE_CALLBACK}/webhook", json=_text_msg("查看提示词"), timeout=TIMEOUT)))

    _test("1号AI 重置提示词",
        lambda: _check("重置提示词",
            requests.post(f"{BASE_CALLBACK}/webhook", json=_text_msg("重置提示词"), timeout=TIMEOUT)))

    _test("1号AI 天气查询",
        lambda: _check("天气",
            requests.post(f"{BASE_CALLBACK}/webhook", json=_text_msg("天气 北京"), timeout=TIMEOUT)))

    _test("1号AI 翻译",
        lambda: _check("翻译",
            requests.post(f"{BASE_CALLBACK}/webhook", json=_text_msg("翻译 hello"), timeout=TIMEOUT)))

    _test("1号AI 知识库查询",
        lambda: _check("知识库",
            requests.post(f"{BASE_CALLBACK}/webhook", json=_text_msg("查知识：测试"), timeout=TIMEOUT)))

    _test("1号AI 身份识别",
        lambda: _check("我是谁",
            requests.post(f"{BASE_CALLBACK}/webhook", json=_text_msg("我是谁"), timeout=TIMEOUT)))

    # ---------- 2号AI 办公助理 ----------
    _test("2号AI #办公 help",
        lambda: _check("#办公",
            requests.post(f"{BASE_CALLBACK}/webhook", json=_text_msg("#办公 help"), timeout=TIMEOUT)))

    _test("2号AI #办公 ppt",
        lambda: _check("#办公 ppt",
            requests.post(f"{BASE_CALLBACK}/webhook",
                          json=_text_msg("#办公 ppt 第一页\n第二页"), timeout=TIMEOUT)))

    _test("2号AI #office help（旧前缀兼容）",
        lambda: _check("#office",
            requests.post(f"{BASE_CALLBACK}/webhook",
                          json=_text_msg("#office help"), timeout=TIMEOUT)))

    _test("2号AI 转PPT",
        lambda: _check("转PPT",
            requests.post(f"{BASE_CALLBACK}/webhook",
                          json=_text_msg("转PPT"), timeout=TIMEOUT)))

    # ---------- 3号AI 生活助手 ----------
    _test("3号AI 日程 列表",
        lambda: _check("日程",
            requests.post(f"{BASE_CALLBACK}/webhook",
                          json=_text_msg("日程 列表"), timeout=TIMEOUT)))

    _test("3号AI 健康 报告",
        lambda: _check("健康",
            requests.post(f"{BASE_CALLBACK}/webhook",
                          json=_text_msg("健康 报告 日报"), timeout=TIMEOUT)))

    _test("3号AI 旅行 列表",
        lambda: _check("旅行",
            requests.post(f"{BASE_CALLBACK}/webhook",
                          json=_text_msg("旅行 列表"), timeout=TIMEOUT)))

    _test("3号AI 锻炼 列表",
        lambda: _check("锻炼",
            requests.post(f"{BASE_CALLBACK}/webhook",
                          json=_text_msg("锻炼 列表"), timeout=TIMEOUT)))

    _test("3号AI 工作 列表",
        lambda: _check("工作",
            requests.post(f"{BASE_CALLBACK}/webhook",
                          json=_text_msg("工作 列表"), timeout=TIMEOUT)))

    _test("3号AI 看板",
        lambda: _check("看板",
            requests.post(f"{BASE_CALLBACK}/webhook",
                          json=_text_msg("看板"), timeout=TIMEOUT)))

    _test("3号AI 帮助",
        lambda: _check("帮助",
            requests.post(f"{BASE_CALLBACK}/webhook",
                          json=_text_msg("帮助"), timeout=TIMEOUT)))

    # ---------- 1号AI schema 2.0 格式 ----------
    _test("1号AI schema 2.0 文本消息",
        lambda: _check("schema2.0",
            requests.post(f"{BASE_CALLBACK}/webhook",
                          json=_text_msg_schema20("你好"), timeout=TIMEOUT)))

    # ---------- 未知消息类型 ----------
    _test("未知消息类型",
        lambda: _check("未知类型",
            requests.post(f"{BASE_CALLBACK}/webhook",
                          json={"schema": "2.0",
                                "header": {"event_type": "im.message.receive_v1"},
                                "event": {"message": {"message_type": "system",
                                                       "content": "{}",
                                                       "message_id": "m_mock"},
                                          "sender": {"sender_id": {"open_id": "u_mock"}}}},
                          timeout=TIMEOUT)))

    # ---------- 看板 ----------
    _test("看板路由",
        lambda: _check("看板",
            requests.get(f"{BASE_CALLBACK}/dashboard/", timeout=TIMEOUT)))


# =====================================================================
# 辅助: 构建飞书 Webhook 模拟 payload
# =====================================================================
def _text_msg(text, open_id="u_e2e_test"):
    return {
        "schema": "1.0",
        "type": "im.message.receive_v1",
        "event": {
            "message": {
                "chat_type": "p2p",
                "message_type": "text",
                "content": json.dumps({"text": text}),
                "message_id": "m_e2e_" + str(int(time.time() * 1000000)),
            },
            "sender": {
                "sender_id": {"open_id": open_id}
            }
        }
    }


def _text_msg_schema20(text, open_id="u_e2e_test"):
    return {
        "schema": "2.0",
        "header": {"event_type": "im.message.receive_v1"},
        "event": {
            "message": {
                "chat_type": "p2p",
                "message_type": "text",
                "content": json.dumps({"text": text}),
                "message_id": "m_e2e_" + str(int(time.time() * 1000000)),
            },
            "sender": {
                "sender_id": {"open_id": open_id}
            }
        }
    }


def _text_msg_type(msg_type, text, open_id="u_e2e_test"):
    return {
        "schema": "1.0",
        "type": "im.message.receive_v1",
        "event": {
            "message": {
                "chat_type": "p2p",
                "message_type": msg_type,
                "content": json.dumps({"text": text}),
                "message_id": "m_e2e_" + str(int(time.time() * 1000000)),
            },
            "sender": {
                "sender_id": {"open_id": open_id}
            }
        }
    }


def _file_msg(filename, file_key, open_id="u_e2e_test"):
    return {
        "schema": "1.0",
        "type": "im.message.receive_v1",
        "event": {
            "message": {
                "chat_type": "p2p",
                "message_type": "file",
                "content": json.dumps({"file_key": file_key, "file_name": filename}),
                "message_id": "m_e2e_" + str(int(time.time() * 1000000)),
            },
            "sender": {
                "sender_id": {"open_id": open_id}
            }
        }
    }


def _image_msg(image_key, open_id="u_e2e_test"):
    return {
        "schema": "1.0",
        "type": "im.message.receive_v1",
        "event": {
            "message": {
                "chat_type": "p2p",
                "message_type": "image",
                "content": json.dumps({"image_key": image_key}),
                "message_id": "m_e2e_" + str(int(time.time() * 1000000)),
            },
            "sender": {
                "sender_id": {"open_id": open_id}
            }
        }
    }


def _audio_msg(file_key, open_id="u_e2e_test"):
    return {
        "schema": "1.0",
        "type": "im.message.receive_v1",
        "event": {
            "message": {
                "chat_type": "p2p",
                "message_type": "audio",
                "content": json.dumps({"file_key": file_key}),
                "message_id": "m_e2e_" + str(int(time.time() * 1000000)),
            },
            "sender": {
                "sender_id": {"open_id": open_id}
            }
        }
    }


# =====================================================================
# 主入口
# =====================================================================
if __name__ == "__main__":
    print("=" * 60)
    print("  飞书客户端模拟 · 端到端 HTTP 测试")
    print(f"  回调服务 :5101")
    print("=" * 60)

    target = filter_service or "all"
    print(f"\n  筛选: {target}\n")

    test_callback_service()

    total = results["pass"] + results["fail"] + results["skip"]
    print(f"\n{'='*60}")
    print(f"  📊 测试报告")
    print(f"{'='*60}")
    print(f"  总计: {total}")
    print(f"  ✅ 通过: {results['pass']}")
    print(f"  ❌ 失败: {results['fail']}")
    print(f"  ⏭️  跳过: {results['skip']}")
    if results["fail"] == 0:
        print(f"  🎉 全部通过!")
    else:
        print(f"  ⚠️  存在失败项")
    print()

    sys.exit(1 if results["fail"] > 0 else 0)
