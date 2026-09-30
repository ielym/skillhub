# arxiv

## 数据源

arXiv 预印本，覆盖物理、数学、计算机、生物等全部学科分类。

- 接口：`https://export.arxiv.org/api/query`（Atom 1.0 XML）
- 类型：论文
- 凭据：无需
- 默认检索式 `cat:*` 覆盖全部分类，不绑定特定领域。

## 指令

```bash
paper-crawler arxiv [参数]
```

## 参数

| 参数 | 默认值 | 说明 |
| --- | --- | --- |
| `--query` | `cat:*` | arXiv 检索式。可用分类、作者、关键词等，如 `cat:cs.AI`、`cat:math.NT`、`au:del_maestro`、`ti:transformer` |
| `--max-results` | `50` | 单次请求返回条数 |
| `--start` | `0` | 起始偏移，用于翻页 |
| `--sort-by` | `submittedDate` | 排序字段，如 `submittedDate`、`lastUpdatedDate`、`relevance` |
| `--sort-order` | `descending` | 排序方向：`descending` / `ascending` |
| `--limit` | 无 | 最多输出条数 |

## 输出

- `source_id`：arXiv ID，如 `2609.38178v1`
- `content_type`：`atom_xml`
- `metadata.query`：本次使用的检索式
- `data`：单条 `<entry>` 的 Atom XML 文本，含 `title` / `summary`（摘要）/ `author` / `category` / `published` / `arxiv:comment` / `arxiv:doi` 等，另含 PDF 链接

## 示例

```bash
# 全学科最新论文
paper-crawler arxiv --max-results 20 --limit 5

# 指定分类
paper-crawler arxiv --query "cat:cs.AI" --max-results 10

# 跨学科：数论
paper-crawler arxiv --query "cat:math.NT" --sort-by submittedDate --limit 5

# 按作者检索
paper-crawler arxiv --query "au:del_maestro" --limit 5

# 翻页
paper-crawler arxiv --query "cat:cs.CL" --start 50 --max-results 50 --limit 10
```

## 注意事项

- 官方建议连续请求间隔约 3 秒；CLI 已内置重试与退避。
- 单次 `--max-results` 上限约为 2000，超过需分页。
- `data` 为原始 XML，字段抽取由使用方按需完成。