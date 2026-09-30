# acl-anthology

## 数据源

ACL Anthology 收录的 ACL / EMNLP / NAACL 等会议与期刊论文。

- 来源：GitHub 仓库 `acl-org/acl-anthology` 的 XML 文件，`https://raw.githubusercontent.com/acl-org/acl-anthology/master/data/xml/{collection}.xml`
- 类型：论文
- 凭据：无需

## 指令

```bash
paper-crawler acl-anthology [参数]
```

## 参数

| 参数 | 默认值 | 说明 |
| --- | --- | --- |
| `--collections` | `2024.acl` | 逗号分隔的 collection id，如 `2024.acl,2023.emnlp` |
| `--limit` | 无 | 最多输出条数 |

collection id 形如 `{年份}.{会议}`，如 `2024.acl`、`2023.emnlp`、`2024.findings`（Findings 是独立 collection，按 `acl`/`emnlp` 等 volume 区分会议）。

## 输出

- `source_id`：官方 Anthology ID，如 `2024.acl-long.1`、`P19-1001`、`W18-6310`
- `content_type`：`json`
- `metadata`：`collection`、`volume`、`venue`
- `data`：结构化论文对象，字段：
  - `anthology_id`：官方 Anthology ID（与 `source_id` 相同）
  - `title` / `abstract` / `pages` / `doi` / `language` / `year` / `month`
  - `authors`：`{name, first, last, id?}` 列表（`id` 为作者 canonical id，可缺失）
  - `venue` / `venues` / `booktitle`
  - `url`：Anthology 论文落地页 `https://aclanthology.org/{id}/`
  - `pdf_url`：Anthology 托管 PDF（`/{id}.pdf`）；XML 无 `<pdf>` 时为 `null`（早期外部出版论文，此时请用 `external_urls`），不保证可下载的链接不编造
  - `external_urls`：站外出版方页面（Springer / LREC / DOI 等），可能为空
  - `attachments`：补充材料 `{type, name, url}`，URL 形如 `https://aclanthology.org/attachments/{name}`，可能为空
  - `videos`：视频链接，可能为空
  - `item_type`：仅在特殊条目（如 `backmatter`）出现

## 输出示例

命令：

```bash
paper-crawler acl-anthology --collections 2024.acl --limit 1
```

输出（外层信封字段同 SKILL.md 通用约定，此处只展示一条 record）：

```json
{
  "source": "acl_anthology",
  "command": "acl-anthology",
  "captured_at": "2026-09-30T14:06:47+00:00",
  "count": 1,
  "records": [
    {
      "source": "acl_anthology",
      "source_id": "2024.acl-long.1",
      "content_type": "json",
      "fetched_at": "2026-09-30T14:06:46+00:00",
      "metadata": {"collection": "2024.acl", "volume": "long", "venue": "acl"},
      "data": {
        "anthology_id": "2024.acl-long.1",
        "title": "Quantized Side Tuning: ...",
        "authors": [
          {"name": "Zhengxin Zhang", "first": "Zhengxin", "last": "Zhang"},
          {"name": "Timothy Baldwin", "first": "Timothy", "last": "Baldwin", "id": "timothy-baldwin"}
        ],
        "year": "2024",
        "month": "August",
        "venue": "acl",
        "venues": ["acl"],
        "booktitle": "Proceedings of the 62nd Annual Meeting of the ACL (Volume 1: Long Papers)",
        "pages": "1-17",
        "doi": "10.18653/v1/2024.acl-long.1",
        "language": null,
        "abstract": "Finetuning large language models ...",
        "url": "https://aclanthology.org/2024.acl-long.1/",
        "pdf_url": "https://aclanthology.org/2024.acl-long.1.pdf",
        "external_urls": [],
        "attachments": [],
        "videos": []
      }
    }
  ]
}
```

## 字段使用要点

- **取论文主链接用 `url`**（落地页，恒有值）；批量下载 PDF 用 `pdf_url`。
- **`pdf_url` 可能为 `null`**（约 0.7%，早期 Springer/LREC 等外部出版论文）。此时不要自己拼 `.pdf`（会 404），改取 `external_urls[0]` 跳站外；两者皆无的条目（约 0.5%）只能通过落地页 `url` 访问。
- **`attachments[].url` 可直接下载**（代码包/checklist/幻灯片等，约 11% 的论文有）；`type` 是自由文本，取值不固定（software/checklist/…），按 `name` 后缀判断格式。
- **`year`/`month`/`venue`/`booktitle` 继承自所属 volume**，paper 本身不带这些字段；过滤"2020 年后 ACL"用 `data.year >= "2020"` 且 `data.venue == "acl"`，注意 Findings 的 `venue` 是 `findings`（会议名在 `booktitle`）。
- **去重/主键用 `anthology_id`（= `source_id`）**，全库唯一；pre-2020 形如 `P19-1001`、`W18-6310`。
- **过滤非正文条目**：`item_type == "backmatter"` 的条目不是论文（卷首 frontmatter 不在 paper 列表中）。
- `authors[].id` 是作者 canonical id（可用于同人合并），缺失即省略；`abstract` 可能为 `null`，`pages`/`doi`/`language` 同理，使用前判空。

## 调用示例

```bash
paper-crawler acl-anthology --collections 2024.acl --limit 10
paper-crawler acl-anthology --collections 2023.emnlp,2024.findings --limit 20
```

## 注意事项

- 一个 collection 可包含多个 volume（long / short / findings 等），逐篇产出。
- collection 不存在或拉取失败时跳过，不中断其他 collection。
- CLI 一次性把全部记录载入内存后输出，全量（约 12.8 万条 / 200 MiB+ JSON）建议按年份或会议分批，每次传几十个 collection。