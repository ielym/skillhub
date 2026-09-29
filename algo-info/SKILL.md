---
name: algo-info
description: 算法信息数据源聚合系统。Invoke when 需要抓取/查询 arxiv、github trending、openreview、huggingface papers、openrouter 等 10 个 AI 数据源，或搜索论文/代码仓库/模型信息时使用。
version: 0.1.0
---

# algo-info — 算法信息数据源聚合系统

统一聚合 10 个算法/AI 领域数据源，抓取后按 arxiv_id → doi → 指纹（标题+第一作者姓+年份）三级去重合并，存入本地 SQLite，提供 CLI 和 HTTP API 查询。

## When to Use

- 需要批量抓取某数据源的最新论文/仓库/模型
- 需要跨源去重搜索论文、代码仓库或模型
- 需要本地离线查询 AI 领域信息
- 需要以 HTTP API 形式对外提供查询

## 前置条件

- Node.js ≥ 18（仅用于 CLI 入口）
- Python 3.12（项目自带 venv）
- 已配置项目路径：`algo-info config set <项目目录>`（或环境变量 `ALGO_INFO_HOME`）

## 命令一览

| 命令 | 说明 |
|------|------|
| `algo-info config set <目录>` | 记录 Python 项目路径（写入 `~/.algo-info.json`） |
| `algo-info config show` | 查看当前配置 |
| `algo-info sources` | 列出所有数据源 |
| `algo-info fetch <source> [--limit N]` | 抓取单个数据源 |
| `algo-info fetch-all [--limit N]` | 抓取所有数据源 |
| `algo-info stats` | 查看库内数据统计 |
| `algo-info search <query> [--limit N]` | 搜索论文 |
| `algo-info repos <query> [--limit N]` | 搜索代码仓库 |
| `algo-info models <query> [--limit N]` | 搜索模型 |
| `algo-info test` | 运行逐项测试（含去重验证） |
| `algo-info serve [--port 8000]` | 启动 FastAPI 查询服务 |

## 数据源说明

| 数据源 | 类型 | 凭据 | 备注 |
|--------|------|------|------|
| `arxiv` | 论文 | 无 | cs.AI/CL/LG/CV |
| `github_trending` | 代码仓库 | 无 | daily trending |
| `openreview` | 论文 | API token | ICLR/NeurIPS 等 |
| `huggingface_papers` | 论文 | 可选 HF token | HF Daily Papers |
| `artificial_analysis` | 模型 | API key | LLM 评测 |
| `openrouter` | 模型 | 无 | 模型元数据与定价 |
| `acl_anthology` | 论文 | 无 | ACL 会议论文 |
| `pmlr` | 论文 | 无 | ICML/NeurIPS 论文集 |
| `cvf` | 论文 | 无 | CVPR/ICCV（URL 需 `?day=all`） |
| `dblp` | 论文 | 无 | Live API 被反爬，改用 XML dump |

## 去重逻辑

管线 `Pipeline._deduplicate_paper` 按三级优先级合并同一论文：
1. **arxiv_id** 一致 → 合并（openreview 无 arxiv_id 的记录不会与 arxiv 重复）
2. **doi** 一致 → 合并
3. **指纹**（标题标准化 + 第一作者姓 + 年份）一致 → 合并

合并时保留更完整的字段（优先非空值）。

## 凭据配置

需凭据的源通过 `--credentials` 传 JSON，或在 `fetch-all` 中由环境变量提供：

```bash
algo-info fetch openreview --credentials '{"token": "YOUR_TOKEN"}'
```

无凭据时这些源返回 0 条，不影响其他源。

## 存储位置

- SQLite：`<项目目录>/data/algo_info.db`
- 原始对象：`<项目目录>/data/raw/<source>/<source_id>.json`

## HTTP API

启动 `algo-info serve` 后访问 `http://127.0.0.1:8000`，主要端点：

- `GET /papers?q=...&limit=20` — 搜索论文
- `GET /repos?q=...&limit=20` — 搜索仓库
- `GET /models?q=...&limit=20` — 搜索模型
- `GET /stats` — 统计信息
- `GET /papers/{id}` — 论文详情
- `GET /docs` — Swagger 文档

## 注意事项

- 首次使用务必先 `algo-info config set` 指向项目目录
- `fetch-all` 会串行抓取所有源，耗时较长，建议加 `--limit` 先试跑
- DBLP live API 被 Anubis 反爬，已改用本地 XML dump 解析
- CVF 的 URL 必须带 `?day=all` 才能获取完整会议列表
- 死信记录在 `dead_letter` 表，便于排查失败条目
