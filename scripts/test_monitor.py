#!/usr/bin/env python3

"""
模块名称：test_monitor
功能描述：TODO: 请补充功能描述
对外接口：
    - check_process_exists()
    - test_llama_not_running()
    - test_llama_running()
    - test_port_check()
依赖：
    - 标准库：logging, subprocess
    - 第三方：无
    - 项目内：无
版本：v1.0
更新记录：
    - 2026-05-23: 自动添加统一注释头
"""
"""
模块名称：test_monitor
功能描述：测试服务监控脚本的核心检测逻辑（模拟进程检查）
对外接口：
    - 直接运行，执行 3 组测试用例并输出结果
依赖：
    - 标准库：logging, subprocess
    - 第三方：无
    - 项目内：无
版本：v1.0
更新记录：
    - 2026-05-23: 初始创建，添加统一注释头
"""
import logging
import subprocess

logging.basicConfig(level=logging.INFO, format='[TEST] %(message)s')
logger = logging.getLogger("test_monitor")

def check_process_exists(process_name):
    """使用 pgrep 检查进程是否存在"""
    try:
        result = subprocess.run(["pgrep", "-f", process_name], capture_output=True)
        return result.returncode == 0
    except Exception:
        return False

def test_llama_not_running():
    """测试检测一个不可能存在的进程"""
    logger.info("1️⃣ 检测不存在的进程...")
    exists = check_process_exists("this_process_should_not_exist_xyz")
    assert exists == False, "预期进程不存在"
    logger.info("✅ 通过：正确返回不存在")

def test_llama_running():
    """测试检测真实存在的进程（系统进程）"""
    logger.info("2️⃣ 检测系统存在的进程...")
    # macOS 下几乎一定存在的进程
    exists = check_process_exists("launchd")
    assert exists == True, "launchd 应该存在"
    logger.info("✅ 通过：正确检测到 launchd")

def test_port_check():
    """测试端口检测（使用 lsof）"""
    logger.info("3️⃣ 检查端口监听...")
    # 检查一个不可能被监听的端口
    result = subprocess.run(["lsof", "-i", "tcp:19999"], capture_output=True, text=True)
    assert result.returncode != 0, "端口 19999 不应被监听"
    logger.info("✅ 通过：正确判断端口未监听")

if __name__ == "__main__":
    logger.info("🚀 开始测试服务监控逻辑...")
    test_llama_not_running()
    test_llama_running()
    test_port_check()
    logger.info("🎉 所有测试通过")