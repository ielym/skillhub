"""
非论文来源管线（non-paper-source）：博客/Release/仓库/榜单/政策/论坛等 → 结构化整理。
单轮：输入原文或网页文本，输出结构化文档（事实/观点/疑点/行动项分离）。
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

import api_client
from prompts import SOURCE_SYS

PROMPT = """请对以下非论文来源做简要整理，直接输出正文（不要输出任何前言/自我说明/分析过程）。
按 system prompt 的「输出结构」完整展开：这是什么、主要内容、为什么值得关注。

【来源文本】
{content}"""

# 简要整理合法性：首行为 # 标题，三要素齐全，且不含行动项/元信息类无关结构
_SECTIONS = ("这是什么", "主要内容", "为什么值得关注")

# 正文允许的收口字符；结尾停在半句/半条列表即判截断
_SAFE_TAIL = set("。！？…；：.!?”\"』】）)]}`|")


def _ends_clean(doc: str) -> bool:
    lines = [ln for ln in doc.splitlines() if ln.strip()]
    if not lines:
        return False
    tail = lines[-1].strip()
    if tail.startswith("```") or tail.replace("$", "").strip() == "":
        return True
    return tail[-1] in _SAFE_TAIL


def _valid(doc: str) -> bool:
    lines = [ln for ln in doc.splitlines() if ln.strip()]
    if not lines or not lines[0].strip().startswith("#"):
        return False
    if any(bad in doc for bad in ("## 行动项", "## 疑点", "## 元信息", "读取日期")):
        return False
    if not all(f"## {s}" in doc for s in _SECTIONS):
        return False
    return _ends_clean(doc)


def run(src: dict) -> str:
    text = src.get("text", "")
    if src["type"] == "pdf":
        # 非论文模式一般不接 PDF，但若给了 PDF 则提取文本
        pages = src["pages"]
        text = "\n".join(f"--- 第{p['page']}页 ---\n{p['text']}" for p in pages if p["text"])
    content = text[:24000]

    def _gen():
        return api_client.chat_text(SOURCE_SYS, PROMPT.format(content=content), thinking=False)

    return api_client.call_until_valid(_gen, "source", _valid)
