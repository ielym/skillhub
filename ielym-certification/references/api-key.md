# api-key provider 参考

第三方服务的 API Key / Token，按**服务名**维度取回（如 `artificial-analysis`、`openrouter`）。凭证内容为 JSON 原文，取哪个字段由调用方约定。

> 本文档不含任何具体业务密钥；`<name>` 等均为占位符。

## 前置条件

与 `aliyun-oss` provider 共用同一套引导信任根：

1. 已安装 **ossutil**（读取 OSS 对象的底层工具）；
2. 已执行过一次 `ielym-certification bootstrap`（每台设备一次）。

api-key provider 自身不需要额外引导；未引导时会提示先执行 bootstrap。

## OSS 凭证存放约定

```
oss://<store-bucket>/certification/api-key/<name>/<name>.json
```

- `<name>` 即 `--name` 指定的第三方服务名（如 `artificial-analysis`）；
- `<store-bucket>` 缺省为引导凭证所在的 Bucket（凭证库 Bucket）；
- 凭证文件内容为 JSON，字段名由调用方约定，例如：

  ```json
  {
    "AA_API_KEY": "aa_...",
    "name": "ielym"
  }
  ```

- 也可用 `--key` 直接指定完整对象 key，绕过模板。

### 登记一个新服务的凭证

```bash
# 1) 准备本地 JSON（权限建议 600），然后上传到约定路径
aliyun-oss upload ./<name>.json \
  oss://<store-bucket>/certification/api-key/<name>/<name>.json

# 2) 验证
ielym-certification api-key --name <name>
```

## 参数

| 参数 | 说明 |
| --- | --- |
| `--name <name>` | 第三方服务名（`--list` 时可省略） |
| `--store-bucket <name>` | 凭证文件所在 Bucket；缺省用引导凭证的 Bucket |
| `--key <object-key>` | 直接指定凭证对象 key，覆盖默认模板 |
| `-e, --endpoint` | 覆盖 OSS 访问域名（默认用引导凭证中的内网域名） |
| `--region` | 覆盖地域 ID（默认用引导凭证中的地域） |

通用参数 `--json` / `--out` / `--list` 见 skill 主文档。

## 用法示例

```bash
# 取回某服务的凭证 JSON（直接输出原文）
ielym-certification api-key --name artificial-analysis

# 带定位信息的 JSON 信封
ielym-certification api-key --name artificial-analysis --json

# 只取某个字段
ielym-certification api-key --name artificial-analysis | jq -r '.AA_API_KEY'

# 列出已登记的第三方服务
ielym-certification api-key --list

# 凭证集中存放在另一个 Bucket
ielym-certification api-key --name <name> --store-bucket <store-bucket>
```

## 输出格式

`--json` 信封：

```json
{
  "cli": "ielym-certification",
  "provider": "api-key",
  "command": "get",
  "ok": true,
  "name": "<name>",
  "store_bucket": "<store-bucket>",
  "key": "certification/api-key/<name>/<name>.json",
  "oss_path": "oss://<store-bucket>/certification/api-key/<name>/<name>.json",
  "content": "..."
}
```

## 故障排查

| 现象 | 原因与处理 |
| --- | --- |
| `尚未引导` | 该设备首次使用，先执行 `ielym-certification bootstrap` |
| `凭证不存在`（退出 2） | 服务名拼写错误，或该服务尚未登记；先 `api-key --list` 查看已登记名单 |
| `必须用 --name 指定第三方服务名` | 取回单个凭证时必须带 `--name`（仅 `--list` 可省略） |
| 调用方报「JSON 中缺少字段」 | 对象存在但内容没有约定的字段（如 `AA_API_KEY`）；按调用方文档补字段后重新上传 |
| `AccessDenied` | 引导凭证无权访问凭证库 Bucket；确认引导为最新后 `bootstrap --force` |
