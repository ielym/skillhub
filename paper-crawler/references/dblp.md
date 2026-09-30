# dblp

## 数据源

DBLP 计算机领域文献库（CC0 协议）。

- 实时接口（search / rec / pid）受反爬保护，采用 XML dump 解析
- 类型：论文
- 凭据：无需

## 指令

```bash
paper-crawler dblp [参数]
```

## 参数

| 参数 | 默认值 | 说明 |
| --- | --- | --- |
| `--mode` | `sample` | 抓取模式，见下表 |
| `--dump` | 空 | `mode=local` 时的本地 XML / XML.GZ 路径 |
| `--limit` | 无 | 最多输出条数 |

| 模式 | 说明 |
| --- | --- |
| `sample` | 使用内置样本，用于连通性与流程自检 |
| `local` | 解析本地 dump 文件（需 `--dump` 指定路径） |
| `download` | 下载最新 dump 后解析（文件较大，适合全量同步） |

## 输出

- `source_id`：DBLP key，如 `journals/corr/abs-1706-03762`、`conf/icml/AbadiZ16`
- `content_type`：`xml`
- `metadata.type`：记录类型，如 `article` / `inproceedings`
- `data`：单条记录的 XML 文本，含 `author` / `title` / `year` / `booktitle` / `pages` / `ee`（外部链接）等

## 示例

```bash
# 内置样本自检
paper-crawler dblp --mode sample --limit 5

# 解析本地 dump
paper-crawler dblp --mode local --dump /data/dblp.xml.gz --limit 20

# 下载最新 dump（耗时较长）
paper-crawler dblp --mode download --limit 20
```

## 注意事项

- `download` 模式拉取的是全量 dump，体积与耗时都较大，建议配合 `--limit` 先试跑。
- dump 更新频率为每日一次，按需拉取即可。
- `sample` 模式仅用于自检，不代表真实数据。