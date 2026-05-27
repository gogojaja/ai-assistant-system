"""
模块名称：crypto.py
功能描述：数据加密留存工具，基于 cryptography.fernet
对外接口：
    - encrypt_text(plaintext, key=None): 加密文本
    - decrypt_text(ciphertext, key=None): 解密文本
    - encrypt_file(filepath, key=None): 加密文件（原地覆盖）
    - decrypt_file(filepath, key=None): 解密文件（原地覆盖）
    - load_or_create_key(key_path=None): 加载或生成密钥文件
依赖：
    - 标准库：os, sys, json, base64
    - 第三方：cryptography
版本：v1.0
更新记录：
    - 2026-05-25: 初始创建
"""

import os
import json
import base64
from pathlib import Path

KEY_PATH = Path(__file__).parent.parent / ".crypto_key"


def load_or_create_key(key_path=None):
    """加载或生成密钥文件"""
    key_path = Path(key_path or KEY_PATH)
    if key_path.exists():
        return key_path.read_bytes().strip()
    from cryptography.fernet import Fernet
    key = Fernet.generate_key()
    key_path.write_bytes(key + b"\n")
    os.chmod(str(key_path), 0o600)
    return key


def encrypt_text(plaintext, key=None):
    """加密文本，返回 base64 字符串"""
    from cryptography.fernet import Fernet
    if key is None:
        key = load_or_create_key()
    f = Fernet(key)
    return f.encrypt(plaintext.encode("utf-8")).decode("utf-8")


def decrypt_text(ciphertext, key=None):
    """解密文本"""
    from cryptography.fernet import Fernet
    if key is None:
        key = load_or_create_key()
    f = Fernet(key)
    return f.decrypt(ciphertext.encode("utf-8")).decode("utf-8")


def encrypt_file(filepath, key=None):
    """加密文件内容（原地覆盖为 base64）"""
    if key is None:
        key = load_or_create_key()
    plaintext = Path(filepath).read_text(encoding="utf-8")
    encrypted = encrypt_text(plaintext, key)
    Path(filepath).write_text(encrypted, encoding="utf-8")


def decrypt_file(filepath, key=None):
    """解密文件（原地恢复原文）"""
    if key is None:
        key = load_or_create_key()
    ciphertext = Path(filepath).read_text(encoding="utf-8")
    plaintext = decrypt_text(ciphertext, key)
    Path(filepath).write_text(plaintext, encoding="utf-8")


def encrypt_json(obj, key=None):
    """加密 JSON 可序列化对象，返回 base64 字符串"""
    return encrypt_text(json.dumps(obj, ensure_ascii=False), key)


def decrypt_json(ciphertext, key=None):
    """解密为 Python 对象"""
    return json.loads(decrypt_text(ciphertext, key))
