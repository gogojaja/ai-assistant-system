# AI 助理系统 · Agent 规则与速查

> 本文件 = 沟通准则 + 安全约束 + 项目速查。需求/追溯/变更细节不再内嵌，统一指向文末「权威参考」。

## AI Agent Quick Start

- 这是一个本地优先、飞书 Bot 入口的 Python 项目，核心 runtime 在 [shared/feishu-callback/callback_server.py](shared/feishu-callback/callback_server.py) 与三角色助手目录： [assistants/chat-assistant](assistants/chat-assistant)、[assistants/office-assistant](assistants/office-assistant)、[assistants/life-assistant](assistants/life-assistant)。
- 默认入口为 Flask 回调服务，端口/环境必须遵守测试环境约束：工作区固定为 `/Volumes/BR256G/ai-assistant-system`，只允许使用 5101/5102/5103 这组测试端口，不可触碰主环境 5001/5002/5003。
- 最常用验证命令：
  - `python3 scripts/check_env.py`：检查 `.env_type` 与环境标记
  - `bash scripts/start_all_services.sh`：启动回调与本地测试服务
  - `bash scripts/restart_callback.sh`：重启 Flask 回调服务
  - `venv/bin/python3 scripts/regression_test.py`：执行全量回归测试
  - `python3 scripts/diagnose.py`：环境诊断与配置核对
- 对于功能修改，优先用最小范围修复；如果涉及入口、路由或回调逻辑，通常需要重启回调服务后复测。
- 关键参考文档： [docs/跨会话交接文档.md](docs/跨会话交接文档.md)、 [docs/design_summary.md](docs/design_summary.md)、 [docs/运维操作手册.md](docs/运维操作手册.md)、 [架构资产/02_架构设计/架构设计文档.md](架构资产/02_架构设计/架构设计文档.md)。
- 代码层面遵守三角色边界：闲聊/办公/日程之间不要直接耦合，统一通过 shared 层共享基础能力与配置。

## 第一部分 沟通与任务处理准则

### 1. 最高优先级规则
- 接收需求后禁止急于作答、禁止立刻动手，先统筹梳理全局信息，规划完整可行**主干方案 + 兜底替代方案**，展示方案待用户确认后再落地执行。
- 专业编程专家态度，不为照顾情绪而工作。
- 会话启动第一时间提醒切换专家模式。
- 输出规避晦涩术语，所有操作复制即可运行。

### 2. 方案验证铁律
- 任何方案必须先到 GitHub Issues/Discussions、Stack Overflow、官方文档查证，确认真实可用、有社区实践支持，严禁凭模型训练数据臆想、拼接不存在的 API 或功能。
- 查询后贴出引用来源，用户确认后再落地。

### 3. 文件操作铁律
- 修改任何文件前，必须先 read 该文件的真实内容，确认当前实际配置后再修改，严禁凭对话上下文记忆或假设判断。

---

## 第二部分 刚性安全约束（最高优先级）

### 1. 操作前影响评估
- 修改入口脚本、导入链路、目录结构等核心文件，必须出具《操作影响评估表》（列明受影响组件、潜在风险、完整回滚方案），等待用户回复同意后方可执行。

### 2. 故障回滚优先
- 服务启动失败、功能异常时，默认优先建议从最新备份恢复，暂停一切诊断修改；仅收到用户明确排查指令，再开展检修工作。

### 3. 文件操作保护
- 无用户明确指令，严禁私自删除、移动、重命名项目任意文件。

### 4. 用户预期模板对齐
- 输出技术方案固定两块：✅ **可稳定达成的效果** / ⚠️ **理论最优效果与当前限制**，清晰划定落地边界。

### 5. 阶段自动固化
- 单独立任务完成后，自动执行：备份核心文件 → 更新文档版本 → 告知用户状态已固化、支持随时回滚。

### 6. 环境隔离铁律（绝对禁止违反）

**第 1 步 — 路径核验（不可跳过）**
- workspace 固定在 `/Volumes/BR256G/ai-assistant-system/`（测试环境）
- **禁止**使用任何以 `/Users/gogo/ai-assistant-system/` 或 `~/ai-assistant-system/` 开头的路径，出现必须立即拒绝操作

**第 2 步 — 端口核验**
- 测试环境端口范围：5101（回调）、5102（文件）、5103（系统）
- **禁止**操作 5001/5002/5003 端口——这些属主环境
- 任何 `lsof -ti:` 命令只允许指定 510x 端口

**第 3 步 — 标记核验**
- 修改任何文件前必须运行 `python3 scripts/check_env.py` 确认标记
- `.env_type` 文件内容必须为 `test`，标记不匹配立即终止操作

**第 4 步 — Bash 操作安全规范**
- 所有 Bash 命令必须使用 `workdir` 参数指向 `/Volumes/BR256G/ai-assistant-system/`
- **禁止** `cd /Users/gogo/` 切换目录；**禁止**使用 5001/5002/5003 端口；**禁止** `kill` 非当前环境的进程

**违反后果**：误改主环境 = 系统不可逆损坏，本会话立即终止并需全量备份恢复。

---

## 第三部分 基础执行约束

- **天花板精准判定**：同一问题遍历网络、环境、依赖、权限、代码逻辑五大维度仍无法解决，且不属于文件缺失、路径错误、语法报错等基础问题，才可判定触及能力上限并切换替代方案；基础报错禁止误判触发。
- **单线串行推进**：单轮对话任务严格串行，当前任务收尾、文档更新、用户确认完毕，再开启下一任务，禁止任务穿插造成上下文污染。
- **对话轮次规则**：每轮对话结束主动标注当前累计轮次；累计 25 轮复述项目总目标、汇总上下文、梳理已完成/待办任务；累计 100 轮整合全量信息，输出需求文档、架构说明、更新日志、README，整理交接内容并提醒新建对话接续工作。
- **代码注释规范**：所有 Python 文件顶部使用固定格式注释（模块名称 / 功能描述 / 对外接口 / 依赖 / 版本 / 更新记录）。
- **问题解决强制原则**：只做根因彻底修复，拒绝临时绕过、注释屏蔽、妥协凑活方案；同类错误重复 2 次以上切换五大维度排查并提供替代落地路径；高阶命令失效改用系统原生简易方式；全程禁止 sudo，只用标准稳定原生指令；报错通俗解释成因，保留原有环境，仅修复故障点位。
- **脚本编写统一标准**：脚本内置 DEBUG 级别日志；业务脚本配套独立测试脚本（3 组基础用例与批量运行命令）；输出前语法自检，确保可直接复制运行；超 500 行按标准目录模块化拆分；不输出残缺半成品。
- **运行环境规范**：统一使用 `python -m venv` 原生虚拟环境，不使用第三方环境工具；完整提供创建、激活、运行全套指令；锁定依赖固定版本与适配 Python 区间；步骤精简无跳步。
- **方案选型优先级**：安全性 > 长期稳定性 > 技术成熟度 > 部署便捷度 > 日常使用便捷度；优先官方 LTS 稳定版本，最小权限运行，适配 macOS 环境，拒绝内测、小众实验工具。
- **网络资源规范**：仅提供可正常访问的有效资源链接；链接失效立即替换本地部署或离线源码方案。
- **日常固定服务**：每日整理归档设备完整环境配置；提供无高危操作的一键备份脚本；定期检测服务、后台、网络、接口状态；阶段完工自动核验文档与真实环境一致性。
- **回复结尾格式**：每轮回复末尾固定标注：**▶️ 下一步：** 填写清晰可直接执行的后续操作。

### 会话复盘经验（持续积累）

1. **目录命名与 import 约定**：目录名统一使用连字符（`chat-assistant`），Python 无法直接导入带连字符的包；在 `assistants/` 下创建同名符号链接（`chat_assistant → chat-assistant`）保持 import 兼容；禁止直接复制目录造成两份冗余。
2. **功能边界清晰化**：实验性/废弃代码完全隔离，不接入生产路由；删除废弃模块前先检查所有 `from xxx import` 引用，更新或移除后再删除；未实现的功能路由应返回明确的"开发中"提示，而非指向临时处理器。
3. **清理策略文档化**：大型清理操作（brew uninstall、目录删除、重命名）需在设计文档中记录变更；清理前先做环境备份；磁盘释放数据附在文档备注栏，便于后续核对。

---

# 项目速查（权威需求见文末「权威参考」）

## 项目概述

**目标**：飞书 Bot 统一交互的 AI 助理系统，核心数据留存本地并加密存储，支持 macOS Apple Silicon 推理。默认 free-api-hub 云端路由，断网自动降级本地推理（llama.cpp/Ollama）。

**架构**：飞书 Bot → cloudflared/ngrok 隧道 → Flask 回调服务（port 5101）→ 推理后端（free-api-hub / llama.cpp / Ollama 三后端可切换）→ 各助手处理器 → 飞书回复。

**环境**：测试环境 `/Volumes/BR256G/ai-assistant-system/`，独立飞书 Bot（APP_ID=`cli_aa9c870de6799bb4`），端口 5101，与主环境 5001 互不干扰。

**升级项目 PRJ-001（进行中）**：五角色 → **三角色（闲聊/办公/日程）**，1 个月上线（2026-08-05~09-05），预算 25 人·日。
- 禁止项：新增业务角色 / Docker / sudo / 数据迁云端 / 更换飞书入口
- 新增能力：跨会话记忆（REQ-034）、任务委派（REQ-035）、文档起草（REQ-036）、主动提醒（REQ-037）

## 三角色定义

| 角色 | 代号 | 目录 | 定位 | 入口 |
|------|------|------|------|------|
| 1号AI | chat-assistant | `assistants/chat-assistant/` | 闲聊对话、天气/翻译/搜索、知识库、语音输入、跨会话记忆、任务委派、文档起草 | `message_handler.process_message()` — 所有文本/语音默认进入 |
| 2号AI | office-assistant | `assistants/office-assistant/` | Word 摘要、Excel 分析、PPT 生成、文件变更监控 | `document_handler.process_document_file()` — 文件消息触发；`process_office_text()` — `#办公` 前缀 |
| 3号AI | life-assistant | `assistants/life-assistant/` | 个人日程/健康/旅行/锻炼/工作管理、主动提醒 | `process()` — 文字以 `日程/健康/旅行/锻炼/工作/看板` 关键词开头触发 |

## 快速启动

```bash
bash scripts/start_all_services.sh          # 启动所有服务（自动识别后端类型）
bash scripts/stop_all_services.sh           # 停止所有服务
bash scripts/monitor_services.sh &          # 服务守护（内存监控+闲置休眠+自动拉起）
bash scripts/restore.sh                     # 一键还原（列出可用备份）
python3 scripts/diagnose.py                 # 环境诊断
bash scripts/init_crypto.sh                 # 初始化数据加密（首次部署运行）
bash scripts/restart_callback.sh            # 重启 Flask 回调服务
```

## 飞书命令表

| 命令 | 功能 |
|------|------|
| `设置提示词：你是幽默的助手` / `查看提示词` / `重置提示词` | 1号：自定义提示词管理 |
| `查知识：<问题>` | 1号：检索知识库 |
| `clear` | 清空对话历史 |
| `日程 添加 明天10:00 开会` / `日程 列表` / `日程 删除 <id>` | 3号：日程管理 |
| `健康 记录 <类型> <数值>` / `健康 报告 <日报/周报/月报>` | 3号：健康管理 |
| `旅行 创建 <目的地> <开始>` / `旅行 列表` | 3号：旅行规划 |
| `锻炼 创建 <名称>` / `锻炼 列表` / `锻炼 记录 <id>` | 3号：锻炼规划 |
| `工作 创建 <标题>` / `工作 列表` / `工作 开始 <id>` | 3号：工作管理 |
| `看板` | 3号：打开网页看板 |
| `#办公 help` / `#办公 ppt <文案>` | 2号：办公帮助 / 生成 PPT |
| `转PPT` | 2号：将上次分析文档转为 PPT |

## 回归测试

```bash
venv/bin/python3 scripts/regression_test.py                           # 全量测试
venv/bin/python3 scripts/regression_test.py --module shared|chat|office|life|callback  # 分模块
```

## Python 模块速查

| 模块路径 | 核心函数 |
|----------|----------|
| `chat-assistant/src/message_handler.py` | `process_message(text, target_id, open_id)` |
| `chat-assistant/src/main.py` | `talk(messages, open_id="")` → 回复文本 |
| `chat-assistant/src/voice_handler.py` | `process_voice_message(file_key, msg_id, open_id)` |
| `office-assistant/src/document_handler.py` | `process_document_file(file_key, msg_id, open_id, filename)` / `process_office_text(cmd, open_id, target_id, rtype)` |
| `office-assistant/src/core/ppt_generator.py` | `generate_presentation(title, slides, path)` |
| `life-assistant/src/scheduler.py` | `schedule_add(time, event)`, `schedule_list(date)`, `schedule_del(id)` |
| `life-assistant/src/health_tracker.py` | `record_health(type, value)`, `health_report(period)` |
| `life-assistant/src/reminder.py` | `check_reminders()` → 到期推送 |
| `life-assistant/src/travel_planner.py` | `create(dest, start)`, `list_trips()`, `add_activity()`, `pack_item()` |
| `life-assistant/src/workout_planner.py` | `create(name)`, `list_plans()`, `add_exercise()`, `log_workout()` |
| `life-assistant/src/work_planner.py` | `create(title)`, `list_items()`, `set_status()`, `set_priority()` |
| `shared/feishu_api.py` | `send_message()`, `download_file()` |
| `shared/backend_utils.py` | `get_backend_config()`, `wake_model()`, `call_api(messages)`, `clean_reply(text)` |
| `shared/crypto.py` | `encrypt_text/decrypt_text/encrypt_json/decrypt_json` |
| `shared/knowledge_base.py` | `search(query, top_k=3, min_score=0.15)` v2.2 BM25 |
| `shared/speech_utils.py` | `transcribe_audio(path)`, `convert_opus_to_wav()` |

## 日志

```bash
tail -f logs/flask.log          # 回调服务日志
tail -f logs/monitor.log        # 守护脚本日志
tail -f logs/backup_cron.log    # 定时备份日志
```

## 注意点

- API 请求中 `model` 字段：llama.cpp 用 `gpt-3.5-turbo`（假名），Ollama 用实际模型名
- `callback_server.py` 通过 `sys.path.insert` 硬编码了助手 src 路径 — 添加新助手需同步修改
- 修改 `message_handler.py` 或 `callback_server.py` 后需重启 Flask（`bash scripts/restart_callback.sh`）
- 1号AI 对话历史加密存储于 `assistants/chat-assistant/logs/chat_history_{open_id}.json`
- 模型进程闲置 30 分钟自动 SIGSTOP，请求到达自动 SIGCONT 唤醒；推理进程内存超限 8GB 自动重启
- 飞书凭证在 `shared/feishu-bot/.env`（不得提交）
- 2号AI 用 `#办公` 前缀（替代 `#2`/`#office`）；3号AI 用中文关键词路由
- 回归测试用 `venv/bin/python3 scripts/regression_test.py`（全局 venv Python 3.12.13）

## 权威参考

| 内容 | 位置 |
|------|------|
| 需求/SRS/非功能需求（v1.0，29 项三角色基线） | `requirements/SRS_v1.0/`、`requirements/需求收集清单.csv` |
| 需求追溯矩阵（REQ-001~037） | `台账/08_需求追溯矩阵.csv` |
| 需求变更/范围/进度/风险台账 | `台账/`（01~17 全套） |
| 架构资产（策略/设计/决策/原型/评审） | `架构资产/01_架构策略` ~ `06_基准` |
| 跨会话交接文档（当前工作进度权威） | `docs/跨会话交接文档.md` |
| 设计汇总 | `docs/design_summary.md` |
| 环境核验 | `python3 scripts/diagnose.py` |
