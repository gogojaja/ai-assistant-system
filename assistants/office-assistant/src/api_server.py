#!/usr/bin/env python3

"""
模块名称：api_server
功能描述：TODO: 请补充功能描述
对外接口：
    - health_check()
    - process_word()
    - _process_file()
依赖：
    - 标准库：logging, os, pathlib, sys, tempfile
    - 第三方：core, flask
    - 项目内：无
版本：v1.0
更新记录：
    - 2026-05-23: 自动添加统一注释头
"""
"""
2号AI - Flask API 服务
提供 /process_word 接口，接收文件路径并返回摘要
"""

import os
import sys
import tempfile
import logging
from pathlib import Path
from flask import Flask, request, jsonify

sys.path.insert(0, os.path.dirname(__file__))
from core.word_processor import WordProcessor
from core.summarizer import DocumentSummarizer

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("office_api")

# 创建 Flask 应用
app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 20 * 1024 * 1024  # 限制上传 20MB

# 初始化摘要器（全局单例，避免重复连接检查）
summarizer = DocumentSummarizer()


@app.route('/health', methods=['GET'])
def health_check():
    """健康检查接口"""
    return jsonify({
        "status": "ok",
        "service": "2号AI - 办公文档助理"
    })


@app.route('/process_word', methods=['POST'])
def process_word():
    """
    处理 Word 文档接口
    请求格式（JSON）：
    {
        "file_path": "/path/to/document.docx"  # 服务器本地文件路径
    }
    或者直接上传文件（multipart/form-data）：
        file: Word 文档
    返回：
    {
        "success": true,
        "summary": "摘要内容",
        "info": { ... 文件基本信息 ... },
        "error": null
    }
    """
    logger.info("收到 Word 处理请求")
    
    # 处理方式1：multipart 文件上传
    if 'file' in request.files:
        file = request.files['file']
        if file.filename == '':
            return jsonify({"success": False, "error": "未选择文件"}), 400
        
        # 保存为临时文件
        suffix = Path(file.filename).suffix.lower()
        if suffix != '.docx':
            return jsonify({"success": False, "error": f"不支持的文件格式: {suffix}"}), 400
        
        with tempfile.NamedTemporaryFile(suffix='.docx', delete=False) as f:
            temp_path = f.name
            file.save(temp_path)
        logger.info(f"上传文件已保存到: {temp_path}")
        
        try:
            result = _process_file(temp_path)
            return jsonify(result)
        finally:
            # 清理临时文件
            try:
                os.unlink(temp_path)
                logger.debug(f"已清理临时文件: {temp_path}")
            except Exception as e:
                logger.warning(f"清理临时文件失败: {e}")
    
    # 处理方式2：指定服务器文件路径（JSON格式）
    data = request.get_json(silent=True)
    if data and 'file_path' in data:
        file_path = data['file_path']
        logger.info(f"处理指定文件: {file_path}")
        result = _process_file(file_path)
        return jsonify(result)
    
    return jsonify({"success": False, "error": "请提供 file 或 file_path"}), 400


def _process_file(file_path: str) -> dict:
    """
    内部处理函数：提取内容 + 生成摘要
    :param file_path: Word 文档路径
    :return: 处理结果字典
    """
    try:
        # 提取文档内容
        wp = WordProcessor(file_path)
        summary_info = wp.get_summary_info()
        text = wp.extract_text()
        titles = wp.extract_titles()
        tables = wp.extract_tables()
        
        logger.info(f"文档 '{summary_info['file_name']}' 提取完成: {summary_info['character_count']} 字符")
        
        # 生成摘要
        summary_result = summarizer.summarize(text, max_points=5)
        
        return {
            "success": True,
            "summary": summary_result['summary'],
            "info": {
                "file_name": summary_info['file_name'],
                "paragraph_count": summary_info['paragraph_count'],
                "title_count": summary_info['title_count'],
                "table_count": summary_info['table_count'],
                "character_count": summary_info['character_count']
            },
            "titles": titles[:10],  # 前10个标题
            "summary_method": summary_result.get('method', 'unknown'),
            "error": summary_result.get('error')
        }
        
    except FileNotFoundError as e:
        logger.error(f"文件不存在: {e}")
        return {"success": False, "error": str(e)}
    except ValueError as e:
        logger.error(f"文件格式错误: {e}")
        return {"success": False, "error": str(e)}
    except Exception as e:
        logger.error(f"文档处理异常: {e}")
        return {"success": False, "error": f"处理失败: {str(e)}"}


if __name__ == '__main__':
    # 启动服务（独立运行时使用，一般由回调服务调用其函数，不单独占用端口）
    # 如需独立调试，可解除注释：
    # app.run(host='127.0.0.1', port=5002, debug=False)
    logger.info("2号AI API 模块已加载，请通过回调服务或直接调用函数")
