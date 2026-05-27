#!/bin/bash
echo "===== 项目环境核验 $(date) ====="

# ---------- 虚拟环境与 Python ----------
echo ""
echo "--- Python 虚拟环境 ---"
if [ -f "venv/bin/python" ]; then
    echo "✅ 虚拟环境 Python 存在"
    PY_VER=$(./venv/bin/python --version 2>&1)
    echo "   版本：$PY_VER"
    # 关键库检查
    echo "   关键库："
    for lib in flask requests openpyxl dotenv deep_translator yaml; do
        ./venv/bin/python -c "import $lib" 2>/dev/null && echo "   ✅ $lib" || echo "   ❌ $lib 缺失"
    done
else
    echo "❌ 虚拟环境 python 未找到"
fi

# ---------- 目录完整性 ----------
echo ""
echo "--- 目录结构 ---"
for d in assistants assistants/chat-assistant assistants/office-assistant shared docs; do
    [ -d "$d" ] && echo "✅ $d/" || echo "❌ 缺失目录 $d/"
done

# ---------- 软链接与 __init__.py ----------
echo ""
echo "--- 软链接与 __init__.py ---"
check_init() {
    if [ -f "$1" ]; then
        if [ -L "$1" ]; then
            TGT=$(readlink "$1")
            echo "✅ $1 -> $TGT (软链接)"
        else
            echo "✅ $1 (实体文件)"
        fi
    else
        echo "❌ 缺失 $1"
    fi
}
# 根据移交包提及的软链接和 init 文件
check_init "assistants/__init__.py"
check_init "assistants/chat-assistant/__init__.py"
check_init "assistants/office-assistant/__init__.py"
check_init "shared/__init__.py"
# 已知可能软链接指向的文件也检查一下
check_init "shared/utils.py"
check_init "monitor_services.sh"
check_init "daily_backup.sh"

# ---------- 凭证文件 ----------
echo ""
echo "--- 凭证文件 ---"
for f in .env feishu_config.json token.json; do
    [ -f "$f" ] && echo "✅ $f" || echo "⚠️  $f 不存在（或非必需）"
done

# ---------- 服务状态 ----------
echo ""
echo "--- 服务状态 ---"
curl -s http://localhost:5001/health > /dev/null && echo "✅ Flask:5001" || echo "❌ Flask:5001 未响应"
curl -s http://localhost:8080/health > /dev/null && echo "✅ llama.cpp:8080" || echo "❌ llama.cpp:8080 未响应"

# ---------- 核心文件（原有检查） ----------
echo ""
echo "--- 核心文件 ---"
for f in shared/feishu-callback/callback_server.py assistants/chat-assistant/src/message_handler.py shared/utils.py shared/feishu_api.py config/settings.yaml shared/feishu-bot/.env; do
    [ -f "$f" ] && echo "✅ $f" || echo "❌ 缺失 $f"
done

# ---------- 文档一致性 ----------
echo ""
echo "--- 文档一致性 ---"
diff <(head -1 docs/design_summary.md 2>/dev/null) <(echo "# 设计汇总 (自动生成)") > /dev/null 2>&1 && echo "✅ 设计文档版本一致" || echo "⚠️ 文档可能需更新或缺失"

# ---------- 1号AI 功能基础探测 ----------
echo ""
echo "--- 1号AI 功能基础探测 ---"
echo "可用的助理模块："
ls -d assistants/*/  2>/dev/null | sed 's/assistants\///;s/\/$//' | while read mod; do
    echo "  - $mod"
done
echo "正在尝试导入 assistants 包..."
if [ -f "venv/bin/python" ]; then
    ./venv/bin/python -c "import assistants" 2>/dev/null && echo "✅ assistants 包可导入" || echo "❌ assistants 包导入失败"
else
    python3 -c "import assistants" 2>/dev/null && echo "✅ assistants 包可导入" || echo "❌ assistants 包导入失败"
fi
echo "请根据上面列出的模块名称，确认 1号AI 对应哪个模块，后续可针对性验证。"

echo ""
echo "===== 核验完成 ====="