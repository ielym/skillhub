"""
精读管线（deep-read）：三遍法。
R1 框架轮 → R2 分块精读 → R3 批判轮 → FINAL 聚合九章节文档。
中间产物进 cache/，只有最终文档写入 output/。

完整性铁律：任何一轮/分块失败都必须重试，直到成功；绝不允许带着
「内容缺失 / 解析失败」进入 FINAL，更不允许降级输出不完整文档——
不完整就继续重试，重试到成功为止，否则抛错终止（不产出半成品）。
"""
import os
import re
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

import api_client
import pdf_parser
import storage
from prompts import DEEP_FINAL_SYS, DEEP_SYS

# ============================================================
# 各轮 user prompt（只描述本轮任务，全局规范在 system prompt）
# 注意：中间产物不得再使用「块笔记/框架轮/内容轮/批判轮」等内部术语，
#       否则会污染最终文档；一律用中性词。
# ============================================================

R1_PROMPT = """这是论文的【开头与结尾部分】。请完成第一遍阅读，输出：
1. 【论文基础信息·逐字转录】标题（完整英文标题，含主副标题，一字不差）、作者姓名、作者机构、发布日期、期刊/预印本编号（如有）。标题必须原样逐字抄录，不得概括、不得改写、不得遗漏。
2. 5C 总结：Category(类型) / Context(领域与理论) / Correctness(关键假设) / Contributions(贡献) / Clarity(清晰度)
3. 一句话表述可证伪的研究问题
4. 章节标题骨架
5. 5 个关键数字或主张（若有）

只依据给定文本，缺失标「论文未说明」。

【材料】
{content}"""

R2_PROMPT = """这是论文的【第 {page_min}–{page_max} 页】（页码范围 {pages}）。请做内容精读，输出本部分的结构化要点：
1. 本部分主题/章节
2. 核心方法与机制（公式符号含义、数据流）
3. 关键数字与结论（标注页码）
4. 图表发现（轴/单位/关键数值/误差棒/是否可疑）
5. 与前文/后文的衔接
6. 疑点或需批判处

每个重要论断标注页码；缺失标「论文未说明」。

【本部分文本】
{content}"""

R3_PROMPT = """以下是论文各部分的精读要点。请做批判审读，输出：
1. 声称 vs 证据对照表（是否 overclaim）
2. 核心假设清单及失效场景
3. 实验充分性评估（基线公平性、消融、误差棒、泛化）
4. 工程可复现性评估（公开程度、算力、复现难点）
5. 局限与风险（作者承认的 vs 分析得出的）
6. ≥5 个批判问题（实验设计/方法假设/评测方式/外推性）
7. ≥3 条可迁移结论/方法要点及适用条件

每条标注来源页码；无法确认标「论文未说明」。

【精读要点汇总】
{notes}"""

# 九章节结构：编号 / 标题 / 该章写作要求。
# FINAL 不再一次性生成整篇（单次超长生成在限流 API 上极易超时/截断），
# 改为逐章生成、逐章校验、逐章缓存，最后拼装——任一章失败只重试该章。
CHAPTERS = [
    (1, "论文基本信息", "逐字完整转录标题（含主副标题）、全部作者、作者机构、发表时间、期刊/预印本编号、论文与代码链接（无则说明）。随后写：研究问题、应用场景、论文定位；完整摘要原文及其中文翻译；可信度评级（A–D）及理由。"),
    (2, "一句话总结", "用一句话说清「解决了什么问题 + 用什么核心方法 + 得到什么结果」。"),
    (3, "研究背景与相关工作", "问题为何重要；现有路线与局限（写成「方法 X 在条件 Y 下失败，因为 Z」）；本文填补的空白与结论的普适性边界。"),
    (4, "核心贡献与结论", "作者声称的贡献与关键结论；贡献类型（理论/算法/工程/实验）；区分真正新东西 vs 组合优化；核对声称 vs 实际支撑；指出 overclaim。"),
    (5, "方法细节", "假设/设定/输入输出；模型结构或算法流程（用 Mermaid flowchart，覆盖输入→核心模块→输出，标注关键数据）；逐条解释核心公式（符号/维度/假设/推导步骤/直觉）；训练目标与关键超参；数据构造；推理机制与复杂度。"),
    (6, "实验分析", "设置与基线公平性；指标是否真实（方差/CI/多次运行）；消融是否充分；关键结果及实际意义；反常/失败/负面结果；泛化与稳健性。"),
    (7, "工程可复现性", "代码/模型/数据/日志是否公开及许可证；数据与算力规模；最小可行复现步骤；实现难点与未披露细节。本章结尾给出 ≥3 条可迁移结论/方法要点，并注明各自适用条件。"),
    (8, "局限与风险", "关键假设与失效场景；实验缺失/数据污染/基准泄漏；成本/稳定性/安全风险；区分作者承认的与分析得出的。本章结尾给出 ≥5 个批判问题，覆盖实验设计/方法假设/评测方式/外推性。"),
    (9, "证据索引与未披露清单", "汇总本文最重要的 10–14 条判断（不要逐图逐表穷举），逐条简短给出其在论文中的定位（页码/章节/公式/图/表）并标注【论文事实】【作者观点】【AI 分析】，每条不超过两行。另列材料确实未披露、只能标「论文未说明」的内容清单（8–12 条）。整章简洁收口。"),
]

# 每章最小字符数与输出 token 上限（越小越容易在限流 API 上稳定返回）
_CH_MIN = {1: 600, 2: 120, 3: 500, 4: 450, 5: 800, 6: 600, 7: 500, 8: 600, 9: 400}
_CH_TOKENS = {1: 4000, 2: 1800, 3: 5000, 4: 5000, 5: 5500, 6: 4500, 7: 5000, 8: 4500, 9: 6000}

CHAPTER_PROMPT = """下面是一篇论文的全部资料，分四部分：
① 论文首页原文（逐字，用于准确转录标题/作者/机构/日期）；
② 论文框架信息（类型、理论背景、关键假设、贡献、章节骨架、研究问题）；
③ 正文要点（各页的方法、公式、数字、图表、结论，均标注页码）；
④ 批判审读（声称与证据对照、假设与失效场景、复现性、局限与风险、批判问题、可迁移结论）。

现在要产出【九章节精读文档】中的第 §{num} 章，章节标题为「{title}」。
只输出这一章：不要输出其它章节，不要输出目录，不要输出任何前言、说明或结束语。

本章写作要求：
{focus}

通用写作规范（必须遵守）：
- 直接展开本章正文，不要写目录、前言、结束语，也不要重述本章标题。
- 输出完整、连贯的成稿，读者看不出它由分章拼成；只写本章内容，不得混入其它章节。
- 全文按一篇通读后写成的成稿呈现，不得出现任何流程性或阶段性措辞。
- 标题、作者、机构、日期等基础信息必须从首页原文逐字完整转录，不得改写、不得省略。
- 图表给出分析与关键数值（它证明的结论、单位、误差棒），但不要写任何写法说明或元话术。
- 公式行内用 $...$、独立成行用 $$...$$；流程图用 Mermaid flowchart。
- 每个重要论断标注页码/章节/图/表，并使用【论文事实】【作者观点】【AI 分析】标签。
- 上文已给出的信息必须完整采用；只有上文确实没有的信息才标注「论文未说明」。
- 本章必须以一个完整句子收尾（最后以句号、问号或收口标点结束）；不得停在半句、半条列表项或未写完的公式上，也不得在结尾复述或讨论本章的写作要求。

【资料】
{merged}"""

# 模型自述推理的痕迹：一旦出现在成稿里就说明材料/生成被污染，必须重做
META_MARKERS = (
    "我需要", "我只要", "我尝试", "我考虑", "我决定", "我打算", "我应该",
    "让我", "用户要求", "用户提供", "用户提出", "提示模板", "模板是",
    "本块主题", "这一轮", "不完整的输入", "生成R2", "生成 R2", "R2要点", "R2 要点",
    "我们被要求", "我们需要", "我们要输出", "被要求做", "输出以下部分",
)

# 最终文档中绝不允许出现的管线内部术语（命中即判定不完整，触发重试）
FORBIDDEN_TERMS = [
    "未完整转录", "未完整", "内容缺失", "解析失败",
    "块笔记", "产物", "分块", "框架轮", "内容轮", "批判轮",
    "研究材料", "框架概览", "按页笔记",
]


# 最终成稿中禁止出现的「复述任务/自我规划」痕迹。
# 实测 §2 整章曾退化为中文思考链（逐句复述本章要求并反复权衡），且结尾半句截断；
# 这类文本中文占比很高、开头也不含英文元话语，故单列一组标记，只在成稿校验中使用
# （不并入 META_MARKERS，以免误伤已通过校验的 R1/R2/R3 缓存）。
_PLANNING_MARKERS = (
    "我们只需", "任务说", "规范说", "通用规范说", "只输出这一章",
    "不要输出其它章节", "也许应", "这里冲突", "需要判断结果数字",
    "需要平衡", "需要仔细分析", "这算一句", "可以写成", "那么一句话",
    "必须完整信息", "需要严格按照规范", "任务又明确说", "规范中说",
    "本章写作要求", "写作要求",
)


_CH_TITLES = {num: title for num, title, _ in CHAPTERS}


def _cross_chapter_leak(body: str, num: int) -> int | None:
    """判断本章正文是否夹带了【其它章节的章节级标题】。

    只把「带 § 记号」或「编号与其它章标题文字同时出现」的标题行视为串章；
    单纯的 "### 1. 设置" 这类带编号子标题不算——否则每章都会误判、
    导致本章永远无法通过校验。
    """
    for line in re.findall(r"^#{1,4}[^\n]*", body, re.M):
        s = line.strip()
        m = re.match(r"^#{1,4}\s*(?:§\s?)?(\d{1,2})\b", s)
        n = int(m.group(1)) if m else None
        if n is None or n == num:
            continue
        title = _CH_TITLES.get(n)
        if title and title in s:
            return n
    return None


def _final_complete(out: str) -> tuple[bool, str]:
    """完整性校验：九章节齐全，且无管线内部术语。返回 (是否通过, 未通过原因)。"""
    if len(out) < 2500:
        return False, f"过短({len(out)}字符)"
    for term in FORBIDDEN_TERMS:
        if term in out:
            return False, f"含禁词「{term}」"
    heads = re.findall(r"^## §(\d{1,2})\.\s", out, re.M)
    if sorted(int(h) for h in heads) != list(range(1, 10)):
        return False, f"章节标题异常 {heads}"
    if _truncated_body(out.split("\n\n", 1)[1] if "\n\n" in out else out):
        return False, "全文结尾被截断"
    return True, ""


# ============================================================
# 元信息逐字校验：最终文档 §1 的标题/作者/机构/编号必须能在论文首页原文中
# 一字不落地找到（首页原文即 ground truth），否则视为模型虚构/改写 → 触发重做。
# 编号与标题为硬校验（不通过即重做），作者/机构/时间为软校验（仅告警日志，不重做，
# 避免因排版差异误杀）。仅当首页确实检出编号时才启硬校验（无编号的论文标「论文未说明」）。
# ============================================================
def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", s or "").strip()


def _extract_arxiv_id(pages: list[dict]) -> str | None:
    """从论文首页优先检出 arXiv 编号（页脚戳经 _repair_rotated_stamp 已还原到页首）。"""
    texts = [p.get("text") or "" for p in pages]
    for t in texts[:2]:
        m = re.search(r"arXiv\s*[:]?\s*(\d{4}\.\d{4,5})", t, re.I)
        if m:
            return m.group(1)
    for t in texts[2:]:
        m = re.search(r"arXiv\s*[:]?\s*(\d{4}\.\d{4,5})", t, re.I)
        if m:
            return m.group(1)
    return None


def _front_text(pages: list[dict]) -> str:
    """首页+次页原文（归一化），作为逐字比对的 ground truth。"""
    return _norm("\n".join(p.get("text") or "" for p in pages[:2]))


def _field(body: str, label: str) -> str | None:
    """提取 §1 中形如「**标签**：值」的单行字段值（容忍首尾加粗记号与中英冒号）。"""
    m = re.search(rf"^\*{{0,2}}{re.escape(label)}\*{{0,2}}\s*[：:]\s*(.+?)\s*$", body, re.M)
    return m.group(1).strip() if m else None


def _verify_meta(section: str, src: dict) -> list[str]:
    """校验 §1 的元信息与首页原文一致。返回问题列表（空=通过）。"""
    pages = src.get("pages", [])
    if not pages:
        return []
    body = section.split("\n", 1)[1] if "\n" in section else ""
    front = _front_text(pages)
    arx_id = _extract_arxiv_id(pages)

    title = _field(body, "论文标题（逐字）")
    author = _field(body, "作者")
    inst = _field(body, "作者机构")
    date = _field(body, "发表时间")
    arx = _field(body, "预印本编号")

    problems: list[str] = []

    # 编号（硬）：首页检出编号时，§1 必须包含同一编号
    if arx_id is not None:
        if not arx or arx_id not in _norm(arx):
            problems.append(f"预印本编号与首页不符（原文 {arx_id}，文档 {arx}）")

    # 标题（硬）：必须逐字出现在首页原文中
    if not title:
        problems.append("缺少论文标题字段")
    elif _norm(title) not in front:
        problems.append("标题与首页原文不符（疑似改写或虚构）")

    # 作者/机构（硬）：首段（首个姓名/机构）必须出现在首页原文
    def _head_token(val: str) -> str:
        return re.split(r"[、,，;/&]| and | 与 |\n", val.strip(), maxsplit=1)[0].strip()

    if author and author not in ("论文未说明", "来源未说明"):
        if _head_token(author) and _head_token(author) not in front:
            problems.append(f"作者与首页原文不符（{author}）")
    if inst and inst not in ("论文未说明", "来源未说明"):
        if _norm(inst) and _norm(inst) not in front and _head_token(inst) not in front:
            problems.append(f"作者机构与首页原文不符（{inst}）")
    # 日期为软校验：排版差异大，不并入硬 problems，仅告警留痕
    if date and date not in ("论文未说明", "来源未说明"):
        if _norm(date) and _norm(date) not in front:
            print(f"[FINAL §1] 提示：发表时间「{date}」未在首页原文逐字找到，请人工复核", flush=True)

    return problems


def _meta_ok(section: str, src: dict) -> tuple[bool, str]:
    probs = _verify_meta(section, src)
    if probs:
        return False, "元信息不符: " + "; ".join(probs)
    return True, ""

# 旧缓存中可能残留的内部术语 → 中性替换（降低 FINAL 回显风险）
_INTERNAL_FIX = {
    "块笔记": "要点",
    "框架轮": "",
    "内容轮": "",
    "批判轮": "批判",
    "聚合轮": "",
    "产物": "",
    "分块": "",
    "研究材料": "材料",
    "FINAL聚合": "汇总",
    "FINAL": "",
    "第一遍阅读": "",
    "第二遍阅读": "",
    "第三遍阅读": "",
}

# 旧缓存（早期 prompt 生成）里夹带了模型自述的推理过程，这些行是纯噪声：
# 留着会诱导最终文档回显「块笔记/内容轮」等流程术语，直接丢弃整行。
_DROP_MARKERS = (
    "块笔记", "内容轮", "框架轮", "批判轮", "聚合轮", "三遍法",
    "我可以为", "要注意不要", "最后加一个",
    "第一遍阅读", "第二遍阅读", "第三遍阅读",
    "好的，", "好的,", "接下来组织",
) + META_MARKERS


def _sanitize_internal(text: str) -> str:
    """清洗中间产物：丢弃模型自述推理行，并把残留流程术语替换为中性词。"""
    kept = [ln for ln in text.splitlines() if not any(m in ln for m in _DROP_MARKERS)]
    text = "\n".join(kept)
    for a, b in _INTERNAL_FIX.items():
        text = text.replace(a, b)
    return text


# 模型自述/思考过程的"开头痕迹"（中英双语）。
# 关键教训：中文 marker 挡不住英文推理转储——实测中出现过整章都是
# "The user is asking me to ... / Let me now ..." 的英文思考链，必须纳入检测。
_PREAMBLE_MARKERS = (
    "the user is asking", "the user wants", "the user provided", "the user asks",
    "the user requested", "the user is", "let me", "i need to", "i'll ", "i will now",
    "now let me", "here's", "here is the", "sure,", "okay,", "alright,", "first, i",
    "i should", "i want to", "let's ", "as an ai", "looking at the", "let me think",
    "let me draft", "let me structure", "let me write", "let me reconsider",
) + META_MARKERS


def _cjk_ratio(text: str) -> float:
    if not text:
        return 0.0
    cjk = sum(1 for c in text if "\u4e00" <= c <= "\u9fff")
    return cjk / len(text)


def _reasoning_leak(body: str) -> str | None:
    """检测模型把思考过程/自我陈述写进正文。

    正文应当是中文成稿：开头若出现元话语（"让我…/我需要…/The user is asking…"），
    或整体中文占比过低（英文思考链转储），都判为无效生成。
    """
    head = body[:400].lower()
    for m in _PREAMBLE_MARKERS:
        if m.lower() in head:
            return f"开头含思考或自述痕迹「{m}」"
    ratio = _cjk_ratio(body)
    if ratio < 0.25:
        return f"中文占比过低({ratio:.2f})，疑似思考过程转储"
    return None


# 正文允许的收口字符：句末标点、右引号/括号、引用标签「】」、表格行「|」、代码围栏反引号。
# 注意不含「$」——若模型把公式写到一半停住被截断，结尾常停在「$」上，需要判为截断。
_SAFE_TAIL_CHARS = set("。！？…；：.!?”\"』】）)]}`|")


def _truncated_body(body: str) -> bool:
    """判断正文是否被截断（结尾停在半句/半条列表/半个公式上，属"内容不完整"，必须重做）。

    只看正文【最后一行】是否收口：必须以句末标点、右括号/引号、引用标签、表格行或
    代码围栏结尾。旧实现是"最后 40 字里出现过标点就算收口"，会把
    「……成立；论文没有在」这类半句误判为完整，故改为按结尾字符判定。

    例外：最末行若仅为数学围栏（独立成行的 $$ 或 $，闭合 display 块），视为完整——
    「以独立公式收尾」属合法结尾；但行内 $...$（句未标点仍未出现）仍判截断，
    以免把「……与边际价值 $MV_1(θ)$」这种半句误放行。
    """
    lines = body.splitlines()
    while lines and not lines[-1].strip():
        lines.pop()
    if not lines:
        return True
    last = lines[-1].strip()
    if last.startswith("```"):  # 以代码围栏/图围栏收尾
        return False
    if last.replace("$", "").strip() == "":  # 末行仅为 $$ 或 $（闭合的公式围栏）
        return False
    return last[-1] not in _SAFE_TAIL_CHARS


def _strict_clean(text: str, label: str, min_len: int) -> str:
    """中间产物强校验：清洗后若仍含自述痕迹或过短，判为无效生成，触发重试。"""
    cleaned = _sanitize_internal(text)
    for m in META_MARKERS:
        if m in cleaned:
            raise api_client.APIError(f"[{label}] 输出含模型自述痕迹「{m}」")
    leak = _reasoning_leak(cleaned)
    if leak:
        raise api_client.APIError(f"[{label}] {leak}")
    if len(cleaned) < min_len:
        raise api_client.APIError(f"[{label}] 清洗后内容过短({len(cleaned)}字符)")
    return cleaned


def _call_with_retry(fn, label: str, attempts: int | None = None, base_delay: int = 15) -> str:
    """调用 fn，失败则退避重试。

    完整性铁律：attempts=None 表示无限重试，绝不放弃、绝不产出半成品；
    重试过久（API 长时间不可用）时插入健康闸，避免空烧请求加剧限流。
    """
    attempt = 0
    while True:
        attempt += 1
        try:
            return fn()
        except Exception as e:  # noqa: BLE001
            if attempts is not None and attempt >= attempts:
                raise api_client.APIError(f"[{label}] 重试 {attempts} 次后仍失败: {e}")
            wait = min(120, base_delay * attempt)
            print(f"[{label}] 第{attempt}次失败: {e}，{wait}s 后重试...", flush=True)
            time.sleep(wait)
            if attempt % 5 == 0:
                _wait_api(label)


def _r1(src: dict) -> str:
    pages = src["pages"]
    head = "\n".join(f"--- 第{p['page']}页 ---\n{p['text']}" for p in pages[:5] if p["text"])
    tail = "\n".join(f"--- 第{p['page']}页 ---\n{p['text']}" for p in pages[-4:] if p["text"])
    content = f"{head}\n\n[论文结尾部分]\n{tail}"
    print("[R1] 第一遍阅读 ...", flush=True)
    return api_client.chat_text(DEEP_SYS, R1_PROMPT.format(content=content[:28000]))


def _r2_chunk(src: dict, chunk: dict, fig_pages: list[int]) -> str:
    images = []
    for p in chunk["pages"]:
        if p in fig_pages:
            img = pdf_parser.render_page(src["path"], p)
            images.append(api_client.image_to_b64(img))
    prompt = R2_PROMPT.format(
        pages=",".join(map(str, chunk["pages"])),
        page_min=min(chunk["pages"]),
        page_max=max(chunk["pages"]),
        content=chunk["text"][:26000],
    )
    out = api_client.chat_text(DEEP_SYS, prompt, images=images)
    return _strict_clean(out, f"R2 页{min(chunk['pages'])}-{max(chunk['pages'])}", 300)


def _r2_chunk_retry(src: dict, chunk: dict, fig_pages: list[int], page_map: dict) -> str:
    """单块不放弃：先整块重试 6 次，再降级为单页精读（无限重试，绝不产出半成品）。"""
    label = f"R2 页{min(chunk['pages'])}-{max(chunk['pages'])}"
    try:
        return _call_with_retry(lambda: _r2_chunk(src, chunk, fig_pages), label, attempts=6, base_delay=15)
    except api_client.APIError:
        pass
    if len(chunk["pages"]) > 1:
        print(f"[{label}] 整块失败，降级为单页精读 ...", flush=True)
        sub = []
        for p in chunk["pages"]:
            pg = page_map[p]
            one = {"pages": [p], "text": f"--- 第{p}页 ---\n{pg['text']}"}
            sub.append(
                _call_with_retry(
                    lambda one=one: _r2_chunk(src, one, fig_pages),
                    f"{label} 单页{p}",
                )
            )
        return "\n\n".join(sub)
    return _call_with_retry(lambda: _r2_chunk(src, chunk, fig_pages), label)


def _r3(notes_text: str) -> str:
    print("[R3] 批判审读 ...", flush=True)
    out = api_client.chat_text(DEEP_SYS, R3_PROMPT.format(notes=notes_text[:30000]))
    return _strict_clean(out, "R3", 800)


def _wait_api(label: str) -> None:
    """健康闸：限流期不空烧重试，改为长间隔探测，避免加剧账号级限流。"""
    while not api_client.ping(timeout=20, attempts=1):
        print(f"[{label}] API 不健康，120s 后重新探测...", flush=True)
        time.sleep(120)


def _dump_rejected(name: str, content: str) -> None:
    try:
        p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "cache", name)
        with open(p, "w", encoding="utf-8") as f:
            f.write(content)
    except OSError:
        pass


def _normalize_section(num: int, title: str, out: str) -> str:
    """去掉模型可能自带的本章标题行，统一由 harness 输出规范章节标题。"""
    lines = out.strip().splitlines()
    while lines and not lines[0].strip():
        lines.pop(0)
    if lines:
        first = lines[0].strip()
        m = re.match(r"^#{1,2}\s*(?:§\s?)?(\d{1,2})\b", first)
        if first.startswith("#") and ((m and int(m.group(1)) == num) or "§" in first or title in first):
            lines.pop(0)
    body = "\n".join(lines).strip()
    return f"## §{num}. {title}\n\n{body}"


def _chapter_ok(num: int, body: str) -> tuple[bool, str]:
    """单章正文校验：长度、禁词、自述痕迹、是否截断、不得串入其它章节。"""
    if len(body) < _CH_MIN[num]:
        return False, f"过短({len(body)}字符)"
    for term in FORBIDDEN_TERMS:
        if term in body:
            return False, f"含禁词「{term}」"
    for term in META_MARKERS:
        if term in body:
            return False, f"含模型自述痕迹「{term}」"
    for term in _PLANNING_MARKERS:
        if term in body:
            return False, f"含复述任务/自我规划痕迹「{term}」"
    leak = _reasoning_leak(body)
    if leak:
        return False, leak
    if _truncated_body(body):
        return False, "正文结尾被截断（内容不完整）"
    leak_ch = _cross_chapter_leak(body, num)
    if leak_ch is not None:
        return False, f"串入其它章节 {leak_ch}"
    return True, ""


def _make_chapter(merged: str, num: int, title: str, focus: str, extra_ok=None) -> str:
    """生成单章：健康闸 → 调用 → 校验 → 不通过则重试（直到成功）。

    extra_ok(section) 为可选附加校验（返回 (bool, reason)）；§1 借此接入元信息逐字校验。
    """
    label = f"FINAL §{num}"
    prompt = CHAPTER_PROMPT.format(num=num, title=title, focus=focus, merged=merged)
    attempt = 0
    while True:
        attempt += 1
        _wait_api(label)
        try:
            out = api_client.chat_text(
                DEEP_FINAL_SYS, prompt, max_tokens=_CH_TOKENS[num], min_chars=_CH_MIN[num],
                thinking=False,
            )
        except api_client.APIError as e:
            wait = min(60, 10 * attempt)
            print(f"[{label}] 第{attempt}次调用失败: {e}，{wait}s 后重试...", flush=True)
            time.sleep(wait)
            continue
        section = _normalize_section(num, title, out)
        body = section.split("\n", 1)[1].strip() if "\n" in section else ""
        ok, reason = _chapter_ok(num, body)
        if ok and extra_ok is not None:
            ok, reason = extra_ok(section)
        if ok:
            return section
        _dump_rejected(f"debug_final_rejected_ch{num}.md", out)
        wait = min(60, 10 * attempt)
        print(f"[{label}] 第{attempt}次输出不合格({len(out)}字符, 原因:{reason})，{wait}s 后重试...", flush=True)
        time.sleep(wait)


def _final(src: dict, r1: str, notes_text: str, r3: str) -> str:
    print("[FINAL] 逐章生成九章节文档 ...", flush=True)
    # 首页原文逐字注入，保证标题/作者/机构可完整转录
    head_text = "\n".join(
        f"--- 第{p['page']}页 ---\n{p['text']}" for p in src["pages"][:2] if p["text"]
    )
    merged = "\n\n".join(
        [
            "【论文首页原文】\n" + head_text,
            "【论文框架信息】\n" + _sanitize_internal(r1),
            "【正文要点】\n" + _sanitize_internal(notes_text),
            "【批判审读】\n" + _sanitize_internal(r3),
        ]
    )
    merged = merged[:80000]

    parts = []
    for num, title, focus in CHAPTERS:
        key = f"deep_final_ch{num}.md"
        extra_ok = (lambda s: _meta_ok(s, src)) if num == 1 else None
        cached = storage.load_cache(key)
        if cached is not None:
            body = cached.split("\n", 1)[1].strip() if "\n" in cached else ""
            ok, why = _chapter_ok(num, body)
            if ok and extra_ok is not None:
                ok, why = extra_ok(cached)
            if ok:
                print(f"[FINAL] §{num} {title} 复用缓存", flush=True)
                parts.append(cached)
                continue
            print(f"[FINAL] §{num} {title} 缓存无效({why})，重新生成 ...", flush=True)
        print(f"[FINAL] §{num} {title} 生成中 ...", flush=True)
        section = _make_chapter(merged, num, title, focus, extra_ok=extra_ok)
        storage.save_cache(key, section)
        parts.append(section)

    doc = "# 论文精读文档\n\n" + "\n\n".join(parts) + "\n"
    ok, reason = _final_complete(doc)
    if not ok:  # 逐章已校验，此处仅作兜底
        raise api_client.APIError(f"最终文档完整性兜底校验未通过: {reason}")
    return doc


def run(src: dict, chunk_size: int = 4, overlap: int = 0) -> str:
    pages = src["pages"]
    fig_pages = src.get("fig_pages", [])
    page_map = {p["page"]: p for p in pages}

    # R1（断点续跑；失败重试直到成功。复用缓存前先校验，污染缓存一律重做）
    r1 = storage.load_cache("deep_r1.md")
    if r1 is not None:
        try:
            r1 = _strict_clean(r1, "R1缓存", 300)
            print("[R1] 复用缓存", flush=True)
        except api_client.APIError as e:
            print(f"[R1] 缓存无效({e})，重新生成 ...", flush=True)
            r1 = None
    if r1 is None:
        r1 = _call_with_retry(lambda: _r1(src), "R1")
        storage.save_cache("deep_r1.md", r1)

    # R2（断点续跑；每块失败即重试，绝不跳过。复用缓存前先校验）
    chunks = pdf_parser.chunk_pages(pages, chunk_size, overlap)
    print(f"[R2] 共 {len(chunks)} 个分块", flush=True)
    notes = []
    for i, ch in enumerate(chunks, 1):
        key = f"deep_r2_{i}.md"
        cached = storage.load_cache(key)
        if cached is not None:
            try:
                cached = _strict_clean(cached, f"R2缓存{i}", 300)
                print(f"[R2] 分块 {i}/{len(chunks)} 复用缓存", flush=True)
                notes.append(cached)
                continue
            except api_client.APIError as e:
                print(f"[R2] 分块 {i}/{len(chunks)} 缓存无效({e})，重新生成 ...", flush=True)
        print(f"[R2] 分块 {i}/{len(chunks)}（页 {min(ch['pages'])}-{max(ch['pages'])}）...", flush=True)
        note = _r2_chunk_retry(src, ch, fig_pages, page_map)
        notes.append(note)
        storage.save_cache(key, note)

    notes_text = "\n\n".join(notes)

    # R3（断点续跑；失败重试直到成功。复用缓存前先校验）
    r3 = storage.load_cache("deep_r3.md")
    if r3 is not None:
        try:
            r3 = _strict_clean(r3, "R3缓存", 800)
            print("[R3] 复用缓存", flush=True)
        except api_client.APIError as e:
            print(f"[R3] 缓存无效({e})，重新生成 ...", flush=True)
            r3 = None
    if r3 is None:
        r3 = _call_with_retry(lambda: _r3(_sanitize_internal(notes_text)), "R3")
        storage.save_cache("deep_r3.md", r3)

    # FINAL 聚合（重试直到完整；失败抛错，绝不降级输出）
    return _final(src, r1, notes_text, r3)