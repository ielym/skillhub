# openrouter

## 数据源

OpenRouter 模型目录，含模型元数据、上下文长度与定价。

- 接口：`https://openrouter.ai/api/v1/models`（OpenAI 兼容）
- 类型：模型
- 凭据：可选，提供后配额更高

## 指令

```bash
paper-crawler openrouter [参数]
```

## 参数

| 参数 | 默认值 | 说明 |
| --- | --- | --- |
| `--limit` | 无 | 最多输出条数 |
| `--api-key` | 环境变量 `OPENROUTER_API_KEY` | API Key（可选） |

## 输出

- `source_id`：模型 ID，通常为 `provider/model` 形式
- `content_type`：`json`
- `metadata`：空对象
- `data`：原始模型对象，含 `name` / `pricing` / `context_length` / `architecture` / `top_provider` / `endpoints` 等

## 示例

```bash
# 模型目录（无需凭据）
paper-crawler openrouter --limit 20

# 携带 API Key
export OPENROUTER_API_KEY="sk-or-xxx"
paper-crawler openrouter --limit 50
```

## 注意事项

- 无需凭据即可获取模型列表；携带 Key 可获得更高配额。
- 定价字段为字符串形式的单价，抽取时按需转换。