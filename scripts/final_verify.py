#!/usr/bin/env python3
"""
模块名称：final_verify
功能描述：最终验收脚本，汇总检查所有关键服务与模块状态
对外接口：
    - 直接运行，输出各项检查结果
依赖：
    - 标准库：subprocess, logging
    - 第三方：无
    - 项目内：无
版本：v1.0
更新记录：
    - 2026-05-23: 初始创建，添加统一注释头
"""
import subprocess
import logging
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.dirname(SCRIPT_DIR)

logging.basicConfig(level=logging.INFO, format='[VERIFY] %(message)s')
logger = logging.getLogger("final_verify")

WHISPER_CLI = os.path.join(PROJECT, "shared/whisper.cpp/build/bin/whisper-cli")
WHISPER_MODEL = os.path.join(PROJECT, "shared/whisper.cpp/models/ggml-small.bin")
SETTINGS_FILE = os.path.join(PROJECT, "config/settings.yaml")

CHECKS = {
    "llama-server": "pgrep -f llama-server",
    "flask回调": f"lsof -i tcp:$(python3 -c \"import yaml; print(yaml.safe_load(open('{PROJECT}/config/settings.yaml'))['callback_port'])\" 2>/dev/null || echo 5001)",
    "ngrok/cloudflared": "pgrep -f 'ngrok|cloudflared'",
    "feishu回调验证": f"{PROJECT}/venv/bin/python {PROJECT}/scripts/verify_feishu_callback.py >/dev/null 2>&1",
    "whisper-cli": f"test -f '{WHISPER_CLI}'",
    "whisper模型": f"test -f '{WHISPER_MODEL}'",
    "配置文件": f"test -f '{SETTINGS_FILE}'",
}

def run_check(name, cmd):
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            logger.info(f"✅ {name}")
        else:
            logger.warning(f"❌ {name}")
    except Exception as e:
        logger.error(f"⚠️  {name} 检查异常: {e}")

if __name__ == "__main__":
    logger.info("开始最终验收检查...")
    for name, cmd in CHECKS.items():
        run_check(name, cmd)
    logger.info("验收完成")