"""
模块名称：check_env
功能描述：环境隔离检测——在操作前确认当前是否为测试环境，防止误操作主环境
对外接口：
    - check(test_mode=True): 检查是否在测试环境，不在则抛异常
    - is_test_env(): 返回 bool
依赖：标准库 os, sys, pathlib
版本：v1.0
更新记录：
    - 2026-05-27: 初始创建
"""
import os
import sys
from pathlib import Path


def is_test_env() -> bool:
    """判断当前是否为测试环境"""
    project_root = Path(__file__).parent.parent.resolve()
    marker = project_root / ".env_type"
    if marker.exists():
        return marker.read_text().strip() == "test"
    return False


def check(test_mode: bool = True) -> None:
    """环境检测，不匹配则退出"""
    if test_mode and not is_test_env():
        print("=" * 60)
        print("  ❌ 安全拦截：当前不是测试环境！")
        print(f"     实际路径: {Path(__file__).parent.parent.resolve()}")
        print("  🔒 禁止修改主环境文件")
        print("=" * 60)
        sys.exit(1)
    print(f"✅ 环境确认：测试环境 ({Path(__file__).parent.parent.resolve()})")


if __name__ == "__main__":
    check()
