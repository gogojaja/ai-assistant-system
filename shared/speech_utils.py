#!/usr/bin/env python3

"""
模块名称：speech_utils
功能描述：语音处理工具（音频格式转换、语音转文字）
对外接口：
    - transcribe_audio(file_path): 调用 whisper.cpp 转写音频文件，返回文字
    - convert_opus_to_wav(input_path, output_path): 将 opus 音频转为 16kHz 单声道 wav
依赖：
    - 标准库：logging, subprocess, pathlib, os
    - 第三方：无
    - 项目内：无
版本：v1.1
更新记录：
    - 2026-05-25: v1.1 升级 medium 模型、音频归一化、多线程加速、修复命令构建
    - 2026-05-23: v1.0 初始创建
"""
import logging
import subprocess
import os
from pathlib import Path

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).parent.parent
WHISPER_CPP = PROJECT_ROOT / "shared/whisper.cpp"
WHISPER_CLI = WHISPER_CPP / "build/bin/whisper-cli"
WHISPER_MODEL = WHISPER_CPP / "models/ggml-medium.bin"


def transcribe_audio(file_path: str) -> str:
    """调用 whisper.cpp 转写音频文件，返回文字（失败返回空字符串）"""
    if not WHISPER_CLI.exists():
        logger.error(f"whisper-cli 不存在: {WHISPER_CLI}")
        return ""
    if not WHISPER_MODEL.exists():
        logger.error(f"模型不存在: {WHISPER_MODEL}")
        return ""

    cmd = [
        str(WHISPER_CLI),
        "-m", str(WHISPER_MODEL),
        "-f", file_path,
        "-l", "zh",
        "-t", "4",
        "--no-timestamps",
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            logger.error(f"Whisper 识别失败: {result.stderr}")
            return ""
        text = result.stdout.strip()
        logger.info(f"语音识别结果 ({len(text)} 字): {text[:100]}")
        return text
    except Exception as e:
        logger.error(f"Whisper 调用异常: {e}")
        return ""


def convert_opus_to_wav(input_path: str, output_path: str) -> bool:
    """使用 ffmpeg 将 opus 转为 16kHz 单声道 wav（含音量归一化），返回是否成功"""
    try:
        subprocess.run([
            "ffmpeg", "-i", input_path,
            "-af", "dynaudnorm=p=0.9:m=100",
            "-ar", "16000", "-ac", "1",
            "-y", output_path
        ], check=True, capture_output=True)
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"音频转换失败: {e.stderr.decode()}")
        return False
    except FileNotFoundError:
        logger.error("ffmpeg 未安装")
        return False
