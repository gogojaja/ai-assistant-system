#!/bin/bash
# 初始化数据加密密钥
# 生成 .crypto_key 并加密已存在敏感数据

KEY_FILE="$HOME/ai-assistant-system/.crypto_key"
VENV_PYTHON="$HOME/ai-assistant-system/venv/bin/python3"

[ -f "$KEY_FILE" ] && { echo "⚠️  密钥已存在：$KEY_FILE （如需重置请手动删除）"; exit 0; }

# 生成密钥
$VENV_PYTHON -c "from shared.crypto import load_or_create_key; load_or_create_key()"
echo "✅ 密钥已生成：$KEY_FILE"

# 加密已有对话历史
for f in "$HOME/ai-assistant-system"/assistants/chat-assistant/logs/chat_history_*.json; do
    if [ -f "$f" ] && ! grep -q "^gAAAA" "$f" 2>/dev/null; then
        $VENV_PYTHON -c "
import sys; sys.path.insert(0, '$HOME/ai-assistant-system')
from shared.crypto import encrypt_file
encrypt_file('$f')
" && echo "  已加密：$(basename $f)"
    fi
done

echo "✅ 加密初始化完成"
