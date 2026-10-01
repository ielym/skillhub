---
name: github-trending
description: 抓取 GitHub Trending 榜单，输出解析后的结构化 JSON（仓库名 / 链接 / 描述 / 语言 / star / fork / 当日新增 star 等）。当需要获取指定周期（日 / 周 / 月）或指定语言的 GitHub 热门开源仓库榜单时使用。
---

# github-trending（GitHub 热门仓库榜单抓取）

抓取 GitHub Trending 页面，解析为结构化 JSON 记录后输出（不返回原始 HTML）。

## 数据源

- 来源：`https://github.com/trending`（服务端渲染页面，无官方接口）
- 类型：代码仓库
- 凭据：无需

## 安装 CLI

依赖 Node.js ≥ 18 与 Python ≥ 3.10（Node 薄封装 + Python 实现，仅用标准库）。该包未发布到公共 npm registry，从源码目录安装：

```bash
git clone https://github.com/ielym/clihub.git <cli 源码目录>   # 首次；已有则跳过
npm i -g <cli 源码目录>/github-trending                         # 得到 github-trending 命令
```

## 用法

```bash
github-trending --since daily --limit 10
github-trending --language python --since weekly
github-trending --language rust --since monthly
```

## 参数

| 参数 | 默认 | 说明 |
| --- | --- | --- |
| `--since` | `daily` | 榜单周期：`daily` / `weekly` / `monthly` |
| `--language` | 无 | 语言作为路径段，如 `python`、`rust`、`go` |
| `--limit` | 无 | 最多输出条数 |

## 输出

stdout 输出 JSON 信封，`records` 为已解析的仓库记录：

```json
{
  "source": "github-trending",
  "captured_at": "2026-09-30T02:20:45+00:00",
  "count": 1,
  "records": [
    {
      "source": "github-trending",
      "rank": 1,
      "source_id": "vectorize-io/hindsight",
      "url": "https://github.com/vectorize-io/hindsight",
      "description": "Hindsight: Agent Memory That Learns",
      "language": "Python",
      "stars": 44055,
      "forks": 5853,
      "stars_today": 18389
    }
  ]
}
```

字段说明：

- `rank`：榜单位次，从 1 开始
- `source_id`：`owner/repo`
- `stars` / `forks` / `stars_today`：整数（已去千分位；`stars_today` 对应所选周期的新增数）
- `description` / `language`：仓库未填写时为 `null`

## 注意事项

- 解析依赖 Trending 页面结构（`article.Box-row`），GitHub 改版时需同步调整解析规则。
- 抓取失败时原因写入 stderr 并返回退出码 1；榜单为空时 `count` 为 0。