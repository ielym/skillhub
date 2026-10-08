"""
PDF 解析层：将论文 PDF 转成结构化中间表示。
- 文本提取（pdfplumber）
- 页面渲染成图片（PyMuPDF）供多模态使用
- 产出带页码/章节定位的结构化块
"""
import os
import re

import pdfplumber
import pymupdf

WORK_DIR = os.path.join(os.path.dirname(__file__), "work")
os.makedirs(WORK_DIR, exist_ok=True)


def _repair_rotated_stamp(text: str) -> str:
    """修复被旋转 90° 的 arXiv 页脚戳。

    该类戳记被 pdfplumber 逐行、逐字反序提取（如 "1v72860.0162:viXra"），
    会让下游误判为「编号格式不完整」。此处按行倒序 + 行内反转还原原文。
    """
    lines = text.splitlines()
    for i, ln in enumerate(lines):
        if "vixra" not in ln.lower():
            continue
        # 戳记各行都很短，向上收拢到第一个长行（正文）为止，避免误反转正文
        j = i
        while j > 0 and len(lines[j - 1].strip()) <= 12 and (i - j) < 8:
            j -= 1
        fixed = " ".join(s[::-1] for s in reversed(lines[j : i + 1])).strip()
        if re.search(r"arXiv:\S+", fixed, re.I):
            return "\n".join(lines[:j] + [fixed] + lines[i + 1 :])
    return text


def extract_text(pdf_path: str) -> list[dict]:
    """逐页提取文本，返回 [{page, text}]。"""
    pages = []
    with pdfplumber.open(pdf_path) as pdf:
        for i, p in enumerate(pdf.pages):
            try:
                t = p.extract_text() or ""
            except Exception:
                t = ""
            pages.append({"page": i + 1, "text": _repair_rotated_stamp(t)})
    return pages


def render_page(pdf_path: str, page_no: int, dpi: int = 120) -> str:
    """渲染第 page_no 页（1-based）为 PNG，返回路径。"""
    os.makedirs(WORK_DIR, exist_ok=True)
    out = os.path.join(WORK_DIR, f"page_{page_no:03d}.png")
    if os.path.exists(out):
        return out
    doc = pymupdf.open(pdf_path)
    pix = doc[page_no - 1].get_pixmap(dpi=dpi)
    pix.save(out)
    doc.close()
    return out


def detect_figure_pages(pdf_path: str) -> list[int]:
    """检测含图页：嵌入图片 + 矢量图形（矢量图是论文图表的主要形式）。"""
    fig_pages = []
    d = pymupdf.open(pdf_path)
    for i in range(d.page_count):
        page = d[i]
        has_raster = bool(page.get_images(full=True))
        has_vectors = False
        try:
            has_vectors = len(page.get_drawings()) > 30
        except Exception:
            pass
        if has_raster or has_vectors:
            fig_pages.append(i + 1)
    d.close()
    return fig_pages


def chunk_pages(
    pages: list[dict],
    chunk_size: int = 3,
    overlap: int = 1,
) -> list[dict]:
    """把连续页打包成块（带重叠），每块保留页码范围。"""
    chunks = []
    i = 0
    n = len(pages)
    while i < n:
        end = min(i + chunk_size, n)
        block = pages[i:end]
        chunks.append(
            {
                "pages": [b["page"] for b in block],
                "text": "\n\n".join(
                    f"--- 第{p['page']}页 ---\n{p['text']}" for p in block
                ),
                "start": i,
                "end": end,
            }
        )
        i += chunk_size - overlap
    return chunks
