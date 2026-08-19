#!/bin/bash
echo "============================================"
echo " 系统全量诊断 $(date '+%Y-%m-%d %H:%M:%S')"
echo "============================================"
PROJECT=/Users/gogo/ai-assistant-system
cd $PROJECT

# 1. Ollama
echo "[1] Ollama 状态"
pgrep -f "ollama serve" >/dev/null && echo "  ✅ 运行中" || echo "  ❌ 未运行"
ollama list 2>/dev/null | head -5

# 2. 回调服务
echo "[2] 回调服务"
pgrep -f "callback_server.py" >/dev/null && echo "  ✅ 运行中" || echo "  ❌ 未运行"

# 3. 隧道
echo "[3] 隧道"
pgrep -f cloudflared >/dev/null && echo "  ✅ 运行中" || echo "  ❌ 未运行"

# 4. 虚拟环境
echo "[4] 虚拟环境"
for venv in venv-chat venv-office; do
    [ -d "assistants/chat-assistant/$venv" ] || [ -d "assistants/office-assistant/$venv" ] && echo "  ✅ $venv" || echo "  ❌ $venv"
done

# 5. 1号AI 模块测试
echo "[5] 1号AI 模块"
source assistants/chat-assistant/venv-chat/bin/activate
python -c "from main import talk; r=talk([{'role':'user','content':'1+1='}]); print('  ✅ 回复:', r['message']['content'][:50])" 2>&1
deactivate

# 6. 2号AI 测试
echo "[6] 2号AI 测试"
source assistants/office-assistant/venv-office/bin/activate
python -m pytest assistants/office-assistant/src/tests/ -q 2>&1 | tail -5
deactivate

# 7. 文档完整性
echo "[7] 文档"
for f in docs/02-design/01-系统架构.md docs/04-environment/01-环境搭建方案.md docs/03-project-management/01-进度台账.md; do
    [ -f "$f" ] && echo "  ✅ $f" || echo "  ❌ 缺失 $f"
done

# 8. 模型性能
echo "[8] 模型性能快照"
python /tmp/bench.py 2>/dev/null | tail -3

echo "============================================"
echo " 诊断完成"
echo "============================================"
