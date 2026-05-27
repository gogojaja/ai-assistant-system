# 设计汇总 (自动生成)

**项目名称**：五角色 AI 助理系统  
**路径**：`~/ai-assistant-system`  
**最后更新：2026-05-26（v3.4 双 ngrok 隧道架构 + 独立启停脚本）**

---

## 1. 整体架构

系统由五个完全解耦的 AI 助理组成，通过飞书 Bot 统一交互，依赖本地推理引擎（llama.cpp 或 Ollama），所有数据本地留存并加密，默认断网运行。

| 助手 | 定位 | 虚拟环境 | 状态 |
|------|------|----------|------|
| 1号 chat-assistant | 闲聊、搜索、知识库、语音 | `venv-chat` (Python 3.12) | ✅ 功能完成 |
| 2号 office-assistant | Word/Excel/PPT、文件夹监控 | `venv-office` (Python 3.12) | ✅ 功能完成 |
| 3号 life-assistant | 个人日程管理、健康管理 | `venv-life` (Python 3.12) | 📋 待实现 |
| 4号 file-assistant | 文件传输、文件管理 | `venv-file` (Python 3.12) | ✅ v1.0 已实现 |
| 5号 sys-assistant | 系统管理、服务启停、进程管理 | `venv-sys` (Python 3.12) | ✅ v1.0 已实现 |
| — | — | `venv-life` (Python 3.12) | ❌ 尚未创建 |

共享层：全局 `venv`（Python 3.12.13）运行飞书回调服务，各助手独立虚拟环境严格隔离。

**网络架构（2026-05-26 v3.4 双 ngrok）：** 两个 ngrok 账号分别承载不同 Bot：

| ngrok 账号 | 域名 | 指向 | 承载 |
|-----------|------|------|------|
| 主（1号） | `employee-radish-fringe.ngrok-free.dev` | → `:5001` callback_server | 1号/2号/3号（共用 `/webhook_chat`） |
| 第二（2号） | `coastal-speckled-exorcist.ngrok-free.dev` | → `:5001` callback_server | 4号 `/webhook_file` → :5002, 5号 `/webhook_sys` → :5003 |

callback_server.py 路由：
  - `/webhook_chat` → 本机处理（1号闲聊/2号办公/3号日程，按消息类型分派）
  - `/webhook_file` → 反向代理到 :5002（4号文件助手）
  - `/webhook_sys` → 反向代理到 :5003（5号系统管理）
  - `/webhook` → 保留兼容，未使用

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
~/ai-assistant-system/
├── venv/                          # 全局主环境 (Python 3.12)
├── assistants/
│ ├── chat-assistant/              # 1号：闲聊检索+语音
│ │ ├── venv-chat/                 # 独立环境 (Python 3.12)
│ │ └── src/
│ │   ├── __init__.py
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
│ ├── life-assistant/              # 3号：个人日程管理+健康管理
│ │ ├── venv-life/                 # 独立环境 (Python 3.12)
│ │ └── src/
│ │   ├── scheduler.py             # 日程管理（增删改查）
│ │   ├── health_tracker.py        # 健康数据记录
│ │   ├── health_analyzer.py       # 健康趋势分析
│ │   └── reminder.py              # 到期提醒
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
│ ├── file-assistant/              # 4号：文件传输+文件管理
│ │ ├── venv-file/                 # 独立环境 (Python 3.12)
│ │ └── src/
│ │   ├── __init__.py              # process() 入口 + 命令分发
│ │   ├── file_bot_server.py       # 独立 Flask 服务 (端口 5002)
│ │   ├── file_manager.py          # 文件列表/搜索/复制/移动/删除
│ │   ├── file_transfer.py         # 文件上传/下载/分享
│ │   └── security.py              # 路径安全验证
├── shared/
│ ├── feishu_api.py                # 飞书API封装
│ ├── feishu-bot/.env              # 飞书凭证（1号/2号/3号共用）
│ ├── feishu-callback/
│ │ └── callback_server.py         # Flask主入口：/webhook 本地处理 + /webhook_file→5002 + /webhook_sys→5003 反向代理
│ ├── utils.py                     # 通用工具（天气、翻译、搜索）
│ ├── crypto.py                    # 数据加密工具 (Fernet)
│ ├── knowledge_base.py            # 私有知识库检索（支持按 user_id 分用户隔离）
│ ├── speech_utils.py              # 语音识别 (whisper.cpp)
│ └── voice/voice_input.py         # 本地录音输入
├── config/
│ ├── settings.yaml                # 全局配置（后端、端口、资源限制）
│ └── whitelist.yaml               # 文件访问白名单
├── prompts/                       # 用户自定义提示词
├── data/knowledge/                # 知识库文档目录（含 {open_id}/ 子目录分用户隔离）
├── logs/                          # 运行时日志
├── docs/design_summary.md         # 本文档
├── scripts/
│ ├── start_all_services.sh        # 启动所有服务（双后端识别+双ngrok+4/5号）
│ ├── stop_all_services.sh         # 停止所有服务
│ ├── start_chat_bots.sh           # 仅启动1/2/3号（callback_server+主ngrok）
│ ├── stop_chat_bots.sh            # 仅停止1/2/3号
│ ├── start_file_sys_bots.sh       # 仅启动4/5号（file_bot+sys_bot+第二ngrok）
│ ├── stop_file_sys_bots.sh        # 仅停止4/5号
│ ├── backup_models.sh             # 备份所有模型文件到 /Volumes/WDC500G/model_backups/
│ ├── monitor_services.sh          # 服务守护+内存监控+闲置休眠
│ ├── restore.sh                   # 一键还原
│ ├── init_crypto.sh               # 加密初始化
│ ├── diagnose.py                  # 环境诊断
│ ├── restart_callback.sh          # 重启Flask（修正为直接使用venv-chat）
│ └── optimize_voice.sh            # 语音模型下载
├── verify_env.sh                  # 环境核验脚本
├── daily_backup.sh                # 每日备份（crontab）
└── .crypto_key                    # 加密密钥 (600权限)

---

## 4. 当前服务状态

- **回调服务** `127.0.0.1:5001` ✅ callback_server.py (venv-chat)
- **推理引擎** `127.0.0.1:8080` (llama.cpp) ✅
- **文件 Bot** `127.0.0.1:5002` ✅ 独立 Flask (venv-file)
- **系统 Bot** `127.0.0.1:5003` ✅ 独立 Flask (venv-sys)
- **公网隧道** 主 ngrok `employee-radish-fringe.ngrok-free.dev` → :5001 ✅
- **公网隧道** 第二 ngrok `coastal-speckled-exorcist.ngrok-free.dev` → :5001 ✅
- **依赖库**：flask, requests, openpyxl, python-dotenv, deep-translator, pyyaml, python-docx, python-pptx, watchdog, cryptography 全部 ✅
- **核心文件**：全部核心文件完整 ✅
- **备份脚本**：daily_backup.sh（crontab 每日 24:00 → `/Volumes/WDC500G/old_projects/`，保留30天）+ backup_models.sh（模型备份 → `/Volumes/WDC500G/model_backups/`）+ restore.sh ✅
- **数据加密**：.crypto_key 已配置 ✅

---

## 5. 部署流程（简版）

1. 项目放置 `~/ai-assistant-system`
2. 主环境：`python3.12 -m venv venv` → `pip install -r requirements_main_backup.txt`
3. 各助手独立创建虚拟环境（如 `venv-chat`）
4. 配置飞书凭证至 `shared/feishu-bot/.env`
5. 启动 llama.cpp 模型服务
6. 启动 Flask：`source venv/bin/activate && python shared/feishu-callback/callback_server.py &`

---

## 6. 已完成工作

- ✅ 主环境升级至 Python 3.12.13
- ✅ 全部依赖补全（22个库）
- ✅ 核心文件恢复与软链接修复
- ✅ Flask 回调服务正常运行
- ✅ llama.cpp / Ollama 双后端支持
- ✅ 设计文档与实际环境同步
- ✅ 环境核验脚本可用
- ✅ 一键还原脚本 restore.sh
- ✅ 服务守护 monitor_services.sh（内存监控+闲置休眠+自动唤醒）
- ✅ 数据加密留存 (cryptography Fernet)
- ✅ 离线语音识别 (whisper.cpp 飞书接入)
- ✅ 自定义提示词管理（设置/查看/重置）
- ✅ 私有知识库（data/knowledge/ 文件导入+BM25关键词检索）
- ✅ 知识库检索精度优化（v2.2：中文二元组分词 + BM25 评分 + 完整短语加权 + 冗余结果过滤）
- ✅ 2号AI PPT 成品生成 (python-pptx)
- ✅ 2号AI 文件夹监控 (watchdog)
- ✅ crontab 每日备份配置
- ✅ 4号 file-assistant 开发完成（文件管理+传输，独立飞书 Bot 端口5002）
- ✅ 5号 sys-assistant 开发完成（系统状态/服务/进程/日志/备份管理，独立飞书 Bot 端口5003）
- ✅ 单一 ngrok 隧道 + callback_server 内置路由分发三 Bot
- ✅ 知识库按用户隔离（`data/knowledge/{open_id}/` 独立子目录 + 索引文件）
- ✅ 回复引用提问 + 显示提问时间 / 回复时间
- ✅ 双 ngrok 隧道架构（两个账号分别承载 1/2/3号 和 4/5号）
- ✅ 新增 `/webhook_chat` 路由（1/2/3号共用 callback_server 入口）
- ✅ 4号/5号 飞书 Bot 回调 URL 已配置并验证独立工作
- ✅ 系统 prompt 修复（消除格式约束矛盾，模型不再回吐规则）
- ✅ 默认定位改为西安
- ✅ 独立启停脚本（start/stop_chat_bots.sh + start/stop_file_sys_bots.sh）

---

## 7. 待办任务

1. **3号AI life-assistant 开发**（个人日程管理 + 健康管理）—— 含 venv-life 创建 + 全部源文件

---

## 8. 风险说明

- 本地大模型性能受限于 llama.cpp 模型文件质量
- 飞书回调需公网可达，本地开发建议内网穿透
- 凭证文件 `shared/feishu-bot/.env` 不得泄露
- 各助手虚拟环境独立，互不干扰，可随时启停
- **venv-life 尚未创建**（3号AI 待开发）

---

## 9. 进度台账

| 日期 | 操作 | 备注 |
|------|------|------|
| 2026-05-24 | 主环境 Python 3.12 升级 | pip 全量重装，22库成功 |
| 2026-05-24 | 补装 python-docx | 消除文档处理器导入报错 |
| 2026-05-24 | 设计文档同步更新 | 模型引擎修正为 llama.cpp |
| 2026-05-25 | v2.0 → v2.2 知识库检索升级 | TF-IDF→BM25，中文单字→二元组分词，min_score 0.05→0.15，短语加权 |
| 2026-05-25 | 1号AI 严重bug修复 | fallback talk 补 open_id 参数、KB 上下文不再污染历史、解密失败加日志、移除遗留 debug |
| 2026-05-25 | 1号AI UX 优化 P0+P2 | \"正在思考\"中间态+替换、回复尾部记忆轮次提示、超长回复自动分块 |
| 2026-05-25 | 语音识别优化 v1.1 | 升级 medium 模型、音频归一化、4 线程加速、修复命令构建 |
| 2026-05-25 | 回复截断修复 | _format_reply 修标点误补、_extract_from_reasoning 段落优先于引号、max_tokens 1024→2048 |
| 2026-05-25 | 记忆轮次改用持久计数器 | 独立 counter 文件，10轮后自动重置 |
| 2026-05-25 | 身份识别修复 | 自我介绍同时识别当前消息而非仅查历史 |
| 2026-05-25 | v2.2 → v3.0 角色重构 | 3号改为个人日程+健康管理，新增4号文件管理，5号系统管理 |
| 2026-05-25 | v3.0 4号 file-assistant 实现 | 安全校验+文件管理+传输+独立飞书 Bot 服务 |
| 2026-05-25 | 4号 file-assistant 优化 | 回收站、图片/PDF预览、批量操作、下载改飞书发送、中文命令去#4前缀、monitor集成 |
| 2026-05-26 | 5号 sys-assistant v1.0 实现 | 系统状态监控、服务管理、进程管理、日志查看、备份管理 |
| 2026-05-26 | 5号 独立飞书 Bot 服务 | 端口 5003，独立 Bot 凭证，与主回调完全隔离 |
| 2026-05-26 | ngrok 统一代理 | 单 ngrok 隧道 + 路径路由分发三 Bot（5001 代理→5005/5002/5003） |
| 2026-05-26 | 架构回退 + 内置路由 | 移除 ngrok_proxy，callback_server 直接监听 5001 并内置反向代理（/webhook_file→5002, /webhook_sys→5003） |
| 2026-05-26 | docs: v3.2 同步 | 文档与实际架构对齐 |
| 2026-05-26 | v3.3 知识库按用户隔离 | `knowledge_base.py` 全部函数支持 `user_id` 参数，文档存入 `data/knowledge/{open_id}/` |
| 2026-05-26 | v3.3 回复引用+时间戳 | `_quote_reply_header()` 在 AI 聊天回复前引用用户提问，显示提问时间与回复时间 |
| 2026-05-26 | 双 ngrok 隧道架构 | 第二 ngrok 账号 + 独立进程，4/5号通过 callback_server 代理走第二隧道 |
| 2026-05-26 | 新增 `/webhook_chat` 路由 | 1/2/3号共用回调路径；callback_server 根据消息类型分派 |
| 2026-05-26 | 系统 prompt 修复 | 消除编号列表与"不需要结构化模板"的矛盾，模型不再回吐格式规则 |
| 2026-05-26 | 默认定位 → 西安 | `config/settings.yaml location` 改为西安 |
| 2026-05-26 | 独立启停脚本 | `start/stop_chat_bots.sh` + `start/stop_file_sys_bots.sh` |
| 2026-05-26 | restart_callback.sh 修复 | 修正为直接使用 `venv-chat/bin/python` |
| 2026-05-26 | docs: v3.4 同步 | 文档与实际架构对齐 |
