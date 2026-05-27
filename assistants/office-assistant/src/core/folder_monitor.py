"""
模块名称：folder_monitor.py
功能描述：办公文件夹监控，监测文件变更并记录日志
对外接口：
    - start_monitor(watch_dir, callback=None): 启动文件夹监控
    - stop_monitor(): 停止监控
依赖：
    - 标准库：logging, os, time, threading
    - 第三方：watchdog
    - 项目内：无
版本：v1.0
更新记录：
    - 2026-05-25: 初始创建
"""

import logging
import os
import threading

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

logger = logging.getLogger(__name__)

_observer = None
_thread = None


class ChangeHandler(FileSystemEventHandler):
    def __init__(self, callback=None):
        self.callback = callback

    def on_modified(self, event):
        if event.is_directory:
            return
        logger.info(f"文件变更: {event.src_path}")
        if self.callback:
            self.callback(event.src_path, "modified")

    def on_created(self, event):
        if event.is_directory:
            return
        logger.info(f"文件新增: {event.src_path}")
        if self.callback:
            self.callback(event.src_path, "created")

    def on_deleted(self, event):
        if event.is_directory:
            return
        logger.info(f"文件删除: {event.src_path}")
        if self.callback:
            self.callback(event.src_path, "deleted")


def start_monitor(watch_dir, callback=None):
    """启动文件夹监控（异步线程）"""
    global _observer, _thread
    if _observer and _observer.is_alive():
        logger.warning("监控已在运行")
        return

    os.makedirs(watch_dir, exist_ok=True)
    event_handler = ChangeHandler(callback=callback)
    _observer = Observer()
    _observer.schedule(event_handler, watch_dir, recursive=False)

    def _run():
        _observer.start()
        logger.info(f"文件夹监控已启动: {watch_dir}")
        _observer.join()

    _thread = threading.Thread(target=_run, daemon=True)
    _thread.start()


def stop_monitor():
    """停止文件夹监控"""
    global _observer, _thread
    if _observer and _observer.is_alive():
        _observer.stop()
        _observer.join()
        _observer = None
        _thread = None
        logger.info("文件夹监控已停止")
        return True
    return False
