#!/bin/bash
# 一键更新所有项目文档至最新状态
# 运行前自动备份旧文档到 backups/ 目录

set -e
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT="$(dirname "$SCRIPT_DIR")"
TS=$(date +%Y%m%d_%H%M%S)
mkdir -p "$PROJECT/backups/$TS"

echo "正在备份旧文档到 backups/$TS ..."
for f in \
    docs/02-design/01-系统架构.md \
    docs/04-environment/01-环境搭建方案.md \
    docs/03-project-management/01-进度台账.md \
    scripts/README.md
do
    [ -f "$PROJECT/$f" ] && cp "$PROJECT/$f" "$PROJECT/backups/$TS/"
done

echo "正在更新文档..."

# ------------------ 设计文档 ------------------
cat > "$PROJECT/docs/02-design/01-系统架构.md" << 'MDEOF'
# 三角色 AI 助理系统 · 设计文档

**版本**：v1.2  
**最后更新**：2026-05-23  

---

## 一、系统架构

### 1.1 总体架构图
飞书客户端 → Cloudflared 隧道 → Flask 回调服务 (5001)
├── 1号AI 闲聊检索助理（main.py）
├── 2号AI 办公文档助理（Word/Excel处理）
└── 共享层（语音识别 Whisper.cpp）
↓
llama.cpp server (8080)
模型: qwen3:4b (Metal 加速)

text

### 1.2 模块划分

| 模块 | 位置 | 职责 |
|------|------|------|
| 飞书回调服务 | `shared/feishu-callback/callback_server.py` | 接收事件、分发、调用 AI |
| 1号AI 核心 | `assistants/chat-assistant/src/main.py` | 对话管理、搜索、知识库 |
| 2号AI 办公文档助理 | `assistants/office-assistant/src/` | Word/Excel 解析、摘要、格式转换 |
| 3号AI | `assistants/dev-assistant/src/` | 代码审查、文档生成（待开发） |
| 语音识别 | `shared/whisper.cpp/` + `shared/voice/` | 音频转文字（Whisper.cpp） |
| 隧道管理 | `scripts/start_all_services.sh` | 后台启动 Cloudflared |
| 推理后端 | `~/llama.cpp/build/bin/llama-server` | 高性能 Metal 推理服务，监听 8080 |

---

## 二、核心数据流

### 2.1 文本消息
飞书发送文字 → Flask 回调 → process_message → generate_reply → talk(messages) → llama.cpp API → 返回字符串 → send_message

### 2.2 语音消息
飞书语音 → 下载 .opus → ffmpeg 转 WAV → whisper-cli 识别 → 文字结果 → 交给 process_message

### 2.3 文档消息（.docx / .xlsx）
飞书发送文件 → 下载 → 根据后缀调用 WordProcessor 或 ExcelProcessor → 提取内容/分析 → 生成摘要 → 发送回复

---

## 三、技术选型与版本

| 组件 | 选型 | 版本 | 理由 |
|------|------|------|------|
| 运行环境 | Python venv | 3.12.13 | 原生、无需 sudo |
| Web 框架 | Flask | 2.3.3 | 轻量、易集成 |
| 推理服务 | llama.cpp server | latest | Metal 优化，速度 33 tok/s |
| 模型 | qwen3:4b (Q4_K_M) | - | 中文友好，4B 参数 |
| 语音识别 | Whisper.cpp | base 模型 | 本地离线、arm64 优化 |
| 音频处理 | ffmpeg | 8.1.1 | 格式转换 |
| 内网穿透 | Cloudflared | latest | 无需注册、稳定 |
| 文档读取 | python-docx, openpyxl | 0.8.11 / 3.1.2 | 稳定成熟 |
| 翻译 | deep-translator (MyMemory) | - | 国内可用，免费 |

---

## 四、目录结构
~/ai-assistant-system/
├── assistants/
│ ├── chat-assistant/src/main.py # 1号AI 主逻辑
│ ├── office-assistant/src/
│ │ ├── core/word_processor.py
│ │ ├── core/summarizer.py
│ │ ├── core/excel_processor.py
│ │ └── core/converters.py
│ └── dev-assistant/ # 待开发
├── shared/feishu-callback/callback_server.py
├── config/settings.yaml # 位置等信息
├── scripts/ # 运维脚本
├── docs/ # 项目文档
└── logs/ # 运行日志

text

---

## 五、当前状态与已知问题

- **推理服务**：llama.cpp server 运行正常，Metal 加速，速度约 33 tok/s。
- **回调服务**：Flask 服务正常，飞书隧道连通。
- **已知问题**：qwen3:4b 模型在 llama.cpp 中会将推理过程放入 `reasoning_content` 字段，导致 `content` 为空，机器人返回兜底回复。  
  修复方向：在 `main.py` 的 `talk` 函数中兼容 `reasoning_content`，或为 llama-server 添加 `--no-reasoning` 参数（需测试兼容性）。

---

## 六、部署与运维

- **一键启动**：`scripts/start_all_services.sh`
- **一键停止**：`scripts/stop_all_services.sh`
- **重启回调**：`scripts/restart_callback.sh`
- **模型测速**：`scripts/benchmark_llama.sh qwen3:4b`
- **环境诊断**：`scripts/diagnose.sh`

MDEOF
echo "  ✅ 设计文档已更新"

# ------------------ 环境搭建方案 ------------------
cat > "$PROJECT/docs/04-environment/01-环境搭建方案.md" << 'MDEOF'
# 环境搭建方案文档

**版本**：v1.2  
**最后更新**：2026-05-23  

（前略，保留之前内容，仅更新/追加以下部分）

---

## 十一、2号AI 依赖补充

### 11.1 安装 Word/Excel 处理依赖
```bash
source ~/ai-assistant-system/assistants/office-assistant/venv-office/bin/activate
pip install python-docx==0.8.11 mammoth==1.6.0 openpyxl==3.1.2
deactivate
11.2 验证 2号AI 模块

bash
cd ~/ai-assistant-system
source assistants/office-assistant/venv-office/bin/activate
python -m pytest assistants/office-assistant/src/tests/ -v
deactivate
十二、当前推理后端（llama.cpp server）

12.1 编译 llama.cpp

bash
cd ~
git clone https://github.com/ggerganov/llama.cpp.git
cd llama.cpp
cmake -B build -DGGML_METAL=ON -DGGML_METAL_EMBED_LIBRARY=ON -DLLAMA_BUILD_UI=OFF
cmake --build build --config Release -j4
12.2 启动服务（已集成到 start_all_services.sh）

bash
MODEL_FILE=$(find ~/.local/lib/ollama/blobs -name "sha256-3e4cb1417446*" -size +1G | head -1)
nohup ~/llama.cpp/build/bin/llama-server \
    -m "$MODEL_FILE" \
    --host 0.0.0.0 --port 8080 \
    -ngl 99 -c 4096 \
    --threads 8 --threads-http 4 \
    > ~/ai-assistant-system/logs/llama_server.log 2>&1 &
12.3 停止

bash
pkill -f llama-server
十三、已知问题排查

模型返回空内容：检查 main.py 中的 talk 函数是否兼容 reasoning_content 字段。若 llama-server 启动时添加 --no-reasoning 参数，可能解决问题（但需测试是否会导致启动失败）。
MDEOF
echo " ✅ 环境搭建文档已更新"

------------------ 进度台账 ------------------

cat > "$PROJECT/docs/03-project-management/01-进度台账.md" << 'MDEOF'

三角色 AI 助理系统 · 项目计划与进度台账

版本：v3.1
最后更新：2026-05-23

一、总体计划

周次	阶段	核心目标	状态
第1周	阶段0	环境地基	✅
第2周	阶段1	1号AI 终端版	✅
第3周	共享层	飞书接入 + 语音模块	✅
第4周	阶段2	2号AI 办公文档助理	🟡 进行中
第5周	阶段3+4	3号AI 编程 + 系统管控	⬜
第6周	阶段5	联调验收	⬜
二、详细进度台账

天次	任务	状态	完成日期	备注
...	（前期任务略）	...	...	...
Day12-16	2号AI Word 处理功能开发	✅	2026-05-22	解析、摘要、转换、飞书回调
Day17	模型更换为 qwen3:4b，切换推理后端至 llama.cpp	✅	2026-05-23	速度提升至 33 tok/s
Day18	天气查询、翻译功能优化	✅	2026-05-23	
Day19	上下文时间/位置注入	✅	2026-05-23	
Day20	2号AI Excel 处理核心类开发	✅	2026-05-23	数据提取、统计、异常检测
Day21	待修复：模型返回空内容问题	🟡	-	reasoning_content 兼容问题
Day22+	Excel 集成到飞书回调	⬜		
...	3号AI 编程助理开发	⬜		
三、当前阻塞

模型空回复：qwen3:4b 推理输出在 reasoning_content 字段，需修复代码或启动参数。
MDEOF
echo " ✅ 进度台账已更新"

------------------ 脚本 README ------------------

cat > "$PROJECT/scripts/README.md" << 'MDEOF'

脚本目录说明

脚本文件	中文名称	功能说明
backup_env.sh	环境备份	备份关键配置与代码
benchmark_llama.sh	Llama 测速	测试 llama.cpp server 推理速度
benchmark_model.sh	通用模型测速	测试指定模型（已适配 llama）
daily_verify_day8.sh	每日核验	检查系统健康状态
diagnose.sh	系统诊断	全模块健康检查
final_verify.py	最终核验	环境与文档一致性校验
get_tunnel_url.sh	隧道地址	输出当前 Cloudflared 公网地址
logs.sh	日志查看	快速查看各服务日志
optimize_voice.sh	语音优化	调整语音识别参数
restart_callback.sh	重启回调	单独重启飞书回调服务
start_all_services.sh	启动所有服务	启动 llama + 回调 + 隧道
start-llama.sh	启动 llama	单独启动 llama.cpp server
stop_all_services.sh	停止所有服务	停止所有后台进程
stop-llama.sh	停止 llama	单独停止 llama.cpp server
test_office_integration.py	办公模块集成测试	测试 Word/Excel 处理流程
update_model.sh	模型名称更新	批量替换项目中的模型引用
update_docs.sh	文档更新	一键更新所有项目文档
verify_environment.py	环境校验	检查 Python 版本、依赖等
verify_phase2.sh	阶段2验收	运行 2号AI 测试并检查文档
MDEOF		
echo " ✅ 脚本 README 已更新"		
echo "============================================"
echo " ✅ 所有文档更新完成！"
echo " 旧文档备份位置: 
P
R
O
J
E
C
T
/
b
a
c
k
u
p
s
/
PROJECT/backups/TS"
echo "============================================"
