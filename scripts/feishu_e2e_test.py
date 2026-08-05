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
版本：v1.0
更新记录：
    - 2026-05-28: 初始创建，覆盖 3 个服务 5 个角色全部路由
"""
import os
import sys
import json
import time
import requests

BASE_CALLBACK = "http://127.0.0.1:5101"
BASE_FILE = "http://127.0.0.1:5102"
BASE_SYS = "http://127.0.0.1:5103"

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

    # ---------- 代理路由 ----------
    _test("反向代理 /webhook_file",
        lambda: _check("代理file",
            requests.post(f"{BASE_CALLBACK}/webhook_file",
                          json={"challenge": "proxy_test"}, timeout=TIMEOUT)))

    _test("反向代理 /webhook_sys",
        lambda: _check("代理sys",
            requests.post(f"{BASE_CALLBACK}/webhook_sys",
                          json={"challenge": "proxy_test"}, timeout=TIMEOUT)))

    _test("反向代理 /health_file",
        lambda: _check("健康file",
            requests.get(f"{BASE_CALLBACK}/health_file", timeout=TIMEOUT)))

    _test("反向代理 /health_sys",
        lambda: _check("健康sys",
            requests.get(f"{BASE_CALLBACK}/health_sys", timeout=TIMEOUT)))

    _test("反向代理 未知路由",
        lambda: _check("未知",
            requests.post(f"{BASE_CALLBACK}/webhook_unknown",
                          json={}, timeout=TIMEOUT), 404))

    # ---------- 看板 ----------
    _test("看板路由",
        lambda: _check("看板",
            requests.get(f"{BASE_CALLBACK}/dashboard/", timeout=TIMEOUT)))


# =====================================================================
# 2. 文件助手服务 (5102) — 4号AI
# =====================================================================
def test_file_service():
    if filter_service and filter_service not in ("file", "all"):
        return
    _section("2. 文件助手 :5102（4号AI）")

    _test("/health",
        lambda: _check("health",
            requests.get(f"{BASE_FILE}/health", timeout=TIMEOUT)))

    _test("challenge 验证",
        lambda: _check("challenge",
            requests.post(f"{BASE_FILE}/webhook",
                          json={"challenge": "e2e_test"}, timeout=TIMEOUT)))

    _test("空 body",
        lambda: _check("空body",
            requests.post(f"{BASE_FILE}/webhook", json={}, timeout=TIMEOUT), 400))

    _test("4号AI 帮助",
        lambda: _check("帮助",
            requests.post(f"{BASE_FILE}/webhook",
                          json=_text_msg("帮助"), timeout=TIMEOUT)))

    _test("4号AI 查看路径",
        lambda: _check("查看",
            requests.post(f"{BASE_FILE}/webhook",
                          json=_text_msg("查看 /"), timeout=TIMEOUT)))

    _test("4号AI 搜索",
        lambda: _check("搜索",
            requests.post(f"{BASE_FILE}/webhook",
                          json=_text_msg("搜索 test"), timeout=TIMEOUT)))

    _test("4号AI 信息",
        lambda: _check("信息",
            requests.post(f"{BASE_FILE}/webhook",
                          json=_text_msg("信息 /"), timeout=TIMEOUT)))

    _test("4号AI 问号",
        lambda: _check("？",
            requests.post(f"{BASE_FILE}/webhook",
                          json=_text_msg("？"), timeout=TIMEOUT)))

    _test("4号AI #4 前缀",
        lambda: _check("#4",
            requests.post(f"{BASE_FILE}/webhook",
                          json=_text_msg("#4 帮助"), timeout=TIMEOUT)))

    _test("4号AI #file 前缀",
        lambda: _check("#file",
            requests.post(f"{BASE_FILE}/webhook",
                          json=_text_msg("#file 帮助"), timeout=TIMEOUT)))

    _test("4号AI 文件消息（模拟）",
        lambda: _check("文件消息",
            requests.post(f"{BASE_FILE}/webhook",
                          json=_file_msg("test.txt", "fk_mock"), timeout=TIMEOUT)))

    _test("4号AI 图片消息（模拟）",
        lambda: _check("图片消息",
            requests.post(f"{BASE_FILE}/webhook",
                          json=_image_msg("ik_mock"), timeout=TIMEOUT)))

    _test("4号AI 语音消息（应拒绝）",
        lambda: _check("语音拒绝",
            requests.post(f"{BASE_FILE}/webhook",
                          json=_audio_msg("ak_mock"), timeout=TIMEOUT)))

    _test("4号AI 未知消息类型",
        lambda: _check("未知类型",
            requests.post(f"{BASE_FILE}/webhook",
                          json=_text_msg_type("system", "unknown"), timeout=TIMEOUT)))

    _test("4号AI schema 2.0",
        lambda: _check("schema2.0",
            requests.post(f"{BASE_FILE}/webhook",
                          json=_text_msg_schema20("帮助"), timeout=TIMEOUT)))


# =====================================================================
# 3. 系统管理服务 (5103) — 5号AI
# =====================================================================
def test_sys_service():
    if filter_service and filter_service not in ("sys", "all"):
        return
    _section("3. 系统管理 :5103（5号AI）")

    _test("/health",
        lambda: _check("health",
            requests.get(f"{BASE_SYS}/health", timeout=TIMEOUT)))

    _test("challenge 验证",
        lambda: _check("challenge",
            requests.post(f"{BASE_SYS}/webhook",
                          json={"challenge": "e2e_test"}, timeout=TIMEOUT)))

    _test("空 body",
        lambda: _check("空body",
            requests.post(f"{BASE_SYS}/webhook", json={}, timeout=TIMEOUT), 400))

    _test("5号AI help",
        lambda: _check("help",
            requests.post(f"{BASE_SYS}/webhook",
                          json=_text_msg("help"), timeout=TIMEOUT)))

    _test("5号AI #5 sys status",
        lambda: _check("#5 sys status",
            requests.post(f"{BASE_SYS}/webhook",
                          json=_text_msg("#5 sys status"), timeout=TIMEOUT)))

    _test("5号AI #5 sys disk",
        lambda: _check("#5 sys disk",
            requests.post(f"{BASE_SYS}/webhook",
                          json=_text_msg("#5 sys disk"), timeout=TIMEOUT)))

    _test("5号AI #5 sys mem",
        lambda: _check("#5 sys mem",
            requests.post(f"{BASE_SYS}/webhook",
                          json=_text_msg("#5 sys mem"), timeout=TIMEOUT)))

    _test("5号AI #5 sys load",
        lambda: _check("#5 sys load",
            requests.post(f"{BASE_SYS}/webhook",
                          json=_text_msg("#5 sys load"), timeout=TIMEOUT)))

    _test("5号AI #5 svc list",
        lambda: _check("#5 svc list",
            requests.post(f"{BASE_SYS}/webhook",
                          json=_text_msg("#5 svc list"), timeout=TIMEOUT)))

    _test("5号AI #5 ps list",
        lambda: _check("#5 ps list",
            requests.post(f"{BASE_SYS}/webhook",
                          json=_text_msg("#5 ps list"), timeout=TIMEOUT)))

    _test("5号AI #5 log flask",
        lambda: _check("#5 log flask",
            requests.post(f"{BASE_SYS}/webhook",
                          json=_text_msg("#5 log flask"), timeout=TIMEOUT)))

    _test("5号AI #5 backup now",
        lambda: _check("#5 backup now",
            requests.post(f"{BASE_SYS}/webhook",
                          json=_text_msg("#5 backup now"), timeout=TIMEOUT)))

    _test("5号AI #5 backup list",
        lambda: _check("#5 backup list",
            requests.post(f"{BASE_SYS}/webhook",
                          json=_text_msg("#5 backup list"), timeout=TIMEOUT)))

    _test("5号AI #sys 前缀（旧前缀兼容）",
        lambda: _check("#sys",
            requests.post(f"{BASE_SYS}/webhook",
                          json=_text_msg("#sys help"), timeout=TIMEOUT)))

    _test("5号AI 文件消息（应拒绝）",
        lambda: _check("文件拒绝",
            requests.post(f"{BASE_SYS}/webhook",
                          json=_file_msg("test.txt", "fk_mock"), timeout=TIMEOUT)))

    _test("5号AI 图片消息（应拒绝）",
        lambda: _check("图片拒绝",
            requests.post(f"{BASE_SYS}/webhook",
                          json=_image_msg("ik_mock"), timeout=TIMEOUT)))

    _test("5号AI 语音消息（应拒绝）",
        lambda: _check("语音拒绝",
            requests.post(f"{BASE_SYS}/webhook",
                          json=_audio_msg("ak_mock"), timeout=TIMEOUT)))

    _test("5号AI schema 2.0",
        lambda: _check("schema2.0",
            requests.post(f"{BASE_SYS}/webhook",
                          json=_text_msg_schema20("#5 sys status"), timeout=TIMEOUT)))


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
    print(f"  回调服务 :5101  |  文件助手 :5102  |  系统管理 :5103")
    print("=" * 60)

    target = filter_service or "all"
    print(f"\n  筛选: {target}\n")

    test_callback_service()
    test_file_service()
    test_sys_service()

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
