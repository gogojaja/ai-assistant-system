#!/bin/bash
# 每日环境核验脚本（支持双环境自适应）
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT="$(dirname "$SCRIPT_DIR")"
echo "===== 五角色 AI 助理系统 · 环境核验 ====="
echo "项目根目录: $PROJECT"

# 1. 时间检查
CURRENT_DATE=$(date "+%Y-%m-%d")
echo "✅ 系统时间: $CURRENT_DATE"

# 2. Python 环境
cd "$PROJECT"
source assistants/chat-assistant/venv-chat/bin/activate
PY_VER=$(python --version 2>&1)
echo "✅ Python 版本: $PY_VER"

# 3. Ollama 与模型
if pgrep -f ollama > /dev/null; then
    echo "✅ Ollama 进程运行中"
else
    echo "❌ Ollama 未运行"
fi
if ollama list | grep -q qwen3:4b; then
    echo "✅ 模型 qwen3:4b 已安装"
else
    echo "❌ 模型缺失"
fi

# 4. Flask 回调服务
CALLBACK_PORT=$(grep callback_port "$PROJECT/config/settings.yaml" 2>/dev/null | awk '{print $2}')
CALLBACK_PORT=${CALLBACK_PORT:-5001}
if curl -s "http://localhost:$CALLBACK_PORT/health" | grep -q "ok"; then
    echo "✅ Flask 回调服务运行中 (端口 $CALLBACK_PORT)"
else
    echo "❌ Flask 回调服务未运行 (端口 $CALLBACK_PORT)"
fi

# 5. 隧道检查
if pgrep -f "cloudflared" > /dev/null; then
    echo "✅ 隧道运行中"
else
    echo "⚠️ 未检测到隧道进程（夜间可关闭）"
fi

# 6. 飞书回调连通性验证
if "$PROJECT/venv/bin/python" "$PROJECT/scripts/verify_feishu_callback.py" >/dev/null 2>&1; then
    echo "✅ 飞书回调本地与公网连通性验证通过"
else
    echo "❌ 飞书回调连通性验证失败"
fi

# 7. 飞书 .env
if grep -q "FEISHU_APP_ID=cli_" "$PROJECT/shared/feishu-bot/.env" 2>/dev/null; then
    echo "✅ 飞书凭证已配置"
else
    echo "❌ 飞书凭证缺失"
fi

echo "===== 核验完成 ====="
