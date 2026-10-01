---
name: artificial-analysis
description: 抓取 ArtificialAnalysis 模型评测，输出解析后的结构化 JSON（智能指数 / 价格 / 吞吐 / Elo 排名等）。当需要获取 LLM 或媒体类模型（文生图 / 图编辑 / 语音 / 视频）的评测榜单数据时使用。配套独立 CLI `artificial-analysis`，必需 API Key 由 ielym-certification 自动取回。
---

# artificial-analysis（ArtificialAnalysis 模型评测抓取）

按模态抓取 ArtificialAnalysis 模型评测，解析为结构化 JSON 记录后输出。必需 API Key 由 **ielym-certification** 从 OSS 凭证库自动取回。

## 数据源

- 接口：`https://artificialanalysis.ai/api/v2/data/...`（需请求头 `x-api-key`）
- 类型：模型
- 凭据：必需（OSS 凭证库服务名 `artificial-analysis`，JSON 字段 `AA_API_KEY`）

## 安装 CLI

依赖 Node.js ≥ 18 与 Python ≥ 3.10（Node 薄封装 + Python 实现，仅用标准库）。该包未发布到公共 npm registry，从源码目录安装：

```bash
git clone https://github.com/ielym/clihub.git <cli 源码目录>   # 首次；已有则跳过
npm i -g <cli 源码目录>/artificial-analysis                     # 得到 artificial-analysis 命令
```

首次在一台设备上使用时，若命令提示未引导，按 **ielym-certification** skill 的说明完成一次性引导即可。

## 用法

```bash
artificial-analysis --modality llm --limit 20
artificial-analysis --modality text-to-image --limit 10
artificial-analysis --modality all --limit 30
```

## 参数

| 参数 | 默认 | 说明 |
| --- | --- | --- |
| `--modality` | `llm` | 模态：`all` / `llm` / `text-to-image` / `image-editing` / `text-to-speech` / `text-to-video` / `image-to-video`；`all` 遍历全部模态 |
| `--limit` | 无 | 最多输出条数 |

## 输出

stdout 输出 JSON 信封，`records` 为已解析的模型记录：

```json
{
  "source": "artificial-analysis",
  "captured_at": "2026-09-30T02:20:45+00:00",
  "count": 1,
  "records": [
    {
      "source": "artificial-analysis",
      "source_id": "2f3c4dc9-a450-4303-8697-0237257cf08f",
      "name": "Claude Opus 5.5 (Adaptive Reasoning, Max Effort, Default Fallback)",
      "creator": "Anthropic",
      "modality": "llm",
      "elo": null,
      "rank": null,
      "price": null,
      "release_date": "2026-09-22",
      "metrics": {
        "evaluations": {"…": "…"},
        "pricing": {"…": "…"},
        "median_output_tokens_per_second": 123.4,
        "median_time_to_first_token_seconds": 0.8
      }
    }
  ]
}
```

字段说明：

- `source_id`：模型 ID
- `creator`：模型厂商名
- `elo` / `rank` / `price`：媒体类模态的 Elo 评分、排名与价格；不适用时为 `null`
- `metrics`：该模态的其余指标（LLM 的评测分、定价、吞吐与时延等均在此对象内）

## 凭据

API Key 只从 OSS 凭证库读取，不接受命令行参数或环境变量：

- 凭证对象：`oss://<凭证库 Bucket>/certification/api-key/artificial-analysis/artificial-analysis.json`
- 内容为 JSON，至少包含字段 `AA_API_KEY`
- 手工查看：`ielym-certification api-key --name artificial-analysis`

## 注意事项

- 免费额度有限（约 1000 请求/天），请节制调用。
- 必需凭据未登记、ielym-certification 未安装 / 未引导、或凭证 JSON 缺少 `AA_API_KEY` 时，向 stderr 打印原因并返回退出码 1。
- `--modality all` 下某个模态抓取失败（如 401、网络错误）时，原因写入 stderr，其余模态继续抓取，最终退出码为 1。