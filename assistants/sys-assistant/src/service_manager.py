import subprocess
import os
import signal
import logging
import yaml
from pathlib import Path

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
LOG_DIR = PROJECT_ROOT / "logs"
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
CONFIG_PATH = PROJECT_ROOT / "config" / "settings.yaml"


def _load_port_config() -> dict:
    try:
        with open(CONFIG_PATH) as f:
            cfg = yaml.safe_load(f) or {}
        return {
            "callback_port": int(cfg.get("callback_port", 5001)),
            "llama_port": int(cfg.get("llama_port", 8080)),
            "ollama_port": int(cfg.get("ollama_port", 11434)),
            "file_bot_port": int(cfg.get("file_bot_port", 5002)),
            "sys_bot_port": int(cfg.get("sys_bot_port", 5003)),
        }
    except Exception:
        return {"callback_port": 5001, "llama_port": 8080, "ollama_port": 11434,
                "file_bot_port": 5002, "sys_bot_port": 5003}


def _get_service_config() -> dict:
    p = _load_port_config()
    return {
        "flask": {
            "name": "Flask 回调服务",
            "port": p["callback_port"],
            "start_cmd": f"cd {PROJECT_ROOT} && {PROJECT_ROOT}/venv/bin/python "
                         f"shared/feishu-callback/callback_server.py > {LOG_DIR}/flask.log 2>&1 &",
        },
        "llama": {
            "name": "llama.cpp 推理引擎",
            "port": p["llama_port"],
            "start_cmd": f"cd {PROJECT_ROOT} && bash scripts/restart_llama.sh 2>/dev/null || "
                         f"echo '请手动启动 llama-server'",
        },
        "ollama": {
            "name": "Ollama 推理引擎",
            "port": p["ollama_port"],
            "start_cmd": "nohup ollama serve > /dev/null 2>&1 &",
        },
        "file_bot": {
            "name": "4号文件助手",
            "port": p["file_bot_port"],
            "start_cmd": f"cd {PROJECT_ROOT} && env FILE_BOT_PORT={p['file_bot_port']} "
                         f"{PROJECT_ROOT}/assistants/file-assistant/venv-file/bin/python "
                         f"{PROJECT_ROOT}/assistants/file-assistant/src/file_bot_server.py "
                         f"> {LOG_DIR}/file_bot.log 2>&1 &",
        },
        "sys_bot": {
            "name": "5号系统管理助手",
            "port": p["sys_bot_port"],
            "start_cmd": f"cd {PROJECT_ROOT} && env SYS_BOT_PORT={p['sys_bot_port']} "
                         f"{PROJECT_ROOT}/assistants/sys-assistant/venv-sys/bin/python "
                         f"{PROJECT_ROOT}/assistants/sys-assistant/src/bot_server.py "
                         f"> {LOG_DIR}/sys_bot.log 2>&1 &",
        },
        "ngrok": {
            "name": "ngrok 隧道",
            "start_cmd": f"nohup ngrok start ai-system "
                         f"--config=\"$HOME/Library/Application Support/ngrok/ngrok.yml\" "
                         f"> {LOG_DIR}/ngrok.log 2>&1 &",
        },
        "monitor": {
            "name": "服务守护",
            "start_cmd": f"cd {PROJECT_ROOT} && bash {SCRIPTS_DIR}/monitor_services.sh > /dev/null 2>&1 &",
        },
    }


def _get_pids_by_port(port: int) -> list:
    try:
        result = subprocess.run(
            ["lsof", "-ti", f"tcp:{port}"],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0 and result.stdout.strip():
            return [int(p) for p in result.stdout.strip().split()]
    except Exception:
        pass
    return []


def _get_pids_by_name(name_filter: str) -> list:
    try:
        result = subprocess.run(
            ["pgrep", "-f", name_filter],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0 and result.stdout.strip():
            return [int(p) for p in result.stdout.strip().split()]
    except Exception:
        pass
    return []


def _detect_pids(config: dict) -> list:
    if "port" in config:
        return _get_pids_by_port(config["port"])
    name = config.get("name", "")
    if "ngrok" in name.lower():
        return _get_pids_by_name("ngrok start")
    if "守护" in name:
        return _get_pids_by_name(f"monitor_services.*{PROJECT_ROOT}")
    return []


def _check_port(port: int) -> bool:
    try:
        result = subprocess.run(
            ["lsof", "-i", f"tcp:{port}"],
            capture_output=True, text=True, timeout=5
        )
        return result.returncode == 0
    except Exception:
        return False


def cmd_service_list() -> str:
    services = _get_service_config()
    lines = ["====== 项目服务状态 ======"]
    for key, config in services.items():
        pids = _detect_pids(config)
        port_info = f":{config['port']}" if "port" in config else ""
        if pids:
            lines.append(f"  🟢 {config['name']}{port_info}  (PID: {', '.join(str(p) for p in pids)})")
        else:
            lines.append(f"  🔴 {config['name']}{port_info}  (未运行)")
    return "\n".join(lines)


def cmd_service_status(name: str) -> str:
    services = _get_service_config()
    config = services.get(name)
    if not config:
        svc_names = "\n  ".join(services.keys())
        return f"未知服务: {name}\n可用服务:\n  {svc_names}"
    pids = _detect_pids(config)
    if pids:
        pid_str = ", ".join(str(p) for p in pids)
        result = f"🟢 {config['name']} 运行中 (PID: {pid_str})"
        if "port" in config:
            port_ok = _check_port(config["port"])
            if port_ok:
                result += f"\n   端口 {config['port']}: 已监听"
            else:
                result += f"\n   ⚠️ 端口 {config['port']}: 未监听"
        return result
    return f"🔴 {config['name']} 未运行"


def cmd_service_start(name: str) -> str:
    services = _get_service_config()
    config = services.get(name)
    if not config:
        svc_names = "\n  ".join(services.keys())
        return f"未知服务: {name}\n可用服务:\n  {svc_names}"
    pids = _detect_pids(config)
    if pids:
        return f"🟢 {config['name']} 已在运行 (PID: {', '.join(str(p) for p in pids)})"
    cmd = config.get("start_cmd", "")
    if not cmd:
        return f"❌ {config['name']} 没有配置启动命令"
    try:
        subprocess.Popen(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return f"正在启动 {config['name']}..."
    except Exception as e:
        return f"❌ 启动 {config['name']} 失败: {e}"


def cmd_service_stop(name: str) -> str:
    services = _get_service_config()
    config = services.get(name)
    if not config:
        svc_names = "\n  ".join(services.keys())
        return f"未知服务: {name}\n可用服务:\n  {svc_names}"
    pids = _detect_pids(config)
    if not pids:
        return f"🔴 {config['name']} 未运行"
    killed = []
    for pid in pids:
        if pid <= 0 or pid == os.getpid():
            continue
        try:
            os.kill(pid, signal.SIGTERM)
            killed.append(str(pid))
        except ProcessLookupError:
            pass
        except PermissionError:
            return f"❌ 无权限终止 PID {pid}"
        except Exception as e:
            return f"❌ 终止 PID {pid} 失败: {e}"
    if killed:
        return f"已发送 SIGTERM 至 {config['name']} (PID: {', '.join(killed)})"
    return f"未终止任何进程"


def cmd_service_restart(name: str) -> str:
    stop_result = cmd_service_stop(name)
    return f"{stop_result}\n正在重启..."


def cmd_service_start_all() -> str:
    script = SCRIPTS_DIR / "start_all_services.sh"
    if not script.exists():
        return f"❌ 启动脚本不存在: {script}"
    try:
        subprocess.Popen(["bash", str(script)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return "正在启动所有服务..."
    except Exception as e:
        return f"❌ 启动失败: {e}"


def cmd_service_stop_all() -> str:
    script = SCRIPTS_DIR / "stop_all_services.sh"
    if not script.exists():
        return f"❌ 停止脚本不存在: {script}"
    try:
        subprocess.Popen(["bash", str(script)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return "正在停止所有服务..."
    except Exception as e:
        return f"❌ 停止失败: {e}"
