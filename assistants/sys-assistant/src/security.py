"""
模块名称：security
功能描述：5号AI 系统管理助理 — 安全操作限制（禁止 sudo、白名单命令校验、路径安全）
对外接口：
    - check_command(cmd): 校验命令是否在安全白名单内
    - check_no_sudo(cmd): 确保命令不含 sudo 提权
    - sanitize_path(path): 规范化路径，阻止路径穿越
    - is_allowed_log_file(path): 校验日志文件路径是否在白名单内
依赖：
    - 标准库：os, re, pathlib, logging
    - 第三方：无
    - 项目内：无
版本：v1.0
更新记录：
    - 2026-05-26: 初始创建
"""
import os
import re
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent

SUDO_PATTERN = re.compile(r'\bsudo\b')

CMD_WHITELIST = {
    "status": {"desc": "系统状态总览", "needs_path": False},
    "disk": {"desc": "磁盘使用详情", "needs_path": False},
    "mem": {"desc": "内存使用详情", "needs_path": False},
    "cpu": {"desc": "CPU 使用详情", "needs_path": False},
    "load": {"desc": "系统负载", "needs_path": False},
    "uptime": {"desc": "系统运行时间", "needs_path": False},
    "network": {"desc": "网络连接状态", "needs_path": False},
    "svc_list": {"desc": "查看所有服务状态", "needs_path": False},
    "svc_status": {"desc": "查看单个服务状态", "needs_path": False},
    "svc_start": {"desc": "启动服务", "needs_path": False},
    "svc_stop": {"desc": "停止服务", "needs_path": False},
    "svc_restart": {"desc": "重启服务", "needs_path": False},
    "ps_list": {"desc": "查看进程列表", "needs_path": False},
    "ps_kill": {"desc": "终止进程", "needs_path": False},
    "log": {"desc": "查看日志", "needs_path": True},
    "log_search": {"desc": "搜索日志关键词", "needs_path": True},
    "backup_now": {"desc": "触发手动备份", "needs_path": False},
    "backup_list": {"desc": "查看备份列表", "needs_path": False},
    "backup_restore": {"desc": "从备份还原", "needs_path": False},
    "tunnel": {"desc": "查看当前隧道地址", "needs_path": False},
    "help": {"desc": "显示帮助信息", "needs_path": False},
}

ALLOWED_SERVICES = [
    "flask", "callback", "llama", "ollama", "ngrok",
    "file-bot", "file_bot", "sys-bot", "sys_bot", "monitor",
    "chat", "office", "life", "file", "sys", "all",
]

ALLOWED_LOG_FILES = {
    "flask": "logs/flask.log",
    "callback": "logs/flask.log",
    "monitor": "logs/monitor.log",
    "backup": "logs/backup_cron.log",
    "chat": "logs/chat_service.log",
    "office": "logs/office.log",
    "llama": "logs/llama_server.log",
    "ollama": "logs/ollama.log",
    "file_bot": "logs/file_bot.log",
    "file-bot": "logs/file_bot.log",
    "sys": "logs/sys_bot.log",
    "sys_bot": "logs/sys_bot.log",
}


def check_command(cmd: str) -> bool:
    if cmd in CMD_WHITELIST:
        return True
    logger.warning(f"禁止的命令: {cmd}")
    return False


def check_no_sudo(cmd_str: str) -> bool:
    if SUDO_PATTERN.search(cmd_str):
        logger.warning(f"命令包含 sudo: {cmd_str}")
        return False
    return True


def sanitize_path(user_path: str) -> str:
    path_str = str(Path(user_path).expanduser().resolve())
    project_str = str(PROJECT_ROOT.resolve())
    if not path_str.startswith(project_str):
        logger.warning(f"路径不在项目目录内: {path_str}")
        return ""
    if ".." in path_str.split(os.sep):
        logger.warning(f"路径含目录穿越: {path_str}")
        return ""
    return path_str


def is_allowed_log_file(name: str) -> bool:
    return name in ALLOWED_LOG_FILES


def get_log_path(name: str) -> str:
    if name in ALLOWED_LOG_FILES:
        return str(PROJECT_ROOT / ALLOWED_LOG_FILES[name])
    return ""


def validate_service_name(name: str) -> bool:
    return name in ALLOWED_SERVICES


def get_allowed_commands() -> list:
    return list(CMD_WHITELIST.keys())


def get_command_description(cmd: str) -> str:
    info = CMD_WHITELIST.get(cmd)
    if info:
        return info["desc"]
    return ""
