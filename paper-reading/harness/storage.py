"""
存储与状态管理：中间态放 cache/，最终文档放 output/。
用户只关心 output/ 的最终文档；cache/ 仅用于断点续跑。
"""
import os
import shutil

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CACHE_DIR = os.path.join(BASE_DIR, "cache")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")


def ensure_dirs() -> None:
    for d in (CACHE_DIR, OUTPUT_DIR):
        os.makedirs(d, exist_ok=True)


def cache_path(name: str) -> str:
    ensure_dirs()
    return os.path.join(CACHE_DIR, name)


def output_path(name: str) -> str:
    ensure_dirs()
    return os.path.join(OUTPUT_DIR, name)


def load_cache(name: str) -> str | None:
    """读缓存；不存在或含 FAILED 标记返回 None。"""
    p = cache_path(name)
    if not os.path.exists(p):
        return None
    try:
        with open(p, encoding="utf-8") as f:
            content = f.read()
    except OSError:
        return None
    if "FAILED" in content or not content.strip():
        return None
    return content


def save_cache(name: str, content: str) -> str:
    p = cache_path(name)
    with open(p, "w", encoding="utf-8") as f:
        f.write(content)
    return p


def save_output(name: str, content: str) -> str:
    p = output_path(name)
    with open(p, "w", encoding="utf-8") as f:
        f.write(content)
    return p


def clear_cache() -> None:
    """清空中间态缓存（用于强制全量重跑）。"""
    if os.path.exists(CACHE_DIR):
        shutil.rmtree(CACHE_DIR)
    ensure_dirs()
