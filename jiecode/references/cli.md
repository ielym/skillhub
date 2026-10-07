# jiecode CLI 参考

## 安装

```bash
npm i -g D:\clihub\jiecode
```

CLI 源码在 `D:\clihub\jiecode`。

## 配置

默认读取 `~/.config/jiecode/config.json`，也可用 `--config` 或 `$JIE_CODE_CONFIG` 覆盖。

配置结构：

```json
{
  "default_provider": "d1jiema",
  "providers": {
    "d1jiema": {
      "account": "...",
      "api_token": "...",
      "api_base": "https://api.d1jiema.com/zc/data.php"
    }
  }
}
```

provider 也可通过各自的专用环境变量注入，例如：

```bash
export D1_TOKEN=xxx
export D1_API_BASE=https://api.d1jiema.com/zc/data.php
```

## 命令

```bash
jiecode providers
```

列出已注册 provider。

```bash
jiecode --provider <name> status [--json]
```

查询余额。

```bash
jiecode --provider <name> get-phone [--keyword <关键词>] [--phone <号码>] [--province <省份>] [--card-type <实卡|虚卡|全部>] [--json]
```

获取手机号。`--phone` 不填时随机取号；额外参数是否生效取决于 provider。

```bash
jiecode --provider <name> get-msg --phone <号码> --keyword <关键词> [--json]
```

收取短信。

```bash
jiecode --provider <name> history [--json]
```

查询历史记录。

```bash
jiecode credential-path
```

打印当前全局配置文件路径，不打印密钥。

## 输出

`--json` 输出统一信封：

```json
{
  "ok": true,
  "command": "status",
  "provider": "d1jiema",
  "data": "29.00"
}
```

非 `--json` 模式直接输出平台返回值。失败时 `ok=false`，`data` 为 `ERROR:` 原文，退出码为 1。