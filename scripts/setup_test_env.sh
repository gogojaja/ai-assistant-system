#!/bin/bash
# 测试环境一键初始化脚本
# 在 /Volumes/BR256G/ai-assistant-system 中创建 venv + 符号链接
set -e
cd "$(dirname "$0")/.."
PROJECT=$(pwd)

echo "=== 创建虚拟环境 ==="
echo "  全局 venv..."
python3.12 -m venv venv 2>/dev/null || python3 -m venv venv
venv/bin/pip install flask requests pyyaml python-dotenv cryptography 2>&1 | tail -1

echo "  venv-chat..."
python3.12 -m venv assistants/chat-assistant/venv-chat 2>/dev/null || python3 -m venv assistants/chat-assistant/venv-chat
assistants/chat-assistant/venv-chat/bin/pip install flask requests pyyaml python-dotenv \
  deep-translator cryptography 2>&1 | tail -1

echo "  venv-file..."
python3.12 -m venv assistants/file-assistant/venv-file 2>/dev/null || python3 -m venv assistants/file-assistant/venv-file
assistants/file-assistant/venv-file/bin/pip install flask requests pyyaml python-dotenv 2>&1 | tail -1

  echo "  venv-office..."
python3.12 -m venv assistants/office-assistant/venv-office 2>/dev/null || python3 -m venv assistants/office-assistant/venv-office
assistants/office-assistant/venv-office/bin/pip install flask requests pyyaml python-dotenv \
  openpyxl python-docx python-pptx watchdog 2>&1 | tail -1

echo ""
echo "=== 创建 symlink（Python import 兼容） ==="
cd assistants
ln -sf chat-assistant chat_assistant
ln -sf office-assistant office_assistant
cd ..

echo ""
echo "=== 初始化加密 ==="
if [ ! -f .crypto_key ]; then
    python3 -c "from cryptography.fernet import Fernet; open('.crypto_key','wb').write(Fernet.generate_key())"
    chmod 600 .crypto_key
    echo "  ✅ 已生成新加密密钥"
else
    echo "  ⏭️ 加密密钥已存在"
fi

echo ""
echo "=== 配置文件检查 ==="
echo "  飞书凭证路径: shared/feishu-bot/.env"
echo "  ⚠️  请复制飞书 Bot 凭证到 shared/feishu-bot/.env"
echo ""
echo "=== 测试环境就绪 ==="
echo "运行: bash scripts/start_all_services.sh"
