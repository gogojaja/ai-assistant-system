#!/bin/bash
# 一键发布：测试环境 → 主环境（git 版本管理 + rsync 同步 + 自动重启）
# 用法: bash scripts/promote.sh
# 安全: 配置文件（settings.yaml, .env）被排除，绝不覆盖
set -e

TEST="$(cd "$(dirname "$0")/.." && pwd)"
MAIN="$HOME/ai-assistant-system"

echo "========================================"
echo " 发布测试环境 → 主环境"
echo " 测试: $TEST"
echo " 主:   $MAIN"
echo "========================================"

# 1. 提交测试环境当前变更
echo ""
echo "🔄 [1/4] 提交测试环境变更..."
cd "$TEST"
git add -A
git diff --quiet || git commit -m "auto promote $(date +%Y%m%d_%H%M%S)"
echo "  最新提交: $(git log --oneline -1)"

# 2. 同步到主环境（排除环境特定配置）
echo ""
echo "📦  [2/4] 同步代码到主环境..."
rsync -avz --delete \
  --exclude='.git' \
  --exclude='.gitignore' \
  --exclude='venv' \
  --exclude='assistants/*/venv-*' \
  --exclude='shared/whisper.cpp' \
  --exclude='logs/*' \
  --exclude='.crypto_key' \
  --exclude='*.bak' \
  --exclude='backups/*' \
  --exclude='config/settings.yaml' \
  --exclude='**/.env' \
  "$TEST/" "$MAIN/"
echo "  ✅ 同步完成"

# 3. 重启主环境服务
echo ""
echo "♻️  [3/4] 重启主环境服务..."
bash "$MAIN/scripts/stop_all_services.sh" 2>/dev/null || true
sleep 2
bash "$MAIN/scripts/start_all_services.sh"
echo "  ✅ 服务已重启"

# 4. 验证
echo ""
echo "🔍 [4/4] 快速验证..."
for port in 5001 5002 5003; do
  if lsof -ti:"$port" >/dev/null 2>&1; then
    echo "  ✅ 端口 $port 已启动"
  else
    echo "  ❌ 端口 $port 未启动"
  fi
done

echo ""
echo "========================================"
echo " ✅ 发布完成"
echo "  测试环境: $(git log --oneline -1)"
echo "  主环境:   服务已重启"
echo "========================================"
