# pmlr

## 数据源

PMLR（Proceedings of Machine Learning Research）论文集，收录 ICML、AISTATS 等会议论文。

- 来源：`https://proceedings.mlr.press/v{volume}/` 静态 HTML（无官方接口）
- 类型：论文
- 凭据：无需

## 指令

```bash
paper-crawler pmlr [参数]
```

## 参数

| 参数 | 默认值 | 说明 |
| --- | --- | --- |
| `--volumes` | `235` | 逗号分隔的卷号，如 `235,202` |
| `--limit` | 无 | 最多输出条数 |

卷号对应具体会议，如 `235` 为 ICML 2024。

## 输出

- `source_id`：`v{卷号}/{论文 ID}`，如 `v235/abad-rocamora24a`
- `content_type`：`html`
- `metadata`：`volume`、`booktitle`、`href`（论文页链接）
- `data`：论文条目的 HTML 片段，含标题、作者、摘要链接

## 示例

```bash
paper-crawler pmlr --volumes 235 --limit 10
paper-crawler pmlr --volumes 235,202 --limit 20
```

## 注意事项

- 论文条目来自卷首页列表；标题、作者、摘要链接由使用方从 HTML 抽取。
- 卷号不存在或拉取失败时跳过，不中断其他卷。