# artificial-analysis

## 数据源

ArtificialAnalysis 模型评测数据（智能指数、价格、吞吐等）。

- 接口：`https://artificialanalysis.ai/api/v2/data/...`，需 `x-api-key`
- 类型：模型
- 凭据：需要 API Key，未提供时报错并返回非 0

## 指令

```bash
paper-crawler artificial-analysis [参数]
```

## 参数

| 参数 | 默认值 | 说明 |
| --- | --- | --- |
| `--modality` | `llm` | 模态：`all` / `llm` / `text-to-image` / `image-editing` / `text-to-speech` / `text-to-video` / `image-to-video`，`all` 遍历全部模态 |
| `--limit` | 无 | 最多输出条数 |
| `--api-key` | 环境变量 `AA_API_KEY` | API Key |

## 输出

- `source_id`：模型 ID
- `content_type`：`json`
- `metadata.modality`：模态
- `data`：原始模型对象
  - `llm`：含 `name` / `slug` / `model_creator` / `evaluations`（评测指标）/ `pricing`（价格）/ 吞吐与时延等
  - 媒体类（`text-to-image` / `image-editing` / `text-to-speech` / `text-to-video` / `image-to-video`）：含 `name` / `slug` / `model_creator` / `elo` / `rank` / `ci95` / `appearances` / `release_date`（部分含 `categories`）

## 示例

```bash
export AA_API_KEY="YOUR_KEY"

# 全部模态（遍历 6 个接口，--limit 为总条数上限）
paper-crawler artificial-analysis --modality all --limit 20

# LLM 榜单
paper-crawler artificial-analysis --modality llm --limit 20

# 文生图模型
paper-crawler artificial-analysis --modality text-to-image --limit 10

# 图生视频模型
paper-crawler artificial-analysis --modality image-to-video --limit 10

# 参数传入 key
paper-crawler artificial-analysis --api-key "YOUR_KEY" --limit 10
```

## 注意事项

- 免费额度有限（约 1000 请求/天），请节制调用。
- 未提供 API Key 时，指令向 stderr 打印缺失提示并返回退出码 1。
- 某个模态抓取失败（如 401、网络错误）时，失败原因写入 stderr；`--modality all` 下其余模态继续抓取，最终退出码为 1。