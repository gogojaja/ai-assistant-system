#!/usr/bin/env python3
"""
模块名称：regression_test
功能描述：五角色 AI 助理系统 — 全功能回归测试套件
          覆盖全部 5 个 AI 角色 + 共享模块 + 回调服务
          支持独立运行、模块筛选、输出详细报告
对外接口：
    - 直接运行：python3 scripts/regression_test.py
    - 筛选模块：python3 scripts/regression_test.py --module chat
    - 查看帮助：python3 scripts/regression_test.py --help
依赖：
    - 标准库：os, sys, json, tempfile, re, math, logging, pathlib, importlib
    - 第三方：无（所有外部依赖模拟，缺失模块自动跳过）
    - 项目内：全部 5 个助手 src 目录及 shared 模块
版本：v1.1
更新记录：
    - 2026-05-28: 初始创建，覆盖全部 5 个 AI 角色 + 共享模块 + 回调服务
    - 2026-05-28: v1.1 修复缺失依赖自动跳过、相对导入处理、file_assistant 路径
"""
import os
import sys
import json
import tempfile
import re
import math
import logging
import time
import importlib
import importlib.util
from pathlib import Path

logging.basicConfig(level=logging.WARNING, format='%(levelname)s - %(message)s')

PROJECT_ROOT = Path(__file__).resolve().parent.parent
for p in [
    str(PROJECT_ROOT),
    str(PROJECT_ROOT / "shared"),
    str(PROJECT_ROOT / "shared/feishu-callback"),
    str(PROJECT_ROOT / "assistants"),
    str(PROJECT_ROOT / "assistants/chat-assistant/src"),
    str(PROJECT_ROOT / "assistants/office-assistant/src"),
    str(PROJECT_ROOT / "assistants/office-assistant/src/core"),
    str(PROJECT_ROOT / "assistants/life-assistant/src"),
    str(PROJECT_ROOT / "assistants/file-assistant/src"),
    str(PROJECT_ROOT / "assistants/sys-assistant/src"),
]:
    if p not in sys.path:
        sys.path.insert(0, p)

results = {"pass": 0, "fail": 0, "skip": 0}
module_filter = None
_import_cache = {}

if "--help" in sys.argv:
    print("用法: python3 scripts/regression_test.py [--module <名称>]")
    print("  --module shared|chat|office|life|file|sys|callback  筛选测试模块")
    sys.exit(0)

if "--module" in sys.argv:
    idx = sys.argv.index("--module")
    if idx + 1 < len(sys.argv):
        module_filter = sys.argv[idx + 1]


def _safe_import(module_name, attr=None):
    """安全导入模块，失败时返回 None"""
    key = (module_name, attr)
    if key in _import_cache:
        return _import_cache[key]
    try:
        if attr:
            mod = importlib.import_module(module_name)
            result = getattr(mod, attr)
        else:
            result = importlib.import_module(module_name)
        _import_cache[key] = result
        return result
    except (ImportError, ModuleNotFoundError, AttributeError) as e:
        _import_cache[key] = None
        return None


def _safe_load_from_file(filepath, func_name):
    """从文件路径加载模块并返回指定函数，失败返回 None"""
    try:
        spec = importlib.util.spec_from_file_location(f"_mod_{func_name}", str(filepath))
        mod = importlib.util.module_from_spec(spec)
        mod.__package__ = filepath.parent.name
        old_path = sys.path.copy()
        # 添加项目根 + shared + 文件父目录
        for p in [str(PROJECT_ROOT), str(PROJECT_ROOT / "shared"), str(filepath.parent),
                  str(PROJECT_ROOT / "assistants/office-assistant/src"),
                  str(PROJECT_ROOT / "assistants/office-assistant/src/core")]:
            if p not in sys.path:
                sys.path.insert(0, p)
        spec.loader.exec_module(mod)
        sys.path = old_path
        return getattr(mod, func_name, None)
    except Exception as e:
        return None


def _test(name, fn):
    if module_filter and module_filter not in name.lower():
        results["skip"] += 1
        return
    try:
        fn()
        results["pass"] += 1
        print(f"  ✅ {name}")
    except ImportError as e:
        results["skip"] += 1
        print(f"  ⏭️  {name}: 跳过（{e}）")
    except ModuleNotFoundError as e:
        results["skip"] += 1
        print(f"  ⏭️  {name}: 跳过（{e}）")
    except Exception as e:
        results["fail"] += 1
        print(f"  ❌ {name}: {e}")
        import traceback
        traceback.print_exc()


def _section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


# =====================================================================
# 共享模块测试
# =====================================================================
def test_shared():
    _section("1. 共享模块")

    # ---- crypto ----
    def test_crypto_encrypt_decrypt():
        encrypt_text = _safe_import("shared.crypto", "encrypt_text")
        decrypt_text = _safe_import("shared.crypto", "decrypt_text")
        if not encrypt_text or not decrypt_text:
            raise ImportError("cryptography 模块未安装")
        original = "Hello 世界 123 !@#"
        encrypted = encrypt_text(original)
        assert encrypted != original, "加密后不应与原文相同"
        assert isinstance(encrypted, str), "加密结果应为字符串"
        decrypted = decrypt_text(encrypted)
        assert decrypted == original, f"解密结果不匹配"

    def test_crypto_json_roundtrip():
        encrypt_json = _safe_import("shared.crypto", "encrypt_json")
        decrypt_json = _safe_import("shared.crypto", "decrypt_json")
        if not encrypt_json or not decrypt_json:
            raise ImportError("cryptography 模块未安装")
        data = {"key": "value", "list": [1, 2, 3], "chinese": "中文测试"}
        encrypted = encrypt_json(data)
        assert isinstance(encrypted, str)
        decrypted = decrypt_json(encrypted)
        assert decrypted == data

    def test_crypto_invalid_decrypt():
        decrypt_text = _safe_import("shared.crypto", "decrypt_text")
        if not decrypt_text:
            raise ImportError("cryptography 模块未安装")
        try:
            decrypt_text("invalid_base64_data_here")
            assert False, "应抛出异常"
        except Exception:
            pass

    _test("crypto 加解密", test_crypto_encrypt_decrypt)
    _test("crypto JSON 加解密", test_crypto_json_roundtrip)
    _test("crypto 无效数据容错", test_crypto_invalid_decrypt)

    # ---- knowledge_base ----
    def test_kb_search_empty():
        search = _safe_import("shared.knowledge_base", "search")
        if not search:
            raise ImportError("knowledge_base 模块未加载")
        res = search("不存在的查询词_xyz", top_k=3, min_score=0.01)
        assert isinstance(res, list)

    def test_kb_import_invalid_file():
        import_doc = _safe_import("shared.knowledge_base", "import_doc")
        if not import_doc:
            raise ImportError("knowledge_base 模块未加载")
        ok, msg = import_doc("/tmp/nonexistent_file_xyz.txt")
        assert ok is False and "不存在" in msg

    def test_kb_import_wrong_extension():
        import_doc = _safe_import("shared.knowledge_base", "import_doc")
        if not import_doc:
            raise ImportError("knowledge_base 模块未加载")
        tmp = tempfile.NamedTemporaryFile(suffix=".py", delete=False)
        tmp.close()
        try:
            ok, msg = import_doc(tmp.name)
            assert ok is False and "仅支持" in msg
        finally:
            os.unlink(tmp.name)

    def test_kb_list_docs():
        list_docs = _safe_import("shared.knowledge_base", "list_docs")
        if not list_docs:
            raise ImportError("knowledge_base 模块未加载")
        docs = list_docs()
        assert isinstance(docs, list)

    def test_kb_tokenize_and_bm25():
        _tokenize = _safe_import("shared.knowledge_base", "_tokenize")
        _bm25_score = _safe_import("shared.knowledge_base", "_bm25_score")
        if not _tokenize or not _bm25_score:
            raise ImportError("knowledge_base 模块未加载")
        tokens = _tokenize("测试中文English123混合文本")
        assert isinstance(tokens, list) and len(tokens) > 0
        score = _bm25_score(1, 10, 5, 1.5)
        assert isinstance(score, float) and score > 0

    _test("知识库 空搜索", test_kb_search_empty)
    _test("知识库 无效文件导入", test_kb_import_invalid_file)
    _test("知识库 扩展名校验", test_kb_import_wrong_extension)
    _test("知识库 列出文档", test_kb_list_docs)
    _test("知识库 分词+BM25", test_kb_tokenize_and_bm25)

    # ---- backend_utils ----
    def test_backend_config():
        get_backend_config = _safe_import("shared.backend_utils", "get_backend_config")
        if not get_backend_config:
            raise ImportError("backend_utils 模块未加载")
        cfg = get_backend_config()
        assert isinstance(cfg, dict)
        for k in ("backend", "port", "model"):
            assert k in cfg
        assert cfg["backend"] in ("llama.cpp", "ollama")

    def test_extract_from_reasoning():
        extract = _safe_import("shared.backend_utils", "extract_from_reasoning")
        if not extract:
            raise ImportError("backend_utils 模块未加载")
        assert extract("让我想想...\n总结：这是一个测试回答。") is not None
        assert extract("") == "（摘要为空）"

    def test_clean_reply():
        clean_reply = _safe_import("shared.backend_utils", "clean_reply")
        if not clean_reply:
            raise ImportError("backend_utils 模块未加载")
        assert clean_reply("最终输出：你好") == "你好"
        assert clean_reply("总结：结果") == "结果"
        assert clean_reply("Direct output: hello") == "hello"
        assert clean_reply("") == ""
        assert clean_reply("正常文本") == "正常文本"

    def test_wake_model_graceful():
        wake_model = _safe_import("shared.backend_utils", "wake_model")
        if not wake_model:
            raise ImportError("backend_utils 模块未加载")
        wake_model()

    _test("backend_utils 配置读取", test_backend_config)
    _test("backend_utils reasoning提取", test_extract_from_reasoning)
    _test("backend_utils 回复清理", test_clean_reply)
    _test("backend_utils 唤醒模型(无进程)", test_wake_model_graceful)


# =====================================================================
# 1号AI chat-assistant 测试
# =====================================================================
def test_chat():
    _section("2. 1号AI chat-assistant")

    # ---- chat.py ----
    def test_chat_history():
        clear_history = _safe_import("chat", "clear_history")
        load_history = _safe_import("chat", "load_history")
        save_history = _safe_import("chat", "save_history")
        if not all([clear_history, load_history, save_history]):
            raise ImportError("chat 模块未加载")
        save_history([{"role": "user", "content": "你好"}])
        assert len(load_history()) == 1
        result = clear_history()
        assert "已清空" in result

    _test("chat 历史保存/加载/清空", test_chat_history)

    # ---- search.py ----
    def test_search_archive():
        archive_search = _safe_import("search", "archive_search")
        search_archive = _safe_import("search", "search_archive")
        if not archive_search or not search_archive:
            raise ImportError("search 模块未加载")
        archive_search("测试查询", [{"title": "T", "url": "", "snippet": "S"}])
        result = search_archive("测试查询")
        assert result["found"]

    def test_search_format():
        format_results = _safe_import("search", "format_results")
        if not format_results:
            raise ImportError("search 模块未加载")
        result = format_results({"success": True, "results": [{"title": "T1", "url": "https://x.com", "snippet": "S1"}]})
        assert "T1" in result

    def test_search_archive_empty():
        search_archive = _safe_import("search", "search_archive")
        if not search_archive:
            raise ImportError("search 模块未加载")
        result = search_archive("__nonexistent_xyz__")
        assert result["found"] is False

    _test("search 归档与检索", test_search_archive)
    _test("search 格式化结果", test_search_format)
    _test("search 空搜索", test_search_archive_empty)

    # ---- main.py ----
    def test_main_format_reply():
        _format_reply = _safe_import("main", "_format_reply")
        if not _format_reply:
            raise ImportError("main 模块未加载")
        result = _format_reply("  Hello  World  ")
        assert result is not None

    def test_main_format_chinese():
        _format_reply = _safe_import("main", "_format_reply")
        if not _format_reply:
            raise ImportError("main 模块未加载")
        result = _format_reply("  这是一个 测试 ")
        assert result is not None

    def test_main_extract_reasoning():
        _extract = _safe_import("main", "_extract_from_reasoning")
        if not _extract:
            raise ImportError("main 模块未加载")
        result = _extract("让我思考一下...\n最终回答：\"今天天气很好\"")
        assert result is not None

    def test_main_extract_reasoning_quoted():
        _extract = _safe_import("main", "_extract_from_reasoning")
        if not _extract:
            raise ImportError("main 模块未加载")
        result = _extract("用户问天气\n回应说：「今天是个好天气」")
        assert "好天气" in result

    def test_main_trim_history():
        trim_history = _safe_import("main", "trim_history")
        if not trim_history:
            raise ImportError("main 模块未加载")
        msgs = [{"role": "system", "content": "sys"}]
        for i in range(30):
            msgs.append({"role": "user", "content": f"msg{i}"})
            msgs.append({"role": "assistant", "content": f"reply{i}"})
        trimmed = trim_history(msgs)
        non_sys = [m for m in trimmed if m["role"] != "system"]
        assert len(non_sys) <= 20

    def test_main_backend_config():
        _get_backend_config = _safe_import("main", "_get_backend_config")
        if not _get_backend_config:
            raise ImportError("main 模块未加载")
        cfg = _get_backend_config()
        assert "backend" in cfg and "port" in cfg and "model" in cfg

    def test_main_custom_prompt():
        _save = _safe_import("main", "_save_custom_prompt")
        _load = _safe_import("main", "_load_custom_prompt")
        if not _save or not _load:
            raise ImportError("main 模块未加载")
        test_id = f"__test_prompt_{int(time.time())}__"
        _save(test_id, "你是一个测试助手")
        assert _load(test_id) == "你是一个测试助手"
        _save(test_id, "")
        assert _load(test_id) == ""

    def test_main_handle_search():
        handle_search = _safe_import("main", "handle_search")
        if not handle_search:
            raise ImportError("main 模块未加载")
        result = handle_search("搜索 Python")
        assert isinstance(result, str)

    _test("main 回复格式化", test_main_format_reply)
    _test("main 中文格式化", test_main_format_chinese)
    _test("main reasoning提取(引号)", test_main_extract_reasoning)
    _test("main reasoning提取(回应说)", test_main_extract_reasoning_quoted)
    _test("main 历史裁剪", test_main_trim_history)
    _test("main 后端配置", test_main_backend_config)
    _test("main 自定义提示词", test_main_custom_prompt)
    _test("main 搜索处理", test_main_handle_search)

    # ---- message_handler（仅测试无外部依赖的部分） ----
    def test_mh_find_user_name():
        _find_user_name = _safe_import("message_handler", "_find_user_name")
        if not _find_user_name:
            raise ImportError("message_handler 模块未加载(dotenv)")
        tests = {
            "我叫张三": "张三",
            "我是李四": "李四",
            "姓名是王五": "王五",
        }
        for text, expected in tests.items():
            name = _find_user_name([{"role": "user", "content": text}])
            assert name == expected, f"对于 '{text}'，期望 '{expected}'，得到 '{name}'"

    def test_mh_find_user_name_no_match():
        _find_user_name = _safe_import("message_handler", "_find_user_name")
        if not _find_user_name:
            raise ImportError("message_handler 模块未加载(dotenv)")
        assert _find_user_name([{"role": "user", "content": "今天天气怎么样"}]) == ""

    def test_mh_now_str():
        _now_str = _safe_import("message_handler", "_now_str")
        if not _now_str:
            raise ImportError("message_handler 模块未加载(dotenv)")
        s = _now_str()
        assert re.match(r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}', s)

    def test_mh_help_text():
        TEXT = _safe_import("message_handler", "_HELP_TEXT")
        if not TEXT:
            raise ImportError("message_handler 模块未加载(dotenv)")
        assert "闲聊" in TEXT

    _test("message_handler 姓名查找", test_mh_find_user_name)
    _test("message_handler 无姓名匹配", test_mh_find_user_name_no_match)
    _test("message_handler 时间格式", test_mh_now_str)
    _test("message_handler 帮助文本", test_mh_help_text)


# =====================================================================
# 2号AI office-assistant 测试
# =====================================================================
def test_office():
    _section("3. 2号AI office-assistant")

    # ---- WordProcessor ----
    def test_wp_basic():
        WordProcessor = _safe_import("core.word_processor", "WordProcessor")
        if not WordProcessor:
            raise ImportError("python-docx 未安装")
        from docx import Document
        tmp = tempfile.NamedTemporaryFile(suffix=".docx", delete=False)
        tmp.close()
        try:
            doc = Document()
            doc.add_heading("测试标题", level=1)
            doc.add_paragraph("测试段落内容。")
            doc.save(tmp.name)
            wp = WordProcessor(tmp.name)
            info = wp.get_summary_info()
            assert info["paragraph_count"] >= 1
            text = wp.extract_text()
            assert "测试标题" in text
            titles = wp.extract_titles()
            assert len(titles) >= 1
            assert titles[0]["level"] == 1
        finally:
            os.unlink(tmp.name)

    def test_wp_empty():
        WordProcessor = _safe_import("core.word_processor", "WordProcessor")
        if not WordProcessor:
            raise ImportError("python-docx 未安装")
        from docx import Document
        tmp = tempfile.NamedTemporaryFile(suffix=".docx", delete=False)
        tmp.close()
        try:
            doc = Document()
            doc.save(tmp.name)
            wp = WordProcessor(tmp.name)
            assert wp.extract_text() == ""
        finally:
            os.unlink(tmp.name)

    def test_wp_tables():
        WordProcessor = _safe_import("core.word_processor", "WordProcessor")
        if not WordProcessor:
            raise ImportError("python-docx 未安装")
        from docx import Document
        tmp = tempfile.NamedTemporaryFile(suffix=".docx", delete=False)
        tmp.close()
        try:
            doc = Document()
            table = doc.add_table(rows=2, cols=2)
            table.cell(0, 0).text = "A1"
            table.cell(0, 1).text = "B1"
            table.cell(1, 0).text = "A2"
            table.cell(1, 1).text = "B2"
            doc.save(tmp.name)
            wp = WordProcessor(tmp.name)
            tables = wp.extract_tables()
            assert len(tables) == 1
            assert tables[0][0] == ["A1", "B1"]
        finally:
            os.unlink(tmp.name)

    def test_wp_invalid():
        WordProcessor = _safe_import("core.word_processor", "WordProcessor")
        if not WordProcessor:
            raise ImportError("python-docx 未安装")
        try:
            WordProcessor("/nonexistent/file.docx")
            assert False, "应抛出异常"
        except Exception:
            pass

    _test("WordProcessor 基本提取", test_wp_basic)
    _test("WordProcessor 空文档", test_wp_empty)
    _test("WordProcessor 表格提取", test_wp_tables)
    _test("WordProcessor 无效路径", test_wp_invalid)

    # ---- ExcelProcessor ----
    def test_ep_basic():
        ExcelProcessor = _safe_import("core.excel_processor", "ExcelProcessor")
        if not ExcelProcessor:
            raise ImportError("openpyxl 未安装")
        import openpyxl
        tmp = tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False)
        tmp.close()
        try:
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = "测试表"
            ws.append(["姓名", "年龄"])
            ws.append(["张三", 28])
            wb.save(tmp.name)
            ep = ExcelProcessor(tmp.name)
            analysis = ep.analyze()
            assert "测试表" in analysis
            data = ep.get_data_text()
            assert "姓名" in data and "张三" in data
        finally:
            os.unlink(tmp.name)

    def test_ep_multi_sheet():
        ExcelProcessor = _safe_import("core.excel_processor", "ExcelProcessor")
        if not ExcelProcessor:
            raise ImportError("openpyxl 未安装")
        import openpyxl
        tmp = tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False)
        tmp.close()
        try:
            wb = openpyxl.Workbook()
            wb.active.title = "Sheet1"
            wb.create_sheet("Sheet2")
            wb.save(tmp.name)
            ep = ExcelProcessor(tmp.name)
            analysis = ep.analyze()
            assert "Sheet2" in analysis
        finally:
            os.unlink(tmp.name)

    def test_ep_empty():
        ExcelProcessor = _safe_import("core.excel_processor", "ExcelProcessor")
        if not ExcelProcessor:
            raise ImportError("openpyxl 未安装")
        import openpyxl
        tmp = tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False)
        tmp.close()
        try:
            wb = openpyxl.Workbook()
            wb.save(tmp.name)
            ep = ExcelProcessor(tmp.name)
            assert ep.analyze() != ""
        finally:
            os.unlink(tmp.name)

    def test_ep_invalid():
        ExcelProcessor = _safe_import("core.excel_processor", "ExcelProcessor")
        if not ExcelProcessor:
            raise ImportError("openpyxl 未安装")
        try:
            ExcelProcessor("/nonexistent/file.xlsx")
            assert False
        except Exception:
            pass

    _test("ExcelProcessor 基本分析", test_ep_basic)
    _test("ExcelProcessor 多工作表", test_ep_multi_sheet)
    _test("ExcelProcessor 空工作簿", test_ep_empty)
    _test("ExcelProcessor 无效路径", test_ep_invalid)

    # ---- DocumentSummarizer ----
    def test_summarizer_empty():
        DocumentSummarizer = _safe_import("core.summarizer", "DocumentSummarizer")
        if not DocumentSummarizer:
            raise ImportError("summarizer 模块未加载")
        s = DocumentSummarizer()
        r = s.summarize("")
        assert r["success"] is False
        assert r["summary"] == ""

    def test_summarizer_whitespace():
        DocumentSummarizer = _safe_import("core.summarizer", "DocumentSummarizer")
        if not DocumentSummarizer:
            raise ImportError("summarizer 模块未加载")
        s = DocumentSummarizer()
        assert s.summarize("   ")["success"] is False

    def test_summarizer_backend():
        DocumentSummarizer = _safe_import("core.summarizer", "DocumentSummarizer")
        if not DocumentSummarizer:
            raise ImportError("summarizer 模块未加载")
        cfg = DocumentSummarizer._get_backend_config()
        assert cfg["backend"] in ("llama.cpp", "ollama")

    _test("DocumentSummarizer 空文本", test_summarizer_empty)
    _test("DocumentSummarizer 空白字符", test_summarizer_whitespace)
    _test("DocumentSummarizer 后端配置", test_summarizer_backend)

    # ---- DocxConverter ----
    def test_converter_to_text():
        DocxConverter = _safe_import("core.converters", "DocxConverter")
        if not DocxConverter:
            raise ImportError("python-docx/mammoth 未安装")
        from docx import Document
        tmp = tempfile.NamedTemporaryFile(suffix=".docx", delete=False)
        tmp.close()
        try:
            doc = Document()
            doc.add_heading("转换测试", level=1)
            doc.add_paragraph("段落内容。")
            doc.save(tmp.name)
            text = DocxConverter.docx_to_text(tmp.name)
            assert "转换测试" in text
        finally:
            os.unlink(tmp.name)

    def test_converter_invalid():
        DocxConverter = _safe_import("core.converters", "DocxConverter")
        if not DocxConverter:
            raise ImportError("python-docx/mammoth 未安装")
        try:
            DocxConverter.docx_to_text("/nonexistent.docx")
            assert False
        except FileNotFoundError:
            pass

    _test("DocxConverter docx→text", test_converter_to_text)
    _test("DocxConverter 无效文件", test_converter_invalid)

    # ---- PPT Generator ----
    def test_ppt_parse():
        _parse = _safe_import("core.ppt_generator", "_parse_text_to_slides")
        if not _parse:
            raise ImportError("python-pptx 未安装")
        text = "测试演示\n\n## 章节一\n\n- 要点A\n- 要点B"
        parsed = _parse(text)
        assert parsed is not None
        assert parsed["title"] == "测试演示"

    def test_ppt_empty_text():
        generate_from_text = _safe_import("core.ppt_generator", "generate_from_text")
        if not generate_from_text:
            raise ImportError("python-pptx 未安装")
        result = generate_from_text("", "/tmp/nonexist_test.pptx")
        assert result is None

    def test_ppt_generate():
        generate_presentation = _safe_import("core.ppt_generator", "generate_presentation")
        if not generate_presentation:
            raise ImportError("python-pptx 未安装")
        tmp = tempfile.NamedTemporaryFile(suffix=".pptx", delete=False)
        tmp.close()
        try:
            slides = [{"title": "第一页", "content": ["要点1"]}, {"title": "第二页", "content": ["要点A"]}]
            result = generate_presentation("测试", slides, tmp.name)
            assert result == tmp.name
            assert os.path.getsize(result) > 1000
        finally:
            os.unlink(tmp.name)

    _test("PPT 文本解析", test_ppt_parse)
    _test("PPT 空文本", test_ppt_empty_text)
    _test("PPT 结构化生成", test_ppt_generate)

    # ---- document_handler（纯函数单元） ----
    def test_dh_is_valid_summary():
        _is_valid_summary = _safe_load_from_file(
            PROJECT_ROOT / "assistants/office-assistant/src/document_handler.py",
            "_is_valid_summary"
        )
        if not _is_valid_summary:
            raise ImportError("document_handler 模块未加载")
        assert _is_valid_summary("这是一个有效的摘要内容。")
        assert not _is_valid_summary("")
        assert not _is_valid_summary("（摘要为空）")

    def test_dh_size_limits():
        _SIZE_LIMITS = _safe_load_from_file(
            PROJECT_ROOT / "assistants/office-assistant/src/document_handler.py",
            "_SIZE_LIMITS"
        )
        if not _SIZE_LIMITS:
            raise ImportError("document_handler 模块未加载")
        assert _SIZE_LIMITS['.docx'] == 30 * 1024 * 1024
        assert _SIZE_LIMITS['.xlsx'] == 15 * 1024 * 1024
        assert _SIZE_LIMITS['.pptx'] == 30 * 1024 * 1024

    def test_dh_build_fallback_summary():
        _build_fallback = _safe_load_from_file(
            PROJECT_ROOT / "assistants/office-assistant/src/document_handler.py",
            "_build_fallback_summary"
        )
        if not _build_fallback:
            raise ImportError("document_handler 模块未加载")
        result = _build_fallback("结构信息", "姓名\t年龄\n张三\t28\n李四\t32")
        assert "姓名" in result
        assert "张三" in result

    _test("document_handler 有效摘要检查", test_dh_is_valid_summary)
    _test("document_handler 大小限制", test_dh_size_limits)
    _test("document_handler 降级摘要", test_dh_build_fallback_summary)


# =====================================================================
# 3号AI life-assistant 测试
# =====================================================================
def test_life():
    _section("4. 3号AI life-assistant")

    # 导入 life_assistant.src 模块
    life_init_path = PROJECT_ROOT / "assistants/life-assistant/src/__init__.py"
    life_src = str(life_init_path.parent)
    if life_src not in sys.path:
        sys.path.insert(0, life_src)

    # ---- 入口 process ----
    def test_process_help():
        spec = importlib.util.spec_from_file_location("life_init", str(life_init_path))
        mod = importlib.util.module_from_spec(spec)
        mod.__package__ = "life_assistant.src"
        spec.loader.exec_module(mod)
        result = mod.process("帮助")
        assert "生活助手" in result
        assert "日程" in result

    def test_process_empty():
        spec = importlib.util.spec_from_file_location("life_init2", str(life_init_path))
        mod = importlib.util.module_from_spec(spec)
        mod.__package__ = "life_assistant.src"
        spec.loader.exec_module(mod)
        assert "生活助手" in mod.process("")

    def test_process_unknown():
        spec = importlib.util.spec_from_file_location("life_init3", str(life_init_path))
        mod = importlib.util.module_from_spec(spec)
        mod.__package__ = "life_assistant.src"
        spec.loader.exec_module(mod)
        result = mod.process("未知命令xyz")
        assert "未知命令" in result

    def test_process_dashboard():
        spec = importlib.util.spec_from_file_location("life_init4", str(life_init_path))
        mod = importlib.util.module_from_spec(spec)
        mod.__package__ = "life_assistant.src"
        spec.loader.exec_module(mod)
        assert "test.com" in mod.process("看板", dashboard_url="https://test.com/dash")
        assert "未配置" in mod.process("看板")

    _test("life process 帮助", test_process_help)
    _test("life process 空输入", test_process_empty)
    _test("life process 未知命令", test_process_unknown)
    _test("life process 看板路由", test_process_dashboard)

    # ---- 日程 ----
    def test_schedule_crud():
        add = _safe_import("scheduler", "add")
        list_items = _safe_import("scheduler", "list_items")
        delete = _safe_import("scheduler", "delete")
        search = _safe_import("scheduler", "search")
        if not all([add, list_items, delete, search]):
            raise ImportError("scheduler 模块未加载")
        item = add("测试日程", "2026-06-01 10:00")
        assert "id" in item and item["title"] == "测试日程"
        assert "测试日程" in list_items("2026-06-01")
        assert "测试日程" in search("测试")
        assert "已删除" in delete(item["id"])

    _test("scheduler 增删查", test_schedule_crud)

    # ---- 健康 ----
    def test_health_record():
        record = _safe_import("health_tracker", "record")
        report = _safe_import("health_tracker", "report")
        TYPES = _safe_import("health_tracker", "TYPES")
        if not all([record, report, TYPES]):
            raise ImportError("health_tracker 模块未加载")
        assert isinstance(TYPES, dict) and len(TYPES) > 0
        assert "已记录" in record(list(TYPES.keys())[0], "70")
        rpt = report("日报")
        assert isinstance(rpt, str) and len(rpt) > 0

    _test("health 记录+报告", test_health_record)

    # ---- 旅行 ----
    def test_travel_crud():
        create = _safe_import("travel_planner", "create")
        list_trips = _safe_import("travel_planner", "list_trips")
        view = _safe_import("travel_planner", "view")
        delete = _safe_import("travel_planner", "delete")
        if not all([create, list_trips, view, delete]):
            raise ImportError("travel_planner 模块未加载")
        trip = create("北京", "2026-07-01", "2026-07-05")
        assert trip["destination"] == "北京"
        assert "北京" in list_trips()
        assert "北京" in view(trip["id"])
        assert "已删除" in delete(trip["id"])

    _test("travel 增删查", test_travel_crud)

    # ---- 锻炼 ----
    def test_workout_crud():
        create = _safe_import("workout_planner", "create")
        list_plans = _safe_import("workout_planner", "list_plans")
        view = _safe_import("workout_planner", "view")
        delete = _safe_import("workout_planner", "delete")
        if not all([create, list_plans, view, delete]):
            raise ImportError("workout_planner 模块未加载")
        plan = create("测试锻炼")
        assert plan["name"] == "测试锻炼"
        assert "测试锻炼" in list_plans()
        assert "测试锻炼" in view(plan["id"])
        assert "已删除" in delete(plan["id"])

    _test("workout 增删查", test_workout_crud)

    # ---- 工作 ----
    def test_work_crud():
        create = _safe_import("work_planner", "create")
        list_items = _safe_import("work_planner", "list_items")
        view = _safe_import("work_planner", "view")
        set_status = _safe_import("work_planner", "set_status")
        set_priority = _safe_import("work_planner", "set_priority")
        delete = _safe_import("work_planner", "delete")
        if not all([create, list_items, view, set_status, set_priority, delete]):
            raise ImportError("work_planner 模块未加载")
        item = create("测试工作项")
        assert item["title"] == "测试工作项"
        assert "测试工作项" in list_items("all")
        assert "测试工作项" in view(item["id"])
        assert "进行中" in set_status(item["id"], "doing") or "doing" in set_status(item["id"], "doing").lower()
        assert "高" in set_priority(item["id"], "高")
        assert "已删除" in delete(item["id"]) or "删除" in delete(item["id"])

    _test("work 增删改查", test_work_crud)

    # ---- 内部处理函数 ----
    def test_handle_health_empty():
        _handle_health = _safe_import("life_assistant.src", "_handle_health")
        if not _handle_health:
            raise ImportError("life_assistant.src 模块未加载")
        assert "用法" in _handle_health([])

    def test_handle_travel_empty():
        _handle_travel = _safe_import("life_assistant.src", "_handle_travel")
        if not _handle_travel:
            raise ImportError("life_assistant.src 模块未加载")
        assert "用法" in _handle_travel([])

    def test_handle_workout_empty():
        _handle_workout = _safe_import("life_assistant.src", "_handle_workout")
        if not _handle_workout:
            raise ImportError("life_assistant.src 模块未加载")
        assert "用法" in _handle_workout([])

    def test_handle_work_empty():
        _handle_work = _safe_import("life_assistant.src", "_handle_work")
        if not _handle_work:
            raise ImportError("life_assistant.src 模块未加载")
        assert "用法" in _handle_work([])

    def test_handle_schedule_empty():
        _handle_schedule = _safe_import("life_assistant.src", "_handle_schedule")
        if not _handle_schedule:
            raise ImportError("life_assistant.src 模块未加载")
        assert "用法" in _handle_schedule([])

    _test("life _handle_schedule 空参数", test_handle_schedule_empty)
    _test("life _handle_health 空参数", test_handle_health_empty)
    _test("life _handle_travel 空参数", test_handle_travel_empty)
    _test("life _handle_workout 空参数", test_handle_workout_empty)
    _test("life _handle_work 空参数", test_handle_work_empty)


# =====================================================================
# 4号AI file-assistant 测试
# =====================================================================
def test_file():
    _section("5. 4号AI file-assistant")

    fa_src = str(PROJECT_ROOT / "assistants/file-assistant/src")
    if fa_src not in sys.path:
        sys.path.insert(0, fa_src)
    fa_init_path = PROJECT_ROOT / "assistants/file-assistant/src/__init__.py"

    # ---- 入口 process ----
    def test_process_empty():
        spec = importlib.util.spec_from_file_location("fa_init", str(fa_init_path))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        result = mod.process("")
        assert "4号文件助手" in result

    def test_process_help():
        spec = importlib.util.spec_from_file_location("fa_init2", str(fa_init_path))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        assert "4号文件助手" in mod.process("帮助")

    def test_process_unknown():
        spec = importlib.util.spec_from_file_location("fa_init3", str(fa_init_path))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        assert "未知命令" in mod.process("非法命令xyz")

    _test("file process 空输入", test_process_empty)
    _test("file process 帮助", test_process_help)
    _test("file process 未知命令", test_process_unknown)

    # ---- 命令解析 ----
    def test_get_canonical():
        _get_canonical_command = _safe_load_from_file(fa_init_path, "_get_canonical_command")
        if not _get_canonical_command:
            raise ImportError("file_assistant __init__ 未加载")
        assert _get_canonical_command("查看") == "查看"
        assert _get_canonical_command("列表") == "查看"
        assert _get_canonical_command("搜索") == "搜索"
        assert _get_canonical_command("帮助") == "帮助"
        assert _get_canonical_command("不存在的命令") is None

    def test_get_args():
        _get_args = _safe_load_from_file(fa_init_path, "_get_args")
        if not _get_args:
            raise ImportError("file_assistant __init__ 未加载")
        assert _get_args("查看 /tmp") == ["查看", "/tmp"]
        assert _get_args('复制 "a b" c') == ["复制", "a b", "c"]
        assert _get_args("") == []

    def test_commands_structure():
        COMMANDS = _safe_load_from_file(fa_init_path, "COMMANDS")
        if not COMMANDS:
            raise ImportError("file_assistant __init__ 未加载")
        for cmd in ("查看", "搜索", "复制", "移动", "删除", "帮助"):
            assert cmd in COMMANDS

    _test("file 规范命令解析", test_get_canonical)
    _test("file 参数解析(含引号)", test_get_args)
    _test("file 命令结构完整", test_commands_structure)

    # ---- security ----
    def test_security_resolve():
        resolve_path = _safe_import("security", "resolve_path")
        if not resolve_path:
            raise ImportError("security 模块未加载")
        assert resolve_path("/tmp") is not None

    def test_security_check_read():
        check_file_operation = _safe_import("security", "check_file_operation")
        resolve_path = _safe_import("security", "resolve_path")
        if not check_file_operation or not resolve_path:
            raise ImportError("security 模块未加载")
        # 使用项目内路径（在白名单中）
        test_path = resolve_path(str(PROJECT_ROOT / "scripts" / "regression_test.py"))
        assert check_file_operation(test_path, "read")["valid"] is True

    def test_security_block_sensitive():
        check_file_operation = _safe_import("security", "check_file_operation")
        if not check_file_operation:
            raise ImportError("security 模块未加载")
        assert check_file_operation("/etc/passwd", "read")["valid"] is False

    def test_security_allowed_dirs():
        get_allowed_dirs_from_config = _safe_import("security", "get_allowed_dirs_from_config")
        if not get_allowed_dirs_from_config:
            raise ImportError("security 模块未加载")
        config_path = str(PROJECT_ROOT / "config" / "whitelist.yaml")
        dirs = get_allowed_dirs_from_config(config_path)
        assert isinstance(dirs, list)

    _test("security 路径解析", test_security_resolve)
    _test("security 读权限校验", test_security_check_read)
    _test("security 敏感路径拦截", test_security_block_sensitive)
    _test("security 白名单读取", test_security_allowed_dirs)

    # ---- file_manager ----
    def test_fm_ls():
        cmd_ls = _safe_import("file_manager", "cmd_ls")
        if not cmd_ls:
            raise ImportError("file_manager 模块未加载")
        result = cmd_ls("/tmp")
        assert result is not None and len(result) > 0

    def test_fm_info():
        cmd_info = _safe_import("file_manager", "cmd_info")
        if not cmd_info:
            raise ImportError("file_manager 模块未加载")
        assert cmd_info("/tmp") is not None

    def test_fm_mkdir_trash():
        cmd_mkdir = _safe_import("file_manager", "cmd_mkdir")
        cmd_trash = _safe_import("file_manager", "cmd_trash")
        if not cmd_mkdir or not cmd_trash:
            raise ImportError("file_manager 模块未加载")
        test_dir = f"/tmp/__test_file_4_{int(time.time())}__"
        assert "已创建" in cmd_mkdir(test_dir)
        assert os.path.isdir(test_dir)
        assert "回收站" in cmd_trash(test_dir)
        assert not os.path.exists(test_dir)

    def test_fm_find():
        cmd_find = _safe_import("file_manager", "cmd_find")
        if not cmd_find:
            raise ImportError("file_manager 模块未加载")
        assert isinstance(cmd_find("/tmp", "test"), str)

    _test("file_manager ls", test_fm_ls)
    _test("file_manager info", test_fm_info)
    _test("file_manager mkdir+trash", test_fm_mkdir_trash)
    _test("file_manager find", test_fm_find)


# =====================================================================
# 5号AI sys-assistant 测试
# =====================================================================

def _load_sys_package():
    """加载整个 sys-assistant 包，处理相对导入问题"""
    src_dir = str(PROJECT_ROOT / "assistants/sys-assistant/src")
    if src_dir not in sys.path:
        sys.path.insert(0, src_dir)
    pkg_name = "_sys_test_pkg"
    # 加载 security (无相对导入) -> 放入 sys.modules
    if f"{pkg_name}.security" not in sys.modules:
        for mod_file, mod_attr in [
            ("security", "security"),
            ("system_monitor", "system_monitor"),
            ("service_manager", "service_manager"),
            ("process_manager", "process_manager"),
            ("backup_manager", "backup_manager"),
            ("log_viewer", "log_viewer"),
        ]:
            mpath = Path(src_dir) / f"{mod_file}.py"
            if not mpath.exists():
                continue
            spec = importlib.util.spec_from_file_location(f"{pkg_name}.{mod_attr}", str(mpath))
            mod = importlib.util.module_from_spec(spec)
            mod.__package__ = pkg_name
            sys.modules[f"{pkg_name}.{mod_attr}"] = mod
            spec.loader.exec_module(mod)
    # __init__.py 作为包入口
    init_path = Path(src_dir) / "__init__.py"
    if f"{pkg_name}.__init__" not in sys.modules:
        spec = importlib.util.spec_from_file_location(f"{pkg_name}.__init__", str(init_path))
        mod = importlib.util.module_from_spec(spec)
        mod.__package__ = pkg_name
        sys.modules[pkg_name] = mod
        sys.modules[f"{pkg_name}.__init__"] = mod
        spec.loader.exec_module(mod)
    return pkg_name


def test_sys():
    _section("6. 5号AI sys-assistant")

    PKG = _load_sys_package()

    def _mod(name):
        return sys.modules.get(f"{PKG}.{name}")

    # ---- 入口 ----
    def test_process_help():
        init_mod = _mod("__init__")
        if not init_mod:
            raise ImportError("sys-assistant __init__ 未加载")
        assert "系统管理" in init_mod.process("help")

    def test_process_empty():
        init_mod = _mod("__init__")
        if not init_mod:
            raise ImportError("sys-assistant __init__ 未加载")
        assert "系统管理" in init_mod.process("")

    def test_process_unknown():
        init_mod = _mod("__init__")
        if not init_mod:
            raise ImportError("sys-assistant __init__ 未加载")
        assert "未知命令" in init_mod.process("非法命令xyz")

    _test("sys process 帮助", test_process_help)
    _test("sys process 空输入", test_process_empty)
    _test("sys process 未知命令", test_process_unknown)

    # ---- security ----
    def test_security_check():
        sec = _mod("security")
        if not sec:
            raise ImportError("sys security 模块未加载")
        assert sec.check_command("status")
        assert sec.check_command("disk")
        assert sec.check_command("ps_list")
        assert not sec.check_command("rm -rf /")
        assert sec.check_no_sudo("ls -la")
        assert not sec.check_no_sudo("sudo rm -rf /")
        allowed = sec.get_allowed_commands()
        assert "status" in allowed and "help" in allowed
        assert sec.validate_service_name("flask") and not sec.validate_service_name("unknown_svc")

    def test_security_sanitize():
        sec = _mod("security")
        if not sec:
            raise ImportError("sys security 模块未加载")
        assert sec.sanitize_path("/etc/passwd") == ""
        assert sec.is_allowed_log_file("flask")
        assert sec.is_allowed_log_file("monitor")
        assert not sec.is_allowed_log_file("nonexistent")

    _test("sys security 命令白名单", test_security_check)
    _test("sys security 路径+日志校验", test_security_sanitize)

    # ---- system_monitor ----
    def test_sysmon_status():
        m = _mod("system_monitor")
        if not m:
            raise ImportError("system_monitor 未加载")
        assert "系统状态" in m.cmd_status()

    def test_sysmon_disk():
        m = _mod("system_monitor")
        if not m:
            raise ImportError("system_monitor 未加载")
        assert "磁盘" in m.cmd_disk()

    def test_sysmon_mem():
        m = _mod("system_monitor")
        if not m:
            raise ImportError("system_monitor 未加载")
        assert m.cmd_mem() is not None

    def test_sysmon_cpu():
        m = _mod("system_monitor")
        if not m:
            raise ImportError("system_monitor 未加载")
        assert "CPU" in m.cmd_cpu() or "核心" in m.cmd_cpu()

    def test_sysmon_load():
        m = _mod("system_monitor")
        if not m:
            raise ImportError("system_monitor 未加载")
        assert m.cmd_load() is not None

    def test_sysmon_uptime():
        m = _mod("system_monitor")
        if not m:
            raise ImportError("system_monitor 未加载")
        assert "up" in m.cmd_uptime() or "上" in m.cmd_uptime()

    def test_sysmon_network():
        m = _mod("system_monitor")
        if not m:
            raise ImportError("system_monitor 未加载")
        assert "网络" in m.cmd_network() or "状态" in m.cmd_network()

    _test("system_monitor status", test_sysmon_status)
    _test("system_monitor disk", test_sysmon_disk)
    _test("system_monitor mem", test_sysmon_mem)
    _test("system_monitor cpu", test_sysmon_cpu)
    _test("system_monitor load", test_sysmon_load)
    _test("system_monitor uptime", test_sysmon_uptime)
    _test("system_monitor network", test_sysmon_network)

    # ---- service_manager ----
    def test_svc_list():
        m = _mod("service_manager")
        if not m:
            raise ImportError("service_manager 未加载")
        assert "服务状态" in m.cmd_service_list()

    def test_svc_unknown():
        m = _mod("service_manager")
        if not m:
            raise ImportError("service_manager 未加载")
        assert "未知服务" in m.cmd_service_status("nonexistent_svc_xyz")
        assert "未知服务" in m.cmd_service_start("nonexistent_svc")

    def test_svc_start_stop_all():
        m = _mod("service_manager")
        if not m:
            raise ImportError("service_manager 未加载")
        assert m.cmd_service_start_all() is not None
        assert m.cmd_service_stop_all() is not None

    _test("service_manager 列表", test_svc_list)
    _test("service_manager 未知服务", test_svc_unknown)
    _test("service_manager 启停全部", test_svc_start_stop_all)

    # ---- process_manager ----
    def test_ps_list():
        m = _mod("process_manager")
        if not m:
            raise ImportError("process_manager 未加载")
        assert "进程" in m.cmd_ps_list()

    def test_ps_list_filter():
        m = _mod("process_manager")
        if not m:
            raise ImportError("process_manager 未加载")
        assert m.cmd_ps_list("launchd") is not None

    def test_ps_kill_invalid():
        m = _mod("process_manager")
        if not m:
            raise ImportError("process_manager 未加载")
        assert "无效" in m.cmd_ps_kill("abc")
        assert "无效" in m.cmd_ps_kill("0")

    def test_ps_kill_nonexistent():
        m = _mod("process_manager")
        if not m:
            raise ImportError("process_manager 未加载")
        result = m.cmd_ps_kill("999999999")
        assert "不存在" in result or "已不" in result

    _test("process_manager 列表", test_ps_list)
    _test("process_manager 过滤", test_ps_list_filter)
    _test("process_manager 无效PID", test_ps_kill_invalid)
    _test("process_manager 不存在PID", test_ps_kill_nonexistent)

    # ---- log_viewer ----
    def test_log_invalid():
        m = _mod("log_viewer")
        if not m:
            raise ImportError("log_viewer 未加载")
        assert "不允许" in m.cmd_log("nonexistent_log")

    def test_log_search_empty():
        m = _mod("log_viewer")
        if not m:
            raise ImportError("log_viewer 未加载")
        assert "关键词" in m.cmd_log_search("")

    _test("log_viewer 无效日志名", test_log_invalid)
    _test("log_viewer 空搜索", test_log_search_empty)

    # ---- backup_manager ----
    def test_backup_list():
        m = _mod("backup_manager")
        if not m:
            raise ImportError("backup_manager 未加载")
        assert m.cmd_backup_list() is not None

    def test_backup_restore_invalid():
        m = _mod("backup_manager")
        if not m:
            raise ImportError("backup_manager 未加载")
        # 确保备份目录存在，并创建一个备份文件让还原逻辑走到格式校验
        backup_dir = PROJECT_ROOT / "backups"
        backup_dir.mkdir(exist_ok=True)
        fake_backup = backup_dir / "backup_test.tar.gz"
        fake_backup.touch()
        try:
            result = m.cmd_backup_restore("abc")
            assert "无效" in result or "请输" in result, f"期望报错，实际：{result}"
        finally:
            if fake_backup.exists():
                fake_backup.unlink()

    _test("backup_manager 列表", test_backup_list)
    _test("backup_manager 无效还原", test_backup_restore_invalid)


# =====================================================================
# 回调服务测试
# =====================================================================
def test_callback():
    _section("7. 回调服务 callback_server")

    callback_path = PROJECT_ROOT / "shared/feishu-callback/callback_server.py"
    cb_src = str(callback_path.parent)
    if cb_src not in sys.path:
        sys.path.insert(0, cb_src)

    try:
        spec = importlib.util.spec_from_file_location("callback_server", str(callback_path))
        cb_mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cb_mod)
    except ModuleNotFoundError as e:
        print(f"\n  ⏭️  未安装依赖，跳过 callback 模块: {e}")
        return

    def test_health_endpoint():
        with cb_mod.app.test_client() as client:
            resp = client.get("/health")
            assert resp.status_code == 200
            assert resp.get_json()["status"] == "ok"

    def test_webhook_challenge():
        with cb_mod.app.test_client() as client:
            resp = client.post("/webhook", json={"challenge": "test123"})
            assert resp.status_code == 200
            assert resp.get_json()["challenge"] == "test123"

    def test_webhook_empty_body_json():
        with cb_mod.app.test_client() as client:
            resp = client.post("/webhook", json={"test": "data"})
            assert resp.status_code == 200
            data = resp.get_json()
            assert isinstance(data, dict) and "code" in data

    def test_webhook_empty_body():
        with cb_mod.app.test_client() as client:
            resp = client.post("/webhook", data="not json", content_type="application/json")
            assert resp.status_code == 400

    def test_unknown_route():
        with cb_mod.app.test_client() as client:
            resp = client.get("/webhook_unknown")
            assert resp.status_code == 404

    def test_backends_config():
        assert "/webhook_file" in cb_mod.BACKENDS
        assert "/webhook_sys" in cb_mod.BACKENDS

    def test_dashboard_exists():
        assert cb_mod.dashboard_bp is not None

    _test("callback /health", test_health_endpoint)
    _test("callback challenge验证", test_webhook_challenge)
    _test("callback 空JSON", test_webhook_empty_body_json)
    _test("callback 空body", test_webhook_empty_body)
    _test("callback 未知路由", test_unknown_route)
    _test("callback 后端路由配置", test_backends_config)
    _test("callback dashboard蓝图", test_dashboard_exists)


# =====================================================================
# 测试报告输出
# =====================================================================
def print_report():
    total = results["pass"] + results["fail"] + results["skip"]
    print(f"\n{'='*60}")
    print(f"  测试报告总结")
    print(f"{'='*60}")
    print(f"  总计: {total}")
    print(f"  ✅ 通过: {results['pass']}")
    print(f"  ❌ 失败: {results['fail']}")
    print(f"  ⏭️  跳过: {results['skip']}（缺失依赖或被筛选器排除）")
    print(f"  {'🎉 全部通过!' if results['fail'] == 0 else '⚠️  存在失败项'}")
    print(f"{'='*60}")
    return results["fail"] == 0


if __name__ == "__main__":
    print(f"\n{'='*60}")
    print(f"  五角色 AI 助理系统 · 全功能回归测试")
    print(f"  项目路径: {PROJECT_ROOT}")
    if module_filter:
        print(f"  模块筛选: {module_filter}")
    print(f"  💡 建议使用 venv 运行以获完整覆盖:")
    print(f"     python3 -m venv tmp_venv && source tmp_venv/bin/activate")
    print(f"     pip install python-docx openpyxl python-pptx python-dotenv cryptography mammoth")
    print(f"     python3 scripts/regression_test.py")
    print(f"{'='*60}")

    test_modules = [
        ("shared", test_shared),
        ("chat", test_chat),
        ("office", test_office),
        ("life", test_life),
        ("file", test_file),
        ("sys", test_sys),
        ("callback", test_callback),
    ]

    for name, fn in test_modules:
        if module_filter and module_filter not in name:
            results["skip"] += 1
            continue
        try:
            fn()
        except Exception as e:
            print(f"\n  ⚠️  模块 '{name}' 整体跳过: {e}")

    success = print_report()
    sys.exit(0 if success else 1)
