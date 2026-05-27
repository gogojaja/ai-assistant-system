"""
模块名称：process_manager
功能描述：5号AI 系统管理助理 — 进程管理（查看进程树/终止进程）
对外接口：
    - cmd_ps_list(filter_str=""): 查看进程列表，可选关键词过滤
    - cmd_ps_kill(pid): 终止指定 PID 的进程
依赖：
    - 标准库：subprocess, os, signal, logging
    - 第三方：无
    - 项目内：无
版本：v1.0
更新记录：
    - 2026-05-26: 初始创建
"""
import subprocess
import os
import signal
import logging

logger = logging.getLogger(__name__)


def cmd_ps_list(filter_str: str = "") -> str:
    lines = ["====== 进程列表 ======"]
    try:
        if filter_str:
            cmd = ["ps", "-eo", "pid,ppid,%cpu,%mem,rss,comm", "-r"]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            filtered = []
            for line in result.stdout.strip().split("\n"):
                if filter_str.lower() in line.lower():
                    filtered.append(line)
            if len(filtered) <= 1:
                return f"未找到匹配 '{filter_str}' 的进程"
            lines.append(f"匹配 '{filter_str}' 的进程 ({len(filtered)-1} 个):")
            lines.append("  PID  PPID  %CPU %MEM  RSS     COMMAND")
            for line in filtered[1:][:30]:
                lines.append(f"  {line}")
            if len(filtered) > 31:
                lines.append(f"  ... 还有 {len(filtered)-31} 个进程")
        else:
            cmd = ["ps", "-eo", "pid,ppid,%cpu,%mem,rss,comm", "-r"]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            output_lines = result.stdout.strip().split("\n")
            lines.append(f"共 {len(output_lines)-1} 个进程 (按 CPU 排序，显示前 30):")
            lines.append("  PID  PPID  %CPU %MEM  RSS     COMMAND")
            for line in output_lines[1:31]:
                lines.append(f"  {line}")
            if len(output_lines) > 31:
                lines.append(f"  ... 还有 {len(output_lines)-31} 个进程")
        return "\n".join(lines)
    except subprocess.TimeoutExpired:
        return "获取进程列表超时"
    except Exception as e:
        return f"获取进程列表失败: {e}"


def cmd_ps_kill(pid: str) -> str:
    try:
        pid_int = int(pid)
    except ValueError:
        return f"无效的 PID: {pid}"

    if pid_int <= 0:
        return "无效的 PID"

    if pid_int == os.getpid():
        return "❌ 不能终止自己"

    try:
        os.kill(pid_int, 0)
    except ProcessLookupError:
        return f"PID {pid} 不存在"
    except PermissionError:
        return f"❌ 无权限访问 PID {pid}"

    try:
        os.kill(pid_int, signal.SIGTERM)
        return f"已发送 SIGTERM 至 PID {pid}"
    except PermissionError:
        return f"❌ 无权限终止 PID {pid}"
    except ProcessLookupError:
        return f"PID {pid} 已不存在"
    except Exception as e:
        return f"终止 PID {pid} 失败: {e}"
