# 沟通与任务处理准则（最高优先级）

接收需求后禁止急于作答、禁止立刻动手编写内容，优先统筹梳理全局信息，规划完整可行主干方案 + 兜底替代方案，展示方案待用户确认后再落地执行。

会话启动第一时间提醒切换专家模式，保障高阶规则正常生效。

输出规避晦涩术语，所有操作复制即可运行。项目启动即刻生成《环境搭建方案设计文档》，记录架构、选型、目录、版本、部署、风险、进度等信息，内容变动即时同步更新，保障跨 AI 无缝接续工作。

阶段与每日收尾后，生成信息核验脚本，自动比对实际环境与文档数据，标注偏差保证同步。

对话交接前完成全文档校准更新，生成新会话开场话术；新会话接收文档后静待指令，不擅自操作。

会话结束复盘全部交互，结合执行效果给出提示词优化建议。

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

**目标**：构建一套完全本地离线、基于飞书 Bot 统一交互的五角色 AI 助理系统，数据不离开本地设备，支持 macOS Apple Silicon 推理。

**架构**：飞书 Bot → cloudflared 隧道 → Flask 回调服务 (port 5001) → 推理后端 (llama.cpp 或 Ollama) → 各助手处理器 → 飞书回复

**物理路径**：`~/ai-assistant-system/`

---

## 2. 五角色定义

| 角色 | 代号 | 目录 | 定位 | 入口 |
|------|------|------|------|------|
| 1号AI | chat-assistant | `assistants/chat-assistant/` | 闲聊对话、天气查询、翻译搜索、知识库、语音输入 | `message_handler.process_message()` — 所有文本/语音默认进入 |
| 2号AI | office-assistant | `assistants/office-assistant/` | Word 摘要、Excel 分析、PPT 生成、文件变更监控 | `document_handler.process_document_file()` — 飞书文件消息触发 |
| 3号AI | life-assistant | `assistants/life-assistant/` | 个人日程管理、健康管理 | `process()` — 飞书文字 `#3`/`#life` 前缀触发 |
| 4号AI | file-assistant | `assistants/file-assistant/` | 文件传输、文件管理 | `process()` — 飞书文字 `#4`/`#file` 前缀触发 |
| 5号AI | sys-assistant | `assistants/sys-assistant/` | 系统管理、服务启停、进程管理 | `process()` — 飞书文字 `#5`/`#sys` 前缀触发 |

---

## 3. 功能需求

### 3.1 1号AI 闲聊助理

| ID | 需求 | 优先级 | 状态 | 实现位置 |
|----|------|--------|------|----------|
| CHAT-01 | 接收飞书文本消息，调用模型回复 | P0 | ✅ 已实现 | `callback_server.py:111` → `message_handler.process_message()` → `main.talk()` |
| CHAT-02 | 流式调用模型，拼接 content 和 reasoning_content | P0 | ✅ 已实现 | `main.py:talk()` |
| CHAT-03 | content 为空时从 reasoning 提取回答（5 层策略） | P0 | ✅ 已实现 | `main.py:_extract_from_reasoning()` |
| CHAT-04 | 对话历史 per-user 持久化（最多 10 轮） | P0 | ✅ 已实现 | `message_handler.py:_load_history/_save_history()` |
| CHAT-05 | 对话历史加密存储 | P0 | ✅ 已实现 | `shared/crypto.py` Fernet 加解密，`message_handler.py` 读写时调用 |
| CHAT-06 | 天气查询（识别城市名，默认北京） | P1 | ✅ 已实现 | `message_handler.py:124-155` + `main.py:get_weather()` |
| CHAT-07 | 中英翻译（MyMemory 免费 API） | P1 | ✅ 已实现 | `message_handler.py:114-121` + `shared/utils.py:translate_text()` |
| CHAT-08 | 网络搜索（Bing） | P2 | ✅ 已实现 | `message_handler.py:132-136` + `shared/utils.py:handle_search()` |
| CHAT-09 | 清空历史指令 `clear` | P1 | ✅ 已实现 | `message_handler.py:100-104` |
| CHAT-10 | 身份识别（"我是谁"问题从历史正则提取） | P1 | ✅ 已实现 | `message_handler.py:_find_user_name()` |
| CHAT-11 | 自定义提示词管理（设置/查看/重置） | P2 | ✅ 已实现 | `message_handler.py:106-130` + `main.py:_load_custom_prompt/_save_custom_prompt()` |
| CHAT-12 | 私有知识库检索（`查知识：<问题>`） | P2 | ✅ 已实现 | `shared/knowledge_base.py` v2.2（BM25+中文二元组+短语加权） + `message_handler.py:133-148` |
| CHAT-13 | 离线语音消息接收（whisper.cpp 转文字） | P1 | ✅ 已实现 | `callback_server.py:113-121` → `voice_handler.py` → `speech_utils.py` |
| CHAT-14 | 知识库文件导入（放入 data/knowledge/ 自动索引） | P2 | ✅ 已实现 | `shared/knowledge_base.py:import_doc()` |
| CHAT-15 | 模型进程闲置休眠/唤醒 | P1 | ✅ 已实现 | `monitor_services.sh:idle_sleep_check()` + `main.py:_wake_model()` |
| CHAT-16 | 多后端支持（llama.cpp / Ollama 配置切换） | P2 | ✅ 已实现 | `config/settings.yaml:backend` + `main.py:_get_backend_config()` |

### 3.2 2号AI 办公助理

| ID | 需求 | 优先级 | 状态 | 实现位置 |
|----|------|--------|------|----------|
| OFF-01 | 接收飞书 .docx 文件，提取文本生成摘要 | P1 | ✅ 已实现 | `document_handler.py:91-119` → `core/word_processor.py` + `core/summarizer.py` |
| OFF-02 | 接收飞书 .xlsx 文件，分析结构与数据 | P1 | ✅ 已实现 | `document_handler.py:120-145` → `core/excel_processor.py` |
| OFF-03 | Excel 数据 AI 智能摘要 | P1 | ✅ 已实现 | `document_handler.py:generate_excel_summary()` 调用 `main.talk()` |
| OFF-04 | 根据文案生成 .pptx 成品文件 | P2 | ✅ 已实现 | `core/ppt_generator.py:generate_from_text()` / `generate_presentation()` |
| OFF-05 | 办公文件夹变更监控（watchdog） | P2 | ✅ 已实现 | `core/folder_monitor.py:start_monitor()` / `stop_monitor()` |
| OFF-06 | PPT 内容自动分段解析 | P2 | ✅ 已实现 | `ppt_generator.py:generate_from_text()` 按行自动拆分幻灯片 |

### 3.3 3号AI 个人日程与健康管理助理

| ID | 需求 | 优先级 | 状态 | 实现位置 |
|----|------|--------|------|----------|
| LIFE-01 | 日程创建（标题、时间、地点、备注） | P1 | 📋 待实现 | `life-assistant/src/scheduler.py` |
| LIFE-02 | 日程查询（按日期/关键词/范围） | P1 | 📋 待实现 | `life-assistant/src/scheduler.py` |
| LIFE-03 | 日程修改/删除 | P1 | 📋 待实现 | `life-assistant/src/scheduler.py` |
| LIFE-04 | 日程到期提醒推送 | P2 | 📋 待实现 | `life-assistant/src/reminder.py` |
| LIFE-05 | 健康数据记录（体重、步数、睡眠、心率等） | P1 | 📋 待实现 | `life-assistant/src/health_tracker.py` |
| LIFE-06 | 健康数据统计与可视化（日报/周报/月报） | P2 | 📋 待实现 | `life-assistant/src/health_tracker.py` |
| LIFE-07 | 健康趋势分析与建议 | P2 | 📋 待实现 | `life-assistant/src/health_analyzer.py` |
| LIFE-08 | 飞书 `#3`/`#life` 前缀路由 | P1 | 📋 待实现 | `callback_server.py` 路由到 `life-assistant` |

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
| FILE-08 | 独立飞书 Bot Webhook 服务（端口5002） | P1 | ✅ 已实现 | `file-assistant/src/file_bot_server.py` |
| FILE-09 | 中文命令交互（无需前缀，非法命令拒绝） | P1 | ✅ 已实现 | `file-assistant/src/__init__.py` |
| FILE-10 | 自动守护集成（monitor_services.sh） | P2 | ✅ 已实现 | `scripts/monitor_services.sh` |

### 3.5 5号AI 系统管理助理

| ID | 需求 | 优先级 | 状态 | 实现位置 |
|----|------|--------|------|----------|
| SYSADM-01 | 系统状态查询（CPU/内存/磁盘/网络/负载） | P1 | 📋 待实现 | `sys-assistant/src/system_monitor.py` |
| SYSADM-02 | 服务管理（启动/停止/重启/查看状态） | P1 | 📋 待实现 | `sys-assistant/src/service_manager.py` |
| SYSADM-03 | 进程管理（查看进程树/终止进程/优先级调整） | P1 | 📋 待实现 | `sys-assistant/src/process_manager.py` |
| SYSADM-04 | 日志查看（实时 tail/关键词过滤/日志归档） | P2 | 📋 待实现 | `sys-assistant/src/log_viewer.py` |
| SYSADM-05 | 备份管理（手动触发备份/查看备份列表/还原） | P2 | 📋 待实现 | `sys-assistant/src/backup_manager.py` |
| SYSADM-06 | 远程服务启停（通过飞书命令控制远端服务） | P1 | 📋 待实现 | `sys-assistant/src/service_manager.py` |
| SYSADM-07 | 安全操作限制（禁止 sudo、白名单命令校验） | P0 | 📋 待实现 | `sys-assistant/src/security.py` |
| SYSADM-08 | 飞书 `#5`/`#sys` 前缀路由 | P1 | 📋 待实现 | `callback_server.py` 路由到 `sys-assistant` |

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
| SYS-12 | 后端配置切换（llama.cpp / Ollama） | P2 | ✅ 已实现 | `config/settings.yaml` + `main.py:_get_backend_config()` |

---

## 4. 数据流

```
飞书用户发送消息
  │
  ├─ cloudflared 隧道 (https → localhost:5001)
  │
  └─ Flask callback_server.py
       │
       ├─ message_type == "text" ──┬─ 前缀 #5/#sys  → 5号AI sys-assistant process()
       │                           ├─ 前缀 #4/#file → 4号AI file-assistant process()
       │                           ├─ 前缀 #3/#life → 3号AI life-assistant process()
       │                           └─ 其他文本 → 1号AI process_message()
       │                                ├─ 天气/翻译/搜索/清空/提示词/知识库 → 直接回复
       │                                ├─ 身份问题 → 历史正则提取 → 回复
       │                                └─ 闲聊 → 加载历史 → 检索知识库 → talk() → 保存历史 → 回复
       │
       ├─ message_type == "audio" → voice_handler (下载 opus → ffmpeg 转 wav → whisper.cpp 识别 → process_message)
       │
       └─ message_type == "file"  → document_handler (下载 → Word/Excel/PPT 处理)

推理后端 (由 settings.yaml 决定):
  ├─ backend=llama.cpp → localhost:8080 (llama-server + qwen3:4b)
  └─ backend=ollama    → localhost:11434 (ollama serve + ollama_model)
```

---

## 5. 非功能需求

| 类别 | 需求 | 指标/约束 |
|------|------|-----------|
| 离线 | 默认断网运行，所有服务本地启动 | 天气/翻译/搜索需要网络，失败时优雅降级 |
| 安全 | 数据加密存储 | 对话历史、敏感文件使用 cryptography.fernet 加密 |
| 安全 | 飞书凭证隔离 | APP_ID/APP_SECRET 存于 `shared/feishu-bot/.env`，不提交 |
| 安全 | 禁止 sudo | 全程使用用户权限，无提权操作 |
| 性能 | 推理内存上限 | 默认 8GB，超限自动重启 |
| 性能 | 闲置资源释放 | 模型进程空闲 30 分钟自动 SIGSTOP |
| 可靠 | 服务守护 | 自动检测进程/端口状态，故障自动拉起 |
| 可靠 | 备份恢复 | 每日备份保留 7 天，restore.sh 一键还原 |
| 隔离 | 文件访问 | 五助手互不可见各自数据目录（whitelist.yaml） |
| 隔离 | 虚拟环境 | 全局 + 五个助手共 6 个独立 venv，不可混用 |
| 兼容 | 推理后端 | 同时支持 llama.cpp 和 Ollama，配置切换 |
| 平台 | macOS Apple Silicon | M 系列芯片，Metal GPU 加速 |

---

## 6. 部署需求

### 6.1 依赖清单

| 组件 | 版本/路径 | 用途 |
|------|-----------|------|
| Python | 3.12.x (macOS 原生或 Homebrew) | 运行时 |
| llama.cpp | `~/llama.cpp/build/bin/llama-server` | 推理引擎 (Metal) |
| qwen3:4b 模型 | `~/.local/lib/ollama/blobs/sha256-3e4cb1417446*` (5.8GB) | 推理模型 |
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
│   │       └── reminder.py             # 到期提醒
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
| ❌ 无自动联网 | 仅天气/翻译/搜索功能按需联网，核心服务离线 |
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
| 模型推理 | qwen3:4b (5.8GB) | 推理模型参数 |
| 上下文长度 | 4096 tokens | llama.cpp 配置 |
| 回复 max_tokens | 1024 | 兼顾 reasoning 和 content |
| API 超时 | 60 秒 | requests timeout |
| 对话记忆 | 最多 10 轮 | per-user 裁剪 |
| 内存上限 | 8 GB | 模型进程超限重启 |
| 闲置休眠 | 30 分钟 | SIGSTOP 挂起 |
| 启动耗时 | ~5 秒 | 服务启动 + 3 秒等待 |
| 备份保留 | 7 天 | find -mtime +7 -delete |

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
| `#3 schedule add <时间> <事件>` / `#3 schedule list` / `#3 schedule del <id>` | 3号AI：日程管理 |
| `#3 health record <类型> <数值>` / `#3 health report <日报/周报/月报>` | 3号AI：健康管理 |
| `#3 help` | 3号AI：帮助 |
| `查看 <路径>` / `搜索 <关键词>` / `信息 <路径>` | 4号AI：文件查看/搜索 |
| `复制 <源> <目标>` / `移动 <源> <目标>` / `重命名 <路径> <新名>` | 4号AI：文件操作 |
| `删除 <路径1> [路径2 ...]` | 4号AI：批量移入回收站 |
| `上传 [保存路径]` / `下载 <路径>` / `分享 <路径>` | 4号AI：文件传输 |
| `创建目录 <路径>` | 4号AI：创建目录 |
| `帮助` | 4号AI：帮助 |
| `#5 sys status` / `#5 sys disk` / `#5 sys mem` / `#5 sys load` | 5号AI：系统状态 |
| `#5 svc start <name>` / `#5 svc stop <name>` / `#5 svc restart <name>` / `#5 svc list` | 5号AI：服务管理 |
| `#5 ps list` / `#5 ps kill <pid>` | 5号AI：进程管理 |
| `#5 log <name> [lines]` / `#5 log search <keyword>` | 5号AI：日志查看 |
| `#5 backup now` / `#5 backup list` / `#5 backup restore <id>` | 5号AI：备份管理 |
| `#2 help` | 2号AI：帮助 |
| `#2 ppt <文案>` / `#2 生成ppt：<文案>` | 2号AI：根据文案生成专业级 PPT（支持 `##` 章节、`-` 要点、`左|右` 双栏） |
| `#5 help` | 5号AI：帮助 |
| `clear` | 清空对话历史 |

## Python 模块速查

| 模块路径 | 核心函数 |
|----------|----------|
| `chat-assistant/src/message_handler.py` | `process_message(text, target_id, open_id)` |
| `chat-assistant/src/main.py` | `talk(messages, open_id="")` → 回复文本 |
| `chat-assistant/src/voice_handler.py` | `process_voice_message(file_key, msg_id, open_id)` |
| `office-assistant/src/document_handler.py` | `process_document_file(file_key, msg_id, open_id, filename)` — 文档分析 + `process_office_text(cmd, open_id, target_id, rtype)` — #2 命令处理，v3.0 新增 PPT 支持 |
| `office-assistant/src/core/ppt_generator.py` | `generate_presentation(title, slides, path)` |
| `office-assistant/src/core/folder_monitor.py` | `start_monitor(dir, cb)` / `stop_monitor()` |
| `life-assistant/src/scheduler.py` | `schedule_add(time, event)`, `schedule_list(date)`, `schedule_del(id)` |
| `life-assistant/src/health_tracker.py` | `record_health(type, value)`, `health_report(period)` |
| `life-assistant/src/health_analyzer.py` | `analyze_trend(period)` → 趋势分析 |
| `life-assistant/src/reminder.py` | `check_reminders()` → 到期推送 |
| `file-assistant/src/__init__.py` | `process(text, open_id)` → 中文命令解析/分发/校验 |
| `file-assistant/src/file_manager.py` | `cmd_ls(path)`, `cmd_find(name)`, `cmd_cat(path)`(含图片/PDF预览), `cmd_cp(src,dst)`, `cmd_mv(src,dst)`, `cmd_trash(path)`, `cmd_mkdir(path)` |
| `file-assistant/src/file_transfer.py` | `cmd_share(path, target_id)` → 通过飞书发送文件 |
| `file-assistant/src/security.py` | `validate_path(path)` → 白名单校验, `check_file_operation(path, op)` → 操作权限校验 |
| `file-assistant/src/file_bot_server.py` | 独立 Flask 服务(端口5002)，处理飞书 webhook |
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

## 测试

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

## 文件访问隔离

| 助手 | 允许路径 | 禁止路径 |
|------|----------|----------|
| chat | data/chat, chat-assistant | 其他助手 data/ 目录 |
| office | data/office, office-assistant | 其他助手 data/ 目录 |
| life | data/life, life-assistant | 其他助手 data/ 目录 |
| file | 全局可配置（whitelist.yaml） | 系统敏感路径（/etc, /var, ~/.ssh 等） |
| sys | 仅日志和备份目录 | 用户数据目录 |
