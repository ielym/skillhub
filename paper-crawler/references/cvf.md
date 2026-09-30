# cvf

## 数据源

CVF Open Access 收录的 CVPR / ICCV / WACV 等计算机视觉会议论文。

- 来源：`https://openaccess.thecvf.com/{Conference}{Year}` 静态 HTML（无官方接口）
- 类型：论文
- 凭据：无需

## 指令

```bash
paper-crawler cvf [参数]
```

## 参数

| 参数 | 默认值 | 说明 |
| --- | --- | --- |
| `--conferences` | `CVPR2024` | 逗号分隔的会议标识，如 `CVPR2024,ICCV2023` |
| `--limit` | 无 | 最多输出条数 |

## 输出

- `source_id`：`{会议}/{论文 ID}`，如 `CVPR2024/Zeng_Unmixing_..._CVPR_2024_paper`
- `content_type`：`json`
- `metadata`：`conference`、`href`（论文页相对路径）
- `data`：`{ "title": ..., "authors": ..., "href": ... }`

## 示例

```bash
paper-crawler cvf --conferences CVPR2024 --limit 10
paper-crawler cvf --conferences CVPR2024,ICCV2023 --limit 20
```

## 注意事项

- CVF 的列表 URL 必须带 `?day=all` 才能取到完整论文列表，CLI 已内置该参数。
- `authors` 为原始作者串（逗号分隔），拆分由使用方按需完成。