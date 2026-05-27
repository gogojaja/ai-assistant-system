"""
模块名称：voice_handler
功能描述：语音消息处理流程（下载、格式转换、语音识别、交给消息处理器）
对外接口：
    - process_voice_message(file_key, message_id, open_id): 完整处理语音消息
依赖：
    - 标准库：logging, tempfile, os, threading
    - 第三方：无
    - 项目内：shared.feishu_api (download_file, send_message),
               shared.speech_utils (transcribe_audio, convert_opus_to_wav),
               assistants.chat-assistant.src.message_handler (process_message)
版本：v1.0
更新记录：
    - 2026-05-23: 初始创建，从 callback_server.py 剥离语音消息处理
"""
import logging
import tempfile
import os
import threading
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..'))
from shared.feishu_api import download_file, send_message
from shared.speech_utils import transcribe_audio, convert_opus_to_wav
from assistants.chat_assistant.src.message_handler import process_message

logger = logging.getLogger(__name__)


def process_voice_message(file_key: str, message_id: str, open_id: str):
    """
    语音消息处理主流程：
    1. 下载 opus 文件
    2. 转换为 wav
    3. 语音识别
    4. 将识别文字交给文本消息处理器
    """
    with tempfile.NamedTemporaryFile(suffix=".opus", delete=False) as tmp:
        audio_file = tmp.name
    if not download_file(message_id, file_key, audio_file):
        send_message(open_id, "语音下载失败，请稍后重试。")
        return
    wav_file = audio_file.replace(".opus", ".wav")
    try:
        if not convert_opus_to_wav(audio_file, wav_file):
            send_message(open_id, "语音格式转换失败。")
            return
        text = transcribe_audio(wav_file)
        if not text:
            send_message(open_id, "无法识别语音内容，请尝试文字输入。")
            return
        logger.info(f"语音识别结果: {text}")
        process_message(text, open_id)
    finally:
        # 清理临时文件
        for f in [audio_file, wav_file]:
            try:
                if os.path.exists(f):
                    os.unlink(f)
            except Exception:
                pass
