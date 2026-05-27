#!/usr/bin/env python3
"""
模块名称：generate_design_doc
功能描述：扫描项目 Python 文件，提取统一注释块，生成设计文档汇总
对外接口：
    - 直接运行，输出到 docs/design_summary.md
依赖：
    - 标准库：os, re, pathlib, datetime
    - 第三方：无
    - 项目内：无
版本：v1.0
更新记录：
    - 2026-05-23: 初始创建
"""
import os
import re
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent.parent
SCAN_DIRS = ["shared", "assistants", "scripts"]
OUTPUT_FILE = PROJECT_ROOT / "docs/design_summary.md"


def extract_doc_info(filepath: Path) -> dict:
    """提取 Python 文件顶部的模块注释信息，返回字典"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception:
        return None
    # 匹配 """ ... """ 文档字符串
    match = re.search(r'"""(.*?)"""', content, re.DOTALL)
    if not match:
        return None
    doc = match.group(1).strip()
    info = {}
    current_key = None
    for line in doc.split('\n'):
        line = line.strip()
        if line.startswith("模块名称："):
            info['name'] = line.replace("模块名称：", "").strip()
        elif line.startswith("功能描述："):
            info['desc'] = line.replace("功能描述：", "").strip()
        elif line.startswith("对外接口："):
            info['interfaces'] = []
            current_key = 'interfaces'
        elif line.startswith("依赖："):
            info['deps'] = []
            current_key = 'deps'
        elif line.startswith("版本："):
            info['version'] = line.replace("版本：", "").strip()
        elif line.startswith("更新记录："):
            info['updates'] = []
            current_key = 'updates'
        elif current_key == 'interfaces' and line.startswith("- "):
            info.setdefault('interfaces', []).append(line.strip('- '))
        elif current_key == 'deps' and line.startswith("- "):
            info.setdefault('deps', []).append(line.strip('- '))
        elif current_key == 'updates' and line.startswith("- "):
            info.setdefault('updates', []).append(line.strip('- '))
    return info


def generate_report():
    """扫描目录并生成汇总文档"""
    modules = []
    for scan_dir in SCAN_DIRS:
        base = PROJECT_ROOT / scan_dir
        if not base.exists():
            continue
        for py_file in base.rglob("*.py"):
            info = extract_doc_info(py_file)
            if info and info.get('name'):
                rel_path = py_file.relative_to(PROJECT_ROOT)
                info['path'] = str(rel_path)
                modules.append(info)

    # 生成 Markdown
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines = [
        f"# 三角色 AI 助理系统 · 模块设计文档（自动生成）",
        f"生成时间：{now}\n",
        "## 模块清单\n"
    ]
    for mod in sorted(modules, key=lambda x: x['path']):
        lines.append(f"### {mod['path']}")
        lines.append(f"- **模块名称**：{mod.get('name', '')}")
        lines.append(f"- **功能描述**：{mod.get('desc', '')}")
        lines.append(f"- **版本**：{mod.get('version', '')}")
        if mod.get('interfaces'):
            lines.append("- **对外接口**：")
            for iface in mod['interfaces']:
                lines.append(f"  - {iface}")
        if mod.get('deps'):
            lines.append("- **依赖**：")
            for dep in mod['deps']:
                lines.append(f"  - {dep}")
        if mod.get('updates'):
            lines.append("- **更新记录**：")
            for upd in mod['updates']:
                lines.append(f"  - {upd}")
        lines.append("")
    # 写入文件
    OUTPUT_FILE.parent.mkdir(exist_ok=True)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    print(f"✅ 设计文档已生成：{OUTPUT_FILE}")


if __name__ == "__main__":
    generate_report()
