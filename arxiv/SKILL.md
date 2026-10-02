---
name: arxiv
description: 抓取 arXiv 预印本，输出解析后的结构化 JSON（标题 / 作者 / 摘要 / 分类 / PDF 与落地页链接等）。当需要按检索式（分类 / 作者 / 关键词）获取 arXiv 最新或指定范围的论文条目时使用。
---

# arxiv（arXiv 预印本抓取）

从 arXiv Atom 接口抓取论文，解析为结构化 JSON 记录后输出（不返回原始 XML）。

## 数据源

- 接口：`https://export.arxiv.org/api/query`（Atom 1.0）
- 类型：论文
- 凭据：无需

## 安装 CLI

依赖 Node.js ≥ 18 与 Python ≥ 3.10（Node 薄封装 + Python 实现，仅用标准库）。该包未发布到公共 npm registry，从源码目录安装：

```bash
git clone https://github.com/ielym/clihub.git <cli 源码目录>   # 首次；已有则跳过
npm i -g <cli 源码目录>/arxiv                                   # 得到 arxiv 命令
```

## 用法

```bash
arxiv --query "cat:cs.AI" --max-results 20
arxiv --query "au:del_maestro" --max-results 10
arxiv --query "ti:transformer" --sort-by submittedDate --sort-order descending
arxiv --query "cat:cs.CL" --start 100 --max-results 50
```

## 参数

| 参数 | 默认 | 说明 |
| --- | --- | --- |
| `--query` | `cat:cs.AI` | 检索式 `search_query`，语法见下方[检索式语法](#检索式语法) |
| `--start` | `0` | 起始偏移，翻页用 |
| `--max-results` | `20` | 返回条数上限（单次切片 ≤2000，总量 ≤30000） |
| `--sort-by` | `submittedDate` | `relevance` / `lastUpdatedDate` / `submittedDate` |
| `--sort-order` | `descending` | `ascending` / `descending` |

## 检索式语法

`--query` 传入 arXiv `search_query`，由「字段前缀 + 布尔运算」组合而成。

**字段前缀**（官方支持的全部字段）：

| 前缀 | 含义 |
| --- | --- |
| `ti` | Title 标题 |
| `au` | Author 作者 |
| `abs` | Abstract 摘要 |
| `co` | Comment 备注/评论 |
| `jr` | Journal Reference 期刊引用 |
| `cat` | Subject Category 学科分类，如 `cat:cs.CV` |
| `rn` | Report Number 报告号 |
| `id` | arXiv ID（官方建议改用 `id_list`，CLI 未暴露此参数） |
| `all` | 以上全部字段（不写前缀时的默认范围） |

**布尔运算与分组**：

- 运算符 `AND` / `OR` / `ANDNOT` 必须大写；
- 用括号 `( ... )` 分组子表达式；
- 用双引号 `"..."` 表示精确短语；
- 相邻项以空格连接等价于分词，**建议显式写 `AND` / `OR` / `ANDNOT` 以避免歧义**。

```bash
arxiv --query "all:electron AND all:proton"
arxiv --query "au:bengio OR au:lecun"
arxiv --query "cat:cs.LG ANDNOT cat:cs.CV"
arxiv --query "(ti:sparse AND ti:autoencoder) AND cat:cs.LG"
arxiv --query "ti:\"electron thermal conductivity\""
arxiv --query "(ti:\"video generation\" OR abs:\"video generation\") AND (cat:cs.CV OR cat:cs.AI)"
```

**日期区间**（仅 `submittedDate` / `lastUpdatedDate` 支持）：

```bash
arxiv --query "cat:cs.CV AND submittedDate:[202501010000 TO 202512312359]"
arxiv --query "cat:cs.CV AND lastUpdatedDate:[202501010000 TO 202512312359]"
```

## 输出

stdout 输出 JSON 信封，`records` 为已解析的论文记录：

```json
{
  "source": "arxiv",
  "captured_at": "2026-09-30T02:20:45+00:00",
  "count": 2,
  "records": [
    {
      "source": "arxiv",
      "source_id": "2609.40360v1",
      "title": "Semifactual Credit-Augmented Policy Optimization",
      "abstract": "…",
      "authors": ["Junshu Pan", "Zhizhang Fu"],
      "categories": ["cs.LG", "cs.AI"],
      "primary_category": "cs.LG",
      "published_at": "2026-09-30T17:59:56Z",
      "updated_at": "2026-09-30T17:59:56Z",
      "abs_url": "https://arxiv.org/abs/2609.40360v1",
      "pdf_url": "https://arxiv.org/pdf/2609.40360v1",
      "comment": null,
      "doi": null,
      "journal_ref": null
    }
  ]
}
```

字段说明：

- `source_id`：arXiv ID（含版本号，如 `2609.40360v1`）
- `title` / `abstract`：已合并换行、压缩空白
- `categories` / `primary_category`：分类列表与主分类
- `pdf_url` / `abs_url`：PDF 直链与落地页
- `comment` / `doi` / `journal_ref`：存在时才有值，否则为 `null`

## 注意事项

- arXiv 官方建议请求间隔约 3 秒；CLI 已内置 3 次指数退避重试。
- 单次 `max-results` 上限约 2000，超出需用 `--start` 分页。
- 抓取失败或响应不是合法 Atom XML 时，原因写入 stderr 并返回退出码 1。