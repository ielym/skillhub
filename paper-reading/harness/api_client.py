"""
API 客户端：封装对测试 API 的 chat 请求。
- 支持多模态（图片 base64）
- 自动重试（503 限流 / 5xx / 超时），指数退避
- 所有解析都走这里，本 harness 不自行理解论文内容
"""
import base64
import json
import os
import time

import requests

# 凭证/端点一律走环境变量，不写死在代码里。
BASE_URL = os.environ.get("PAPER_HARNESS_BASE_URL", "https://8888ok.cc/v1")
API_KEY = os.environ.get("PAPER_HARNESS_API_KEY", "")

# 候选模型：默认用 4.1-flash（自带视觉）；文本请求遇到该模型限流时自动轮换到备用模型。
# 有图请求固定用 4.1-flash（视觉能力），避免切到不支持图片的模型。
MODELS = ["deepseek-v4.1-flash", "deepseek-v4-pro", "deepseek-v4-flash"]
MODEL = MODELS[0]

MAX_RETRIES = 6
RETRY_BASE_DELAY = 10  # 秒，指数退避（该 API 有上游速率限制，需要更长退避）
REQUEST_TIMEOUT = 240  # 秒，该模型单次响应可能很慢（实测大请求成功需 ~137s）；超时过短会把有效慢响应当失败丢弃并重打，反而加剧上游排队


class APIError(Exception):
    pass


def _require_key() -> str:
    """取 API 凭证；未配置时给出明确报错，避免夹带密钥进入报错正文。"""
    if not API_KEY:
        raise APIError("未配置 PAPER_HARNESS_API_KEY 环境变量")
    return API_KEY


def chat(
    system: str,
    user_text: str,
    images: list | None = None,  # list of (base64_str, mime_type)
    max_tokens: int = 4096,
    temperature: float = 0.2,
    thinking: bool | None = None,
) -> dict:
    """调用 chat completions。返回完整响应 JSON。

    thinking=False 时下发 enable_thinking=false：实测该提供方在模型"思考"时
    偶发把思考链直接写进 content（reasoning_content 反而为空），导致成稿中
    出现「我需要/我们被要求」等自述文字；关掉思考可从根源消除该污染。
    """
    content: list = []
    if user_text:
        content.append({"type": "text", "text": user_text})
    if images:
        for b64, mime in images:
            content.append(
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:{mime};base64,{b64}"},
                }
            )

    payload = {
        "model": MODEL,
        "messages": [{"role": "system", "content": system}] if system else [],
    }
    if system:
        payload["messages"].append({"role": "user", "content": content})
    else:
        payload["messages"] = [{"role": "user", "content": content}]
    payload["max_tokens"] = max_tokens
    payload["temperature"] = temperature
    if thinking is not None:
        payload["enable_thinking"] = bool(thinking)

    headers = {
        "Authorization": f"Bearer {_require_key()}",
        "Content-Type": "application/json",
    }

    # 有图请求固定用视觉模型；文本请求在重试间轮换模型，规避单模型上游限流
    models = [MODEL] if images else MODELS

    last_err = None
    for attempt in range(1, MAX_RETRIES + 1):
        payload["model"] = models[(attempt - 1) % len(models)]
        try:
            resp = requests.post(
                f"{BASE_URL}/chat/completions",
                headers=headers,
                json=payload,
                timeout=(10, REQUEST_TIMEOUT),  # (连接超时, 读取超时)
            )
            if resp.status_code == 200:
                return resp.json()
            if resp.status_code == 429 or resp.status_code >= 500:
                last_err = f"{payload['model']} HTTP {resp.status_code}: {resp.text[:200]}"
                print(f"[api] 第{attempt}次失败({last_err})，{RETRY_BASE_DELAY * attempt}s 后重试...", flush=True)
                time.sleep(RETRY_BASE_DELAY * attempt)
                continue
            raise APIError(f"HTTP {resp.status_code}: {resp.text[:300]}")
        except requests.exceptions.Timeout:
            last_err = f"{payload['model']} timeout"
            print(f"[api] 第{attempt}次超时({last_err})，{RETRY_BASE_DELAY * attempt}s 后重试...", flush=True)
            time.sleep(RETRY_BASE_DELAY * attempt)
        except requests.exceptions.ConnectionError as e:
            last_err = f"{payload['model']} connection: {e}"
            print(f"[api] 第{attempt}次连接失败，{RETRY_BASE_DELAY * attempt}s 后重试...", flush=True)
            time.sleep(RETRY_BASE_DELAY * attempt)
    raise APIError(f"重试 {MAX_RETRIES} 次后仍失败: {last_err}")


def chat_text(system: str, user_text: str, min_chars: int = 0, **kw) -> str:
    """返回纯文本回复。

    - content 为空时重试（该模型偶发 content 为空，reasoning_content 仅思考链）。
    - min_chars > 0 时，非空但长度不足视为「截断响应」（限流/超长输出被服务端截断），也重试。
    - 全部重试仍失败：最后一次若有非空内容则返回它（降级），否则抛 APIError。
    """
    last = ""
    last_content = None
    for attempt in range(5):
        resp = chat(system, user_text, **kw)
        try:
            msg = resp["choices"][0]["message"]
            content = msg.get("content") or ""
            finish = msg.get("finish_reason")
            if content:
                last_content = content
                if len(content) >= min_chars:
                    return content
                last = f"内容截断({len(content)}字符, finish={finish}, min_chars={min_chars})"
            elif finish is None:
                # 服务端假成功响应（无 finish），按限流长退避
                last = "finish=None（服务端异常空响应）"
            else:
                last = f"content 为空 (finish={finish})"
        except (KeyError, IndexError):
            last = f"响应结构异常: {json.dumps(resp)[:200]}"
        print(f"[api] {last}，重试 {attempt+1}/5，{8 * (attempt + 1)}s 后...", flush=True)
        time.sleep(8 * (attempt + 1))
    if last_content is not None and min_chars <= 0:
        return last_content
    # min_chars > 0 表示调用方要求内容达标：宁可抛错重试，也不返回截断的降级结果
    raise APIError(f"5 次尝试后仍未取得达标内容: {last}")


def image_to_b64(path: str) -> tuple[str, str]:
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode(), "image/png"


def call_until_valid(fn, label: str, is_valid, base_delay: int = 15, max_wait: int = 120) -> str:
    """无限重试直到 fn() 成功且 is_valid(输出) 通过；期间指数退避 + 服务端健康闸。

    供 skim/source 等单轮管线使用，语义与 deep 的完整性铁律一致：不产出半成品。
    """
    attempt = 0
    while True:
        attempt += 1
        try:
            out = fn()
            if is_valid(out):
                return out
            print(f"[{label}] 第{attempt}次输出不合格，{min(max_wait, base_delay * attempt)}s 后重试...", flush=True)
        except APIError as e:
            print(f"[{label}] 第{attempt}次失败: {e}，{min(max_wait, base_delay * attempt)}s 后重试...", flush=True)
        time.sleep(min(max_wait, base_delay * attempt))
        if attempt % 5 == 0:
            while not ping(timeout=20, attempts=1):
                print(f"[{label}] API 不健康，120s 后重新探测...", flush=True)
                time.sleep(120)


def ping(timeout: int = 30, attempts: int = 5) -> bool:
    """服务端健康检查：发一个最小请求确认 API 可用。带多次重试，避免单次抖动误判。"""
    for attempt in range(1, attempts + 1):
        model = MODELS[(attempt - 1) % len(MODELS)]
        try:
            resp = requests.post(
                f"{BASE_URL}/chat/completions",
                headers={"Authorization": f"Bearer {_require_key()}", "Content-Type": "application/json"},
                json={
                    "model": model,
                    "messages": [{"role": "user", "content": "ping"}],
                    "max_tokens": 1,
                },
                timeout=timeout,
            )
            if resp.status_code != 200:
                print(f"[ping] API 响应异常 HTTP {resp.status_code}: {resp.text[:120]}", flush=True)
            else:
                data = resp.json()
                content = data.get("choices", [{}])[0].get("message", {}).get("content") or ""
                if content:
                    return True
        except Exception as e:  # noqa: BLE001
            print(f"[ping] 第{attempt}/{attempts}次不可用: {e}", flush=True)
        if attempt < attempts:
            time.sleep(10 * attempt)
    return False
