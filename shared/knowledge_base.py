"""
模块名称：knowledge_base.py
功能描述：私有知识库管理，基于 BM25 的关键词检索
对外接口：
    - import_doc(filepath): 将文件导入知识库
    - list_docs(): 列出已导入文档
    - remove_doc(filename): 删除文档
    - search(query, top_k=3, min_score=0.05): 检索相关内容
依赖：
    - 标准库：os, re, json, pathlib, collections, math
    - 第三方：无
版本：v2.2
更新记录：
    - 2026-05-25: v2.0 重写为 TF-IDF 检索，增加 IDF 权重、相关度阈值、智能摘要
    - 2026-05-25: v2.1 中文改为字符二元组分词，提升检索精度
    - 2026-05-25: v2.2 改为 BM25 评分，解决长段落 TF 稀释问题
"""

import os
import re
import json
import math
from pathlib import Path
from collections import Counter

DATA_DIR = Path(__file__).parent.parent / "data"
GLOBAL_KNOWLEDGE_DIR = DATA_DIR / "knowledge"
GLOBAL_INDEX_FILE = DATA_DIR / "knowledge_index.json"

os.makedirs(GLOBAL_KNOWLEDGE_DIR, exist_ok=True)

K1 = 1.5
B = 0.75


def _kb_dirs(user_id=None):
    """获取知识库目录和索引文件路径。user_id 为 None 时使用全局知识库。"""
    if user_id:
        kdir = DATA_DIR / "knowledge" / user_id
        idx = DATA_DIR / f"knowledge_index_{user_id}.json"
    else:
        kdir = GLOBAL_KNOWLEDGE_DIR
        idx = GLOBAL_INDEX_FILE
    os.makedirs(kdir, exist_ok=True)
    return kdir, idx


def _read_doc(filepath):
    """读取文档，按段落分割，返回段落列表"""
    text = Path(filepath).read_text(encoding="utf-8", errors="replace")
    paras = [p.strip() for p in re.split(r'\n\s*\n', text) if p.strip()]
    return [p for p in paras if len(p) > 10]


def _tokenize(text):
    """分词：保留完整短语 + 字符二元组 + 英文单词 + 数字"""
    text_lower = text.lower()
    tokens = re.findall(r'[a-zA-Z]+|\d+', text_lower)
    chinese_seq = re.findall(r'[\u4e00-\u9fff]+', text_lower)
    for seq in chinese_seq:
        L = len(seq)
        tokens.append(seq)
        if L >= 4:
            for i in range(L - 1):
                tokens.append(seq[i:i+2])
    return tokens


def _build_index(user_id=None):
    """重建 BM25 倒排索引"""
    kdir, idx = _kb_dirs(user_id)
    docs = []
    index = {}
    doc_lengths = []

    for f in sorted(kdir.glob("*")):
        if f.suffix.lower() not in (".txt", ".md", ".json", ".csv"):
            continue
        paras = _read_doc(str(f))
        for i, para in enumerate(paras):
            doc_id = f"{f.name}#{i}"
            tokens = _tokenize(para)
            doc_lengths.append(len(tokens))
            freq = Counter(tokens)
            docs.append({
                "id": doc_id, "file": f.name,
                "text": para, "len": len(tokens),
                "freq": dict(freq)
            })
            for t in freq:
                if t not in index:
                    index[t] = {"df": 0}
                index[t]["df"] += 1

    num_docs = len(docs)
    avg_dl = sum(doc_lengths) / num_docs if num_docs else 1

    for term, info in index.items():
        df = info["df"]
        info["idf"] = math.log((num_docs - df + 0.5) / (df + 0.5) + 1)

    idx.write_text(
        json.dumps({
            "docs": docs, "index": index,
            "num_docs": num_docs, "avg_dl": avg_dl
        }, ensure_ascii=False),
        encoding="utf-8"
    )
    return docs, index


def _bm25_score(doc_freq, doc_len, avg_dl, idf):
    """计算单个词项的 BM25 贡献值"""
    tf = doc_freq
    return idf * tf * (K1 + 1) / (tf + K1 * (1 - B + B * doc_len / avg_dl))


def search(query, top_k=3, min_score=0.15, user_id=None):
    """
    BM25 检索知识库，返回相关段落列表。
    user_id: 指定用户的知识库；None 则检索全局知识库。
    min_score: 最低相关度得分（低于此值的结果被过滤）
    """
    kdir, idx = _kb_dirs(user_id)
    if not idx.exists():
        _build_index(user_id)
    data = json.loads(idx.read_text(encoding="utf-8"))
    docs = data["docs"]
    index = data["index"]
    num_docs = data["num_docs"]
    avg_dl = data["avg_dl"]

    query_tokens = _tokenize(query)
    if not query_tokens:
        return []

    # 识别查询中的完整短语（3+字中文序列）
    full_phrases = set()
    for seq in re.findall(r'[\u4e00-\u9fff]{3,}', query):
        full_phrases.add(seq.lower())

    query_freq = Counter(query_tokens)
    scores = {}
    fp_docs = set()

    for q_token, q_count in query_freq.items():
        term_info = index.get(q_token)
        if not term_info:
            continue
        idf = term_info["idf"]
        q_is_fp = q_token in full_phrases
        for doc in docs:
            doc_freq = doc.get("freq", {}).get(q_token, 0)
            if doc_freq == 0:
                continue
            score = _bm25_score(doc_freq, doc["len"], avg_dl, idf) * q_count
            scores[doc["id"]] = scores.get(doc["id"], 0) + score
            if q_is_fp:
                fp_docs.add(doc["id"])

    # 文档级短语加权：包含完整查询短语的文档总分 × 2.5
    if full_phrases:
        for doc_id in scores:
            if doc_id in fp_docs:
                scores[doc_id] *= 2.5

    if not scores:
        return []

    ranked = sorted(scores.items(), key=lambda x: -x[1])
    max_score = ranked[0][1]
    results = []
    seen_texts = set()

    for doc_id, score in ranked:
        if score / max_score < min_score:
            continue
        for d in docs:
            if d["id"] == doc_id:
                text = d["text"]
                if text in seen_texts:
                    continue
                seen_texts.add(text)
                snippet = _make_snippet(text, query_tokens)
                results.append({"file": d["file"], "text": snippet, "score": round(score, 4)})
                break
        if len(results) >= top_k:
            break

    return results


def _make_snippet(text, query_tokens, max_len=200):
    """从文本中提取包含查询词的最相关片段"""
    if len(text) <= max_len:
        return text
    sentences = re.split(r'(?<=[。！？!?])', text)
    if len(sentences) <= 2:
        return text[:max_len] + "…"
    scored = []
    for s in sentences:
        s = s.strip()
        if not s:
            continue
        base = sum(1 for _ in re.finditer('|'.join(re.escape(t) for t in query_tokens), s))
        pos_bonus = max(0, (len(sentences) - len(scored)) * 0.1)
        scored.append((base + pos_bonus, s))
    scored.sort(key=lambda x: -x[0])
    best = scored[0][1] if scored else text[:max_len]
    if len(best) > max_len:
        best = best[:max_len] + "…"
    return best


def _highlight(text, query_tokens):
    """在文本中用 ** 标记查询词（当前未使用，保留备用）"""
    for t in query_tokens:
        if len(t) > 1:
            text = re.sub(f'({re.escape(t)})', r'**\1**', text, flags=re.IGNORECASE)
    return text


def import_doc(filepath, user_id=None):
    """导入文件到知识库"""
    src = Path(filepath)
    if not src.exists():
        return False, "文件不存在"
    if src.suffix.lower() not in (".txt", ".md", ".json", ".csv"):
        return False, "仅支持 txt/md/json/csv 文件"
    kdir, _ = _kb_dirs(user_id)
    dst = kdir / src.name
    dst.write_bytes(src.read_bytes())
    _build_index(user_id)
    return True, f"已导入：{src.name}"


def list_docs(user_id=None):
    """列出知识库文档"""
    kdir, _ = _kb_dirs(user_id)
    return [f.name for f in sorted(kdir.glob("*")) if f.suffix.lower() in (".txt", ".md", ".json", ".csv")]


def remove_doc(filename, user_id=None):
    """删除文档"""
    kdir, _ = _kb_dirs(user_id)
    target = kdir / filename
    if target.exists():
        target.unlink()
        _build_index(user_id)
        return True, f"已删除：{filename}"
    return False, "文件不存在"
