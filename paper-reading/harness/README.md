# 论文/资料解析 Harness（多模式）

> **定位**：本 harness 仅为 `paper-reading` skill 的一个**示例实现**，用于演示「用外部 API 分轮解析」的思路，并非 skill 的组成部分或默认路径。支持使用者**自定义或在此基础上优化调整**（换 API、改管线、改写 prompt 等）。它不得反向修改或覆盖 skill 的 `references/` 目标规则。
> 约束：一切解析走测试 API；工具只用免费方案；harness 自身不做内容理解

---

## 0. 配置（环境变量）

凭证与端点**不写死在代码里**，通过环境变量注入：

| 变量 | 必填 | 说明 |
|---|---|---|
| `PAPER_HARNESS_API_KEY` | ✅ | API 访问密钥（ak/sk） |
| `PAPER_HARNESS_BASE_URL` | ❌ | API 端点，默认 `https://8888ok.cc/v1` |

```bash
export PAPER_HARNESS_API_KEY="sk-..."
python3 main.py paper.pdf --mode deep
```

未设置 `PAPER_HARNESS_API_KEY` 时，任何 API 调用会明确报错退出，不会静默失败。

---

## 1. 能力总览

对齐 `paper-reading` skill 的三个子规则，一个入口、三种模式：

| 模式 | 对应子规则 | 产出 | 方法 |
|---|---|---|---|
| `deep` | 论文精读 | 九章节完整文档 | 三遍法（R1 框架 → R2 分块 → R3 批判 → FINAL 聚合） |
| `skim` | 论文泛读 | 一张决策卡（精读/存档/弃/引用） | 元信息 + 结构 + 关键图表 + 结论 |
| `source` | 非论文来源 | 结构化整理（事实/观点/疑点/行动项） | 单轮 |

三个模式共用：`api_client`（API 调用+重试）、`pdf_parser`（PDF 解析）、`prompts`（专业 system prompt）、`storage`（缓存/输出）。

---

## 2. 架构

```
input (PDF / 文本文件 / 直接文本)
   │
   ▼
main.py ── 路由 ──> mode=deep / skim / source
   │
   ▼
┌────────────────────────────────────────────────────┐
│ 输入解析层（本地免费工具，无语义理解）                  │
│  pdfplumber 文本 + 表格 │ PyMuPDF 渲染页面 │ 图页检测 │
└────────────────────────────────────────────────────┘
   │
   ▼
┌────────────────────────────────────────────────────┐
│ 编排层（全部走测试 API，多轮）                        │
│  deep  : R1→R2(分块)→R3→FINAL                        │
│  skim  : 单轮（渲染前3含图页 + 一次出完整决策卡）      │
│  source: 单轮                                        │
└────────────────────────────────────────────────────┘
   │
   ▼
storage: 中间产物 → cache/（断点续跑）
         最终文档 → output/（用户唯一关注点）
```

---

## 3. 使用方式

```bash
# 论文精读（默认）
python3 main.py paper.pdf --mode deep --chunk 4

# 论文泛读（决策卡）
python3 main.py paper.pdf --mode skim

# 非论文来源（直接传文本或文件）
python3 main.py "blog 文本内容..." --mode source
python3 main.py release_notes.md --mode source

# 其他选项
--chunk N      R2 分块页数（deep，默认 4）
--overlap N    分块重叠（deep，默认 0）
--fig-pages    手动指定渲染图片的页
--no-cache     忽略缓存强制重跑
--dry-run      只做输入解析不调 API
--out NAME     最终文档文件名
```

**用户只关注 `output/` 下的最终文档**；`cache/` 是断点续跑中间态，可随时删除。

---

## 4. 专业 system prompt

`prompts.py` 从 skill 子规则提炼三个 system prompt，每个都包含：

- **共享底座**：只依据材料作答、来源标注、标签体系（【论文事实】【作者观点】【AI 分析】）、Markdown+飞书兼容（`$...$`/`$$...$$` 公式、Mermaid）、数值可对比性。
- **deep**：三遍法分工、图表类型学 T1–T8 + 通用四问、九章节交付结构、可信度 A–D、完成检查（≥5 批判问题 / ≥3 可迁移项）。
- **skim**：阅读顺序、Kill Criteria 六条、相关度 0–5 与可信度 A–D 评分、决策矩阵、泛读卡格式。
- **source**：一手>二手、事实/观点分离、交叉验证、立场标注、时效衰减、可行动化、按来源类型关注点、六段输出结构。

---

## 5. 关键工程决策（实测依据）

| 决策 | 原因 |
|---|---|
| 分块多轮而非单轮全塞 | 上下文 ≥200k 但长上下文+长输出质量塌陷；三遍法本身递进依赖 |
| deep 分块 4 页/块 | 每块 4–8k token，稳定 |
| 图页双信号检测 | 论文图表多为矢量图，`get_images` 只检出 2/16 页，加 `get_drawings` 后 16/16 |
| 多模态内联 base64 | 该 API 的 flash 模型自带视觉，无需额外 OCR |
| 重试+容错+断点续跑 | 实测 503/finish=None/content 空高频出现，必须重试；单块失败不终止；中断可续跑 |
| 中间态进 cache/ | 用户只关心最终文档，中间产物仅服务断点续跑 |

---

## 6. 成本与规模预估

| 模式 | API 调用数（96 页论文） |
|---|---|
| deep | 1(R1) + 24(R2, chunk=4) + 1(R3) + 1(FINAL) ≈ 27 |
| skim | 1（单轮决策卡，附前 3 含图页图片输入） |
| source | 1 |

单次 20–90s（含重试），deep 全流程约 30–60 分钟（**API 高峰期可达 2–3 小时**，因限流重试频繁）。

---

## 7. 实测验证状态（2026-10-06）

| 模式 | 状态 | 产物 | 结果 |
|---|---|---|---|
| `deep` | ✅ R1/R2/R3/FINAL 全链路验证 | `output/deep_read_notes.md` | 九章节结构、标签体系、页码定位均正确；24 分块断点续跑 + 单块容错生效（个别块因 API 空响应失败后自动跳过，重跑自动补齐） |
| `skim` | ✅ 端到端验证 | `output/skim_card.md` | 单轮输出完整决策卡，含元信息/结构骨架/评分/一句话结论/关键数字/「决策：精读」及 3 条理由 |
| `source` | ✅ 端到端验证 | `output/source_notes.md` | 六段结构化整理，事实/观点分离、疑点交叉验证、行动项齐全 |

**API 稳定性注意事项**（测试环境）：

- 服务端限流严重：高频出现 `HTTP 502`、`finish=None` 空响应、`content` 为空（仅 `reasoning_content` 有值）。
- 空响应不能把思考链当答案：`chat_text` 已对空 content 最多重试 5 次；main.py 兜底还会截断混入缓存的思考链特征段。
- 高峰期 deep 全量（24 块）可能需 2–3 小时，多数时间在重试；`ping()` 健康检查避免 API 不可用时空转。
- 生产建议：换稳定计费 API 后，只需设置 `PAPER_HARNESS_API_KEY` / `PAPER_HARNESS_BASE_URL` 两个环境变量，管线代码不变。

---

## 8. 已知限制与后续优化

- **表格抽取**：pdfplumber 对本论文检出率低（以图为主）；表格密集论文需调参数。
- **并行化**：deep 的 R2 块相互独立，可并行发送把时间降 10 倍（当前串行保稳定）。
- **附录策略**：可改为正文优先 + 附录按需回捞，进一步省 token。
- **公式论文**：需单独 LaTeX 抽取。
- **OpenReview 交叉核对**：可加 R0 轮抓取评审注入。
