#!/bin/bash
# 模型名称替换脚本：qwen3:4b → qwen3:4b
# 仅修改文本文件，跳过虚拟环境、__pycache__、.git 等目录
# 用法: ./update_model.sh [旧模型名] [新模型名]

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
OLD_MODEL="${1:-qwen3:4b}"
NEW_MODEL="${2:-qwen3:4b}"
echo "============================================"
echo " 模型名称替换脚本"
echo " $OLD_MODEL → $NEW_MODEL"
echo " 项目根目录: $PROJECT_ROOT"
echo "============================================"

# 定义要搜索的文件扩展名（文本类型）
TEXT_EXTS=("py" "yaml" "yml" "md" "txt" "env" "sh" "cfg" "conf" "json")

# 构建 find 条件：忽略的目录
IGNORE_DIRS="-not -path '*/.git/*' -not -path '*/__pycache__/*' -not -path '*/venv*/*' -not -path '*/whisper.cpp/*' -not -path '*/models/*' -not -path '*/node_modules/*'"

# 遍历所有文本文件
changed_count=0
while IFS= read -r -d '' file; do
    if grep -q "$OLD_MODEL" "$file"; then
        echo "🔧 修改: $file"
        # macOS 兼容的 sed -i ''
        sed -i '' "s/$OLD_MODEL/$NEW_MODEL/g" "$file"
        changed_count=$((changed_count+1))
    fi
done < <(find "$PROJECT_ROOT" -type f $IGNORE_DIRS \( -name "*.py" -o -name "*.yaml" -o -name "*.yml" -o -name "*.md" -o -name "*.txt" -o -name "*.env" -o -name "*.sh" -o -name "*.cfg" -o -name "*.json" \) -print0)

echo ""
echo "============================================"
echo " ✅ 替换完成，共修改 $changed_count 个文件"
echo "============================================"

# 如果有修改，提示重启服务
if [ $changed_count -gt 0 ]; then
    echo ""
    echo "⚠️  请重启相关服务使修改生效："
    echo "  bash \"$PROJECT_ROOT/scripts/stop_all_services.sh\""
    echo "  bash \"$PROJECT_ROOT/scripts/start_all_services.sh\""
fi
