"""
模块名称：external_doc_tools
功能描述：2号AI 文档处理能力弱化后的外部工具适配层，将 PPT 生成/文档摘要委托给外部项目技能（PPTAgent、dashi-ppt），本地仅保留转接逻辑
对外接口：
    - generate_ppt_via_pptagent(prompt, output_path, attachments=None, pages=None, aspect="16:9", lang="zh"): 调 PPTAgent CLI 生成 PPTX
    - generate_ppt_via_dashi(prompt, output_path, theme="theme01", pages=10, title=None): 调 dashi-ppt skill 生成 PPTX
    - summarize_doc_via_external(text, hint=""): 委托后端 LLM 生成文档摘要（本地 summarizer 弱化为兜底）
    - check_external_ready(): 探测外部工具可用性，返回状态 dict
依赖：
    - 标准库：logging, os, json, sys, subprocess, tempfile, shutil, datetime, re
    - 第三方：无
    - 项目内：shared.backend_utils (call_api, clean_reply, get_backend_config)
版本：v1.0
更新记录：
    - 2026-08-16: 初始创建，承载 PPT + Word/Excel 文档处理能力弱化改造
"""
import json
import logging
import os
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "shared"))

logger = logging.getLogger(__name__)

# 外部工具根目录（固定测试环境路径，可用环境变量覆盖）
EXTERNAL_ROOT = Path(os.environ.get("EXTERNAL_TOOLS_ROOT", "/Volumes/BR256G/lark-training-ppt-generator"))

PPTAGENT_DIR = EXTERNAL_ROOT / "PPTAgent"
PPTAGENT_CLI = PPTAGENT_DIR / ".venv" / "bin" / "pptagent"
PPTAGENT_CONFIG = PPTAGENT_DIR / "deeppresenter" / "config.yaml"

DASHI_DIR = EXTERNAL_ROOT / "dashiAI-ppt-skill" / "skills" / "dashi-ppt"
DASHI_PROJECT = DASHI_DIR / "project"
DASHI_RENDER = DASHI_DIR / "scripts" / "render_goal_deck.sh"
DASHI_EXPORT = DASHI_PROJECT / "scripts" / "export-pptx.mjs"

# 输出根目录（本项目的 data/office）
OUTPUT_ROOT = PROJECT_ROOT / "data" / "office"

# 生成超时（秒）：PPTAgent 单次 5-10 分钟；dashi 渲染 + 导出给足 15 分钟
_PPTAGENT_TIMEOUT = 900
_DASHI_TIMEOUT = 900


def check_external_ready() -> dict:
    """探测外部工具可用性，返回各工具就绪状态"""
    status = {
        "pptagent_cli": PPTAGENT_CLI.exists() and os.access(str(PPTAGENT_CLI), os.X_OK),
        "pptagent_config": PPTAGENT_CONFIG.exists(),
        "pptagent_docker": _check_docker(),
        "dashi_project": (DASHI_PROJECT / "node_modules").exists(),
        "dashi_render": DASHI_RENDER.exists(),
        "node": shutil.which("node") is not None,
    }
    status["pptagent_ready"] = all([
        status["pptagent_cli"], status["pptagent_config"], status["pptagent_docker"]
    ])
    status["dashi_ready"] = all([
        status["dashi_project"], status["dashi_render"], status["node"]
    ])
    status["any_ready"] = status["pptagent_ready"] or status["dashi_ready"]
    return status


def _check_docker() -> bool:
    """检测 Docker daemon 是否存活"""
    try:
        r = subprocess.run(
            ["docker", "ps"],
            capture_output=True, timeout=10, text=True,
        )
        return r.returncode == 0
    except Exception:
        return False


def _run_cmd(cmd, cwd=None, timeout=None, env=None):
    """执行外部命令，返回 (returncode, stdout, stderr)"""
    try:
        r = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout,
            env=env,
        )
        return r.returncode, r.stdout or "", r.stderr or ""
    except subprocess.TimeoutExpired:
        return -1, "", "执行超时（{}秒）".format(timeout)
    except FileNotFoundError as e:
        return -2, "", f"命令不存在: {e}"
    except Exception as e:
        return -3, "", str(e)


# ===================== PPTAgent 生成 =====================

def generate_ppt_via_pptagent(
    prompt: str,
    output_path: str,
    attachments: list = None,
    pages: str = None,
    aspect: str = "16:9",
    lang: str = "zh",
) -> tuple:
    """
    调用 PPTAgent CLI 生成 PPTX。
    返回 (success, result)：success=True 时 result 为输出路径，否则为错误信息。
    """
    status = check_external_ready()
    if not status["pptagent_ready"]:
        missing = [k for k, v in status.items() if v is False and k.startswith("pptagent_")]
        return (False, f"PPTAgent 未就绪（缺失：{', '.join(missing)}）")

    if not prompt.strip():
        return (False, "生成提示词不能为空")

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)

    cmd = [str(PPTAGENT_CLI), "generate", prompt, "-o", str(out), "-l", lang]
    if pages:
        cmd += ["-p", str(pages)]
    if aspect:
        cmd += ["-a", str(aspect)]
    if attachments:
        for att in attachments:
            ap = Path(att)
            if ap.exists():
                cmd += ["-f", str(ap.resolve())]
            else:
                logger.warning(f"附件不存在，跳过: {att}")

    logger.info(f"调用 PPTAgent 生成 PPT: {' '.join(cmd[:6])}…")
    rc, stdout, stderr = _run_cmd(cmd, cwd=str(PPTAGENT_DIR), timeout=_PPTAGENT_TIMEOUT)
    if rc == 0 and out.exists() and out.stat().st_size > 1000:
        logger.info(f"PPTAgent 生成成功: {out} ({out.stat().st_size} bytes)")
        return (True, str(out))
    err_tail = (stderr or stdout or "").strip().splitlines()
    detail = err_tail[-3:] if err_tail else []
    return (False, "PPTAgent 生成失败：{}".format(" | ".join(detail)))


# ===================== dashi-ppt 生成 =====================

def _build_goal_json(prompt: str, title: str, theme: str, pages: int) -> str:
    """从文本生成 dashi-ppt 所需的 goal.json（schema v2）"""
    goal = {
        "schemaVersion": 2,
        "title": title,
        "goal": prompt,
        "audience": "",
        "owner": "AI 助理系统",
        "randomSeed": f"assist-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "workflowRunId": datetime.now().strftime("%Y%m%dT%H%M%S000") + "-assist",
        "pageCount": pages,
        "themePack": theme,
        "variantOutputMode": "selected-only",
        "slides": [],
    }
    # 生成 pages 页，每页一个简化 content（封面 + 正文骨架）
    goal["slides"].append({
        "id": "s1",
        "content": {
            "presentation": {
                "title": title,
                "summary": prompt[:120],
                "takeaway": "核心结论",
                "items": [],
            },
            "media": [],
            "meta": {"brand": "AI 助理系统", "pageLabel": "2026", "panelTitle": title[:20]},
        },
        "selectedVariant": "v1",
        "variants": [
            {"id": "v1", "kind": "template", "layout": f"{theme}_page001",
             "props": {}, "contentMap": {
                 "kicker": "meta.panelTitle", "titleTop": "presentation.title",
                 "titleBottom": "presentation.summary", "lead": "presentation.takeaway"}},
            {"id": "v2", "kind": "template", "layout": f"{theme}_page002",
             "props": {}, "contentMap": {
                 "enKicker": "meta.panelTitle", "titleTop": "presentation.title",
                 "titleBottom": "presentation.summary", "subtitle": "presentation.takeaway"}},
            {"id": "v3", "kind": "template", "layout": f"{theme}_page003",
             "props": {}, "contentMap": {
                 "kicker": "meta.panelTitle", "titleTop": "presentation.title",
                 "titleBottom": "presentation.summary", "bigNumber": "meta.pageLabel"}},
            {"id": "v4", "kind": "bespoke", "adjustable": False,
             "composition": {
                 "designIntent": {
                     "objective": prompt[:60], "audience": "", "narrativeRole": "封面定调",
                     "emphasis": "presentation.title", "rationale": "封面页",
                     "compositionFamily": "hero"},
                 "background": "light",
                 "elements": [
                     {"id": "title", "type": "text", "grid": {"column": 1, "row": 1, "width": 10, "height": 2},
                      "role": "title", "text": ""},
                     {"id": "summary", "type": "text", "grid": {"column": 1, "row": 4, "width": 7, "height": 2},
                      "role": "body", "text": ""},
                 ],
             },
             "contentMap": {"elements[0].text": "presentation.title",
                            "elements[1].text": "presentation.summary"}},
        ],
    })
    # 正文页：内容自动展开
    body_prompt = prompt
    for i in range(2, pages + 1):
        goal["slides"].append({
            "id": f"s{i}",
            "content": {
                "presentation": {
                    "title": f"内容 {i-1}",
                    "summary": body_prompt[:80],
                    "takeaway": "要点",
                    "items": [
                        {"id": f"i{j}", "label": f"要点 {j}", "value": "",
                         "displayValue": "", "detail": body_prompt[:40],
                         "unit": "", "required": True, "priority": 1}
                        for j in range(1, 4)
                    ],
                },
                "media": [],
                "meta": {"brand": "AI 助理系统", "pageLabel": "2026", "panelTitle": title[:20]},
            },
            "selectedVariant": "v1",
            "variants": [
                {"id": "v1", "kind": "template", "layout": f"{theme}_page00{i+1:02d}",
                 "props": {}, "contentMap": {"title": "presentation.title",
                                              "summary": "presentation.summary",
                                              "items": "presentation.items"}},
                {"id": "v2", "kind": "template", "layout": f"{theme}_page00{i+1:02d}",
                 "props": {}, "contentMap": {"title": "presentation.title"}},
                {"id": "v3", "kind": "template", "layout": f"{theme}_page00{i+1:02d}",
                 "props": {}, "contentMap": {"title": "presentation.title",
                                              "summary": "presentation.summary"}},
            ],
        })
    return json.dumps(goal, ensure_ascii=False, indent=2)


def generate_ppt_via_dashi(
    prompt: str,
    output_path: str,
    theme: str = "theme01",
    pages: int = 10,
    title: str = None,
) -> tuple:
    """
    调用 dashi-ppt skill 生成 PPTX。
    返回 (success, result)：success=True 时 result 为输出路径，否则为错误信息。
    """
    status = check_external_ready()
    if not status["dashi_ready"]:
        missing = [k for k, v in status.items() if v is False and k.startswith("dashi")]
        return (False, f"dashi-ppt 未就绪（缺失：{', '.join(missing)}）")

    if not prompt.strip():
        return (False, "生成提示词不能为空")

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    deck_name = "deck_" + datetime.now().strftime("%Y%m%d_%H%M%S")
    work_dir = out.parent / deck_name
    work_dir.mkdir(parents=True, exist_ok=True)
    title = title or prompt.strip()[:30]

    # 1. 写 goal.json
    goal_spec = work_dir / "goal.json"
    goal_spec.write_text(_build_goal_json(prompt, title, theme, pages), encoding="utf-8")

    # 2. 渲染 HTML
    ppt_dir = work_dir / "ppt"
    html_out = ppt_dir / "index.html"
    rc, stdout, stderr = _run_cmd(
        ["bash", str(DASHI_RENDER), str(goal_spec), str(html_out)],
        cwd=str(work_dir),
        timeout=_DASHI_TIMEOUT,
    )
    if rc != 0 or not html_out.exists():
        err_tail = (stderr or stdout or "").strip().splitlines()
        return (False, "dashi 渲染失败：{}".format(" | ".join(err_tail[-3:])))

    # 3. 导出 PPTX
    rc, stdout, stderr = _run_cmd(
        ["node", str(DASHI_EXPORT), str(ppt_dir), str(out)],
        cwd=str(DASHI_PROJECT),
        timeout=_DASHI_TIMEOUT,
    )
    if rc == 0 and out.exists() and out.stat().st_size > 1000:
        logger.info(f"dashi-ppt 生成成功: {out} ({out.stat().st_size} bytes)")
        return (True, str(out))
    err_tail = (stderr or stdout or "").strip().splitlines()
    return (False, "dashi 导出失败：{}".format(" | ".join(err_tail[-3:])))


# ===================== 摘要委托 =====================

def summarize_doc_via_external(text: str, hint: str = "") -> tuple:
    """
    委托后端 LLM 生成文档摘要，返回 (summary_text, is_external)。
    本地 summarizer 弱化为兜底路径（由 document_handler 决定是否回退）。
    """
    stripped = (text or "").strip()
    if not stripped or len(stripped) < 10:
        return ("", False)
    try:
        from shared.backend_utils import call_api, clean_reply
        prefix = f"文件结构：{hint}\n\n" if hint else ""
        user_msg = (
            f"{prefix}"
            f"以下是文档内容（可能被截断）：\n\n{stripped[:3000]}\n\n"
            "请用 3-5 句话总结文档核心信息，列出关键要点，语言与原文一致。"
        )
        result = call_api([{"role": "user", "content": user_msg}])
        if result:
            cleaned = clean_reply(result)
            if cleaned and len(cleaned) >= 10:
                return (cleaned, True)
    except Exception as e:
        logger.warning(f"外部摘要失败，交由本地兜底: {e}")
    return ("", False)
