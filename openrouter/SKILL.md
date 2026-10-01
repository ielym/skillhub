---
name: openrouter
description: 抓取 OpenRouter 模型目录，输出解析后的结构化 JSON（模型 ID / 上下文长度 / 模态 / 定价 / 支持的参数等）。当需要获取 OpenRouter 上可用模型清单及其定价与能力信息时使用。
---

# openrouter（OpenRouter 模型目录抓取）

抓取 OpenRouter 模型接口，解析为结构化 JSON 记录后输出。

## 数据源

- 接口：`https://openrouter.ai/api/v1/models`（OpenAI 兼容）
- 类型：模型
- 凭据：可选（匿名可访问；携带 Key 配额更高）

## 安装 CLI

依赖 Node.js ≥ 18 与 Python ≥ 3.10（Node 薄封装 + Python 实现，仅用标准库）。该包未发布到公共 npm registry，从源码目录安装：

```bash
git clone https://github.com/ielym/clihub.git <cli 源码目录>   # 首次；已有则跳过
npm i -g <cli 源码目录>/openrouter                              # 得到 openrouter 命令
```

## 用法

```bash
openrouter --limit 20
openrouter            # 输出全部模型
```

## 参数

| 参数 | 默认 | 说明 |
| --- | --- | --- |
| `--limit` | 无 | 最多输出条数 |

## 输出

stdout 输出 JSON 信封，`records` 为已解析的模型记录：

```json
{
  "source": "openrouter",
  "captured_at": "2026-09-30T02:20:45+00:00",
  "count": 1,
  "records": [
    {
      "source": "openrouter",
      "source_id": "openai/gpt-6.1-sol-pro",
      "name": "OpenAI: GPT-6.1 Sol Pro",
      "description": "…",
      "context_length": 1050000,
      "created_at": "2026-09-29T17:28:06+00:00",
      "modality": "text+image+file->text",
      "input_modalities": ["file", "image", "text"],
      "output_modalities": ["text"],
      "pricing": {"prompt": "0.000002", "completion": "0.00001"},
      "top_provider": {"context_length": 1050000, "max_completion_tokens": 128000, "is_moderated": true},
      "supported_parameters": ["tools", "reasoning"]
    }
  ]
}
```

字段说明：

- `source_id`：形如 `provider/model`
- `pricing` 中的单价为字符串（每 token 单价），换算时按需转换
- `pricing.overrides`（存在时）为按 prompt token 数分档的定价

## 凭据（可选）

Key 只从 OSS 凭证库读取，不接受命令行参数或环境变量：

- 凭证对象：`oss://<凭证库 Bucket>/certification/api-key/openrouter/openrouter.json`
- 内容为 JSON，至少包含字段 `OPENROUTER_API_KEY`
- 未登记时自动按匿名访问继续（配额较低），不报错

## 注意事项

- 无需凭据即可获取完整模型列表；登记 Key 后自动获得更高配额。
- 抓取失败时原因写入 stderr 并返回退出码 1。