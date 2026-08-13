# AI Assistant System

这是一个基于飞书 Bot 的本地优先 AI 助理系统，当前基线为三角色架构：

- 闲聊助手：chat-assistant
- 办公助手：office-assistant
- 日程助手：life-assistant

## 运行环境

- 工作区：/Volumes/BR256G/ai-assistant-system
- 测试环境标记：.env_type = test
- 回调端口：5101
- 只允许使用测试端口 5101/5102/5103，禁止操作主环境 5001/5002/5003

## 快速开始

```bash
python3 scripts/check_env.py
bash scripts/start_all_services.sh
```

## 常用命令

```bash
python3 scripts/diagnose.py
bash scripts/restart_callback.sh
venv/bin/python3 scripts/regression_test.py
```

## 关键入口

- 回调服务：[shared/feishu-callback/callback_server.py](shared/feishu-callback/callback_server.py)
- 闲聊入口：[assistants/chat-assistant/src/message_handler.py](assistants/chat-assistant/src/message_handler.py)
- 办公入口：[assistants/office-assistant/src/document_handler.py](assistants/office-assistant/src/document_handler.py)
- 日程入口：[assistants/life-assistant/src/__init__.py](assistants/life-assistant/src/__init__.py)
- 设计与交接文档：[docs/跨会话交接文档.md](docs/跨会话交接文档.md)
- 项目规则：[AGENTS.md](AGENTS.md)

## 注意事项

- 修改入口、路由、回调逻辑后，通常需要执行回调重启和回归测试。
- 保持三角色边界清晰，避免直接耦合多个助手。
- 拒绝在主环境中操作 5001/5002/5003 或非当前工作区路径。
