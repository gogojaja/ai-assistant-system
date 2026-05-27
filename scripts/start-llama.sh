#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT="$(dirname "$SCRIPT_DIR")"
MODEL_FILE=$(find ~/.local/lib/ollama/blobs -name "sha256-3e4cb1417446*" -size +1G | head -1)
lsof -ti:8080 | xargs kill -9 2>/dev/null
sleep 1
nohup ~/llama.cpp/build/bin/llama-server \
    -m "$MODEL_FILE" \
    --host 0.0.0.0 --port 8080 \
    -ngl 99 -c 4096 \
    --threads 8 --threads-http 4 \
    > "$PROJECT/logs/llama_server.log" 2>&1 &
sleep 3
echo "llama-server 已启动"
