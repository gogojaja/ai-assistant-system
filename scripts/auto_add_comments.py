#!/usr/bin/env python3

"""
模块名称：auto_add_comments
功能描述：TODO: 请补充功能描述
对外接口：
    - load_exclude_patterns()
    - is_excluded()
    - is_stdlib()
    - extract_top_level_defs()
    - extract_imports()
    - has_doc_comment()
    - generate_comment()
    - add_comment_to_file()
    - main()
依赖：
    - 标准库：argparse, ast, datetime, os, pathlib, re, sys
    - 第三方：无
    - 项目内：无
版本：v1.0
更新记录：
    - 2026-05-23: 自动添加统一注释头
"""
"""
模块名称：auto_add_comments
功能描述：自动为项目中缺少统一设计注释头的 Python 文件生成并插入注释头，排除列表从配置文件读取
对外接口：
    - 命令行：--dry-run 预览 / --apply 实际执行 / --exclude 添加额外排除模式 / --exclude-file 指定配置文件
依赖：
    - 标准库：os, sys, re, pathlib, argparse, datetime, ast
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
import sys
import re
import argparse
import ast
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent.parent
SCAN_DIRS = ["shared", "assistants", "scripts"]

REQUIRED_KEYWORDS = ["模块名称", "功能描述", "对外接口", "依赖", "版本", "更新记录"]

STDLIB_LIST = {
    "os", "sys", "re", "json", "logging", "datetime", "time", "pathlib", "subprocess",
    "tempfile", "shutil", "platform", "argparse", "importlib", "ast", "threading",
    "collections", "functools", "itertools", "math", "random", "typing", "unittest",
    "urllib", "http", "io", "csv", "configparser", "hashlib", "base64", "glob",
    "copy", "pprint", "textwrap", "string", "traceback", "warnings"
}

DEFAULT_EXCLUDE_FILE = PROJECT_ROOT / "scripts/doc_exclude.conf"


def load_exclude_patterns(file_path: Path) -> list:
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


def is_stdlib(module_name: str) -> bool:
    top_level = module_name.split('.')[0]
    return top_level in STDLIB_LIST


def extract_top_level_defs(file_path: Path) -> list:
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            source = f.read()
        tree = ast.parse(source)
        defs = []
        for node in ast.iter_child_nodes(tree):
            if isinstance(node, ast.FunctionDef):
                defs.append(node.name + "()")
            elif isinstance(node, ast.ClassDef):
                defs.append(node.name)
        return defs
    except Exception:
        return []


def extract_imports(file_path: Path) -> tuple:
    stdlib, third_party, internal = [], [], []
    import_pattern = re.compile(r'^\s*(?:from|import)\s+([a-zA-Z_][a-zA-Z0-9_\.]*)')
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                m = import_pattern.match(line)
                if m:
                    mod = m.group(1).split('.')[0]
                    if is_stdlib(mod):
                        if mod not in stdlib:
                            stdlib.append(mod)
                    else:
                        common_third = {"requests", "flask", "openpyxl", "python-docx", "mammoth",
                                        "dotenv", "deep_translator", "yaml", "urllib3"}
                        if mod in common_third:
                            if mod not in third_party:
                                third_party.append(mod)
                        else:
                            possible_path = PROJECT_ROOT / (mod.replace('.', '/') + ".py")
                            if possible_path.exists():
                                if mod not in internal:
                                    internal.append(mod)
                            else:
                                if mod not in third_party:
                                    third_party.append(mod)
    except Exception:
        pass
    return sorted(stdlib), sorted(third_party), sorted(internal)


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


def generate_comment(file_path: Path) -> str:
    module_name = file_path.stem
    desc = "TODO: 请补充功能描述"
    defs = extract_top_level_defs(file_path)
    stdlib, third_party, internal = extract_imports(file_path)
    version = "v1.0"
    today = datetime.now().strftime("%Y-%m-%d")

    lines = ['"""']
    lines.append(f"模块名称：{module_name}")
    lines.append(f"功能描述：{desc}")
    lines.append("对外接口：")
    if defs:
        for d in defs[:10]:
            lines.append(f"    - {d}")
    else:
        lines.append("    - 无")
    lines.append("依赖：")
    if stdlib:
        lines.append(f"    - 标准库：{', '.join(stdlib)}")
    else:
        lines.append("    - 标准库：无")
    if third_party:
        lines.append(f"    - 第三方：{', '.join(third_party)}")
    else:
        lines.append("    - 第三方：无")
    if internal:
        lines.append(f"    - 项目内：{', '.join(internal)}")
    else:
        lines.append("    - 项目内：无")
    lines.append(f"版本：{version}")
    lines.append("更新记录：")
    lines.append(f"    - {today}: 自动添加统一注释头")
    lines.append('"""')
    return '\n'.join(lines)


def add_comment_to_file(file_path: Path, dry_run=False):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            original = f.read()
    except Exception as e:
        print(f"  ⚠️ 读取失败: {file_path} ({e})")
        return

    comment = generate_comment(file_path)

    if original.startswith("#!/"):
        pos = original.index('\n') + 1
        new_content = original[:pos] + '\n' + comment + '\n' + original[pos:]
    else:
        new_content = comment + '\n' + original

    if dry_run:
        print(f"  📝 [预览] {file_path.relative_to(PROJECT_ROOT)}")
        return

    backup_path = file_path.with_suffix(file_path.suffix + '.bak')
    try:
        os.rename(file_path, backup_path)
    except Exception as e:
        print(f"  ⚠️ 备份失败: {file_path} ({e})")
        return

    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"  ✅ 已添加: {file_path.relative_to(PROJECT_ROOT)}")
        os.remove(backup_path)
    except Exception as e:
        os.rename(backup_path, file_path)
        print(f"  ❌ 写入失败: {file_path} ({e})，已恢复原文件")


def main():
    parser = argparse.ArgumentParser(description="自动为项目 Python 文件添加统一注释头")
    parser.add_argument("--dry-run", action="store_true", help="仅预览")
    parser.add_argument("--apply", action="store_true", help="实际执行")
    parser.add_argument("--exclude", nargs="*", default=[], help="额外的排除模式（glob）")
    parser.add_argument("--exclude-file", type=Path, default=DEFAULT_EXCLUDE_FILE,
                        help="排除配置文件路径（默认 scripts/doc_exclude.conf）")
    args = parser.parse_args()

    if not args.dry_run and not args.apply:
        print("请指定 --dry-run 或 --apply")
        sys.exit(1)

    # 加载排除列表
    excludes = load_exclude_patterns(args.exclude_file) + args.exclude

    all_py_files = []
    for scan_dir in SCAN_DIRS:
        base = PROJECT_ROOT / scan_dir
        if not base.exists():
            continue
        for py_file in base.rglob("*.py"):
            if is_excluded(py_file, excludes):
                continue
            all_py_files.append(py_file)

    missing = [f for f in all_py_files if not has_doc_comment(f)]

    if not missing:
        print("✅ 所有需检查的文件已包含统一注释头。")
        return

    print(f"发现 {len(missing)} 个文件缺少注释头。")
    if args.dry_run:
        print("--- 预览模式 ---")
        for f in sorted(missing):
            add_comment_to_file(f, dry_run=True)
        print("\n请确认后使用 --apply 执行。")
    else:
        print("开始添加注释...")
        for f in sorted(missing):
            add_comment_to_file(f, dry_run=False)
        print("✅ 注释添加完成。")


if __name__ == "__main__":
    main()