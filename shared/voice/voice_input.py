#!/usr/bin/env python3
"""
模块名称：voice_input
功能描述：语音输入模块，使用 ffmpeg 录音后通过 Whisper.cpp 的 whisper-cli 工具进行语音识别，返回转写文本
对外接口：
    - record_and_transcribe(duration=5, sample_rate=16000): 录制指定时长的音频，调用 whisper-cli 识别，返回识别文本字符串
依赖：
    - 标准库：logging, pathlib, subprocess, tempfile
    - 第三方：无（依赖外部工具 ffmpeg 和 whisper-cli）
    - 项目内：无
版本：v1.0
更新记录：
    - 2026-05-23: 自动添加统一注释头，补充功能描述
"""

import subprocess
import tempfile
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

WHISPER_CPP = Path(__file__).parent.parent / "whisper.cpp"
WHISPER_CLI = WHISPER_CPP / "build/bin/whisper-cli"
MODEL = WHISPER_CPP / "models/ggml-base.bin"

def record_and_transcribe(duration=5, sample_rate=16000):
    if not WHISPER_CLI.exists():
        logger.error(f"whisper-cli 未找到: {WHISPER_CLI}")
        return ""
    if not MODEL.exists():
        logger.error(f"模型文件未找到: {MODEL}")
        return ""

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        tmp_path = tmp.name

    try:
        subprocess.run([
            "ffmpeg", "-f", "avfoundation", "-i", ":0", "-t", str(duration),
            "-ar", str(sample_rate), "-ac", "1", tmp_path, "-y"
        ], check=True, capture_output=True)
    except subprocess.CalledProcessError as e:
        logger.error(f"录音失败: {e.stderr.decode()}")
        return ""

    cmd = [str(WHISPER_CLI), "-m", str(MODEL), "-f", tmp_path, "--no-timestamps"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    Path(tmp_path).unlink()

    if result.returncode != 0:
        logger.error(f"Whisper 识别失败: {result.stderr}")
        return ""
    return result.stdout.strip()

if __name__ == "__main__":
    print("请说话...")
    text = record_and_transcribe(duration=4)
    print(f"识别结果: {text}")