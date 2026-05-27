#!/usr/bin/env python3
"""
模块名称：verify_environment
功能描述：运行环境验证脚本，检查依赖、目录和关键文件
对外接口：
    - 直接运行，输出检查结果
依赖：
    - 标准库：os, sys, logging, importlib
    - 第三方：无
    - 项目内：无
版本：v1.0
更新记录：
    - 2026-05-23: 初始创建，添加统一注释头
"""
import os
import sys
import logging
import importlib

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.dirname(SCRIPT_DIR)

logging.basicConfig(level=logging.INFO, format='[ENV CHECK] %(message)s')
logger = logging.getLogger("verify_env")

REQUIRED_LIBS = {
    "flask": "flask",
    "requests": "requests",
    "pyyaml": "yaml",
    "dotenv": "dotenv",
    "deep_translator": "deep_translator"
}
REQUIRED_DIRS = [
    "assistants/chat-assistant/src",
    "assistants/office-assistant/src/core",
    "assistants/office-assistant/src",
    "shared/feishu-callback",
    "scripts",
    "logs",
    "config"
]

# 注意：assistants/chat_assistant 和 assistants/office_assistant 是指向带连字符目录的符号链接，
#       scripts 会优先检查实际目录路径。

def check_libs():
    for lib_name, module_name in REQUIRED_LIBS.items():
        try:
            importlib.import_module(module_name)
            logger.info(f"✅ {lib_name}")
        except ImportError:
            logger.error(f"❌ {lib_name} 未安装")

def check_dirs():
    for d in REQUIRED_DIRS:
        path = os.path.join(PROJECT, d)
        if os.path.isdir(path):
            logger.info(f"✅ {d}")
        else:
            logger.error(f"❌ {d} 缺失")

if __name__ == "__main__":
    logger.info("检查依赖库...")
    check_libs()
    logger.info("检查目录结构...")
    check_dirs()
    logger.info("环境验证完毕")