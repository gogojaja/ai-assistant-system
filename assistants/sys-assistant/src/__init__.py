import logging
from pathlib import Path

from .security import check_command, CMD_WHITELIST, validate_service_name
from .system_monitor import (
    cmd_status, cmd_disk, cmd_mem, cmd_cpu, cmd_load, cmd_uptime, cmd_network,
)
from .service_manager import (
    cmd_service_list, cmd_service_status, cmd_service_start,
    cmd_service_stop, cmd_service_restart,
    cmd_service_start_all, cmd_service_stop_all,
)
from .process_manager import cmd_ps_list, cmd_ps_kill
from .log_viewer import cmd_log, cmd_log_search
from .backup_manager import cmd_backup_now, cmd_backup_list, cmd_backup_restore

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent

HELP_TEXT = """\
=== 5号AI 系统管理助理 ===
系统状态:
  status                 系统状态总览
  disk                   磁盘使用详情
  mem                    内存使用详情
  cpu                    CPU 使用详情
  load                   系统负载
  uptime                 系统运行时间
  network                网络连接状态
服务管理:
  svc list               查看所有服务状态
  svc status <name>      查看指定服务状态
  svc start <name>       启动服务
  svc stop <name>        停止服务
  svc restart <name>     重启服务
  svc start all          启动所有服务
  svc stop all           停止所有服务
进程管理:
  ps list [filter]       查看进程列表（可选关键词过滤）
  ps kill <pid>          终止进程
日志查看:
  log <name> [lines]     查看日志（默认 20 行）
  log search <keyword>   搜索日志关键词
网络:
  tunnel                 查看当前 Bot 隧道地址
备份管理:
  backup now             触发手动备份
  backup list            查看备份列表
  backup restore <id>    还原备份
可用服务: flask, llama, ollama, ngrok, file_bot, sys_bot, monitor
可用日志: flask, monitor, backup, chat, office, llama, ollama, file_bot, sys
  help                   显示此帮助"""


TWO_WORD_COMMANDS = {
    "svc list", "svc status", "svc start", "svc stop", "svc restart",
    "ps list", "ps kill",
    "log search",
    "backup now", "backup list", "backup restore",
}


def process(text: str, open_id: str = "") -> str:
    text = text.strip()

    if not text or text in ("help", "帮助"):
        return HELP_TEXT

    parts = text.split()
    two_word = " ".join(parts[:2]) if len(parts) >= 2 else ""

    if two_word in TWO_WORD_COMMANDS:
        cmd = two_word.replace(" ", "_")
        args = parts[2:]
    else:
        cmd = parts[0]
        args = parts[1:]

    if not check_command(cmd):
        return f"未知命令: '{cmd}'\n输入 #5 help 查看可用命令"

    return _dispatch(cmd, args)


def _dispatch(cmd: str, args: list) -> str:
    try:
        if cmd == "help":
            return HELP_TEXT
        elif cmd == "status":
            return cmd_status()
        elif cmd == "disk":
            return cmd_disk()
        elif cmd == "mem":
            return cmd_mem()
        elif cmd == "cpu":
            return cmd_cpu()
        elif cmd == "load":
            return cmd_load()
        elif cmd == "uptime":
            return cmd_uptime()
        elif cmd == "network":
            return cmd_network()
        elif cmd == "svc_list":
            return cmd_service_list()
        elif cmd == "svc_status":
            name = args[0] if args else ""
            if not name:
                return "用法: svc status <服务名>\n可用服务: flask, llama, ollama, ngrok, file_bot, sys_bot, monitor"
            if not validate_service_name(name):
                return f"未知服务: {name}\n可用服务: flask, llama, ollama, ngrok, file_bot, sys_bot, monitor"
            return cmd_service_status(name)
        elif cmd == "svc_start":
            name = args[0] if args else ""
            if not name:
                return "用法: svc start <服务名>\n  svc start all  启动所有服务"
            if name == "all":
                return cmd_service_start_all()
            if not validate_service_name(name):
                return f"未知服务: {name}"
            return cmd_service_start(name)
        elif cmd == "svc_stop":
            name = args[0] if args else ""
            if not name:
                return "用法: svc stop <服务名>\n  svc stop all   停止所有服务"
            if name == "all":
                return cmd_service_stop_all()
            if not validate_service_name(name):
                return f"未知服务: {name}"
            return cmd_service_stop(name)
        elif cmd == "svc_restart":
            name = args[0] if args else ""
            if not name:
                return "用法: svc restart <服务名>"
            if name == "all":
                return "不支持批量重启，请使用 svc stop all 再 svc start all"
            if not validate_service_name(name):
                return f"未知服务: {name}"
            return cmd_service_restart(name)
        elif cmd == "ps_list":
            filter_str = args[0] if args else ""
            return cmd_ps_list(filter_str)
        elif cmd == "ps_kill":
            pid = args[0] if args else ""
            if not pid:
                return "用法: ps kill <PID>"
            return cmd_ps_kill(pid)
        elif cmd == "log":
            name = args[0] if args else ""
            if not name:
                return "用法: log <日志名> [行数]\n可用日志: flask, monitor, backup, chat, office, llama, ollama, file_bot, sys"
            lines = 20
            if len(args) > 1:
                try:
                    lines = int(args[1])
                except ValueError:
                    pass
            return cmd_log(name, lines)
        elif cmd == "log_search":
            keyword = " ".join(args) if args else ""
            if not keyword:
                return "用法: log search <关键词>"
            return cmd_log_search(keyword)
        elif cmd == "tunnel":
            return _get_tunnel_url()
        elif cmd == "backup_now":
            return cmd_backup_now()
        elif cmd == "backup_list":
            return cmd_backup_list()
        elif cmd == "backup_restore":
            id_str = args[0] if args else ""
            if not id_str:
                return "用法: backup restore <编号>"
            return cmd_backup_restore(id_str)
        else:
            return HELP_TEXT
    except Exception as e:
        logger.error(f"命令执行异常: cmd={cmd}, args={args}, error={e}", exc_info=True)
        return f"执行 '{cmd}' 时出错: {e}"


def _get_tunnel_url() -> str:
    import urllib.request, json
    # 根据 PROEJCT_ROOT 路径判断环境：主环境 coastal，测试环境 employee-radish-fringe
    project_str = str(PROJECT_ROOT)
    is_main = "ai-assistant-system" in project_str and "BR256G" not in project_str
    domain = "coastal-speckled-exorcist" if is_main else "employee-radish-fringe"

    ngrok_api_port = 4040 if is_main else 4041
    try:
        resp = urllib.request.urlopen(f"http://127.0.0.1:{ngrok_api_port}/api/tunnels", timeout=5)
        data = json.loads(resp.read())
        for tunnel in data.get("tunnels", []):
            pub = tunnel.get("public_url", "")
            if pub:
                return (f"ngrok 公网地址: {pub}\n"
                        f"本 Bot 回调:    https://{domain}.ngrok-free.dev/webhook_sys\n"
                        f"主回调:         https://{domain}.ngrok-free.dev/webhook_chat\n"
                        f"文件助手:       https://{domain}.ngrok-free.dev/webhook_file")
    except Exception:
        pass
    return (f"无法获取 ngrok API（127.0.0.1:{ngrok_api_port}）\n"
            f"预期域名: {domain}.ngrok-free.dev")
