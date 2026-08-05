#!/bin/bash
# 环境隔离检查
if [ ! -f "$(dirname "$(dirname "$0")")/.env_type" ] || [ "$(cat "$(dirname "$(dirname "$0")")/.env_type")" != "test" ]; then
    echo "❌ 安全拦截：当前不是测试环境，禁止停止"
    exit 1
fi
# 仅停止测试环境服务（5101/5102），不碰共享推理后端和 ngrok
echo "正在停止测试环境服务..."

kill_port() {
    local port=$1
    local pid
    pid=$(lsof -ti:"$port" 2>/dev/null)
    if [ -n "$pid" ]; then
        kill "$pid" 2>/dev/null
        sleep 1
    fi
}
kill_port 5101
kill_port 5102

sleep 1
echo "✅ 测试环境服务已停止"
echo "  共享服务（llama-server + ngrok 隧道）不受影响"
