# 沟通与任务处理准则（最高优先级）

接收需求后禁止急于作答、禁止立刻动手编写内容，优先统筹梳理全局信息，规划完整可行主干方案 + 兜底替代方案，展示方案待用户确认后再落地执行。

你是一个专业的编程专家，不要为了照顾我的情绪而工作，要有专业的态度。

会话启动第一时间提醒切换专家模式，保障高阶规则正常生效。

输出规避晦涩术语，所有操作复制即可运行。项目启动即刻生成《环境搭建方案设计文档》，记录架构、选型、目录、版本、部署、风险、进度等信息，内容变动即时同步更新，保障跨 AI 无缝接续工作。

阶段与每日收尾后，生成信息核验脚本，自动比对实际环境与文档数据，标注偏差保证同步。

对话交接前完成全文档校准更新，生成新会话开场话术；新会话接收文档后静待指令，不擅自操作。

会话结束复盘全部交互，结合执行效果给出提示词优化建议。

禁止使用 Python 脚本来修改项目文件，必须使用专用的文件编辑工具（如 edit、write）。

### 方案验证铁律
后续任何方案必须先到 GitHub Issues / Discussions、Stack Overflow、官方文档查证，确认是真实可用、有社区实践支持的方案，严禁凭模型训练数据臆想、拼接不存在的 API 或功能。查询后贴出引用来源，用户确认后再落地。

### 文件操作铁律
修改任何文件前，必须先 read 该文件的真实内容，确认当前实际配置后再做修改，严禁凭对话上下文记忆或假设判断文件内容。

## 刚性安全约束规则（最高优先级）

### 操作前影响评估
修改入口脚本、导入链路、目录结构等核心文件，必须出具《操作影响评估表》，列明受影响组件、潜在风险、完整回滚方案，等待用户回复同意后方可执行。

### 故障回滚优先
服务启动失败、功能异常时，默认优先建议从最新备份恢复，暂停一切诊断修改；仅收到用户明确排查指令，再开展检修工作。

### 文件操作保护
无用户明确指令，严禁私自删除、移动、重命名项目任意文件。

### 用户预期模板对齐
输出技术方案固定分为两块：
- ✅ **可稳定达成的效果**
- ⚠️ **理论最优效果与当前限制**

清晰划定落地边界。

### 阶段自动固化
单独立任务完成后，自动执行：备份核心文件→更新文档版本→告知用户状态已固化、支持随时回滚。

### 环境隔离铁律（绝对禁止违反）
AI 助理在任何操作前必须执行以下环境确认流程：

**第 1 步 — 路径核验（不可跳过）**
- AI 的 workspace 固定在 `/Volumes/BR256G/ai-assistant-system/`（测试环境）
- **禁止** 使用任何以 `/Users/gogo/ai-assistant-system/` 或 `~/ai-assistant-system/` 开头的路径
- 文件读写、编辑、Bash 命令中出现上述路径，必须立即拒绝操作

**第 2 步 — 端口核验**
- 测试环境端口范围：5101（回调）、5102（文件）、5103（系统）
- **禁止** 操作 5001/5002/5003 端口——这些属主环境
- 任何 `lsof -ti:` 命令只允许指定 510x 端口

**第 3 步 — 标记核验**
- 修改任何文件前必须运行 `python3 scripts/check_env.py` 确认标记
- `.env_type` 文件内容必须为 `test`
- 标记不匹配则立即终止操作

**第 4 步 — Bash 操作安全规范**
- 所有 Bash 命令必须使用 `workdir` 参数指向 `/Volumes/BR256G/ai-assistant-system/`
- **禁止** `cd /Users/gogo/` 切换目录
- **禁止** 使用端口号 5001/5002/5003
- **禁止** `kill` 非当前环境的进程

**违反后果**：误改主环境 = 系统不可逆损坏，本会话立即终止并需全量备份恢复。

## 基础执行约束规则

### 天花板精准判定
同一问题遍历网络、环境、依赖、权限、代码逻辑五大维度仍无法解决，且不属于文件缺失、路径错误、语法报错等基础问题，才可判定触及能力上限并切换替代方案；基础报错禁止误判触发。

### 单线串行推进
单轮对话任务严格串行，当前任务收尾、文档更新、用户确认完毕，再开启下一任务，禁止任务穿插造成上下文污染。

### 对话轮次专属规则
- 每轮对话结束主动标注当前累计轮次
- 累计 25 轮：复述项目总目标、汇总上下文、梳理已完成/待办任务
- 累计 100 轮：整合全量信息，输出需求文档、架构说明、更新日志、README，复盘环境与关键资料，整理交接内容并提醒新建对话接续工作

### 统一代码注释强制规范
所有 Python 文件顶部必须使用固定格式注释：
```
"""
模块名称：<文件名或模块名>
功能描述：<一句话说明模块做什么>
对外接口：
    - function1(param): 功能说明
    - function2(param): 功能说明
依赖：
    - 标准库：os, sys, json, logging, threading, subprocess, tempfile, pathlib, datetime, urllib.parse
    - 第三方：requests, flask, openpyxl, python-dotenv, deep-translator, pyyaml
    - 项目内：shared.feishu_api, assistants.chat-assistant.src.main (talk, search), assistants.office-assistant.src.core (WordProcessor, ExcelProcessor, DocumentSummarizer), assistants.life-assistant.src.scheduler, assistants.file-assistant.src.file_manager, assistants.sys-assistant.src.system_monitor
版本：v1.0
更新记录：
    - 2026-05-23: 初始创建，从 callback_server.py 剥离
"""
```

### 命令输出格式规范
命令执行、脚本运行、日志输出结束后，强制空 4 行换行，提升查阅可读性。

### 问题解决强制原则
- 只做根因彻底修复，拒绝临时绕过、注释屏蔽、妥协凑活方案
- 同类错误重复 2 次以上，切换五大维度排查并提供替代落地路径
- 高阶命令失效改用系统原生简易方式，拒绝炫技冗余操作
- 全程禁止 sudo 权限，只用标准稳定原生指令
- 报错通俗解释成因，保留原有环境，仅修复故障点位

### 脚本编写统一标准
- 脚本内置 DEBUG 级别日志，记录变量、交互、状态变化
- 业务脚本配套独立测试脚本，附带 3 组基础用例与批量运行命令
- 输出前语法自检，确保无报错、无版本冲突，可直接复制运行
- 超 500 行脚本按标准目录模块化拆分，附带目录与调用说明
- 不输出残缺半成品，按需生成检测、部署、备份、比对类脚本

### 运行环境规范
- 统一使用 `python -m venv` 原生虚拟环境，不使用第三方环境工具
- 完整提供创建、激活、运行全套指令
- 锁定依赖固定版本与适配 Python 区间，规避兼容问题
- 步骤精简无跳步，适配零基础操作

### 方案选型优先级
安全性 > 长期稳定性 > 技术成熟度 > 部署便捷度 > 日常使用便捷度
优先官方 LTS 稳定版本，最小权限运行，适配 macOS 环境，拒绝内测、小众实验工具

### 网络资源规范
- 仅提供可正常访问的有效资源链接
- 链接失效立即替换本地部署或离线源码方案

### 日常固定服务
- 每日整理归档设备完整环境配置
- 提供无高危操作的一键备份脚本
- 定期检测服务、后台、网络、接口状态
- 阶段完工自动核验文档与真实环境一致性

### 会话复盘经验（持续积累）

以下经验来自各轮会话复盘，新会话应继承执行：

**1. 目录命名与 Python import 约定**
- 目录名统一使用**连字符**（`chat-assistant`），Python 无法直接导入带连字符的包
- 在 `assistants/` 下创建同名**符号链接**（`chat_assistant → chat-assistant`），保持 import 兼容
- 禁止直接复制目录造成两份冗余

**2. 功能边界清晰化**
- 实验性/废弃代码完全隔离，不接入生产路由
- 删除废弃模块前先检查所有 `from xxx import` 引用，更新或移除后再删除
- 未实现的功能路由应返回明确的"开发中"提示，而非指向临时处理器

**3. 清理策略文档化**
- 大型清理操作（brew uninstall、目录删除、重命名）需在设计文档中记录变更
- 清理前先做环境备份（`scripts/backup_models.sh` 或全量备份）
- 磁盘释放数据附在文档备注栏，便于后续核对

### 回复结尾格式
每轮回复末尾固定标注：**▶️ 下一步：** 填写清晰可直接执行的后续操作

## 核心精简备忘

- 会话初始提醒切换专家模式，每轮标注对话轮次
- 25 轮汇总复盘进度，100 轮整编全套项目资料并交接
- 核心文件修改必先评估并获用户同意
- 故障优先备份回滚，无授权不改动任何文件
- 方案标注效果边界，任务完成自动固化存档
- 代码、命令严格遵循格式规范，任务串行不交叉
- 会话结束复盘交互，出具提示词优化建议

---

# 五角色 AI 助理系统 · 需求文档

## 1. 项目概述

**目标**：构建一套基于飞书 Bot 统一交互的五角色 AI 助理系统，核心数据留存本地设备并加密存储，支持 macOS Apple Silicon 推理。默认使用 free-api-hub 云端路由，断网时自动降级至本地推理（llama.cpp/Ollama）。

**架构**：飞书 Bot → cloudflared/ngrok 隧道 → Flask 回调服务 (port 5101) → 推理后端 (free-api-hub 云端路由 / llama.cpp / Ollama，三后端可切换) → 各助手处理器 → 飞书回复

**物理路径**：`~/ai-assistant-system/`（主环境）、`/Volumes/BR256G/ai-assistant-system/`（测试环境）

**测试环境**：独立飞书 Bot（APP_ID=`cli_aa9c870de6799bb4`），端口 5101，与主环境 5001 互不干扰

---

## 2. 五角色定义

| 角色 | 代号 | 目录 | 定位 | 入口 |
|------|------|------|------|------|
| 1号AI | chat-assistant | `assistants/chat-assistant/` | 闲聊对话、天气查询、翻译搜索、知识库、语音输入 | `message_handler.process_message()` — 所有文本/语音默认进入 |
| 2号AI | office-assistant | `assistants/office-assistant/` | Word 摘要、Excel 分析、PPT 生成、文件变更监控 | `document_handler.process_document_file()` — 飞书文件消息触发；`process_office_text()` — `#办公` 前缀命令 |
| 3号AI | life-assistant | `assistants/life-assistant/` | 个人日程/健康/旅行/锻炼/工作规划管理 | `process()` — 飞书文字以 `日程/健康/旅行/锻炼/工作/看板` 关键词开头触发 |
| 4号AI | file-assistant | `assistants/file-assistant/` | 文件传输、文件管理 | `process()` — 飞书文字 `#4`/`#file` 前缀触发 |
| 5号AI | sys-assistant | `assistants/sys-assistant/` | 系统管理、服务启停、进程管理 | `process()` — 飞书文字 `#5`/`#sys` 前缀触发 | ❌ 测试环境未实现，待补建 |

---

## 3. 功能需求

### 3.1 1号AI 闲聊助理

| ID | 需求 | 优先级 | 状态 | 实现位置 |
|----|------|--------|------|----------|
| CHAT-01 | 接收飞书文本消息，调用模型回复 | P0 | ✅ 已实现 | `shared/feishu-callback/callback_server.py:192` → `message_handler.process_message()` → `main.talk()` |
| CHAT-02 | 流式调用模型，拼接 content 和 reasoning_content | P0 | ✅ 已实现 | `chat-assistant/src/main.py:talk()` (L191) |
| CHAT-03 | content 为空时从 reasoning 提取回答（5 层策略） | P0 | ✅ 已实现 | `chat-assistant/src/main.py:_extract_from_reasoning()` (L273) |
| CHAT-04 | 对话历史 per-user 持久化（最多 10 轮） | P0 | ✅ 已实现 | `chat-assistant/src/message_handler.py:_load_history()` (L112) / `_save_history()` (L123) |
| CHAT-05 | 对话历史加密存储 | P0 | ✅ 已实现 | `shared/crypto.py` Fernet 加解密，`message_handler.py` 读写时调用 |
| CHAT-06 | 天气查询（识别城市名，默认北京） | P1 | ✅ 已实现 | `chat-assistant/src/message_handler.py:221-260` + `shared/utils.py:get_weather()` (L191) |
| CHAT-07 | 中英翻译（MyMemory 免费 API） | P1 | ✅ 已实现 | `chat-assistant/src/message_handler.py:211-218` + `shared/utils.py:translate_text()` |
| CHAT-08 | 网络搜索（Bing） | P2 | ✅ 已实现 | `chat-assistant/src/message_handler.py:311-340` + `shared/utils.py:handle_search()` |
| CHAT-09 | 清空历史指令 `clear` | P1 | ✅ 已实现 | `chat-assistant/src/message_handler.py:156-157` |
| CHAT-10 | 身份识别（"我是谁"问题从历史正则提取） | P1 | ✅ 已实现 | `chat-assistant/src/message_handler.py:_find_user_name()` (L69) |
| CHAT-11 | 自定义提示词管理（设置/查看/重置） | P2 | ✅ 已实现 | `chat-assistant/src/message_handler.py:162-186` + `chat-assistant/src/main.py:_load_custom_prompt()` (L40) / `_save_custom_prompt()` (L53) |
| CHAT-12 | 私有知识库检索（`查知识：<问题>`） | P2 | ✅ 已实现 | `shared/knowledge_base.py` v2.2（BM25+中文二元组+短语加权） + `chat-assistant/src/message_handler.py:188-209` |
| CHAT-13 | 离线语音消息接收（whisper.cpp 转文字） | P1 | ✅ 已实现 | `shared/feishu-callback/callback_server.py:202` → `chat-assistant/src/voice_handler.py:process_voice_message()` (L30) → `shared/speech_utils.py` |
| CHAT-14 | 知识库文件导入（放入 data/knowledge/ 自动索引） | P2 | ✅ 已实现 | `shared/knowledge_base.py:import_doc()` |
| CHAT-15 | 模型进程闲置休眠/唤醒 | P1 | ✅ 已实现 | `scripts/monitor_services.sh:idle_sleep_check()` + `chat-assistant/src/main.py:_wake_model()` (L143) |
| CHAT-16 | 多后端支持（free-api-hub 云端路由 / llama.cpp / Ollama 三后端切换） | P2 | ✅ 已实现 | `config/settings.yaml:chat_api_url/backend` + `shared/backend_utils.py:get_backend_config()` (L33) |

### 3.2 2号AI 办公助理

| ID | 需求 | 优先级 | 状态 | 实现位置 |
|----|------|--------|------|----------|
| OFF-01 | 接收飞书 .docx 文件，提取文本生成摘要 | P1 | ✅ 已实现 | `office-assistant/src/document_handler.py:309-326` → `core/word_processor.py` + `core/summarizer.py` |
| OFF-02 | 接收飞书 .xlsx 文件，分析结构与数据 | P1 | ✅ 已实现 | `office-assistant/src/document_handler.py:328-339` → `core/excel_processor.py` |
| OFF-03 | Excel 数据 AI 智能摘要 | P1 | ✅ 已实现 | `office-assistant/src/document_handler.py:generate_excel_summary()` (L101) 调用 `backend_utils.call_api()` |
| OFF-04 | 根据文案生成 .pptx 成品文件 | P2 | ✅ 已实现 | `core/ppt_generator.py:generate_from_text()` / `generate_presentation()` |
| OFF-05 | 办公文件夹变更监控（watchdog） | P2 | ✅ 已实现 | `core/folder_monitor.py:start_monitor()` / `stop_monitor()` |
| OFF-06 | PPT 内容自动分段解析 | P2 | ✅ 已实现 | `ppt_generator.py:generate_from_text()` 按行自动拆分幻灯片 |
| OFF-07 | `#办公` 前缀路由（替代 `#2`/`#office`） | P1 | ✅ 已实现 | `shared/feishu-callback/callback_server.py:161-169` |
| OFF-08 | `转PPT` 直接路由（无需前缀） | P1 | ✅ 已实现 | `shared/feishu-callback/callback_server.py:171-173` |

### 3.3 3号AI 个人日程与健康管理助理

| ID | 需求 | 优先级 | 状态 | 实现位置 |
|----|------|--------|------|----------|
| LIFE-01 | 日程创建（标题、时间、地点、备注） | P1 | ✅ 已实现 | `life-assistant/src/scheduler.py` |
| LIFE-02 | 日程查询（按日期/关键词/范围） | P1 | ✅ 已实现 | `life-assistant/src/scheduler.py` |
| LIFE-03 | 日程修改/删除 | P1 | ✅ 已实现 | `life-assistant/src/scheduler.py` |
| LIFE-04 | 日程到期提醒推送 | P2 | ✅ 已实现 | `life-assistant/src/reminder.py` |
| LIFE-05 | 健康数据记录（体重、步数、睡眠、心率等） | P1 | ✅ 已实现 | `life-assistant/src/health_tracker.py` |
| LIFE-06 | 健康数据统计与可视化（日报/周报/月报） | P2 | ✅ 已实现 | `life-assistant/src/health_tracker.py` |
| LIFE-07 | 健康趋势分析与建议 | P2 | ✅ 已实现 | `life-assistant/src/health_analyzer.py` |
| LIFE-08 | 旅行规划（创建/行程/行李/打包） | P1 | ✅ 已实现 | `life-assistant/src/travel_planner.py` |
| LIFE-09 | 锻炼规划（计划/训练/记录/历史） | P1 | ✅ 已实现 | `life-assistant/src/workout_planner.py` |
| LIFE-10 | 工作管理（创建/状态/优先级/截止/备注） | P1 | ✅ 已实现 | `life-assistant/src/work_planner.py` |
| LIFE-11 | 看板网页访问 | P2 | ✅ 已实现 | `life-assistant/src/__init__.py` |
| LIFE-12 | 关键词路由（日程/健康/旅行/锻炼/工作/看板） | P1 | ✅ 已实现 | `shared/feishu-callback/callback_server.py:175-192` |

### 3.4 4号AI 文件管理助理

| ID | 需求 | 优先级 | 状态 | 实现位置 |
|----|------|--------|------|----------|
| FILE-01 | 文件列表（按目录/类型/时间排序） | P1 | ✅ 已实现 | `file-assistant/src/file_manager.py` |
| FILE-02 | 文件搜索（按名称） | P1 | ✅ 已实现 | `file-assistant/src/file_manager.py` |
| FILE-03 | 文件查看（文本/图片/PDF预览） | P1 | ✅ 已实现 | `file-assistant/src/file_manager.py` |
| FILE-04 | 文件复制/移动/重命名/批量移入回收站 | P1 | ✅ 已实现 | `file-assistant/src/file_manager.py` |
| FILE-05 | 文件上传（接收飞书文件/图片保存至本地） | P1 | ✅ 已实现 | `file-assistant/src/file_bot_server.py` |
| FILE-06 | 文件下载/分享（通过飞书发送文件） | P1 | ✅ 已实现 | `file-assistant/src/file_transfer.py` |
| FILE-07 | 路径安全验证（白名单+敏感文件过滤） | P0 | ✅ 已实现 | `file-assistant/src/security.py` |
| FILE-08 | 独立飞书 Bot Webhook 服务（测试环境端口5102 / 主环境5002） | P1 | ✅ 已实现 | `file-assistant/src/file_bot_server.py` |
| FILE-09 | 中文命令交互（无需前缀，非法命令拒绝） | P1 | ✅ 已实现 | `file-assistant/src/__init__.py` |
| FILE-10 | 自动守护集成（monitor_services.sh） | P2 | ✅ 已实现 | `scripts/monitor_services.sh` |

### 3.5 5号AI 系统管理助理

| ID | 需求 | 优先级 | 状态 | 实现位置 |
|----|------|--------|------|----------|
| SYSADM-01 | 系统状态查询（CPU/内存/磁盘/网络/负载） | P1 | ❌ 未实现 | `sys-assistant/src/system_monitor.py`（测试环境目录缺失，待补建） |
| SYSADM-02 | 服务管理（启动/停止/重启/查看状态） | P1 | ❌ 未实现 | `sys-assistant/src/service_manager.py`（测试环境目录缺失，待补建） |
| SYSADM-03 | 进程管理（查看进程树/终止进程） | P1 | ❌ 未实现 | `sys-assistant/src/process_manager.py`（测试环境目录缺失，待补建） |
| SYSADM-04 | 日志查看（实时 tail/关键词过滤） | P2 | ❌ 未实现 | `sys-assistant/src/log_viewer.py`（测试环境目录缺失，待补建） |
| SYSADM-05 | 备份管理（手动触发备份/查看备份列表/还原） | P2 | ❌ 未实现 | `sys-assistant/src/backup_manager.py`（测试环境目录缺失，待补建） |
| SYSADM-06 | 远程服务启停（通过飞书命令控制远端服务） | P1 | ❌ 未实现 | `sys-assistant/src/service_manager.py` — 待补建独立 Bot 服务(:5103) |
| SYSADM-07 | 安全操作限制（禁止 sudo、白名单命令校验） | P0 | ❌ 未实现 | `sys-assistant/src/security.py`（测试环境目录缺失，待补建） |
| SYSADM-08 | 飞书 `#5`/`#sys` 前缀路由 | P1 | ❌ 未实现 | 待补建：独立 Bot 服务 + `callback_server.py` 反向代理 `/webhook_sys` → `:5103` |

### 3.6 系统层需求

| ID | 需求 | 优先级 | 状态 | 实现位置 |
|----|------|--------|------|----------|
| SYS-01 | 启动所有服务（一键） | P0 | ✅ 已实现 | `scripts/start_all_services.sh` |
| SYS-02 | 停止所有服务 | P0 | ✅ 已实现 | `scripts/stop_all_services.sh` |
| SYS-03 | 服务守护自动拉起 | P0 | ✅ 已实现 | `scripts/monitor_services.sh` |
| SYS-04 | 推理进程内存超限自动重启（默认 8GB） | P1 | ✅ 已实现 | `monitor_services.sh:check_memory()` |
| SYS-05 | 模型进程闲置自动挂起（默认 30 分钟） | P1 | ✅ 已实现 | `monitor_services.sh:idle_sleep_check()` |
| SYS-06 | 请求到达自动唤醒模型进程 | P1 | ✅ 已实现 | `main.py:_wake_model()` |
| SYS-07 | 每日自动备份（crontab 3:00，保留 7 天） | P1 | ✅ 已实现 | `daily_backup.sh` + crontab |
| SYS-08 | 一键还原（列出备份 -> 确认 -> 停服务 -> 备份当前 -> 还原） | P1 | ✅ 已实现 | `scripts/restore.sh` |
| SYS-09 | 环境诊断脚本 | P1 | ✅ 已实现 | `scripts/diagnose.py` |
| SYS-10 | 数据加密初始化 | P2 | ✅ 已实现 | `scripts/init_crypto.sh` + `shared/crypto.py` |
| SYS-11 | 文件访问隔离（五助手独立白名单） | P0 | ✅ 已实现 | `config/whitelist.yaml` |
| SYS-12 | 后端配置切换（free-api-hub / llama.cpp / Ollama 三后端） | P2 | ✅ 已实现 | `config/settings.yaml:chat_api_url/backend` + `shared/backend_utils.py:get_backend_config()` |

---

## 4. 数据流

```
飞书用户发送消息
  │
  ├─ cloudflared 隧道 (https → localhost:5101 测试环境 / 5001 主环境)
  │
  └─ Flask callback_server.py
       │
       ├─ message_type == "text" ──┬─ 前缀 #5/#sys  → 5号AI sys-assistant process()
       │                           ├─ 前缀 #4/#file → 4号AI file-assistant process()
       │                           ├─ 前缀 #2/#office/#办公 → 2号AI process_office_text()
       │                           ├─ 转PPT          → 2号AI process_office_text("转PPT")
       │                           ├─ 日程/健康/旅行/锻炼/工作/看板 → 3号AI life-assistant process()
       │                           └─ 其他文本 → 1号AI process_message()
       │                                ├─ 天气/翻译/搜索/清空/提示词/知识库 → 直接回复
       │                                ├─ 身份问题 → 历史正则提取 → 回复
       │                                └─ 闲聊 → 加载历史 → 检索知识库 → talk() → 保存历史 → 回复
       │
       ├─ message_type == "audio" → voice_handler (下载 opus → ffmpeg 转 wav → whisper.cpp 识别 → process_message)
       │
       └─ message_type == "file"  → document_handler (下载 → Word/Excel/PPT 处理)

推理后端 (由 settings.yaml 决定，优先级从高到低):
  ├─ chat_api_url 配置存在 → free-api-hub 云端路由 (:5080 聊天 / :5081 编程)
  ├─ backend=llama.cpp → localhost:8080 (llama-server + qwen2.5:7b)
  └─ backend=ollama    → localhost:11434 (ollama serve + ollama_model)
```

---

## 5. 非功能需求

### 5.1 离线运行（DEF-006 整改：明确定义）

| 类别 | 需求 | 指标/约束 |
|------|------|-----------|
| 离线-核心 | **核心功能离线可用**：飞书消息接收/路由、1~4 号 AI 本地处理、文件管理、日程管理在断网时必须可用 | 断网时核心功能可用率 100%（free-api-hub 云端路由不可用时自动降级至 llama.cpp 本地推理） |
| 离线-降级 | **联网功能优雅降级**：天气/翻译/搜索/free-api-hub 云端路由断网时返回明确提示文案 | 降级响应时间 < 3 秒，提示文案明确说明"该功能需联网，当前不可用" |
| 离线-恢复 | **联网恢复自动恢复**：网络恢复后联网功能自动恢复，无需重启服务 | 恢复检测间隔 <= 60 秒 |

### 5.2 性能效率（DEF-004 整改：补充量化标准）

| 类别 | 需求 | 指标/约束 | 验收方法 |
|------|------|-----------|----------|
| 性能-响应 | 闲聊回复响应时间 | P95 < 30 秒（free-api-hub）/ P95 < 60 秒（llama.cpp 本地） | 压测脚本发送 20 条消息统计 P50/P95/P99 |
| 性能-并发 | 并发用户数 | 支持 1-3 人同时使用（个人系统） | 模拟 3 用户并发发送消息，无超时无报错 |
| 性能-内存 | 推理进程内存上限 | 默认 8GB，超限自动重启 | monitor_services.sh 内存监控触发验证 |
| 性能-资源 | 闲置资源释放 | 模型进程空闲 30 分钟自动 SIGSTOP | 闲置 30 分钟后验证进程状态为 T（stopped） |
| 性能-启动 | 服务启动耗时 | <= 10 秒（Flask 回调 + 3 秒等待） | 计时 start_all_services.sh 执行到服务就绪 |

### 5.3 可靠性（DEF-010 整改：补充 SLA/灾备）

| 类别 | 需求 | 指标/约束 | 验收方法 |
|------|------|-----------|----------|
| 可靠-守护 | 服务守护自动拉起 | 自动检测进程/端口状态，故障 60 秒内自动拉起 | kill 进程后验证 60 秒内自动恢复 |
| 可靠-备份 | 每日自动备份 | crontab 3:00 执行，保留 7 天 | 验证 backup 目录有 7 天内备份文件 |
| 可靠-恢复 | 一键还原 | restore.sh 列出备份 -> 确认 -> 停服务 -> 备份当前 -> 还原 | 执行 restore.sh 验证完整流程 |
| 可靠-SLA | 系统可用性 | SLA >= 99%（个人系统，允许计划停机） | 月度统计可用时间/总时间 |
| 可靠-MTTR | 故障恢复时间 | MTTR <= 30 分钟（从故障到服务恢复） | 模拟故障验证恢复耗时 |
| 可靠-灾备 | 数据一致性校验 | 每日备份后自动校验备份完整性 | 校验脚本对比源文件与备份文件数量/大小 |
| 可靠-单点 | Flask 回调服务高可用 | 当前单点运行，需评估主备方案（待规划） | 风险登记，纳入架构评审 |

### 5.4 安全性（DEF-011/012/013 整改：扩展加密/审计/隧道控制）

| 类别 | 需求 | 指标/约束 | 验收方法 |
|------|------|-----------|----------|
| 安全-加密 | 数据加密存储 | 对话历史、健康数据、日程数据、旅行数据使用 cryptography.fernet 加密 | 验证 data/ 下敏感文件均为密文 |
| 安全-凭证 | 飞书凭证隔离 | APP_ID/APP_SECRET 存于 .env，不提交 git | 验证 .gitignore 包含 .env |
| 安全-权限 | 禁止 sudo | 全程用户权限运行，5 号 AI 仅可查看不可提权 | 验证所有脚本无 sudo 调用 |
| 安全-审计 | 安全审计日志 | 所有文件操作、服务启停、配置变更记录审计日志，保留 180 天 | 验证安全审计台账 Sheet 有记录 |
| 安全-隧道 | 隧道访问控制 | cloudflared/ngrok 隧道配置请求频率限制与来源验证（待规划） | 渗透测试验证隧道安全性 |
| 安全-脱敏 | 日志脱敏 | 日志输出时对敏感数据（手机号/邮箱/密钥）脱敏 | 检查日志文件无明文敏感信息 |
| 安全-路径 | 文件访问隔离 | 五助手互不可见各自数据目录（whitelist.yaml） | 验证 whitelist.yaml 配置与实际访问一致 |

### 5.5 监控告警（DEF-007 整改：新增需求域）

| 类别 | 需求 | 指标/约束 | 验收方法 |
|------|------|-----------|----------|
| 监控-服务 | 服务异常告警 | 服务进程异常退出时自动推送飞书告警消息 | kill 进程验证飞书收到告警 |
| 监控-资源 | 资源阈值告警 | 内存 > 7GB 或磁盘 > 90% 时推送飞书告警 | 模拟资源超限验证告警推送 |
| 监控-隧道 | 隧道断开告警 | cloudflared/ngrok 隧道断开时推送飞书告警 | 停止隧道验证告警推送 |

### 5.6 容量规划（DEF-014 整改：新增需求域）

| 类别 | 需求 | 指标/约束 | 验收方法 |
|------|------|-----------|----------|
| 容量-用户 | 并发用户预估 | 1-3 人日常使用，峰值 5 人 | 压测验证 |
| 容量-数据 | 数据量增长预估 | 对话历史 ~1MB/月/人，知识库 ~100MB，日志 ~50MB/月 | 季度评估存储使用率 |
| 容量-存储 | 存储容量阈值 | 磁盘使用率 > 80% 告警，> 90% 自动清理旧日志 | 验证告警触发 |

### 5.7 数据保留（DEF-008 整改：新增需求域）

| 类别 | 需求 | 指标/约束 | 验收方法 |
|------|------|-----------|----------|
| 保留-对话 | 对话历史保留 | 保留 90 天，超期自动清理 | 验证 90 天前记录被清理 |
| 保留-日志 | 日志保留 | 保留 30 天，超期自动清理 | 验证 30 天前日志被清理 |
| 保留-备份 | 备份保留 | 保留 7 天，超期 find -mtime +7 -delete | 验证 7 天前备份被清理 |
| 保留-审计 | 审计日志保留 | 保留 180 天 | 验证审计日志保留策略 |

### 5.8 合规（DEF-015 整改：新增需求域）

| 类别 | 需求 | 指标/约束 | 验收方法 |
|------|------|-----------|----------|
| 合规-隐私 | 个人数据知情同意 | 系统采集个人数据前告知用户数据用途（待规划） | 首次使用时展示隐私提示 |
| 合规-删除 | 用户数据删除权 | 用户可请求删除全部个人数据（对话/健康/日程）（待规划） | 验证删除命令清空相关数据 |
| 合规-出境 | 数据出境评估 | free-api-hub 云端路由涉及数据出境，需评估合规性（待评估） | 法律咨询评估 |

### 5.9 兼容性与可维护性

| 类别 | 需求 | 指标/约束 |
|------|------|-----------|
| 兼容-后端 | 三后端可切换：free-api-hub 云端路由（默认）/ llama.cpp（本地备选）/ Ollama（本地备选） |
| 兼容-OS | macOS 14+ (Sonoma/Sequoia)，Apple Silicon M 系列芯片 |
| 兼容-Python | Python 3.12.x（3.13+ 兼容性待评估） |
| 隔离-venv | 全局 + 五个助手共 6 个独立 venv，不可混用 |
| 隔离-文件 | 五助手互不可见各自数据目录（whitelist.yaml） |
| 可维护-模块 | 五助手完全解耦，shared 共享层统一封装 |

---

## 6. 部署需求

### 6.1 依赖清单

| 组件 | 版本/路径 | 用途 |
|------|-----------|------|
| Python | 3.12.x (macOS 原生或 Homebrew) | 运行时 |
| llama.cpp | `~/llama.cpp/build/bin/llama-server` | 本地推理引擎 (Metal)，备选后端 |
| free-api-hub | `:5080`(聊天) / `:5081`(编程) | 云端模型路由，默认后端（需联网） |
| qwen2.5:7b 模型 | `~/.local/lib/ollama/blobs/sha256-2bada8a74506*` (4.4GB) | 推理模型 |
| whisper.cpp | `shared/whisper.cpp/build/bin/whisper-cli` | 语音识别 |
| cloudflared | Homebrew 安装 | HTTPS 隧道 |
| ffmpeg | Homebrew 安装 | 音频格式转换 |
| ngrok (备选) | Homebrew 安装 | 隧道备用 |

### 6.2 Python 第三方库

| 库 | 所在 venv | 用途 |
|----|-----------|------|
| flask | 全局 venv | Web 回调服务 |
| requests | 全局 + 各助手 | HTTP 请求 |
| pyyaml | 全局 + 各助手 | 配置解析 |
| python-dotenv | 全局 | .env 文件读取 |
| deep-translator | chat-assistant | 翻译 |
| openpyxl | office-assistant | Excel 处理 |
| python-docx | office-assistant | Word 处理 |
| python-pptx | office-assistant | PPT 生成 |
| cryptography | chat-assistant | 数据加密 |
| watchdog | office-assistant | 文件夹监控 |
| mammoth | 全局 venv | docx→text 转换 |

### 6.3 目录结构

```
~/ai-assistant-system/
├── venv/                              # 全局主环境 (Flask 回调)
├── assistants/
│   ├── chat-assistant/                # 1号AI
│   │   ├── venv-chat/
│   │   └── src/
│   │       ├── main.py                # talk() 流式调用
│   │       ├── message_handler.py     # 消息分发/处理
│   │       ├── voice_handler.py       # 语音链路
│   │       └── chat_feishu.py         # 轮询入口
│   ├── office-assistant/              # 2号AI
│   │   ├── venv-office/
│   │   └── src/
│   │       ├── core/
│   │       │   ├── word_processor.py
│   │       │   ├── excel_processor.py
│   │       │   ├── summarizer.py
│   │       │   ├── ppt_generator.py
│   │       │   └── folder_monitor.py
│   │       ├── document_handler.py
│   │       └── api_server.py
│   ├── life-assistant/                # 3号AI
│   │   ├── venv-life/
│   │   └── src/
│   │       ├── scheduler.py            # 日程管理
│   │       ├── health_tracker.py       # 健康数据记录
│   │       ├── health_analyzer.py      # 健康趋势分析
│   │       ├── reminder.py             # 到期提醒
│   │       ├── travel_planner.py       # 旅行规划
│   │       ├── workout_planner.py      # 锻炼规划
│   │       └── work_planner.py         # 工作管理
│   ├── file-assistant/                # 4号AI
│   │   ├── venv-file/
│   │   └── src/
│   │       ├── file_manager.py         # 文件列表/搜索/复制/移动/删除
│   │       ├── file_transfer.py        # 文件上传/下载/分享
│   │       └── security.py             # 路径安全验证
│   └── sys-assistant/                 # 5号AI
│       ├── venv-sys/
│       └── src/
│           ├── system_monitor.py       # 系统状态监控
│           ├── service_manager.py      # 服务启停管理
│           ├── process_manager.py      # 进程管理
│           ├── log_viewer.py           # 日志查看
│           ├── backup_manager.py       # 备份管理
│           └── security.py             # 安全操作限制
├── shared/
│   ├── feishu_api.py                  # 飞书 API 封装
│   ├── feishu-bot/.env                # 飞书凭证（不提交）
│   ├── feishu-callback/callback_server.py  # Flask 主入口
│   ├── utils.py                       # 工具函数
│   ├── crypto.py                      # 加密工具
│   ├── knowledge_base.py              # 知识库检索
│   └── speech_utils.py                # 语音识别
├── config/
│   ├── settings.yaml                  # 全局配置
│   └── whitelist.yaml                 # 文件访问白名单
├── prompts/                           # 自定义提示词
├── data/knowledge/                    # 知识库文档
├── logs/                              # 运行时日志
├── scripts/                           # 运维脚本
└── docs/design_summary.md             # 设计文档
```

---

## 7. 约束与限制

| 约束 | 说明 |
|------|------|
| ❌ 无 Docker | 纯 Python venv + 原生进程，不自建容器 |
| ❌ 无 OpenClaw | 不使用 OpenClaw 框架 |
| ❌ 无 sudo | 全程用户权限运行（5号AI 仅可查看，不可提权） |
| ❌ 无自动联网 | 核心功能离线可用；天气/翻译/搜索/free-api-hub 按需联网，断网时优雅降级 |
| ❌ 无临时绕过 | 所有修复必须根因，不注释屏蔽 |
| ✅ 飞书统一入口 | 所有交互通过飞书 Bot，无其他 UI |
| ✅ 本地优先 | 所有数据留存本地，对话历史加密 |
| ✅ 快速操作 | 所有操作复制即可运行，输出规避晦涩术语 |
| ✅ 备份保护 | 故障优先回滚，无授权不改动文件 |
| ✅ 串行推进 | 单轮对话任务严格串行，完成再开下一项 |

---

## 8. 关键指标

| 指标 | 当前值 | 说明 |
|------|--------|------|
| 模型推理 | free-api-hub 云端路由（默认）/ qwen2.5:7b (4.4GB) 本地备选 | 当前默认走云端路由，本地模型为 llama.cpp/Ollama 备选 |
| 上下文长度 | 4096 tokens | llama.cpp 配置（free-api-hub 由云端决定） |
| 回复 max_tokens | 1024 | 兼顾 reasoning 和 content |
| API 超时 | 60 秒 | requests timeout |
| 对话记忆 | 最多 10 轮 | per-user 裁剪 |
| 内存上限 | 8 GB | 模型进程超限重启 |
| 闲置休眠 | 30 分钟 | SIGSTOP 挂起 |
| 启动耗时 | ~5 秒 | 服务启动 + 3 秒等待 |
| 备份保留 | 7 天 | find -mtime +7 -delete |

---

## 9. 需求来源追溯矩阵（DEF-005 整改）

> 每条需求关联来源编号、提出人、提出日期，确保可回溯至原始提出方。

### 来源编号说明

| 来源编号 | 来源类型 | 说明 |
|----------|----------|------|
| SRC-001 | 原始需求文档 | 项目立项时用户提供的初始需求 |
| SRC-002 | 用户对话决策 | 开发过程中用户通过飞书对话确定的需求 |
| SRC-003 | 测试反馈 | 回归测试发现的功能缺失或改进建议 |
| SRC-004 | 安全评审 | 安全分析识别的防护需求 |
| SRC-005 | 行业最佳实践 | 基于 IEEE 830 / ISO 25010 标准补充的需求 |
| SRC-006 | 需求评审整改 | 评审报告 DEF-xxx 缺陷整改新增需求 |
| SRC-007 | 运维经验 | 日常运维中发现的需要补充的需求 |

### 9.1 1号AI 闲聊助理需求来源

| 需求ID | 来源编号 | 提出人 | 提出日期 | 来源说明 |
|--------|----------|--------|----------|----------|
| CHAT-01 | SRC-001 | 用户 | 2026-05-20 | 项目立项：飞书消息接收与回复 |
| CHAT-02 | SRC-001 | 用户 | 2026-05-20 | 项目立项：流式调用模型 |
| CHAT-03 | SRC-003 | 开发者 | 2026-05-22 | 测试发现 content 为空时回复异常 |
| CHAT-04 | SRC-001 | 用户 | 2026-05-20 | 项目立项：对话历史持久化 |
| CHAT-05 | SRC-004 | 开发者 | 2026-05-23 | 安全评审：对话数据需加密存储 |
| CHAT-06 | SRC-002 | 用户 | 2026-05-21 | 用户对话：查询天气需求 |
| CHAT-07 | SRC-002 | 用户 | 2026-05-21 | 用户对话：中英翻译需求 |
| CHAT-08 | SRC-002 | 用户 | 2026-05-22 | 用户对话：网络搜索需求 |
| CHAT-09 | SRC-002 | 用户 | 2026-05-22 | 用户对话：清空历史指令 |
| CHAT-10 | SRC-003 | 开发者 | 2026-05-23 | 测试反馈：身份识别功能 |
| CHAT-11 | SRC-002 | 用户 | 2026-05-24 | 用户对话：自定义提示词需求 |
| CHAT-12 | SRC-002 | 用户 | 2026-05-25 | 用户对话：私有知识库检索 |
| CHAT-13 | SRC-001 | 用户 | 2026-05-20 | 项目立项：语音消息支持 |
| CHAT-14 | SRC-003 | 开发者 | 2026-05-26 | 测试反馈：知识库文件导入 |
| CHAT-15 | SRC-007 | 开发者 | 2026-05-28 | 运维经验：模型进程资源管理 |
| CHAT-16 | SRC-005 | 开发者 | 2026-06-05 | 行业实践：多后端可切换架构 |

### 9.2 2号AI 办公助理需求来源

| 需求ID | 来源编号 | 提出人 | 提出日期 | 来源说明 |
|--------|----------|--------|----------|----------|
| OFF-01 | SRC-001 | 用户 | 2026-05-20 | 项目立项：Word 文件摘要 |
| OFF-02 | SRC-001 | 用户 | 2026-05-20 | 项目立项：Excel 文件分析 |
| OFF-03 | SRC-002 | 用户 | 2026-05-22 | 用户对话：Excel AI 摘要 |
| OFF-04 | SRC-002 | 用户 | 2026-05-25 | 用户对话：PPT 生成需求 |
| OFF-05 | SRC-007 | 开发者 | 2026-05-28 | 运维经验：文件夹监控 |
| OFF-06 | SRC-003 | 开发者 | 2026-05-26 | 测试反馈：PPT 分段解析 |
| OFF-07 | SRC-002 | 用户 | 2026-05-24 | 用户对话：#办公 前缀路由 |
| OFF-08 | SRC-002 | 用户 | 2026-05-25 | 用户对话：转PPT 直接路由 |

### 9.3 3号AI 个人助理需求来源

| 需求ID | 来源编号 | 提出人 | 提出日期 | 来源说明 |
|--------|----------|--------|----------|----------|
| LIFE-01~03 | SRC-001 | 用户 | 2026-05-20 | 项目立项：日程管理（创建/查询/修改/删除） |
| LIFE-04 | SRC-002 | 用户 | 2026-05-22 | 用户对话：日程到期提醒 |
| LIFE-05 | SRC-001 | 用户 | 2026-05-20 | 项目立项：健康数据记录 |
| LIFE-06 | SRC-002 | 用户 | 2026-05-23 | 用户对话：健康数据统计 |
| LIFE-07 | SRC-005 | 开发者 | 2026-05-26 | 行业实践：健康趋势分析 |
| LIFE-08 | SRC-002 | 用户 | 2026-05-24 | 用户对话：旅行规划 |
| LIFE-09 | SRC-002 | 用户 | 2026-05-24 | 用户对话：锻炼规划 |
| LIFE-10 | SRC-002 | 用户 | 2026-05-25 | 用户对话：工作管理 |
| LIFE-11 | SRC-002 | 用户 | 2026-05-26 | 用户对话：看板网页 |
| LIFE-12 | SRC-002 | 用户 | 2026-05-24 | 用户对话：中文关键词路由 |

### 9.4 4号AI 文件管理助理需求来源

| 需求ID | 来源编号 | 提出人 | 提出日期 | 来源说明 |
|--------|----------|--------|----------|----------|
| FILE-01~04 | SRC-001 | 用户 | 2026-05-20 | 项目立项：文件管理（列表/搜索/查看/复制移动） |
| FILE-05 | SRC-001 | 用户 | 2026-05-20 | 项目立项：文件上传 |
| FILE-06 | SRC-001 | 用户 | 2026-05-20 | 项目立项：文件下载/分享 |
| FILE-07 | SRC-004 | 开发者 | 2026-05-23 | 安全评审：路径安全验证 |
| FILE-08 | SRC-001 | 用户 | 2026-05-20 | 项目立项：独立 Bot Webhook |
| FILE-09 | SRC-002 | 用户 | 2026-05-24 | 用户对话：中文命令交互 |
| FILE-10 | SRC-007 | 开发者 | 2026-05-28 | 运维经验：自动守护集成 |

### 9.5 5号AI 系统管理助理需求来源

| 需求ID | 来源编号 | 提出人 | 提出日期 | 来源说明 |
|--------|----------|--------|----------|----------|
| SYSADM-01~08 | SRC-001 | 用户 | 2026-05-20 | 项目立项：系统管理全套功能（测试环境待补建） |

### 9.6 系统层需求来源

| 需求ID | 来源编号 | 提出人 | 提出日期 | 来源说明 |
|--------|----------|--------|----------|----------|
| SYS-01~02 | SRC-001 | 用户 | 2026-05-20 | 项目立项：一键启停服务 |
| SYS-03 | SRC-007 | 开发者 | 2026-05-28 | 运维经验：服务守护 |
| SYS-04~05 | SRC-007 | 开发者 | 2026-05-28 | 运维经验：资源管理 |
| SYS-06 | SRC-003 | 开发者 | 2026-05-26 | 测试反馈：唤醒机制 |
| SYS-07~08 | SRC-001 | 用户 | 2026-05-20 | 项目立项：备份恢复 |
| SYS-09 | SRC-005 | 开发者 | 2026-05-26 | 行业实践：环境诊断 |
| SYS-10 | SRC-004 | 开发者 | 2026-05-23 | 安全评审：数据加密初始化 |
| SYS-11 | SRC-004 | 开发者 | 2026-05-23 | 安全评审：文件访问隔离 |
| SYS-12 | SRC-005 | 开发者 | 2026-06-05 | 行业实践：后端配置切换 |

### 9.7 非功能需求来源（5.1~5.9 节）

| 需求域 | 来源编号 | 提出人 | 提出日期 | 来源说明 |
|--------|----------|--------|----------|----------|
| 5.1 离线运行 | SRC-006 | 评审整改 | 2026-08-02 | DEF-006 整改：明确离线定义 |
| 5.2 性能效率 | SRC-006 | 评审整改 | 2026-08-02 | DEF-004 整改：补充量化标准 |
| 5.3 可靠性 | SRC-006 | 评审整改 | 2026-08-02 | DEF-010 整改：补充 SLA/灾备 |
| 5.4 安全性 | SRC-006 | 评审整改 | 2026-08-02 | DEF-011/012/013 整改：扩展加密/审计/隧道 |
| 5.5 监控告警 | SRC-006 | 评审整改 | 2026-08-02 | DEF-007 整改：新增需求域 |
| 5.6 容量规划 | SRC-006 | 评审整改 | 2026-08-02 | DEF-014 整改：新增需求域 |
| 5.7 数据保留 | SRC-006 | 评审整改 | 2026-08-02 | DEF-008 整改：新增需求域 |
| 5.8 合规 | SRC-006 | 评审整改 | 2026-08-02 | DEF-015 整改：新增需求域 |
| 5.9 兼容性 | SRC-005 | 开发者 | 2026-06-05 | 行业实践：兼容性标准 |

---

## 10. 补充规范（DEF-016~023 整改）

### 10.1 需求变更历史（DEF-016 整改）

| 版本 | 日期 | 变更内容 | 变更类型 | 审批人 |
|------|------|----------|----------|--------|
| v1.0 | 2026-05-20 | 初始需求文档创建（66 项需求） | 新建 | 用户 |
| v1.1 | 2026-06-05 | CHAT-16/SYS-12 新增多后端支持（free-api-hub） | 新增 | 用户 |
| v1.2 | 2026-08-02 | DEF-001~015 整改：SYSADM 状态修正、后端架构更新、端口标准化、非功能需求扩展 | 整改 | 用户 |
| v1.3 | 2026-08-02 | DEF-005/009 整改：需求来源追溯矩阵、实现位置引用修正 | 整改 | 用户 |
| v1.4 | 2026-08-02 | DEF-016~023 整改：变更历史、MoSCoW 优先级、量化标准、术语表、编号格式、依赖关系、兼容性 | 整改 | 用户 |

> 变更规则：任何需求新增/修改/删除须先执行变更影响评估，经用户审批后落地，并在此表登记。

### 10.2 MoSCoW 优先级映射（DEF-017 整改）

现有 P0/P1/P2 与 MoSCoW 法的映射关系：

| 优先级 | MoSCoW | 含义 | 数量 | 示例 |
|--------|--------|------|------|------|
| P0 | Must Have | 系统核心功能，缺失则系统不可用 | 9 项 | CHAT-01~05, FILE-07, SYS-01~03 |
| P1 | Should Have | 重要功能，缺失影响用户体验但系统可用 | 37 项 | CHAT-06~07, OFF-01~02, LIFE-01~03 |
| P2 | Could Have | 增强功能，优先级较低，资源允许时实现 | 20 项 | CHAT-08, OFF-04~06, LIFE-04 |

> Won't Have：无 Docker、无 sudo、无 OpenClaw、无自动联网（见约束表第 7 节）

### 10.3 "快速操作"量化标准（DEF-018 整改）

| 维度 | 量化标准 | 验收方法 |
|------|----------|----------|
| 操作步骤 | 用户执行任何操作 <= 3 步（输入命令 → 执行 → 获得结果） | 统计飞书命令交互轮次 |
| 命令可执行性 | 所有命令可直接复制粘贴运行，无需手动修改参数 | 复制命令到飞书验证执行 |
| 响应可读性 | 输出无晦涩术语，非技术用户可理解 | 抽查 10 条回复，无未解释的技术术语 |
| 错误提示 | 操作失败时返回明确的错误原因和建议操作 | 模拟 5 种错误场景验证提示文案 |

### 10.4 "优雅降级"量化标准（DEF-019 整改）

| 联网功能 | 降级条件 | 降级行为 | 响应时间 | 验收方法 |
|----------|----------|----------|----------|----------|
| 天气查询 | 网络不可达 | 返回"天气查询需联网，当前网络不可用，请稍后重试" | < 3 秒 | 断网后发送天气查询 |
| 翻译 | MyMemory API 不可达 | 返回"翻译服务暂时不可用，请稍后重试" | < 3 秒 | 断网后发送翻译命令 |
| 网络搜索 | Bing API 不可达 | 返回"搜索功能需联网，当前不可用" | < 3 秒 | 断网后发送搜索命令 |
| free-api-hub 云端路由 | 云端服务不可达 | 自动降级至 llama.cpp 本地推理（如已配置）或返回"AI 服务暂时不可用" | < 5 秒（降级检测） | 停止 free-api-hub 后发送消息 |
| cloudflared 隧道 | 隧道断开 | 飞书消息无法接收，monitor_services.sh 检测后推送告警 | < 60 秒（检测间隔） | 停止隧道验证告警推送 |

### 10.5 术语表（DEF-020 整改）

| 术语 | 定义 |
|------|------|
| 闲置休眠 | 模型推理进程在无请求超过 30 分钟时，通过 SIGSTOP 信号挂起，释放 CPU 资源；新请求到达时通过 SIGCONT 唤醒 |
| 快速操作 | 用户通过飞书发送单条命令即可完成操作，步骤 <= 3 步，命令可直接复制运行（详见 10.3 节） |
| 优雅降级 | 联网功能在网络不可用时返回明确的不可用提示，而非抛出异常或无响应（详见 10.4 节） |
| 范围基准 | 项目立项时确定的功能边界，任何超出基准的变更须经审批（见第 7 节约束表） |
| 三后端切换 | 系统支持 free-api-hub 云端路由（默认）、llama.cpp 本地推理、Ollama 本地推理三种后端，通过 settings.yaml 配置切换 |
| per-user 持久化 | 每个飞书用户的对话历史独立存储，互不干扰，最多保留 10 轮 |
| 白名单路径 | config/whitelist.yaml 中定义的各助手允许访问的文件路径，超出白名单的访问被拒绝 |
| SIGSTOP/SIGCONT | Unix 信号：SIGSTOP 暂停进程（不释放内存）、SIGCONT 恢复进程执行 |
| free-api-hub | 云端模型路由服务，默认运行在 :5080(聊天)/:5081(编程)，需联网使用 |

### 10.6 需求编号格式说明（DEF-021 整改）

当前编号方案：`<角色前缀>-<序号>`（如 CHAT-01、OFF-01、LIFE-01、FILE-01、SYSADM-01、SYS-01）

| 角色前缀 | 对应角色 | 编号范围 |
|----------|----------|----------|
| CHAT | 1号AI 闲聊助理 | CHAT-01~16 |
| OFF | 2号AI 办公助理 | OFF-01~08 |
| LIFE | 3号AI 个人助理 | LIFE-01~12 |
| FILE | 4号AI 文件管理助理 | FILE-01~10 |
| SYSADM | 5号AI 系统管理助理 | SYSADM-01~08 |
| SYS | 系统层需求 | SYS-01~12 |

> **IEEE 830 推荐格式说明**：IEEE 830 推荐使用 `REQ-<维度>-<模块>-<序号>` 格式（如 REQ-FUNC-CHAT-001）。当前项目采用简化编号方案，因项目规模适中（66 项需求）且角色边界清晰，简化方案可满足可追溯性要求。若后续需求增长至 200+ 项，建议迁移至 IEEE 830 推荐格式。

### 10.7 需求依赖关系（DEF-022 整改）

| 需求ID | 依赖需求 | 依赖类型 | 说明 |
|--------|----------|----------|------|
| CHAT-02 | CHAT-01 | 强依赖 | 流式调用依赖消息接收 |
| CHAT-03 | CHAT-02 | 强依赖 | reasoning 提取依赖流式调用 |
| CHAT-04 | CHAT-01 | 强依赖 | 历史持久化依赖消息接收 |
| CHAT-05 | CHAT-04 | 强依赖 | 加密依赖历史存储 |
| CHAT-06~08 | CHAT-01 | 强依赖 | 天气/翻译/搜索依赖消息路由 |
| CHAT-09 | CHAT-04 | 强依赖 | 清空历史依赖历史存储 |
| CHAT-10 | CHAT-04 | 强依赖 | 身份识别依赖历史数据 |
| CHAT-11 | CHAT-01 | 强依赖 | 提示词管理依赖消息路由 |
| CHAT-12 | CHAT-01 | 强依赖 | 知识库检索依赖消息路由 |
| CHAT-13 | CHAT-01 | 强依赖 | 语音识别依赖消息接收 |
| CHAT-14 | CHAT-12 | 强依赖 | 知识库导入依赖检索功能 |
| CHAT-15 | SYS-03 | 强依赖 | 闲置休眠依赖服务守护 |
| CHAT-16 | SYS-12 | 弱依赖 | 多后端依赖后端配置 |
| OFF-01~08 | SYS-01 | 强依赖 | 办公功能依赖服务启动 |
| OFF-03 | CHAT-16 | 弱依赖 | AI 摘要依赖推理后端 |
| LIFE-01~12 | SYS-01 | 强依赖 | 生活功能依赖服务启动 |
| FILE-01~10 | SYS-01 | 强依赖 | 文件功能依赖服务启动 |
| FILE-08 | SYS-01 | 强依赖 | 独立 Bot 依赖服务启动 |
| SYSADM-01~08 | SYS-01 | 强依赖 | 系统管理依赖服务启动 |
| SYS-03 | SYS-01 | 强依赖 | 守护依赖服务启动 |
| SYS-04~05 | SYS-03 | 强依赖 | 资源管理依赖守护 |
| SYS-06 | CHAT-15 | 强依赖 | 唤醒依赖休眠机制 |
| SYS-08 | SYS-07 | 强依赖 | 还原依赖备份 |

> 关键路径：CHAT-01 → CHAT-02 → CHAT-03（消息接收 → 流式调用 → reasoning 提取）

### 10.8 兼容性需求细化（DEF-023 整改）

| 维度 | 兼容范围 | 已验证 | 待验证 |
|------|----------|--------|--------|
| macOS 版本 | macOS 14+（Sonoma / Sequoia） | macOS 15 (Sequoia) | macOS 14 (Sonoma) |
| 芯片架构 | Apple Silicon M 系列芯片 | M2 | M1 / M3 / M4 |
| Python 版本 | 3.12.x（3.13+ 兼容性待评估） | 3.12.13 | 3.13+ |
| Flask 版本 | 3.x | 3.1.3 | - |
| cloudflared | 最新 Homebrew 版本 | 已验证 | - |
| ffmpeg | 最新 Homebrew 版本 | 已验证 | - |
| whisper.cpp | 本地编译版本 | 已验证 | - |
| 浏览器（看板） | Safari 17+ / Chrome 120+ / Firefox 120+ | Safari | Chrome / Firefox |

---

# 五角色 AI 助理系统 · Agent 备忘录

> **权威参考见本文档第二部分「需求文档」** — 以下仅保留快速操作入口。

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
| `设置提示词：你是幽默的助手` | 设置自定义提示词 |
| `查看提示词` / `重置提示词` | 查看 / 删除自定义提示词 |
| `查知识：<问题>` | 检索知识库 |
| `日程 添加 明天10:00 开会` / `日程 列表` / `日程 删除 <id>` | 3号AI：日程管理 |
| `健康 记录 <类型> <数值>` / `健康 报告 <日报/周报/月报>` | 3号AI：健康管理 |
| `旅行 创建 <目的地> <开始>` / `旅行 列表` | 3号AI：旅行规划 |
| `锻炼 创建 <名称>` / `锻炼 列表` / `锻炼 记录 <id>` | 3号AI：锻炼规划 |
| `工作 创建 <标题>` / `工作 列表` / `工作 开始 <id>` | 3号AI：工作管理 |
| `看板` | 3号AI：打开网页看板 |
| `查看 <路径>` / `搜索 <关键词>` / `信息 <路径>` | 4号AI：文件查看/搜索 |
| `复制 <源> <目标>` / `移动 <源> <目标>` / `重命名 <路径> <新名>` | 4号AI：文件操作 |
| `删除 <路径1> [路径2 ...]` | 4号AI：批量移入回收站 |
| `上传 [保存路径]` / `下载 <路径>` / `分享 <路径>` | 4号AI：文件传输 |
| `创建目录 <路径>` | 4号AI：创建目录 |
| `帮助` | 4号AI：帮助 |
| `#5 sys status` / `#5 sys disk` / `#5 sys mem` / `#5 sys load` | 5号AI：系统状态（❌ 待实现） |
| `#5 svc start <name>` / `#5 svc stop <name>` / `#5 svc restart <name>` / `#5 svc list` | 5号AI：服务管理（❌ 待实现） |
| `#5 ps list` / `#5 ps kill <pid>` | 5号AI：进程管理（❌ 待实现） |
| `#5 log <name> [lines]` / `#5 log search <keyword>` | 5号AI：日志查看（❌ 待实现） |
| `#5 backup now` / `#5 backup list` / `#5 backup restore <id>` | 5号AI：备份管理（❌ 待实现） |
| `#办公 help` / `#办公 ppt <文案>` | 2号AI：办公帮助 / 生成 PPT |
| `转PPT` | 2号AI：将上次分析文档转为 PPT |
| `#5 help` | 5号AI：帮助 |
| `clear` | 清空对话历史 |

## 回归测试

```bash
venv/bin/python3 scripts/regression_test.py                          # 全量 105 项测试
venv/bin/python3 scripts/regression_test.py --module shared          # 仅共享模块
venv/bin/python3 scripts/regression_test.py --module chat            # 仅 1号AI
venv/bin/python3 scripts/regression_test.py --module office          # 仅 2号AI
venv/bin/python3 scripts/regression_test.py --module life            # 仅 3号AI
venv/bin/python3 scripts/regression_test.py --module file            # 仅 4号AI
venv/bin/python3 scripts/regression_test.py --module sys             # 仅 5号AI
venv/bin/python3 scripts/regression_test.py --module callback        # 仅回调服务
```

## Python 模块速查

| 模块路径 | 核心函数 |
|----------|----------|
| `chat-assistant/src/message_handler.py` | `process_message(text, target_id, open_id)` |
| `chat-assistant/src/main.py` | `talk(messages, open_id="")` → 回复文本 |
| `chat-assistant/src/voice_handler.py` | `process_voice_message(file_key, msg_id, open_id)` |
| `office-assistant/src/document_handler.py` | `process_document_file(file_key, msg_id, open_id, filename)` — 文档分析 + `process_office_text(cmd, open_id, target_id, rtype)` — #办公 命令处理，v3.0 新增 PPT 支持 |
| `office-assistant/src/core/ppt_generator.py` | `generate_presentation(title, slides, path)` |
| `office-assistant/src/core/folder_monitor.py` | `start_monitor(dir, cb)` / `stop_monitor()` |
| `life-assistant/src/scheduler.py` | `schedule_add(time, event)`, `schedule_list(date)`, `schedule_del(id)` |
| `life-assistant/src/health_tracker.py` | `record_health(type, value)`, `health_report(period)` |
| `life-assistant/src/health_analyzer.py` | `analyze_trend(period)` → 趋势分析 |
| `life-assistant/src/reminder.py` | `check_reminders()` → 到期推送 |
| `life-assistant/src/travel_planner.py` | `create(dest, start)`, `list_trips()`, `view(id)`, `add_activity()`, `pack_item()` — 旅行规划 |
| `life-assistant/src/workout_planner.py` | `create(name)`, `list_plans()`, `view(id)`, `add_exercise()`, `log_workout()` — 锻炼规划 |
| `life-assistant/src/work_planner.py` | `create(title)`, `list_items()`, `set_status()`, `set_priority()` — 工作管理 |
| `file-assistant/src/__init__.py` | `process(text, open_id)` → 中文命令解析/分发/校验 |
| `file-assistant/src/file_manager.py` | `cmd_ls(path)`, `cmd_find(name)`, `cmd_cat(path)`(含图片/PDF预览), `cmd_cp(src,dst)`, `cmd_mv(src,dst)`, `cmd_trash(path)`, `cmd_mkdir(path)` |
| `file-assistant/src/file_transfer.py` | `cmd_share(path, target_id)` → 通过飞书发送文件 |
| `file-assistant/src/security.py` | `validate_path(path)` → 白名单校验, `check_file_operation(path, op)` → 操作权限校验 |
| `file-assistant/src/file_bot_server.py` | 独立 Flask 服务（测试环境:5102 / 主环境:5002），处理飞书 webhook |
| `sys-assistant/src/system_monitor.py` | `cmd_status()`, `cmd_disk()`, `cmd_mem()`, `cmd_load()` |
| `sys-assistant/src/service_manager.py` | `cmd_service_start(name)`, `cmd_service_stop(name)`, `cmd_service_restart(name)`, `cmd_service_list()` |
| `sys-assistant/src/process_manager.py` | `cmd_ps_list()`, `cmd_ps_kill(pid)` |
| `sys-assistant/src/log_viewer.py` | `cmd_log(name, lines)`, `cmd_log_search(keyword)` |
| `sys-assistant/src/backup_manager.py` | `cmd_backup_now()`, `cmd_backup_list()`, `cmd_backup_restore(id)` |
| `sys-assistant/src/security.py` | `check_command(cmd)` → 白名单命令校验 |
| `shared/feishu_api.py` | `send_message()`, `download_file()` |
| `shared/backend_utils.py` | `get_backend_config()`, `wake_model()`, `call_api(messages)`, `clean_reply(text)`, `extract_from_reasoning(text)` — 推理后端通用工具 |
| `shared/crypto.py` | `encrypt_text/decrypt_text/encrypt_json/decrypt_json` |
| `shared/knowledge_base.py` | `search(query, top_k=3, min_score=0.15)` v2.2 BM25 |
| `shared/speech_utils.py` | `transcribe_audio(path)`, `convert_opus_to_wav()` |

## 辅助测试（按需）

```bash
python3 assistants/chat-assistant/tests/test_chat.py                   # 1号AI 单元测试
venv-office/bin/python3 assistants/office-assistant/tests/test_office.py # 2号AI 单元测试
python3 scripts/verify_chat.py                                          # 1号AI 回复验证
python3 scripts/test_talk_fix.py                                        # 空回复修复测试
python3 scripts/test_monitor.py                                         # 监控逻辑测试
python3 scripts/verify_feishu_callback.py                               # 飞书回调连通性
```

## 日志

```bash
tail -f logs/flask.log          # 回调服务日志
tail -f logs/monitor.log        # 守护脚本日志
tail -f logs/backup_cron.log    # 定时备份日志
```

## 文档入口

```bash
cat AGENTS.md                   # 沟通准则 → 需求文档 → 备忘录
cat docs/design_summary.md      # 设计汇总
python3 scripts/diagnose.py     # 环境核验
```

## 注意点

- API 请求中 `model` 字段：llama.cpp 用 `gpt-3.5-turbo`（假名），Ollama 用实际模型名
- `callback_server.py` 通过 `sys.path.insert` 硬编码了助手 src 路径 — 添加新助手需同步修改
- 修改 `message_handler.py` 或 `callback_server.py` 后需重启 Flask（`bash scripts/restart_callback.sh`）
- 1号AI 对话历史加密存储于 `assistants/chat-assistant/logs/chat_history_{open_id}.json`
- 2号AI 文件夹监控在 `document_handler.py` 模块加载时自动启动（`data/office/` 目录）
- 模型进程闲置 30 分钟自动 SIGSTOP，请求到达时自动 SIGCONT 唤醒
- 推理进程内存超限 8GB 自动重启
- 飞书凭证在 `shared/feishu-bot/.env`（不得提交）
- `opencode.json` 配置：`provider: openai`, `apiBase: http://localhost:8080/v1`
- 2号AI 改用 `#办公` 前缀（替代 `#2`/`#office`），`转PPT` 可直接发送无需前缀
- 3号AI 改用中文关键词路由（日程/健康/旅行/锻炼/工作/看板），替代 `#3`/`#life` 前缀
- 回复格式简化：无思考过程、无分隔线、时间直接放在问题/回答前
- 回归测试使用 `venv/bin/python3 scripts/regression_test.py`（全局 venv Python 3.12.13），系统 Python 3.9 会因缺少依赖而跳过 23 项

## 文件访问隔离

| 助手 | 允许路径 | 禁止路径 |
|------|----------|----------|
| chat | data/chat, chat-assistant | 其他助手 data/ 目录 |
| office | data/office, office-assistant | 其他助手 data/ 目录 |
| life | data/life, life-assistant | 其他助手 data/ 目录 |
| file | 全局可配置（whitelist.yaml） | 系统敏感路径（/etc, /var, ~/.ssh 等） |
| sys | 仅日志和备份目录 | 用户数据目录 |
