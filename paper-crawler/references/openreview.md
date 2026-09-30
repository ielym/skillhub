# openreview

## 数据源

OpenReview 会议投稿与评审记录。

- 接口：`https://api2.openreview.net`（v2 REST）
- 类型：论文
- 凭据：需要。notes 端点需认证，未提供凭据时报错并返回非 0

## 指令

```bash
paper-crawler openreview [参数]
```

## 参数

| 参数 | 默认值 | 说明 |
| --- | --- | --- |
| `--venue-id` | `ICLR.cc/2024/Conference` | 会议 ID |
| `--status` | `accepted` | 状态标记，随记录一并输出 |
| `--offset` | `0` | 分页偏移 |
| `--limit` | 无（接口页大小默认 `100`） | 输出条数上限，同时作为接口页大小 |
| `--token` | 环境变量 `OPENREVIEW_TOKEN` | API token |

## 输出

- `source_id`：note ID（forum id）
- `content_type`：`json`
- `metadata`：`venue_id`、`status`
- `data`：原始 note 对象，字段位于 `content` 内，含 `title` / `abstract` / `authors` / `keywords` / `arxiv` / `venueid` 等

## 示例

```bash
# 使用环境变量凭据
export OPENREVIEW_TOKEN="YOUR_TOKEN"
paper-crawler openreview --venue-id "ICLR.cc/2024/Conference" --limit 20

# 参数传入 token
paper-crawler openreview --venue-id "NeurIPS.cc/2024/Conference" --token "YOUR_TOKEN" --limit 10

# 分页
paper-crawler openreview --venue-id "ICLR.cc/2024/Conference" --offset 100 --limit 50
```

## 注意事项

- 未提供必需凭据时，指令向 stderr 打印缺失提示并返回退出码 1。
- notes 接口抓取失败（认证失败、网络错误等）时，失败原因写入 stderr 并返回退出码 1。
- `data.content` 中部分字段为 `{ "value": ... }` 结构，抽取时需取 `value`。
- 同一篇论文可能同时带有 `arxiv` 字段，可由使用方据此与 arxiv 数据关联。