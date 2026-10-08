"""
泛读管线（skim）：单篇论文快速定性判断 → 一张决策卡。
策略：元信息 + 结构骨架 + 3 类关键图表 + 结论。单轮或两轮完成。
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

import api_client
import pdf_parser
from prompts import SKIM_SYS

PROMPT = """请对以下论文材料做简要解析，直接输出正文（不要输出任何前言/自我说明/分析过程）。
按 system prompt 的「输出结构」完整展开：研究问题、动机、方法、主要贡献、关键结果、局限与适用范围。

【论文材料（开头+结尾+关键图表）】
{content}"""

# 简要解析合法性：首行为 # 标题，且各要素齐全，不含任何评分/决策类字样
_SECTIONS = ("摘要", "研究问题", "动机", "方法", "主要贡献", "关键结果")

# 正文允许的收口字符（与 deep 一致）；结尾停在半句/半条列表即判截断
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
    if any(bad in doc for bad in ("## 决策", "相关度", "可信度", "评分")):
        return False
    if not all(f"## {s}" in doc for s in _SECTIONS):
        return False
    return _ends_clean(doc)


def _detect_head_tail(pages: list[dict]) -> str:
    head = "\n".join(f"--- 第{p['page']}页 ---\n{p['text']}" for p in pages[:3] if p["text"])
    tail = "\n".join(f"--- 第{p['page']}页 ---\n{p['text']}" for p in pages[-2:] if p["text"])
    return f"{head}\n\n[结尾部分]\n{tail}"


def run(src: dict) -> str:
    if src["type"] == "pdf":
        pages = src["pages"]
        fig_pages = src.get("fig_pages", [])
        text_part = _detect_head_tail(pages)
        # 渲染前 3 个含图页（框架图/主结果/消融通常在前部）
        images = []
        for p in fig_pages[:3]:
            img = pdf_parser.render_page(src["path"], p)
            images.append(api_client.image_to_b64(img))

        def _gen():
            return api_client.chat_text(
                SKIM_SYS, PROMPT.format(content=text_part[:18000]), images=images,
                thinking=False, max_tokens=1400,
            )

        return api_client.call_until_valid(_gen, "skim", _valid)
    # 文本输入：单轮直接出卡

    def _gen():
        return api_client.chat_text(
            SKIM_SYS, PROMPT.format(content=src["text"][:20000]), thinking=False, max_tokens=1400
        )

    return api_client.call_until_valid(_gen, "skim", _valid)
