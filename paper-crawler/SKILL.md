---
name: paper-crawler
description: 多数据源原始抓取 CLI。当需要从 arxiv、github trending、openreview、huggingface papers、artificial analysis、openrouter、acl anthology、pmlr、cvf、dblp 等数据源抓取原始记录（论文 / 代码仓库 / 模型）时使用。每个数据源对应一条独立指令，结果以 JSON 输出到 stdout。
version: 1.0.0
---

# paper-crawler（多数据源原始抓取）

`paper-crawler` 从各公开数据源抓取原始记录。每个数据源一条独立指令，指令只做一件事：从远端拉取记录并以 JSON 输出原始内容，供使用方按需进一步解析、加工或入库。

## 基础能力

- **按数据源拆分**：一条指令对应一个数据源，参数互不影响。
- **原始输出**：统一以 JSON 信封写 stdout，`records[].data` 为该数据源的原始内容。
- **失败可辨**：失败原因写入 stderr 并返回非 0 退出码，绝不静默；单个数据源部分失败时仍输出已抓取记录。

## 前置条件

1. **Node.js** ≥ 18（CLI 入口为 Node 薄封装）。
2. **Python** ≥ 3.10，并在该解释器中安装依赖（`httpx` / `lxml` / `beautifulsoup4`）：

   ```bash
   python3 -m pip install -r requirements.txt
   ```

   CLI 固定调用 `python3`，不探测也不指定解释器路径；依赖缺失时直接抛出 `ModuleNotFoundError` 并以非 0 退出。

## 安装 CLI

```bash
git clone https://github.com/ielym/clihub.git <cli 源码目录>   # 首次；已有则跳过
cd <cli 源码目录>/paper-crawler && npm i -g .                  # 全局安装，得到 paper-crawler 命令
```

## 输出格式

所有指令在 stdout 输出 JSON：

```json
{
  "source": "arxiv",
  "command": "arxiv",
  "captured_at": "2026-09-30T02:20:45+00:00",
  "count": 2,
  "records": [
    {
      "source": "arxiv",
      "source_id": "2609.38178v1",
      "content_type": "atom_xml",
      "fetched_at": "2026-09-30T02:20:45+00:00",
      "metadata": { "query": "cat:cs.AI" },
      "data": "<entry>...</entry>"
    }
  ]
}
```

`content_type` 取值 `json` / `atom_xml` / `xml` / `html`。各数据源 `source_id`、`metadata`、`data` 的具体含义见对应 reference。

## 指令路由

所有指令都支持 `--limit N` 限制输出条数。完整列表：`paper-crawler sources`。

| 指令 | 数据源 | 类型 | 凭据 | 详细说明 |
| --- | --- | --- | --- | --- |
| `paper-crawler arxiv` | arxiv | 论文 | 无 | [references/arxiv.md](references/arxiv.md) |
| `paper-crawler github-trending` | github_trending | 代码仓库 | 无 | [references/github-trending.md](references/github-trending.md) |
| `paper-crawler openreview` | openreview | 论文 | token | [references/openreview.md](references/openreview.md) |
| `paper-crawler huggingface-papers` | huggingface_papers | 论文 | 可选 token | [references/huggingface-papers.md](references/huggingface-papers.md) |
| `paper-crawler artificial-analysis` | artificial_analysis | 模型 | API Key | [references/artificial-analysis.md](references/artificial-analysis.md) |
| `paper-crawler openrouter` | openrouter | 模型 | 可选 API Key | [references/openrouter.md](references/openrouter.md) |
| `paper-crawler acl-anthology` | acl_anthology | 论文 | 无 | [references/acl-anthology.md](references/acl-anthology.md) |
| `paper-crawler pmlr` | pmlr | 论文 | 无 | [references/pmlr.md](references/pmlr.md) |
| `paper-crawler cvf` | cvf | 论文 | 无 | [references/cvf.md](references/cvf.md) |
| `paper-crawler dblp` | dblp | 论文 | 无 | [references/dblp.md](references/dblp.md) |

## 通用说明

- **凭据**：优先取指令参数，其次取对应环境变量；必需凭据缺失时向 stderr 打印缺失提示并返回非 0（不再以 `count: 0` 静默成功）。
- **分页**：需要更多数据时用各源的分页参数（如 arxiv `--start`、openreview `--offset`）分批抓取。
- **网络**：受限网络下部分数据源可能不可达，表现为抓取失败或超时。
- 具体参数、数据字段与示例见各数据源的 reference。