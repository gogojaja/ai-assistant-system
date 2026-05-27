#!/usr/bin/env python3

"""
模块名称：test_websocket_bot
功能描述：TODO: 请补充功能描述
对外接口：
    - TestCoreFunctions
依赖：
    - 标准库：os, pathlib, sys, unittest
    - 第三方：dotenv, websocket_bot
    - 项目内：无
版本：v1.0
更新记录：
    - 2026-05-23: 自动添加统一注释头
"""
import unittest
import sys
from pathlib import Path

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent))

class TestCoreFunctions(unittest.TestCase):
    def test_local_get_response(self):
        from websocket_bot import local_get_response
        res = local_get_response("你好")
        self.assertIsInstance(res, str)
        self.assertNotEqual(res, "")
    
    def test_local_search(self):
        from websocket_bot import local_search_and_archive
        res = local_search_and_archive("测试")
        self.assertIn("测试", res)
    
    def test_env_vars(self):
        from dotenv import load_dotenv
        import os
        env_path = Path(__file__).parent / ".env"
        if env_path.exists():
            load_dotenv(env_path)
            app_id = os.getenv("FEISHU_APP_ID")
            app_secret = os.getenv("FEISHU_APP_SECRET")
            self.assertIsNotNone(app_id)
            self.assertIsNotNone(app_secret)
            self.assertNotEqual(app_secret, "your_app_secret")
        else:
            self.skipTest(".env 文件不存在")

if __name__ == "__main__":
    unittest.main()
