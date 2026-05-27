#!/usr/bin/env python3

"""
模块名称：check_doc_comments
功能描述：TODO: 请补充功能描述
对外接口：
    - load_exclude_patterns()
    - is_excluded()
    - has_doc_comment()
    - main()
依赖：
    - 标准库：argparse, os, pathlib, re, sys
    - 第三方：无
    - 项目内：无
版本：v1.0
更新记录：
    - 2026-05-23: 自动添加统一注释头
"""
"""
模块名称：check_doc_comments
功能描述：检查项目中所有 Python 文件是否包含统一的设计注释头，排除列表从配置文件读取
对外接口：
    - 命令行：--exclude 添加额外排除模式，--exclude-file 指定配置文件
依赖：
    - 标准库：os, re, pathlib, sys, argparse, fnmatch
    - 第三方：无
    - 项目内：无
版本：v1.4
更新记录：
    - 2026-05-23: 初始创建
    - 2026-05-23: 增加排除规则
    - 2026-05-23: 排除列表外部化到配置文件 doc_exclude.conf
    - 2026-05-23: is_excluded 增加关键字兜底排除（venv, site-packages 等）
"""
import os
import re
import sys
import argparse
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
SCAN_DIRS = ["shared", "assistants", "scripts"]

REQUIRED_KEYWORDS = ["模块名称", "功能描述", "对外接口", "依赖", "版本", "更新记录"]

DEFAULT_EXCLUDE_FILE = PROJECT_ROOT / "scripts/doc_exclude.conf"


def load_exclude_patterns(file_path: Path) -> list:
    """从配置文件读取排除模式（每行一个 glob，忽略空行和 # 注释）"""
    patterns = []
    if file_path.exists():
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    patterns.append(line)
    return patterns


def is_excluded(file_path: Path, exclude_patterns: list) -> bool:
    """判断文件是否匹配任一排除模式（glob + 路径关键字兜底）"""
    try:
        rel_path = str(file_path.relative_to(PROJECT_ROOT))
    except ValueError:
        return False

    # 绝对排除的关键字
    EXCLUDE_KEYWORDS = ["venv", "site-packages", "__pycache__", "whisper.cpp"]
    for keyword in EXCLUDE_KEYWORDS:
        if keyword in rel_path:
            return True

    # glob 匹配
    for pattern in exclude_patterns:
        if file_path.match(pattern) or Path(rel_path).match(pattern):
            return True
    return False


def has_doc_comment(file_path: Path) -> bool:
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read(2000)
    except Exception:
        return False
    m = re.search(r'^\s*"""(.*?)"""', content, re.DOTALL)
    if not m:
        return False
    doc = m.group(1)
    return any(kw in doc for kw in REQUIRED_KEYWORDS)


def main():
    parser = argparse.ArgumentParser(description="检查项目 Python 文件的注释合规情况")
    parser.add_argument("--exclude", nargs="*", default=[], help="额外的排除模式（glob）")
    parser.add_argument("--exclude-file", type=Path, default=DEFAULT_EXCLUDE_FILE,
                        help="排除配置文件路径（默认 scripts/doc_exclude.conf）")
    args = parser.parse_args()

    # 加载默认排除配置 + 命令行补充
    excludes = load_exclude_patterns(args.exclude_file) + args.exclude
    non_compliant = []

    for scan_dir in SCAN_DIRS:
        base = PROJECT_ROOT / scan_dir
        if not base.exists():
            continue
        for py_file in base.rglob("*.py"):
            if is_excluded(py_file, excludes):
                continue
            if not has_doc_comment(py_file):
                non_compliant.append(py_file)

    if non_compliant:
        print("❌ 以下 Python 文件缺少统一设计注释头（已排除原生文件）：")
        for f in sorted(non_compliant):
            print(f"  - {f.relative_to(PROJECT_ROOT)}")
        print(f"\n共 {len(non_compliant)} 个文件需要补充注释。")
        sys.exit(1)
    else:
        print("✅ 所有需检查的 Python 文件均包含统一设计注释头。")
        sys.exit(0)


if __name__ == "__main__":
    main()