"""
模块名称：log_viewer
功能描述：5号AI 系统管理助理 — 日志查看（实时 tail / 关键词过滤 / 日志归档）
对外接口：
    - cmd_log(name, lines=20): 查看指定日志文件尾部 N 行
    - cmd_log_search(keyword, name=""): 在日志文件中搜索关键词
依赖：
    - 标准库：subprocess, pathlib, logging
    - 第三方：无
    - 项目内：sys-assistant.src.security
版本：v1.0
更新记录：
    - 2026-05-26: 初始创建
"""
import subprocess
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

from .security import is_allowed_log_file, get_log_path

MAX_LINES = 200
MAX_SEARCH_RESULTS = 50


def cmd_log(name: str, lines: int = 20) -> str:
    if not is_allowed_log_file(name):
        allowed = "flask, monitor, backup, chat, office, llama, ollama, file_bot, sys"
        return f"不允许的日志: {name}\n可用日志: {allowed}"

    log_path = get_log_path(name)
    if not log_path:
        return f"日志路径未配置: {name}"

    log_file = Path(log_path)
    if not log_file.exists():
        return f"日志文件不存在: {log_path}"

    if lines < 1:
        lines = 20
    if lines > MAX_LINES:
        lines = MAX_LINES

    try:
        result = subprocess.run(
            ["tail", "-n", str(lines), log_path],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode != 0:
            return f"读取日志失败: {result.stderr.strip()}"
        output = result.stdout.strip()
        if not output:
            return f"日志文件为空: {log_path}"
        file_size = log_file.stat().st_size
        size_str = _format_size(file_size)
        header = f"====== {name} 日志 (最后 {lines} 行，共 {size_str}) ======"
        return f"{header}\n{output}"
    except subprocess.TimeoutExpired:
        return f"读取日志超时: {log_path}"
    except Exception as e:
        return f"读取日志异常: {e}"


def cmd_log_search(keyword: str, name: str = "") -> str:
    if not keyword:
        return "请提供搜索关键词"

    if name:
        logs_to_search = [name]
    else:
        from .security import ALLOWED_LOG_FILES
        logs_to_search = list(ALLOWED_LOG_FILES.keys())

    results = []
    for log_name in logs_to_search:
        if not is_allowed_log_file(log_name):
            continue
        log_path = get_log_path(log_name)
        if not log_path:
            continue
        log_file = Path(log_path)
        if not log_file.exists():
            continue

        try:
            result = subprocess.run(
                ["grep", "-i", "-n", keyword, log_path],
                capture_output=True, text=True, timeout=15
            )
            if result.returncode == 0 and result.stdout.strip():
                matches = result.stdout.strip().split("\n")
                display = matches[:MAX_SEARCH_RESULTS]
                for match in display:
                    results.append(f"[{log_name}] {match}")
                if len(matches) > MAX_SEARCH_RESULTS:
                    results.append(f"[{log_name}] ... 还有 {len(matches) - MAX_SEARCH_RESULTS} 条匹配")
        except subprocess.TimeoutExpired:
            results.append(f"[{log_name}] 搜索超时")
        except Exception as e:
            results.append(f"[{log_name}] 搜索出错: {e}")

    if not results:
        return f"未找到包含 '{keyword}' 的日志"

    header = f"====== 搜索结果: '{keyword}' ({len(results)} 条) ======"
    return f"{header}\n" + "\n".join(results)


def _format_size(size_bytes: int) -> str:
    for unit in ["B", "KB", "MB", "GB"]:
        if size_bytes < 1024:
            return f"{size_bytes:.1f}{unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f}TB"
