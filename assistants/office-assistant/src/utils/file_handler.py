#!/usr/bin/env python3
"""
模块名称：file_handler
功能描述：文件处理工具：安全删除文件（仅白名单类型）、白名单校验、临时目录清理
对外接口：
    - safe_delete(file_path, delay=False): 安全删除文件，仅删除白名单中的文件类型
    - check_whitelist(file_path): 校验文件是否在白名单中
    - cleanup_temp_dir(temp_dir, max_age_seconds=86400): 清理临时目录中超过一定时间的文件
依赖：
    - 标准库：logging, os, pathlib, sys, time
    - 第三方：无
    - 项目内：无
版本：v1.0
更新记录：
    - 2026-05-23: 自动添加统一注释头，补充功能描述
"""

import os
import logging
from pathlib import Path
from typing import List, Optional

logger = logging.getLogger("FileHandler")
logger.setLevel(logging.DEBUG)
if not logger.handlers:
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)

ALLOWED_EXTENSIONS = {'.docx', '.xlsx', '.pptx', '.pdf', '.txt', '.md', '.json', '.csv'}


def safe_delete(file_path: str, delay: bool = False):
    """
    安全删除文件，仅删除白名单中的文件类型，防止误删
    :param file_path: 文件路径
    :param delay: 是否延迟删除（预留）
    """
    path = Path(file_path)
    if not path.exists():
        return
    if path.suffix.lower() not in ALLOWED_EXTENSIONS:
        logger.warning(f"非白名单文件类型，取消删除: {path}")
        return
    try:
        os.unlink(path)
        logger.info(f"已安全删除: {path}")
    except Exception as e:
        logger.error(f"删除失败: {path} - {e}")


def check_whitelist(file_path: str) -> bool:
    """
    校验文件是否在白名单中（扩展名）
    """
    path = Path(file_path)
    allowed = path.suffix.lower() in ALLOWED_EXTENSIONS
    if not allowed:
        logger.warning(f"文件类型不在白名单: {path.suffix}")
    return allowed


def cleanup_temp_dir(temp_dir: str, max_age_seconds: int = 86400):
    """
    清理临时目录中超过一定时间的文件
    :param temp_dir: 目录路径
    :param max_age_seconds: 最大保留时间（秒），默认24小时
    """
    import time
    now = time.time()
    path = Path(temp_dir)
    if not path.exists() or not path.is_dir():
        return
    for f in path.iterdir():
        if f.is_file():
            if f.suffix.lower() not in ALLOWED_EXTENSIONS:
                continue
            try:
                if now - f.stat().st_mtime > max_age_seconds:
                    safe_delete(str(f))
            except Exception as e:
                logger.error(f"清理失败: {f} - {e}")


# 命令行入口
if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        safe_delete(sys.argv[1])
    else:
        print("用法: python file_handler.py <文件路径>   (安全删除文件)")