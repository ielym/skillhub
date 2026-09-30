# huggingface-papers

## 数据源

HuggingFace Daily Papers 每日热门论文。

- 接口：`https://huggingface.co/api/daily_papers`（列表）、`https://huggingface.co/api/papers/{arxiv_id}`（单篇元数据）
- 类型：论文
- 凭据：可选，携带 HF token 配额更高

## 指令

```bash
paper-crawler huggingface-papers [参数]
```

## 参数

| 参数 | 默认值 | 说明 |
| --- | --- | --- |
| `--date` | 空 | 日期 `YYYY-MM-DD` |
| `--sort` | 空 | 排序字段 |
| `--limit` | 无（接口页大小默认 `50`） | 输出条数上限，同时作为接口页大小 |
| `--token` | 环境变量 `HF_TOKEN` / `HUGGINGFACE_TOKEN` | HF token（可选） |

## 输出

- `source_id`：论文 arXiv ID
- `content_type`：`json`
- `metadata.upvotes`：点赞数
- `data`：`{ "daily": <列表项>, "detail": <单篇元数据> }`，含标题、摘要、作者、发布日期、关联 GitHub / 项目主页、机构等

## 示例

```bash
# 当日热榜
paper-crawler huggingface-papers --limit 10

# 指定日期
paper-crawler huggingface-papers --date 2024-06-01 --limit 10

# 携带 token
export HF_TOKEN="hf_xxx"
paper-crawler huggingface-papers --limit 20
```

## 注意事项

- 列表内每篇论文会再请求一次单篇元数据；若单篇请求失败，回退为列表项内容。
- 受限网络下 `huggingface.co` 可能不可达，表现为抓取失败（stderr 报错、退出码非 0）。