"""
论文/资料解析 Harness —— 多模式统一入口

用法:
  python3 main.py <input> --mode deep   [论文精读：三遍法 → 九章节文档]
  python3 main.py <input> --mode skim   [论文泛读：一张决策卡]
  python3 main.py <input> --mode source [非论文来源：结构化整理]
  python3 main.py <input> --mode deep --dry-run   [只做解析不调 API]

input 可为:
  - 本地 PDF 路径
  - 本地文本/Markdown 路径
  - 直接传入文本内容（--mode source 时常用）

共同参数:
  --chunk N      R2 分块页数（deep，默认 4）
  --overlap N    分块重叠页（deep，默认 0）
  --fig-pages   手动指定需渲染图片的页，逗号分隔（默认自动检测）
  --no-cache     忽略已有缓存强制重跑
  --dry-run      只做输入解析，不调 API
  --out NAME     最终文档文件名（默认 auto）
"""
import argparse
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import api_client
import pdf_parser
import storage
from pipelines import deep_read, skim, source


def resolve_input(raw: str) -> dict:
    """把输入解析成统一的 source dict。"""
    p = os.path.abspath(raw)
    if os.path.exists(p):
        ext = os.path.splitext(p)[1].lower()
        if ext == ".pdf":
            return {"type": "pdf", "path": p}
        with open(p, encoding="utf-8") as f:
            text = f.read()
        return {"type": "text", "path": p, "text": text}
    # 非文件路径：视为直接文本
    return {"type": "text", "path": None, "text": raw}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input", help="PDF 路径 / 文本文件路径 / 直接文本")
    ap.add_argument("--mode", choices=["deep", "skim", "source"], default="deep")
    ap.add_argument("--chunk", type=int, default=4)
    ap.add_argument("--overlap", type=int, default=0)
    ap.add_argument("--fig-pages", default="")
    ap.add_argument("--no-cache", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--out", default="")
    args = ap.parse_args()

    storage.ensure_dirs()
    if args.no_cache:
        storage.clear_cache()

    src = resolve_input(args.input)
    print(f"[input] type={src['type']} path={src.get('path') or '(inline text)'}")

    if src["type"] == "pdf":
        pages = pdf_parser.extract_text(src["path"])
        fig_pages = pdf_parser.detect_figure_pages(src["path"]) if not args.fig_pages else [
            int(x) for x in args.fig_pages.split(",") if x.strip()
        ]
        print(f"[input] PDF {len(pages)} 页, 含图页 {len(fig_pages)}")
        src["pages"] = pages
        src["fig_pages"] = fig_pages
    else:
        src["fig_pages"] = []

    if args.dry_run:
        print("[dry-run] 跳过 API 调用")
        return

    # 服务端健康检查：不可用则长间隔持续探测，直到恢复才开工（绝不因临时不可用而放弃）
    print("[ping] 检查 API 可用性 ...", flush=True)
    while not api_client.ping():
        print("[wait] 测试 API 当前不可用（持续空响应/限流），120s 后重新探测 ...", flush=True)
        time.sleep(120)

    if args.mode == "deep":
        out_name = args.out or "deep_read_notes.md"
        runner = lambda: deep_read.run(src, chunk_size=args.chunk, overlap=args.overlap)
    elif args.mode == "skim":
        out_name = args.out or "skim_card.md"
        runner = lambda: skim.run(src)
    else:
        out_name = args.out or "source_notes.md"
        runner = lambda: source.run(src)

    try:
        final = runner()
    except Exception as e:
        # 完整性铁律：不产出半成品。任何一轮未完成都不得降级拼接中间产物，
        # 而是明确报错退出（可稍后重跑，断点续跑会自动接着跑）。
        print(f"[error] 管线未能产出完整最终文档: {e}", flush=True)
        print("[error] 已保留 cache/ 断点，稍后重跑将自动续跑缺失部分。", flush=True)
        sys.exit(3)

    path = storage.save_output(out_name, final)
    print(f"[done] 最终文档: {path}")


if __name__ == "__main__":
    main()
