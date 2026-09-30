# github-trending

## 数据源

GitHub Trending 榜单，展示指定周期内热度上升的开源代码仓库。

- 来源：`https://github.com/trending` 服务端渲染 HTML（无官方接口）
- 类型：代码仓库
- 凭据：无需

## 指令

```bash
paper-crawler github-trending [参数]
```

## 参数

| 参数 | 默认值 | 说明 |
| --- | --- | --- |
| `--since` | `daily` | 榜单周期：`daily` / `weekly` / `monthly` |
| `--language` | 空 | 按语言过滤，如 `python`、`rust` |
| `--limit` | 无 | 最多输出条数 |

## 输出

- `source_id`：仓库全名 `owner/repo`
- `content_type`：`html`
- `metadata`：`since`（周期）、`language`（语言）、`rank`（榜单名次，从 1 开始）
- `data`：该条目的 `<article class="Box-row">` HTML 片段，含仓库链接、描述、语言、star / fork / 当日新增 star

## 示例

```bash
# 今日总榜
paper-crawler github-trending --limit 10

# 本周 Python 榜
paper-crawler github-trending --since weekly --language python --limit 10

# 本月榜
paper-crawler github-trending --since monthly --limit 20
```

## 注意事项

- 榜单条目为服务端渲染结果，字段抽取由使用方按需完成。
- 页面结构可能随 GitHub 改版变化；`rank` 直接反映榜单位次。