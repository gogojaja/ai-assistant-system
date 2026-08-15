#!/bin/bash
# 停止测试环境 4号 Bot（不影响 1/2/3号）
echo "正在停止测试环境 4号 Bot..."

kill_port() {
    local pid
    pid=$(lsof -ti:"$1" 2>/dev/null)
    [ -n "$pid" ] && kill "$pid" 2>/dev/null; sleep 1
}
kill_port 5082

echo "✅ 测试环境 4号 Bot 已停止"
echo "  1/2/3号 Bot 不受影响"
