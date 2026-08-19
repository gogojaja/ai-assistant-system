# 设计汇总

**项目名称**：三角色 AI 助理系统  
**工作区**：`/Volumes/BR256G/ai-assistant-system`  
**环境基线**：测试环境，`.env_type` = `test`  
**当前状态**：三角色（闲聊 / 办公 / 日程）已成为主运行基线，旧五角色与 4 号文件助手描述仅保留为历史归档，不作为现行运行说明。

---

## 1. 当前架构

系统采用三角色分工，统一由飞书 Bot 入口接收事件，再由回调服务分发到对应助手，用共享基础设施做配置、加密、知识库和推理路由。

| 角色 | 目录 | 职责 | 入口 |
|------|------|------|------|
| 1号 AI | `assistants/chat-assistant/` | 闲聊、天气、翻译、搜索、知识库、语音、跨会话记忆 | `message_handler.process_message()` |
| 2号 AI | `assistants/office-assistant/` | Word 摘要、Excel 分析、PPT 生成、办公文本处理 | `document_handler.process_office_text()` |
| 3号 AI | `assistants/life-assistant/` | 日程、健康、旅行、锻炼、工作管理、提醒 | `process()` |

共享层：`shared/` 提供飞书 API、回调入口、模型路由、加密、知识库和通用工具。当前主入口仍是 `shared/feishu-callback/callback_server.py`，Webhook 统一在 :5101 监听。

---

## 2. 实际运行基线

### 测试环境

- 工作区：`/Volumes/BR256G/ai-assistant-system`
- 入口端口：`5101`
- 回调地址：`https://employee-radish-fringe.ngrok-free.dev/webhook_chat`
- 当前主线：只保留三角色回调入口，不再维护旧 5102 文件助手与 4 号角色（遗留脚本改用 5082 规避 opencode 占用）

### 共享后端

- 默认路由：本地 `ollama` 单容器推理
- 本地兜底：`ollama`（单容器，localhost:11434）
- 统一入口：`shared/backend_utils.py`

### 环境约束

- 仅允许在当前测试工作区中操作 `/Volumes/BR256G/ai-assistant-system`
- 测试端口范围：5101 / 5103（5102 已被 opencode 占用；4号遗留脚本用 5082）
- 禁止操作主环境 5001 / 5002 / 5003
- 修改入口、路由、回调逻辑后，通常需重启回调服务并执行回归测试

---

## 3. 关键目录

```text
/Volumes/BR256G/ai-assistant-system
├── assistants/
│   ├── chat-assistant/
│   ├── office-assistant/
│   ├── life-assistant/
│   └── __init__.py
├── shared/
│   ├── feishu-callback/
│   ├── backend_utils.py
│   ├── feishu_api.py
│   ├── knowledge_base.py
│   ├── crypto.py
│   └── ...
├── scripts/
│   ├── check_env.py
│   ├── diagnose.py
│   ├── start_all_services.sh
│   ├── stop_all_services.sh
│   ├── restart_callback.sh
│   ├── monitor_services.sh
│   └── regression_test.py
├── docs/
│   ├── 跨会话交接文档.md
│   └── design_summary.md
├── data/
├── logs/
├── config/
├── prompts/
├── requirements/
└── AGENTS.md
```

---

## 4. 当前运行策略

- 入口统一：`callback_server.py` 接收文本、语音和文件事件
- 角色分派：在回调服务中按关键词或命令前缀分发到对应助手
- 业务边界：三角色之间不直接耦合，统一通过 `shared/` 提供基础能力
- 安全边界：不在主环境中执行 5001/5002/5003 相关操作，避免环境串扰

---

## 5. 维护说明

- 即使有历史文档保留，当前工程状态以三角色和测试环境基线为准
- 旧五角色/4号文件助手说明不再作为运行或维护依据
- 对入口脚本、回调代码和路由逻辑的改动，必须同步检查 `scripts/check_env.py` 与回归测试

---

## 6. 参考入口

- 回调服务：`shared/feishu-callback/callback_server.py`
- 闲聊入口：`assistants/chat-assistant/src/message_handler.py`
- 办公入口：`assistants/office-assistant/src/document_handler.py`
- 日程入口：`assistants/life-assistant/src/__init__.py`
- 规则说明：`AGENTS.md`
- 交接文档：`docs/跨会话交接文档.md`
- **发布工作流**：promote.sh + diff_envs.sh 就绪 ✅

---

## 5. 已完成工作

- ✅ 主环境升级至 Python 3.12.13
- ✅ 全部依赖补全（22个库）
- ✅ 核心文件恢复与软链接修复
- ✅ Flask 回调服务正常运行
- ✅ ollama 单容器本地推理（已移除 llama.cpp 聊天服务）
- ✅ 环境核验脚本可用
- ✅ 一键还原脚本 restore.sh
- ✅ 服务守护 monitor_services.sh
- ✅ 数据加密留存 (cryptography Fernet)
- ✅ 离线语音识别 (whisper.cpp 飞书接入)
- ✅ 自定义提示词管理
- ✅ 私有知识库（data/knowledge/ BM25关键词检索）
- ✅ 2号AI PPT/Word/Excel 处理
- ✅ 2号AI 文件夹监控 (watchdog)
- ✅ 4号 file-assistant 文件管理+传输
- ✅ 5号 sys-assistant 全部模块（系统监控/服务管理/进程管理/日志查看/备份管理/安全限制）
- ✅ 双 ngrok 隧道架构
- ✅ 双环境共存（主 :5001/2/3 + 测试 :5101/2/3）
- ✅ 脚本全部 `lsof -ti:` 端口级清理
- ✅ 4号相对路径访问（whitelist.yaml 自动解析）
- ✅ 5号动态端口（settings.yaml 驱动）
- ✅ 测试环境 3 套独立飞书凭证
- ✅ ~40 脚本路径修复（`~/ai-assistant-system` → `$(dirname "$0")`）
- ✅ Git 版本管理（测试环境 git init + .gitignore）
- ✅ promote.sh / diff_envs.sh 发布工作流
- ✅ 3号AI life-assistant 全部模块（日程/健康/旅行/锻炼/工作规划 + venv-life + 网页看板）
- ✅ callback_port 从 settings.yaml 读取（不再硬编码 5001）
- ✅ 3号AI 网页看板（dashboard 路由 + 手机适配）
- ✅ shared/backend_utils.py 后端通用工具（配置/唤醒/API调用/回复清理）
- ✅ shared/feishu-bot/ 飞书 WebSocket Bot
- ✅ 2号AI DocxConverter（docx→text/markdown）
- ✅ 2号AI 文件工具（FileHandler）
- ✅ 5号 sys-assistant 独立 Bot 服务（端口 5003/5103）
- ✅ 回复格式简化（无思考过程、时间放在问题/答复前）
- ✅ 中文命令路由（2号: #办公 / 转PPT；3号: 中文关键词）
- ✅ `scripts/regression_test.py` 105 项全量回归测试（全部通过）
- ✅ `_safe_load_from_file` 多路径注入修复（sys.path 补齐项目根+shared+office）
- ✅ 全局 venv 依赖补全（mammoth 1.12.0）
- ✅ 端到端 HTTP 探测：3 个服务 10 个端点全部通过
- ✅ (2026-06-13) AGENTS.md 新增 3 条沟通原则（专业态度、基于验证、不确定告知）
- ✅ (2026-06-13) config/settings.yaml 新增 `chat_api_url` 和 `chat_model` 云端路由配置
- ✅ (2026-06-13) shared/backend_utils.py 新增 ollama 后端支持（配置读取+API调用）
- ✅ (2026-06-13) 飞书1号机器人切换至 ollama 聊天实例（Qwen3-32B）

---

## 6. 待办任务

1. **5号AI sys-assistant 飞书前缀路由 `#5`/`#sys` 集成到 callback_server.py** —— 当前通过独立 Bot 服务 + 反向代理运行，可考虑合并到主路由
2. **飞书 WebSocket Bot（shared/feishu-bot/）** —— 代码结构存在，尚未接入主线流程
3. **dev-assistant 第6角色** —— 目录存在但无代码
4. **watchdog 安装** —— office-assistant 文件夹监控依赖，当前 venv-office 未安装
5. **推理后端接入 E2E 测试** —— 已统一为 ollama 单容器，后端依赖测试收敛（不再依赖 llama-server）
6. **（ollama 已移除，模型优先级项不适用）** —— 当前路由可能落到弱模型，需手动调整优先级
7. **openapi.json provider 命名规范化** —— 已统一为 `ollama-chat` / `ollama-code`，去掉了 `default` 占位符

## 7. 测试覆盖

| 模块 | 测试位置 | 用例数 | 覆盖类型 |
|------|----------|--------|----------|
| 共享模块 | `scripts/regression_test.py` | 12 | 单元测试 |
| 1号AI chat-assistant | `scripts/regression_test.py` | 17 | 单元+模拟集成 |
| 2号AI office-assistant | `scripts/regression_test.py` | 19 | 单元+模拟集成 |
| 3号AI life-assistant | `scripts/regression_test.py` | 14 | 单元+模拟集成 |
| 4号AI file-assistant | `scripts/regression_test.py` | 14 | 单元+模拟集成 |
| 5号AI sys-assistant | `scripts/regression_test.py` | 22 | 单元+模拟集成 |
| 回调服务 callback | `scripts/regression_test.py` | 7 | 模拟集成+HTTP |
| **合计** | `scripts/regression_test.py` | **105** | **全部通过** |
| 1号AI 对话历史 | `assistants/chat-assistant/tests/test_chat.py` | — | 单元测试 |
| 1号AI 搜索 | `assistants/chat-assistant/tests/test_search.py` | — | 单元测试 |
| 2号AI Word/Excel/PPT | `assistants/office-assistant/tests/test_office.py` | — | 单元测试 |
| 2号AI WordProcessor | `assistants/office-assistant/src/tests/test_word_processor.py` | — | 单元测试 |
| 2号AI Summarizer | `assistants/office-assistant/src/tests/test_summarizer.py` | — | 单元测试 |
| 2号AI DocxConverter | `assistants/office-assistant/src/tests/test_converters.py` | — | 单元测试 |
| 环境诊断 | `scripts/diagnose.py` | — | 环境核验 |
| 监控逻辑 | `scripts/test_monitor.py` | — | 逻辑测试 |
| talk修复逻辑 | `scripts/test_talk_fix.py` | — | 逻辑测试 |
| 天气查询 | `scripts/test_weather_query.py` | — | 集成测试 |
| Excel集成 | `scripts/test_excel_integration.py` | — | 集成测试 |
| 搜索工具 | `scripts/test_search.py` | — | 集成测试 |

## 8. 端到端验证（2026-05-28，历史快照）

> **归档注记（2026-08-19）**：下表为五角色时期的验证快照。PRJ-001 已裁剪 4号文件/5号系统助手，`webhook_sys`/`:5102`/`:5103` 路由已移除，现行回调仅暴露 `/health` 与 `/webhook`（:5101）。保留此表仅作历史追溯。

| 端点 | 路由 | 结果 |
|------|------|------|
| `:5101/health` | 健康检查 | ✅ `200 {"status":"ok"}` |
| `:5101/webhook_chat` | challenge 验证 | ✅ `200 {"challenge":"test123"}` |
| `:5101/webhook_chat` | 文本消息（1号闲聊） | ✅ `200 {"code":0,"msg":"success"}` |
| `:5101/webhook_chat` | `#办公 help`（2号办公） | ✅ `200 {"code":0,"msg":"success"}` |
| `:5101/webhook_chat` | `日程 列表`（3号日程） | ✅ `200 {"code":0,"msg":"success"}` |
| `:5101/webhook_sys` | `#5 sys status`（5号系统） | ✅ `200 {"code":0,"msg":"success"}` |
| `:5102/webhook` | challenge 验证（4号文件） | ✅ `200 {"challenge":"test456"}` |
| `:5102/webhook` | `帮助`（4号文件） | ✅ `200 {"code":0,"msg":"success"}` |
| `:5103/webhook` | challenge 验证（5号系统） | ✅ `200 {"challenge":"test789"}` |
| `:5103/webhook` | `help`（5号系统） | ✅ `200 {"code":0,"msg":"success"}` |

全部 10 项端到端 HTTP 探测通过。预计的降级警告（推理后端未启动、watchdog 未安装）不影响路由转发与命令分发。每次修改后执行以下命令验证：

```bash
venv/bin/python3 scripts/regression_test.py          # 全量 88 项
venv/bin/python3 scripts/regression_test.py --module chat  # 按模块筛选
```

---

## 9. 风险说明

- 模型稳定运行 qwen2.5:7b（ollama 后端，localhost:11434），短回答速度 ~30-45 tok/s
- **ollama 本地推理**（qwen2.5:7b）作为聊天后端，速度取决于网络和 Free API Hub 可用性
- 已统一为 ollama 单容器本地推理，移除 llama.cpp 聊天服务；qwen2.5:7b 在 ollama 下性能满足需求，无需保留双后端
- 飞书回调需公网可达，本地开发建议内网穿透
- 凭证文件 `**/.env` 被 .gitignore 排除，不会被提交
- 各助手虚拟环境独立，互不干扰
- 3号AI life-assistant 模块已开发完成（含 venv-life），中文关键词路由已接入飞书回调

---

## 10. 进度台账

| 日期 | 操作 | 备注 |
|------|------|------|
| 2026-05-27 | v3.5 双环境共存 | 主 :5001/2/3 + 测试 :5101/2/3；脚本 `lsof -ti:` 清理 |
| 2026-05-27 | v3.5 5号/4号隔离 | 动态端口 + 相对路径 |
| 2026-05-27 | v3.5 测试环境凭证 | 3 套独立飞书 Bot |
| 2026-05-27 | v3.6 脚本路径修复 | ~40 脚本 `~/ai-assistant-system` → `$(dirname "$0")` |
| 2026-05-27 | v3.6 Git 版本管理 | git init + .gitignore，promote.sh + diff_envs.sh |
| 2026-05-27 | v3.7 3号AI life-assistant | 日程/健康/旅行/锻炼/工作规划模块 + venv-life |
| 2026-05-27 | v3.7 callback_port 动态化 | 从 settings.yaml 读取，含 dashboard_url |
| 2026-05-27 | v3.7 网页看板 | 3号AI dashboard 路由 + 手机适配 |
| 2026-05-27 | 讨论：qwen3.5/Ollama | 确认 qwen3.5 无 7B 版，llama.cpp 保持现状 |
| 2026-05-27 | v3.8 回复格式优化 | 去掉思考过程、分隔线，时间在问题/答复前显示 |
| 2026-05-27 | v3.8 帮助文本适配移动端 | 精简为紧凑格式 |
| 2026-05-27 | v3.8 中文命令路由 | 2号: `#办公` / `转PPT`；3号: 中文关键词（日程/健康/旅行/锻炼/工作/看板） |
| 2026-05-27 | v3.8 文档处理依赖修复 | python-docx/openpyxl/python-pptx 安装至 venv-chat |
| 2026-05-28 | v4.0 全面项目扫描 | 扫描全部 47 个 Python 源文件、34 个 Shell 脚本、7 个测试文件 |
| 2026-05-28 | v4.0 5号AI 状态纠正 | 确认 5 号 AI 全部 8 个模块已实现（含 system_monitor/service_manager/process_manager/log_viewer/backup_manager/security/bot_server） |
| 2026-05-28 | v4.0 回归测试套件 | 创建 `scripts/regression_test.py`，覆盖全部 5 个 AI 角色 + 共享模块 |
| 2026-05-28 | v5.0 回归测试修复 + E2E 验证 | 修复 3 项失败用例（crypto/降级摘要/空JSON），105/105 全绿；安装 mammoth 至全局 venv；完成 10 项 HTTP 端到端探测全部通过 |
| 2026-05-28 | v5.0 模型清理 | 删除 ollama 中 qwen3:4b (2.5 GB) 和 qwen3.5:4b (3.4 GB)，仅保留 qwen2.5:7b |
| 2026-06-13 | v5.1 AGENTS.md 更新 | 新增3条原则，移除1条冗余 |
| 2026-06-13 | v5.1 settings.yaml 云端路由 | 新增 chat_api_url / chat_model 配置 |
| 2026-06-13 | v5.1 backend_utils.py 重构 | 支持 ollama 后端（配置读取+API调用+跳过本地唤醒） |
| 2026-06-13 | v5.1 飞书聊天切换云端 | 1号机器人从 llama.cpp(qwen2.5:7b) 切至 ollama(Qwen3-32B) |
