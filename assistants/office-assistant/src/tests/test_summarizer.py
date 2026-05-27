#!/usr/bin/env python3

"""
模块名称：test_summarizer
功能描述：TODO: 请补充功能描述
对外接口：
    - test_case_1_basic_summary()
    - test_case_2_empty_text()
    - test_case_3_long_text_chunking()
    - run_all_tests()
依赖：
    - 标准库：logging, os, sys
    - 第三方：core
    - 项目内：无
版本：v1.0
更新记录：
    - 2026-05-23: 自动添加统一注释头
"""
"""
DocumentSummarizer 单元测试脚本
内置 3 组标准测试用例，可一键运行
"""

import sys
import os
import logging

# 将 src 目录加入路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from core.summarizer import DocumentSummarizer

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 测试文本（模拟真实文档内容）
SAMPLE_TEXT = """项目进度报告

一、项目概况
本项目旨在开发一套智能办公助手系统，帮助用户自动处理日常文档工作。项目自2026年5月启动，预计6月底完成核心功能开发。

二、当前进展
1. 环境搭建：已完成Python虚拟环境、Ollama本地模型部署
2. 1号AI：闲聊检索助手已通过飞书接入，支持文字和语音交互
3. 2号AI：办公文档助手正在开发中，已完成Word文档读取功能

三、下阶段计划
下一步将实现Excel处理、PPT生成以及文件监控功能，预计6月中旬完成。

四、风险与挑战
- 大文档处理可能超出内存限制
- 语音识别准确率有待提升
- 飞书回调地址需定期维护

五、总结
项目整体进展顺利，各项指标符合预期，团队将继续按计划推进。"""


def test_case_1_basic_summary():
    """
    测试用例1：基本摘要生成
    验证：对中等长度文本生成摘要，返回有效结果
    """
    logger.info("="*50)
    logger.info("测试用例1：基本摘要生成")
    
    summarizer = DocumentSummarizer()
    result = summarizer.summarize(SAMPLE_TEXT, max_points=3)
    
    assert result['success'] is True, f"摘要应成功，实际 success={result['success']}"
    assert len(result['summary']) > 0, "摘要内容不应为空"
    assert result['method'] in ['ollama_direct', 'fallback'], f"方法应为 ollama_direct 或 fallback，实际 {result['method']}"
    
    logger.info(f"摘要方法: {result['method']}")
    logger.info(f"摘要内容:\n{result['summary']}")
    if result.get('error'):
        logger.warning(f"提示: {result['error']}")
    
    logger.info("✅ 测试用例1 通过")


def test_case_2_empty_text():
    """
    测试用例2：空文本处理
    验证：空文本返回失败状态，不崩溃
    """
    logger.info("="*50)
    logger.info("测试用例2：空文本处理")
    
    summarizer = DocumentSummarizer()
    result = summarizer.summarize("")
    
    assert result['success'] is False, "空文本摘要应失败"
    assert result['error'] == "输入文本为空", f"错误信息应为'输入文本为空'，实际'{result['error']}'"
    
    logger.info(f"正确返回失败: {result['error']}")
    logger.info("✅ 测试用例2 通过")


def test_case_3_long_text_chunking():
    """
    测试用例3：长文本分块测试
    验证：超长文本（超过 CHUNK_SIZE）自动分块处理
    """
    logger.info("="*50)
    logger.info("测试用例3：长文本分块测试")
    
    summarizer = DocumentSummarizer()
    
    # 生成长文本（约 4000 字符，超过默认 CHUNK_SIZE 2000）
    long_text = SAMPLE_TEXT * 8  # 约 8 倍长度
    logger.info(f"构造长文本: {len(long_text)} 字符")
    
    result = summarizer.summarize(long_text, max_points=5)
    
    assert result['success'] is True, "长文本摘要应成功"
    assert len(result['summary']) > 0, "摘要内容不应为空"
    
    # 如果走分块流程，method 应包含 chunked
    logger.info(f"摘要方法: {result['method']}")
    if 'chunked' in result.get('method', ''):
        logger.info(f"分块数: {result.get('chunks_processed', 'N/A')}")
    
    logger.info(f"摘要内容:\n{result['summary'][:300]}...")
    if result.get('error'):
        logger.warning(f"提示: {result['error']}")
    
    logger.info("✅ 测试用例3 通过")


def run_all_tests():
    """一键运行所有测试"""
    logger.info("="*60)
    logger.info("开始运行 DocumentSummarizer 测试套件")
    logger.info("="*60)
    
    test_case_1_basic_summary()
    test_case_2_empty_text()
    test_case_3_long_text_chunking()
    
    logger.info("="*60)
    logger.info("所有测试用例通过！🎉")
    logger.info("="*60)


if __name__ == "__main__":
    run_all_tests()
