#!/bin/bash
# 对比测试环境与主环境的源代码差异
# 排除环境特定配置、虚拟环境、日志等
# 用法: bash scripts/diff_envs.sh

TEST="/Volumes/BR256G/ai-assistant-system"
MAIN="$HOME/ai-assistant-system"

EXCLUDES="--exclude=.git --exclude=venv --exclude='assistants/*/venv-*'"
EXCLUDES="$EXCLUDES --exclude='shared/whisper.cpp' --exclude=logs"
EXCLUDES="$EXCLUDES --exclude='.crypto_key' --exclude='*.bak' --exclude=backups"
EXCLUDES="$EXCLUDES --exclude='config/settings.yaml' --exclude='**/.env'"
EXCLUDES="$EXCLUDES --exclude='.DS_Store' --exclude='__pycache__' --exclude='*.pyc'"

echo "========================================"
echo " 环境对比: 测试 ↔ 主"
echo " 测试: $TEST"
echo " 主:   $MAIN"
echo "========================================"

DIFFS=$(diff -rq $EXCLUDES "$TEST" "$MAIN" 2>/dev/null | grep -v '^Only in' || true)

if [ -z "$DIFFS" ]; then
  echo ""
  echo " ✅ 两个环境完全一致（配置差异除外）"
else
  echo ""
  echo "以下文件存在差异："
  echo "$DIFFS"
fi

echo ""
echo "========================================"
echo " 测试环境 git 状态:"
cd "$TEST" && git status --short 2>/dev/null || echo " (无 git 仓库)"
echo "========================================"
