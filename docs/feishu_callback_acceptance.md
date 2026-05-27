# 飞书回调链路验收报告

## 目的

验证飞书机器人回调链路是否完整可用，包括：

- 本地回调服务正常启动并响应健康检查
- 公网隧道 `cloudflared` 成功映射本地回调地址
- `webhook` 公网地址可达并能正确处理飞书事件
- 飞书消息发送与接收闭环可用

## 验收结论

- 本地服务 `/health` 可用
- 公网回调地址 `https://admissions-affair-gem-timeline.trycloudflare.com/webhook` 可达
- 公网 `POST /webhook` 请求返回 `200` 并产生本地事件日志
- 飞书群聊消息发送验证成功
- 飞书私聊 `open_id` 发送验证成功

## 证据

1. 本地健康检查：
   - `curl -sS http://127.0.0.1:5001/health` 返回 `{ "status": "ok" }`

2. 公网隧道地址：
   - 从 `logs/cloudflared.log` 中解析到 `https://admissions-affair-gem-timeline.trycloudflare.com`

3. 公网回调验证：
   - `POST https://admissions-affair-gem-timeline.trycloudflare.com/webhook` 返回 `200 {"code":0,"msg":"success"}`

4. 日志记录：
   - `logs/flask.log` 包含条目：
     - `📩 用户 ou_84b0c82ab02e6aa3c78d42741710ee91 说: 【公网验证】测试消息，请忽略。`
     - `回复成功: 【公网验证】测试消息，请忽略。`

5. 飞书消息校验：
   - 群聊 `chat_id=oc_7e3442d95ddf0b3c226cb528a4db2ced` 发信成功
   - 私聊 `open_id=ou_84b0c82ab02e6aa3c78d42741710ee91` 发信成功

## 复现命令

```bash
cd ~/ai-assistant-system
./venv/bin/python scripts/verify_feishu_callback.py
```

## 建议

- 将 `scripts/verify_feishu_callback.py` 作为日常运维检查项
- 若回调链路异常，优先检查：
  - 本地 `shared/feishu-callback/callback_server.py` 是否运行
  - `cloudflared` 隧道是否连接成功
  - `shared/feishu-bot/.env` 中飞书凭证是否有效
