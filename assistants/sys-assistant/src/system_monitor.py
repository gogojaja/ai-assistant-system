import subprocess
import logging
import yaml
from pathlib import Path

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
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


def _run_cmd(cmd: list, timeout: int = 10) -> str:
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return result.stdout.strip()
    except FileNotFoundError:
        return f"命令未找到: {cmd[0]}"
    except subprocess.TimeoutExpired:
        return f"命令超时（{timeout}秒）"
    except Exception as e:
        return f"执行出错: {e}"


def cmd_status() -> str:
    lines = ["====== 系统状态总览 ======"]
    lines.append(_get_uptime_text())
    lines.append("")
    lines.append(f"CPU 使用率:  {_get_cpu_percent()}")
    lines.append(f"内存使用率:  {_get_mem_percent()}")
    lines.append(f"磁盘使用率:  {_get_disk_percent()}")
    lines.append(f"系统负载:    {_get_load_text()}")
    lines.append(f"进程总数:    {_get_process_count()}")
    lines.append("")
    lines.append("--- 项目服务状态 ---")
    lines.append(_get_project_service_status())
    return "\n".join(lines)


def cmd_disk() -> str:
    lines = ["====== 磁盘使用详情 ======"]
    output = _run_cmd(["df", "-h"])
    for line in output.split("\n"):
        lines.append(line)
    return "\n".join(lines)


def cmd_mem() -> str:
    lines = ["====== 内存使用详情 ======"]
    output = _run_cmd(["vm_stat"])
    if "命令未找到" in output:
        output = _run_cmd(["sysctl", "-n", "hw.memsize"])
        mem_bytes = int(output) if output.isdigit() else 0
        mem_gb = mem_bytes / (1024**3)
        lines.append(f"物理内存: {mem_gb:.1f} GB")
        pages = _run_cmd(["vm_stat"])
        for p_line in pages.split("\n"):
            lines.append(p_line)
    else:
        lines.append(output)
    lines.append("")
    output = _run_cmd(["memory_pressure"])
    lines.append(output)
    return "\n".join(lines)


def cmd_cpu() -> str:
    lines = ["====== CPU 使用详情 ======"]
    output = _run_cmd(["sysctl", "-n", "hw.ncpu"])
    lines.append(f"CPU 核心数: {output}")
    lines.append("")
    output = _run_cmd(["top", "-l", "1", "-n", "0", "-stats", "cpu"])
    for line in output.split("\n"):
        if "CPU" in line:
            lines.append(line)
    lines.append("")
    output = _run_cmd(["ps", "-Ao", "%cpu=,comm=", "-r"])
    proc_lines = output.strip().split("\n")[:10]
    lines.append("Top 10 CPU 进程:")
    for i, p in enumerate(proc_lines, 1):
        parts = p.strip().split(None, 1)
        if len(parts) == 2:
            lines.append(f"  {i}. {parts[1][:40]:40s} {parts[0]}%")
    return "\n".join(lines)


def cmd_load() -> str:
    lines = ["====== 系统负载 ======"]
    lines.append(_get_load_text())
    lines.append("")
    output = _run_cmd(["uptime"])
    lines.append(output)
    return "\n".join(lines)


def cmd_uptime() -> str:
    return _get_uptime_text()


def cmd_network() -> str:
    lines = ["====== 网络状态 ======"]
    output = _run_cmd(["ifconfig", "lo0"])
    lines.append("--- 回环接口 ---")
    for line in output.split("\n"):
        if "inet " in line or "status" in line:
            lines.append(line.strip())
    lines.append("")
    output = _run_cmd(["ifconfig", "en0"])
    lines.append("--- en0 (Wi-Fi) ---")
    for line in output.split("\n"):
        if "inet " in line or "status" in line:
            lines.append(line.strip())
    lines.append("")
    output = _run_cmd(["netstat", "-rn", "-f", "inet"])
    lines.append("--- 路由表 ---")
    for line in output.split("\n")[:10]:
        lines.append(line)
    return "\n".join(lines)


def _get_cpu_percent() -> str:
    output = _run_cmd(["top", "-l", "1", "-n", "0"])
    for line in output.split("\n"):
        if "CPU usage" in line.lower() or "%CPU" in line:
            return line.strip()
    return "N/A"


def _get_mem_percent() -> str:
    output = _run_cmd(["memory_pressure"])
    for line in output.split("\n"):
        if "percentage" in line.lower():
            parts = line.split(":")
            if len(parts) >= 2:
                return parts[1].strip()
    output = _run_cmd(["vm_stat"])
    pages_active = 0
    pages_wired = 0
    pages_free = 0
    for line in output.split("\n"):
        if "pages active" in line.lower():
            try:
                pages_active = int(line.split(":")[1].strip().rstrip("."))
            except ValueError:
                pass
        if "pages wired" in line.lower():
            try:
                pages_wired = int(line.split(":")[1].strip().rstrip("."))
            except ValueError:
                pass
        if "Pages free" in line:
            try:
                pages_free = int(line.split(":")[1].strip().rstrip("."))
            except ValueError:
                pass
    total = pages_active + pages_wired + pages_free
    if total > 0:
        used = pages_active + pages_wired
        pct = (used / total) * 100
        return f"{pct:.1f}%"
    return "N/A"


def _get_disk_percent() -> str:
    output = _run_cmd(["df", "-h", "/"])
    lines = output.strip().split("\n")
    if len(lines) >= 2:
        parts = lines[1].split()
        if len(parts) >= 5:
            return parts[4]
    return "N/A"


def _get_load_text() -> str:
    output = _run_cmd(["sysctl", "-n", "vm.loadavg"])
    return output


def _get_uptime_text() -> str:
    output = _run_cmd(["uptime"])
    return output


def _get_process_count() -> str:
    output = _run_cmd(["ps", "-e", "wc", "-l"])
    return output.strip()


def _get_project_service_status() -> str:
    p = _load_port_config()
    services = {
        f"Flask:{p['callback_port']}": p["callback_port"],
        "llama-server": p["llama_port"],
        "Ollama": p["ollama_port"],
        f"file-bot:{p['file_bot_port']}": p["file_bot_port"],
        "sys-bot": p["sys_bot_port"],
        "ngrok": None,
        "monitor": None,
    }
    lines = []
    for name, port in services.items():
        if port is not None:
            result = subprocess.run(
                ["lsof", "-ti", f"tcp:{port}"],
                capture_output=True, text=True, timeout=5
            )
            pids = result.stdout.strip()
            status = f"🟢 运行中 (PID: {pids.split(chr(10))[0]})" if pids else "🔴 未运行"
        else:
            result = subprocess.run(
                ["pgrep", "-f", name.lower()],
                capture_output=True, text=True, timeout=5
            )
            pids = result.stdout.strip()
            status = f"🟢 运行中 (PID: {pids.split(chr(10))[0]})" if pids else "🔴 未运行"
        lines.append(f"  {name:20s} {status}")
    return "\n".join(lines)
