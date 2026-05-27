#!/usr/bin/env python3

"""
模块名称：test_diagnose
功能描述：TODO: 请补充功能描述
对外接口：
    - test_python_version_check()
    - test_project_root_check()
    - test_service_detection_mock()
依赖：
    - 标准库：logging, os, pathlib, sys
    - 第三方：diagnose
    - 项目内：无
版本：v1.0
更新记录：
    - 2026-05-23: 自动添加统一注释头
"""
"""
模块名称：test_diagnose
功能描述：diagnose.py 的独立测试脚本，包含 3 组基础测试用例，验证核心检查逻辑
对外接口：
    - 直接运行，执行所有测试用例并输出结果
依赖：
    - 标准库：sys, os, logging, pathlib
    - 第三方：无
    - 项目内：diagnose (EnvironmentDiagnoser, EXPECTED)
版本：v1.0
更新记录：
    - 2026-05-23: 初始创建，添加统一注释头
"""
import sys
import os
import logging
from pathlib import Path

# 添加脚本目录到 sys.path 以便导入 diagnose
sys.path.insert(0, os.path.dirname(__file__))
from diagnose import EnvironmentDiagnoser, EXPECTED

logging.basicConfig(level=logging.INFO, format='[TEST] %(message)s')
logger = logging.getLogger("test_diagnose")

def test_python_version_check():
    """测试 Python 版本检查逻辑"""
    logger.info("1️⃣ 测试 Python 版本检查...")
    diag = EnvironmentDiagnoser()
    diag.check_python_version()
    check = diag.report["checks"]["python_version"]
    assert check["ok"] == True, "Python 版本应为合格"
    logger.info(" ✅ 通过")

def test_project_root_check():
    """测试项目根目录检查"""
    logger.info("2️⃣ 测试项目根目录检查...")
    diag = EnvironmentDiagnoser()
    # 模拟不存在路径：临时修改 EXPECTED 后恢复
    original = EXPECTED["project_root"]
    EXPECTED["project_root"] = "/tmp/nonexistent_project"
    diag.check_project_root()
    check = diag.report["checks"]["project_root"]
    assert check["exists"] == False, "应检测到根目录不存在"
    # 恢复
    EXPECTED["project_root"] = original
    logger.info(" ✅ 通过")

def test_service_detection_mock():
    """测试服务检测逻辑（模拟无进程）"""
    logger.info("3️⃣ 测试服务检测逻辑...")
    diag = EnvironmentDiagnoser()
    # 使用系统不存在的进程名，确保检测为空
    original_svcs = EXPECTED["services"]
    EXPECTED["services"] = {"nonexistent_service": {"process_name": "this_process_should_not_exist", "port": 9999}}
    diag.check_services()
    check = diag.report["checks"]["service_nonexistent_service"]
    assert check["pid"] is None, "不应检测到 PID"
    assert check["port_open"] == False, "端口不应开放"
    EXPECTED["services"] = original_svcs
    logger.info(" ✅ 通过")

if __name__ == "__main__":
    logger.info("开始运行诊断测试脚本...")
    test_python_version_check()
    test_project_root_check()
    test_service_detection_mock()
    logger.info("🎉 所有测试用例通过")