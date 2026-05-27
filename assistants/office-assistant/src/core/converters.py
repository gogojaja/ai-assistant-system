#!/usr/bin/env python3

"""
模块名称：converters
功能描述：文档格式转换模块，支持 .docx → .txt / .md
对外接口：
    - DocxConverter: Word 文档转换器
        - docx_to_text(file_path): 转纯文本
        - docx_to_markdown(file_path): 转 Markdown
        - docx_to_markdown_safe(file_path): 安全转换（不抛异常）
        - validate_file(file_path): 校验文件
依赖：
    - 标准库：logging, pathlib
    - 第三方：mammoth
    - 项目内：无
版本：v1.0
更新记录：
    - 2026-05-26: 补充标准模块头模板
"""

import logging
from pathlib import Path
from typing import Optional
import mammoth

logger = logging.getLogger("DocConverter")
logger.setLevel(logging.DEBUG)

# 确保控制台输出
if not logger.handlers:
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)


class DocxConverter:
    """Word 文档转换器"""
    
    @staticmethod
    def validate_file(file_path: str) -> Path:
        """校验文件存在且为 .docx"""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"文件不存在: {path}")
        if path.suffix.lower() != '.docx':
            raise ValueError(f"不支持的文件格式: {path.suffix}，仅支持 .docx")
        return path
    
    @staticmethod
    def docx_to_text(file_path: str) -> str:
        """
        将 .docx 转换为纯文本
        :param file_path: 输入 .docx 路径
        :return: 提取的纯文本字符串
        """
        path = DocxConverter.validate_file(file_path)
        try:
            with open(path, 'rb') as f:
                result = mammoth.extract_raw_text(f)
            logger.info(f"成功转换为 TXT: {path.name} ({len(result.value)} 字符)")
            if result.messages:
                for msg in result.messages:
                    logger.warning(f"转换提示: {msg}")
            return result.value
        except Exception as e:
            logger.error(f"转换为 TXT 失败: {e}")
            raise
    
    @staticmethod
    def docx_to_markdown(file_path: str) -> str:
        """
        将 .docx 转换为 Markdown，保留标题、列表、表格等格式
        :param file_path: 输入 .docx 路径
        :return: Markdown 文本
        """
        path = DocxConverter.validate_file(file_path)
        try:
            with open(path, 'rb') as f:
                result = mammoth.convert_to_markdown(f)
            logger.info(f"成功转换为 Markdown: {path.name} ({len(result.value)} 字符)")
            if result.messages:
                for msg in result.messages:
                    logger.warning(f"转换提示: {msg}")
            return result.value
        except Exception as e:
            logger.error(f"转换为 Markdown 失败: {e}")
            raise
    
    @staticmethod
    def docx_to_markdown_safe(file_path: str) -> dict:
        """
        安全转换 Markdown，失败时返回错误字典，不抛异常
        :return: {"success": bool, "content": str, "error": str}
        """
        try:
            content = DocxConverter.docx_to_markdown(file_path)
            return {"success": True, "content": content, "error": None}
        except Exception as e:
            logger.error(f"转换失败: {e}")
            return {"success": False, "content": "", "error": str(e)}


# 命令行入口
if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        print("用法：python converters.py <输入.docx> <输出格式: txt|md>")
        sys.exit(1)
    
    input_path = sys.argv[1]
    output_format = sys.argv[2].lower()
    
    converter = DocxConverter()
    
    if output_format == 'txt':
        text = converter.docx_to_text(input_path)
        print(text)
        # 可选保存
        output_path = Path(input_path).with_suffix('.txt')
        output_path.write_text(text, encoding='utf-8')
        print(f"\n✅ 已保存 TXT: {output_path}")
    elif output_format in ('md', 'markdown'):
        md = converter.docx_to_markdown(input_path)
        print(md)
        output_path = Path(input_path).with_suffix('.md')
        output_path.write_text(md, encoding='utf-8')
        print(f"\n✅ 已保存 Markdown: {output_path}")
    else:
        print("不支持的目标格式，请使用 txt 或 md")
