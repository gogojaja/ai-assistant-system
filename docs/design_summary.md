# 设计汇总 (自动生成)

**项目名称**：五角色 AI 助理系统  
**路径**：`/Volumes/BR256G/ai-assistant-system`（测试环境）  
**最后更新：2026-05-27（v3.8 回复格式优化 + 中文路由）**

---

## 1. 整体架构

系统由五个完全解耦的 AI 助理组成，通过飞书 Bot 统一交互，依赖本地推理引擎（llama.cpp 或 Ollama），所有数据本地留存并加密，默认断网运行。

| 助手 | 定位 | 虚拟环境 | 状态 |
|------|------|----------|------|
| 1号 chat-assistant | 闲聊、搜索、知识库、语音 | `venv-chat` (Python 3.12) | ✅ 功能完成 |
| 2号 office-assistant | Word/Excel/PPT、文件夹监控 | `venv-office` (Python 3.12) | ✅ 功能完成 |
| 3号 life-assistant | 个人日程/健康/旅行/锻炼/工作规划 | `venv-life` (Python 3.12) | ✅ v1.0 已实现 |
| 4号 file-assistant | 文件传输、文件管理 | `venv-file` (Python 3.12) | ✅ v1.0 已实现 |
| 5号 sys-assistant | 系统管理、服务启停、进程管理 | `venv-sys` (Python 3.12) | ✅ v1.0 已实现 |

共享层：全局 `venv`（Python 3.12.13）运行飞书回调服务，各助手独立虚拟环境严格隔离。

**网络架构（2026-05-27 v3.7）：** 主环境 + 测试环境共享推理后端与 ngrok 隧道，端口隔离运行。开发在测试环境进行，通过 promote.sh 发布到主环境。

**共享层（单实例）：**
  - `llama-server` :8080（推理引擎）
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
| 大模型引擎 | **llama.cpp** (默认) 或 **Ollama** | 端口8080/11434，config/settings.yaml 切换 |
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
│ ├── settings.yaml                # 全局配置（后端、端口、资源限制）
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
- **推理引擎** `127.0.0.1:8080` (llama.cpp) ✅
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
- ✅ 5号 sys-assistant 系统管理
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

---

## 6. 待办任务

1. **5号AI sys-assistant 飞书前缀路由 `#5`/`#sys` 接入** —— 当前独立服务运行

---

## 7. 风险说明

- 模型稳定运行 qwen2.5:7b（llama.cpp 后端），短回答速度 ~30-45 tok/s
- **qwen3.5 无 7B 版本**（只有 0.8B/2B/4B/9B），不推荐切换；Ollama 对比 llama.cpp 性能略低 5-10%，无切換必要
- 飞书回调需公网可达，本地开发建议内网穿透
- 凭证文件 `**/.env` 被 .gitignore 排除，不会被提交
- 各助手虚拟环境独立，互不干扰
- 3号AI life-assistant 模块已开发完成（含 venv-life），中文关键词路由已接入飞书回调

---

## 8. 进度台账

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
