#!/usr/bin/env python3

"""
模块名称：diagnose
功能描述：环境一键诊断脚本，抓取系统环境参数与设计文档预期值比对，生成报告
对外接口：
    - 直接运行，输出诊断报告 JSON 并保存到 logs/diagnose_report.json
依赖：
    - 标准库：os, sys, json, logging, subprocess, platform, shutil, pathlib, datetime
    - 第三方：无
    - 项目内：无
版本：v1.0
更新记录：
    - 2026-05-23: 初始创建，添加统一注释头
"""
import os
import sys
import json
import logging
import subprocess
import platform
import shutil
from pathlib import Path
from datetime import datetime

# 确保始终使用项目 venv 的 Python 执行
_project_root = Path(__file__).resolve().parent.parent
_venv_python = _project_root / "venv" / "bin" / "python"
if _venv_python.exists() and sys.executable != str(_venv_python):
    os.execv(str(_venv_python), [str(_venv_python)] + sys.argv)

# 配置 DEBUG 级别日志
logging.basicConfig(level=logging.DEBUG, format='[%(levelname)s] %(asctime)s - %(message)s')
logger = logging.getLogger("diagnose")

# ------------------------------------------------------------
# 预期配置（来源于设计文档）
# ------------------------------------------------------------
project_root = Path(__file__).resolve().parent.parent
EXPECTED = {
    "project_root": str(project_root),
    "python_version_min": (3, 10),
    "python_version_max": (3, 12),
    "venv_paths": [
        "venv",
        "assistants/chat-assistant/venv-chat",
        "assistants/office-assistant/venv-office"
    ],
    "required_dirs": [
        "assistants/chat-assistant/src",
        "assistants/office-assistant/src/core",
        "shared/feishu-callback",
        "scripts",
        "logs"
    ],
    "critical_scripts": [
        "start_all_services.sh",
        "stop_all_services.sh",
        "restart_callback.sh",
        "diagnose.sh",
        "update_docs.sh",
        "verify_phase2.sh"
    ],
    "services": {
        "ollama": {"port": 11434, "process_name": "ollama"},
        "flask": {"port": 5101, "process_name": "python.*callback_server"},
        "ngrok": {"process_name": "ngrok"}
    },
    "whisper": {
        "cli": "shared/whisper.cpp/build/bin/whisper-cli",
        "model": "shared/whisper.cpp/models/ggml-small.bin"
    },
    "config_file": "config/settings.yaml",
    "model_info": {
        "name": "qwen2.5:7b",
        "expected_speed": 33
    }
}


class EnvironmentDiagnoser:
    def __init__(self):
        self.report = {
            "timestamp": datetime.now().isoformat(),
            "hostname": platform.node(),
            "system": platform.system(),
            "python_version": sys.version,
            "checks": {}
        }

    def check_python_version(self):
        logger.debug("检查 Python 版本")
        ver = sys.version_info[:2]
        ok = EXPECTED["python_version_min"] <= ver <= EXPECTED["python_version_max"]
        self.report["checks"]["python_version"] = {
            "status": "✅" if ok else "❌",
            "current": f"{ver[0]}.{ver[1]}.{sys.version_info[2]}",
            "expected_range": f"{EXPECTED['python_version_min'][0]}.{EXPECTED['python_version_min'][1]} - {EXPECTED['python_version_max'][0]}.{EXPECTED['python_version_max'][1]}",
            "ok": ok
        }
        logger.info(f"Python 版本: {ver} -> {'合格' if ok else '不合格'}")

    def check_project_root(self):
        logger.debug("检查项目根目录")
        root = Path(EXPECTED["project_root"])
        exists = root.is_dir()
        self.report["checks"]["project_root"] = {
            "status": "✅" if exists else "❌",
            "path": str(root),
            "exists": exists
        }
        logger.info(f"项目根目录: {root} -> {'存在' if exists else '缺失'}")

    def check_required_dirs(self):
        logger.debug("检查子目录")
        root = Path(EXPECTED["project_root"])
        for d in EXPECTED["required_dirs"]:
            p = root / d
            exists = p.is_dir()
            self.report["checks"][f"dir_{d}"] = {
                "status": "✅" if exists else "❌",
                "path": str(p),
                "exists": exists
            }
            logger.debug(f"目录 {d}: {'存在' if exists else '缺失'}")

    def check_venv(self):
        logger.debug("检查虚拟环境")
        root = Path(EXPECTED["project_root"])
        for vp in EXPECTED["venv_paths"]:
            venv_path = root / vp
            activate_script = venv_path / "bin" / "activate"
            exists = activate_script.is_file()
            py_bin = venv_path / "bin" / "python"
            self.report["checks"][f"venv_{vp}"] = {
                "status": "✅" if exists else "❌",
                "path": str(venv_path),
                "activate_exists": exists,
                "python_exists": py_bin.is_file()
            }
            logger.debug(f"虚拟环境 {vp}: {'存在' if exists else '缺失'}")

    def check_critical_scripts(self):
        logger.debug("检查关键脚本")
        root = Path(EXPECTED["project_root"]) / "scripts"
        for script in EXPECTED["critical_scripts"]:
            sp = root / script
            exists = sp.is_file()
            self.report["checks"][f"script_{script}"] = {
                "status": "✅" if exists else "❌",
                "path": str(sp),
                "exists": exists
            }
            logger.debug(f"脚本 {script}: {'存在' if exists else '缺失'}")

    def check_services(self):
        logger.debug("检查服务进程与端口")
        for svc_name, svc_info in EXPECTED["services"].items():
            pid = None
            port_open = False
            try:
                result = subprocess.run(
                    ["pgrep", "-f", svc_info["process_name"]],
                    capture_output=True, text=True
                )
                if result.stdout.strip():
                    pid = result.stdout.strip().split('\n')[0]
                    logger.debug(f"发现进程 {svc_name}: PID {pid}")
            except Exception as e:
                logger.error(f"pgrep 异常: {e}")

            if "port" in svc_info:
                try:
                    port = svc_info["port"]
                    lsof = subprocess.run(
                        ["lsof", "-i", f"tcp:{port}"],
                        capture_output=True, text=True
                    )
                    if lsof.returncode == 0 and lsof.stdout.strip():
                        port_open = True
                        logger.debug(f"端口 {port} 正在监听")
                except Exception as e:
                    logger.error(f"lsof 异常: {e}")

            self.report["checks"][f"service_{svc_name}"] = {
                "status": "✅" if (pid and port_open) else ("🟡" if pid or port_open else "❌"),
                "pid": pid,
                "port_open": port_open
            }
            logger.info(f"服务 {svc_name}: PID={pid}, 端口{'开放' if port_open else '未监听'}")

    def check_whisper(self):
        root = Path(EXPECTED["project_root"])
        cli = root / EXPECTED["whisper"]["cli"]
        model = root / EXPECTED["whisper"]["model"]
        cli_ok = cli.is_file()
        model_ok = model.is_file()
        self.report["checks"]["whisper_cli"] = {"status": "✅" if cli_ok else "❌", "path": str(cli), "exists": cli_ok}
        self.report["checks"]["whisper_model"] = {"status": "✅" if model_ok else "❌", "path": str(model), "exists": model_ok}
        logger.info(f"Whisper CLI: {'存在' if cli_ok else '缺失'}, 模型: {'存在' if model_ok else '缺失'}")

    def check_config_file(self):
        root = Path(EXPECTED["project_root"])
        cfg = root / EXPECTED["config_file"]
        exists = cfg.is_file()
        self.report["checks"]["config_file"] = {
            "status": "✅" if exists else "❌",
            "path": str(cfg),
            "exists": exists
        }
        if exists:
            try:
                import yaml
                with open(cfg) as f:
                    data = yaml.safe_load(f)
                self.report["checks"]["config_content"] = {"location": data.get("location", "未知")}
                logger.debug(f"配置文件内容: {data}")
            except ImportError:
                self.report["checks"]["config_content"] = "yaml 库未安装，无法读取内容"
                logger.warning("yaml 未安装，跳过配置解析")

    def check_model_file(self):
        try:
            find_cmd = ["find", str(Path.home() / ".local/lib/ollama/blobs"), "-name", "sha256-2bada8a74506*", "-size", "+1G"]
            result = subprocess.run(find_cmd, capture_output=True, text=True)
            model_path = result.stdout.strip().split('\n')[0] if result.stdout.strip() else None
            self.report["checks"]["model_file"] = {
                "status": "✅" if model_path else "❌",
                "path": model_path if model_path else "未找到",
            }
            logger.info(f"模型文件: {model_path if model_path else '缺失'}")
        except Exception as e:
            logger.error(f"查找模型文件失败: {e}")

    def check_pip_deps(self):
        # 包名 -> 实际 import 模块名（python-docx 的模块名为 docx）
        dep_map = {
            "flask": "flask",
            "requests": "requests",
            "python-docx": "docx",
            "openpyxl": "openpyxl",
            "mammoth": "mammoth",
            "deep-translator": "deep_translator",
        }
        self.report["checks"]["dependencies"] = {}
        for dep, mod in dep_map.items():
            try:
                __import__(mod)
                self.report["checks"]["dependencies"][dep] = "已安装"
            except ImportError:
                self.report["checks"]["dependencies"][dep] = "❌ 未安装"

    def generate_report(self):
        logger.info("生成诊断报告...")
        report_json = json.dumps(self.report, indent=2, ensure_ascii=False)
        print("\n========== 环境诊断报告 ==========\n")
        print(report_json)
        report_file = Path(EXPECTED["project_root"]) / "logs" / "diagnose_report.json"
        report_file.parent.mkdir(exist_ok=True)
        with open(report_file, "w") as f:
            f.write(report_json)
        logger.info(f"报告已保存至 {report_file}")
        return report_json


def main():
    diag = EnvironmentDiagnoser()
    diag.check_python_version()
    diag.check_project_root()
    diag.check_required_dirs()
    diag.check_venv()
    diag.check_critical_scripts()
    diag.check_services()
    diag.check_whisper()
    diag.check_config_file()
    diag.check_model_file()
    diag.check_pip_deps()
    diag.generate_report()


if __name__ == "__main__":
    main()