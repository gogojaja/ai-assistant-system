#!/bin/bash
echo "============================================================"
echo " 五角色 AI 助理系统 · 验收脚本"
echo "============================================================"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"
source assistants/office-assistant/venv-office/bin/activate

echo ""
echo "【1/4】运行 WordProcessor 测试..."
python assistants/office-assistant/src/tests/test_word_processor.py
if [ $? -ne 0 ]; then
    echo "❌ WordProcessor 测试失败"
    exit 1
fi

echo ""
echo "【2/4】运行 DocumentSummarizer 测试..."
python assistants/office-assistant/src/tests/test_summarizer.py
if [ $? -ne 0 ]; then
    echo "❌ Summarizer 测试失败"
    exit 1
fi

echo ""
echo "【3/4】运行 DocxConverter 测试..."
python assistants/office-assistant/src/tests/test_converters.py
if [ $? -ne 0 ]; then
    echo "❌ Converter 测试失败"
    exit 1
fi

echo ""
echo "【4/4】文档一致性检查..."
FILES=(
    "docs/02-design/01-系统架构.md"
    "docs/04-environment/01-环境搭建方案.md"
    "docs/03-project-management/01-进度台账.md"
    "assistants/office-assistant/src/core/word_processor.py"
    "assistants/office-assistant/src/core/summarizer.py"
    "assistants/office-assistant/src/core/converters.py"
    "assistants/office-assistant/src/utils/file_handler.py"
    "shared/feishu-callback/callback_server.py"
)
for file in "${FILES[@]}"; do
    if [ ! -f "$PROJECT_ROOT/$file" ]; then
        echo "❌ 缺失文件: $file"
        exit 1
    fi
done
echo "✅ 所有关键文件存在"

if grep -q "WordProcessor" docs/02-design/01-系统架构.md; then
    echo "✅ 设计文档已包含 2号AI 描述"
else
    echo "❌ 设计文档缺少 2号AI 内容"
    exit 1
fi

echo ""
echo "============================================================"
echo " ✅ 阶段2 验收通过！2号AI Word 处理功能就绪"
echo "============================================================"
