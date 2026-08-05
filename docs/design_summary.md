# 设计汇总 (自动生成)

**项目名称**：五角色 AI 助理系统  
**路径**：`/Volumes/BR256G/ai-assistant-system`（测试环境）  
**最后更新：2026-06-13（v5.1 飞书聊天切云端 + 后端配置重构）**

---

## 1. 整体架构

系统由五个完全解耦的 AI 助理组成，通过飞书 Bot 统一交互，依赖本地推理引擎（llama.cpp 或 Ollama），所有数据本地留存并加密，默认断网运行。

| 助手 | 定位 | 虚拟环境 | 状态 |
|------|------|----------|------|
| 1号 chat-assistant | 闲聊、搜索、知识库、语音 | `venv-chat` (Python 3.12) | ✅ 功能完成 |
| 2号 office-assistant | Word/Excel/PPT、文件夹监控 | `venv-office` (Python 3.12) | ✅ 功能完成 |
| 3号 life-assistant | 个人日程/健康/旅行/锻炼/工作规划 | `venv-life` (Python 3.12) | ✅ 功能完成 |
| 4号 file-assistant | 文件传输、文件管理 | `venv-file` (Python 3.12) | ✅ 功能完成 |
| 5号 sys-assistant | 系统管理、服务启停、进程管理 | `venv-sys` (Python 3.12) | ✅ 功能完成 |

共享层：全局 `venv`（Python 3.12.13）运行飞书回调服务，各助手独立虚拟环境严格隔离。

**网络架构（2026-06-13 v5.1）：** 主环境 + 测试环境共享推理后端与 ngrok 隧道，端口隔离运行。新增 Free API Hub 云端模型路由作为聊天后端的可选增强。

**共享层（单实例）：**
  - `free-api-hub` :5080（聊天实例）/ :5081（编程实例）
  - `llama-server` :8080（推理引擎，备选）
  - `ngrok account 1`：`employee-radish-fringe.ngrok-free.dev` → `:5101`（测试环境入口）
  - `ngrok account 2`：`coastal-speckled-exorcist.ngrok-free.dev` → `:5001`（主环境入口）

**主环境 (`~/ai-assistant-system/`) → `coastal-speckled-exorcist`：**

| 组件 | 端口 | 说明 |
|------|------|------|
| callback_server | 5001 | `/webhook_chat` 本地处理 |
| file_bot | 5002 | 4号文件助手 |
| sys_bot | 5003 | 5号系统管理 |

代理路由：`/webhook_file` → `:5002`, `/webhook_sys` → `:5003`

**测试环境 (`/Volumes/BR256G/ai-assistant-system/`) → `employee-radish-fringe`：**

| 组件 | 端口 | 说明 |
|------|------|------|
| callback_server | 5101 | `/webhook_chat` 本地处理 |
| file_bot | 5102 | 4号文件助手 |
| sys_bot | 5103 | 5号系统管理 |

代理路由：`/webhook_file` → `:5102`, `/webhook_sys` → `:5103`

---

## 2. 技术选型

| 组件 | 选型 | 说明 |
|------|------|------|
| 语言 | Python 3.12.13 | LTS 稳定版 |
| Web框架 | Flask 2.3.3 | 端口5001 |
| 大模型引擎 | **free-api-hub** (默认聊天) 或 **llama.cpp** (备选) | :5080/5081 云端路由 :8080 本地备选 |
| 飞书SDK | 自封装 `shared/feishu_api.py` | 回调服务 |
| 文档处理 | openpyxl 3.1.2, python-docx, python-pptx | Excel/Word/PPT |
| 语音识别 | whisper.cpp + speech_utils | 离线语音转文字 |
| 翻译 | deep-translator 1.11.4 | 免费翻译 |
| 加密 | cryptography (Fernet) | 对话历史/敏感数据加密存储 |
| 知识库检索 | 纯 Python（无第三方） | BM25 评分 + 中文二元组分词 + 短语加权 |
| 配置 | python-dotenv + PyYAML | 凭证分离 |
| 备份 | tar + crontab | 每日自动备份（保留7天） |
| 文件夹监控 | watchdog | 办公文件变更监测 |

---

## 3. 目录结构（实际）

```
~/ai-assistant-system/
├── venv/                          # 全局主环境 (Python 3.12)
├── assistants/
│ ├── chat-assistant/              # 1号：闲聊检索+语音
│ │ ├── venv-chat/                 # 独立环境 (Python 3.12)
│ │ └── src/
│ │   ├── main.py                  # talk() 流式调模型，支持双后端+wake
│ │   ├── message_handler.py       # 消息分发+历史+提示词+知识库+身份
│ │   ├── voice_handler.py         # 语音消息处理链路
│ │   └── chat_feishu.py           # 飞书轮询脚本
│ ├── office-assistant/            # 2号：办公文档
│ │ ├── venv-office/               # 独立环境 (Python 3.12)
│ │ └── src/
│ │   ├── core/
│ │   │ ├── ppt_generator.py       # PPT 成品生成 (python-pptx)
│ │   │ ├── folder_monitor.py      # 文件夹监控 (watchdog)
│ │   │ ├── word_processor.py
│ │   │ ├── excel_processor.py
│ │   │ └── summarizer.py
│ │   ├── document_handler.py      # 文档消息入口
│ │   └── api_server.py
│ ├── life-assistant/              # 3号：个人日程+健康+旅行+锻炼+工作规划
│ │ ├── venv-life/                 # 独立环境 (Python 3.12)
│ │ └── src/
│ │   ├── __init__.py              # process() 入口 + 命令分发 + 完整 HELP_TEXT
│ │   ├── scheduler.py             # 日程管理（增删改查+搜索）
│ │   ├── health_tracker.py        # 健康数据记录（体重/步数/睡眠/心率等）
│ │   ├── health_analyzer.py       # 健康趋势分析
│ │   ├── reminder.py              # 到期提醒推送
│ │   ├── travel_planner.py        # 旅行规划（创建/行程/行李/打包清单）
│ │   ├── workout_planner.py       # 锻炼规划（计划/记录/历史）
│ │   └── work_planner.py          # 工作规划（待办/进行中/已完成/优先级/截止）
│ ├── file-assistant/              # 4号：文件传输+文件管理
│ │ ├── venv-file/                 # 独立环境 (Python 3.12)
│ │ └── src/
│ │   ├── file_manager.py          # 文件列表/搜索/复制/移动/删除
│ │   ├── file_transfer.py         # 文件上传/下载/分享
│ │   └── security.py              # 路径安全验证
│ ├── sys-assistant/               # 5号：系统管理+服务+进程
│ │ ├── venv-sys/                  # 独立环境 (Python 3.12)
│ │ ├── .env                       # 飞书 Bot 凭证
│ │ └── src/
│ │   ├── __init__.py              # process() 入口 + 命令分发
│ │   ├── bot_server.py            # 独立 Flask 服务 (端口 5003)
│ │   ├── system_monitor.py        # 系统状态监控
│ │   ├── service_manager.py       # 服务启停管理
│ │   ├── process_manager.py       # 进程管理
│ │   ├── log_viewer.py            # 日志查看
│ │   ├── backup_manager.py        # 备份管理
│ │   └── security.py              # 安全操作限制
├── shared/
│ ├── feishu_api.py                # 飞书API封装
│ ├── feishu-bot/.env              # 飞书凭证（1号/2号/3号共用）
│ ├── feishu-callback/
│ │ └── callback_server.py         # Flask主入口：/webhook 本地处理 + /webhook_file 反向代理
│ ├── utils.py                     # 通用工具（天气、翻译、搜索）
│ ├── crypto.py                    # 数据加密工具 (Fernet)
│ ├── knowledge_base.py            # 私有知识库检索（支持按 user_id 分用户隔离）
│ ├── speech_utils.py              # 语音识别 (whisper.cpp)
│ └── voice/voice_input.py         # 本地录音输入
├── config/
│ ├── settings.yaml                # 全局配置（后端、端口、资源限制、云端路由）
│ └── whitelist.yaml               # 文件访问白名单
├── prompts/                       # 用户自定义提示词
├── data/knowledge/                # 知识库文档目录
├── logs/                          # 运行时日志
├── docs/design_summary.md         # 本文档
├── scripts/
│ ├── start_all_services.sh        # 启动所有服务
│ ├── stop_all_services.sh         # 停止所有服务
│ ├── promote.sh                   # 一键发布测试→主环境
│ ├── diff_envs.sh                 # 环境对比
│ ├── restart_callback.sh          # 重启 Flask
│ ├── monitor_services.sh          # 服务守护
│ ├── daily_backup.sh              # 每日备份
│ ├── restore.sh                   # 一键还原
│ └── ...（其他运维脚本）
├── .gitignore                     # Git 忽略规则（排除密钥/配置）
└── .git/                          # Git 仓库（仅测试环境）
```

---

## 4. 当前服务状态

**共享层（单实例）：**
- **云端路由** `127.0.0.1:5080` (free-api-hub 聊天) ✅
- **云端编程** `127.0.0.1:5081` (free-api-hub 编程) ✅
- **推理引擎** `127.0.0.1:8080` (llama.cpp，备选) ✅
- **主 ngrok** `employee-radish-fringe.ngrok-free.dev` → `:5101`（测试环境）✅
- **第二 ngrok** `coastal-speckled-exorcist.ngrok-free.dev` → `:5001`（主环境）✅

**主环境 (`~/ai-assistant-system/`)：**
- **回调服务** `127.0.0.1:5001` ✅ callback_server.py (venv-chat)
- **文件 Bot** `127.0.0.1:5002` ✅ 独立 Flask (venv-file)
- **系统 Bot** `127.0.0.1:5003` ✅ 独立 Flask (venv-sys)

**测试环境 (`/Volumes/BR256G/ai-assistant-system/`)：**
- **回调服务** `127.0.0.1:5101` ✅ callback_server.py (venv-chat)
- **文件 Bot** `127.0.0.1:5102` ✅ 独立 Flask (venv-file)
- **系统 Bot** `127.0.0.1:5103` ✅ 独立 Flask (venv-sys)

**基础服务：**
- **依赖库**：flask, requests, openpyxl, python-dotenv, deep-translator, pyyaml, python-docx, python-pptx, watchdog, cryptography 全部 ✅
- **核心文件**：全部核心文件完整 ✅
- **Git 版本管理**：测试环境 git 仓库已初始化 ✅
- **发布工作流**：promote.sh + diff_envs.sh 就绪 ✅

---

## 5. 已完成工作

- ✅ 主环境升级至 Python 3.12.13
- ✅ 全部依赖补全（22个库）
- ✅ 核心文件恢复与软链接修复
- ✅ Flask 回调服务正常运行
- ✅ llama.cpp / Ollama 双后端支持
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
- ✅ (2026-06-13) shared/backend_utils.py 新增 free-api-hub 后端支持（配置读取+API调用）
- ✅ (2026-06-13) 飞书1号机器人切换至 free-api-hub 聊天实例（Qwen3-32B）

---

## 6. 待办任务

1. **5号AI sys-assistant 飞书前缀路由 `#5`/`#sys` 集成到 callback_server.py** —— 当前通过独立 Bot 服务 + 反向代理运行，可考虑合并到主路由
2. **飞书 WebSocket Bot（shared/feishu-bot/）** —— 代码结构存在，尚未接入主线流程
3. **dev-assistant 第6角色** —— 目录存在但无代码
4. **watchdog 安装** —— office-assistant 文件夹监控依赖，当前 venv-office 未安装
5. **推理后端接入 E2E 测试** —— 当前 llama-server 未启动时 23 项后端依赖测试记录为 WARNING 降级
6. **free-api-hub chat.yaml / code.yaml 模型优先级调整** —— 当前路由可能落到弱模型，需手动调整优先级
7. **openapi.json provider 命名规范化** —— 已统一为 `free-api-hub-chat` / `free-api-hub-code`，去掉了 `default` 占位符

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

## 8. 端到端验证（2026-05-28）

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
venv/bin/python3 scripts/regression_test.py          # 全量 105 项
venv/bin/python3 scripts/regression_test.py --module chat  # 按模块筛选
```

---

## 9. 风险说明

- 模型稳定运行 qwen2.5:7b（llama.cpp 后端），短回答速度 ~30-45 tok/s
- **free-api-hub 云端路由**（Qwen3-32B）作为聊天后端，速度取决于网络和 Free API Hub 可用性
- **qwen3.5 无 7B 版本**（只有 0.8B/2B/4B/9B），不推荐切换；Ollama 对比 llama.cpp 性能略低 5-10%，无切換必要
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
| 2026-06-13 | v5.1 backend_utils.py 重构 | 支持 free-api-hub 后端（配置读取+API调用+跳过本地唤醒） |
| 2026-06-13 | v5.1 飞书聊天切换云端 | 1号机器人从 llama.cpp(qwen2.5:7b) 切至 free-api-hub(Qwen3-32B) |
