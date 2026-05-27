#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT="$(dirname "$SCRIPT_DIR")"
CALLBACK_PORT=$(grep callback_port "$PROJECT/config/settings.yaml" 2>/dev/null | awk '{print $2}')
CALLBACK_PORT=${CALLBACK_PORT:-5001}
URL=$(grep -o 'https://[a-z0-9-]*\.trycloudflare\.com' "$PROJECT/logs/cloudflared.log" 2>/dev/null | tail -1)
if [ -n "$URL" ]; then
    echo "当前隧道地址: $URL"
    echo "飞书回调地址应为: ${URL}/webhook"
else
    echo "未检测到隧道地址，请确认 cloudflared 是否在运行。"
    echo "你可以手动启动隧道：cloudflared tunnel --url http://localhost:$CALLBACK_PORT"
fi
