---
name: jiecode
description: 通用接码 CLI：统一处理余额查询、取号、取短信、历史记录，平台通过 provider 接入。当用户需要接收短信验证码、查询接码余额或使用记录时使用；具体平台细节按路由表进入 provider 参考文档。
---

# jiecode 通用接码

## 能力

jiecode 是通用接码 CLI，不做平台绑定。它把不同接码平台抽象为 provider，统一暴露以下能力：

- 查询余额
- 获取手机号
- 收取短信
- 查询历史记录
- 列出可用 provider

通用调用形式：

```bash
jiecode --provider <provider> <command>
```

无 `--provider` 时，从 `$JIE_CODE_PROVIDER` 或 `~/.config/jiecode/config.json` 的 `default_provider` 读取默认平台。

## 凭证

各 provider 的凭证按 provider 名保存：

- 本地 CLI 配置：`~/.config/jiecode/config.json`
- OSS 凭证库：`oss://<store-bucket>/certification/api-key/<provider>/<provider>.json`

CLI 命令说明见 [cli.md](references/cli.md)。凭证取回与更新按各 provider 文档处理。

## 路由

| provider | 场景 | 文档 |
| --- | --- | --- |
| `d1jiema` | D1 接码（易码）的账号、Token、价格、API 字段和 CLI 参数 | [d1jiema.md](references/d1jiema.md) |