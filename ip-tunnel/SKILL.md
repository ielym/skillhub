---
name: ip-tunnel
description: 快代理隧道代理（IP 隧道）工具：从 OSS 凭证库取回隧道账号并生成可用的代理配置，或通过隧道发起 HTTP 请求。每次请求自动换 IP，并内置重试、速率限制、锁 IP（同一 IP 30 秒）与多通道支持。当用户需要“用代理 IP 访问目标网页、爬取数据、切换出口 IP、查看隧道当前出口 IP、验证隧道可用性、或为其他程序接入代理”时使用。
---

# ip-tunnel（快代理隧道代理 / IP 隧道）

按「每次请求换 IP」模式提供出口代理：**账号从 OSS 凭证库取回，代码里不含任何明文密钥**；自带重试与 5 次/s 排队，避免因隧道单次失败就中断任务。

```
┌────────────┐   HTTP(S)  ┌─────────────────┐  目标网站
│ 任意程序    │ ──────────► │ 快代理隧道 e391  │ ───► ──► ──►
└────────────┘  代理URL    │ 每次请求换 IP    │（出口 IP 每次不同）
                           │ 5次/s · 5Mbps   │
                           └─────────────────┘
```

## 何时用 / 不用

- **用**：访问同一个网站或接口，需要不断更换出口 IP（防目标网站频率屏蔽），或抓到一半被目标封 IP 需要切换。
- **不用**：本地/内网互访、已被 GFW/运营商封锁需“抗封锁”的场景（那是 [wireguard-easy](../wireguard-easy/SKILL.md) / [xray-easy](../xray-easy/SKILL.md) 的职责）。

## 前置条件

- Node.js ≥ 18 与 Python ≥ 3.10。
- **ielym-certification 已安装并完成一次性引导**（隧道账号统一由它从 OSS 凭证库提供）。若命令提示未引导，按 [ielym-certification](../ielym-certification/SKILL.md) 说明处理即可。

## 安装 CLI

该包未发布到公共 npm registry，从源码目录安装：

```bash
git clone https://github.com/ielym/clihub.git <本地目录>   # 首次；已有则跳过
npm i -g <本地目录>/ip-tunnel                               # 得到 ip-tunnel 命令
```

## 快速上手

```bash
ip-tunnel ip                 # 查当前出口 IP（每次调用应不同 → 证明在换 IP）
ip-tunnel test               # 验证隧道可用性（GET testproxy，HTTP 200 即成功）
ip-tunnel request <url>      # 通过隧道抓取一个 URL（自动重试，失败不中断）
ip-tunnel export --raw       # 输出可直接喂给 requests 的 proxies JSON（运行时取号）
```

## 命令参考

| 命令 | 说明 |
| --- | --- |
| `ip-tunnel export [--raw] [--sid S]` | 打印隧道配置。默认屏蔽密码；`--raw` 输出含真实密码、可直接接 requests 的 `proxies` JSON。 |
| `ip-tunnel request <url> [--method M] [--data D] [--header K:V×n] [--sid S] [--channel N] [--retries R] [--timeout T] [--rate N] [--json]` | 通过隧道发起一次请求，内置重试与 5 次/s 排队。 |
| `ip-tunnel test [--url U] [--sid S] [--json]` | 验证隧道可用性（HTTP 200 即成功）。 |
| `ip-tunnel ip [--sid S] [--json]` | 打印当前出口 IP（多源回退）。 |
| `ip-tunnel limits [--json]` | 打印本隧道并发/带宽/换 IP/超带宽机制。 |
| `ip-tunnel lock-help` | 解释锁 IP 与多通道用法。 |

默认：重试 `3` 次（指数退避）、单次超时 `30s`、速率 `5` 次/s（来自凭证配置，请求排队）。

## 关键行为（务必知晓）

1. **每次请求换 IP**：连接不复用（无 keep-alive），每发一个请求出口 IP 都会变。要用同一个 IP 时用 `--sid <串>` 锁 30 秒。
2. **自动重试，禁止因单次失败抛异常**：隧道对偶发失败会返回 `440 带宽超限 / 441 请求超频 / 515·516·517 转发失败`。CLI 已把这些视为可重试瞬时错误并指数退避重试（其余 4xx 为配置/目标问题，不重试）。**所有使用者必须在自己的脚本里同样写好重试与捕获 `ok=false` 的逻辑**，单次失败绝不能中断整体任务。
3. **速率排队**：CLI 按 `5 次/s` 令牌桶排队，持续超频目标会返回 `441`，超带宽返回 `440`；二者已是重试集。
4. **目标相关失败（非瞬时，重试无效）**：个别域名（实测 `api.ipify.org`、`httpbin.org`）会被隧道/目标拒绝返回 `517`，属目标相关；`ip` 命令已并入多源回退。遇到此类持续 517，先 `export --raw` 换接入方式或换目标，不要盲目加大重试。
5. **密码不落盘、不进日志**：`--raw` 与运行时注入是唯一暴露凭据的路径，别把它写进脚本日志或提交仓库。

## 在程序中使用（对接 requests）

```python
import requests, subprocess, json

# 运行时从 OSS 取号（一次性），得到 proxies 字典
raw = subprocess.run(["ip-tunnel", "export", "--raw"],
                     capture_output=True, text=True, check=True).stdout
raw = raw[:raw.rfind("提示：")]          # 去掉 stderr 提示外，只保留 JSON（更稳妥用 --json 变体见下）
cfg = json.loads(raw)
proxies = cfg["proxies"]

def fetch(url, timeout=30, retries=3):
    last = None
    for i in range(retries + 1):
        try:
            r = requests.get(url, proxies=proxies, timeout=timeout)
            if r.status_code in (200,):          # 按需放宽
                return r.text
            last = f"HTTP {r.status_code}"
        except Exception as e:                    # 连接/转发失败，重试而非抛弃
            last = f"{type(e).__name__}: {e}"
        time.sleep(1.5 * (2 ** i))                # 指数退避
    raise RuntimeError(f"该 URL 重试 {retries} 次仍失败：{last}")
```

> 注：`proxies` 的 http/https 均为同一隧道地址；requests 会自动为 https 建立 CONNECT。要锁 IP 时在 `--raw` 加 `--sid <串>` 即可让这批请求共用同一出口 30 秒。

## 锁 IP（同一出口 30 秒）

```bash
ip-tunnel ip --sid login-session-1     # 两次都返回同一 IP
ip-tunnel ip --sid login-session-1
ip-tunnel ip --sid other                # 换一个 sid 则换 IP
```

原理：把 `<密码>:<任意串>` 作为代理凭据，同一串锁同一 IP 30 秒；不传即每次随机换 IP。

## 排障（黄金路径）

| 现象 | 大概率原因 | 处理 |
| --- | --- | --- |
| `441 Request Rate Over Limit` | 请求频率超过 5 次/s 且排队仍超限 | 降低并发放宽 `--rate`/脚本内降低频率 |
| `440 Bandwidth Over Limit` | 单次资源过大导致带宽超 5Mbps | 减少并发、压缩内容、分批 |
| `407 Proxy Authentication Required` | 账号/密码错、或鉴权方式与订单不一致 | `ielym-certification bootstrap --force` 重取号后重试 |
| `446 Host DNS Failed` | 目标域名无法解析 | 核对 URL 域名 |
| 持续 `517 Proxy Setup Failed` | 目标域名被隧道/目标拒绝（非瞬时） | 换目标域名，不要盲目加大重试 |
| `export --raw` 里密码是 `****` | 用了默认（非 `--raw`）输出 | 加 `--raw` |

## 注意事项

- 凭证只从 OSS 凭证库读取，不接受命令行/环境变量传密钥；`oss://ielym-data/certification/api-key/ip-tunnel/ip-tunnel.json`（服务名 `ip-tunnel`，字段 `tunnel/username/password`）。
- 本隧道带宽峰值 5Mbps、并发 5 次/s、超带宽为“请求排队”。采集大体积内容时注意带宽顶格。
- 快代理官方建议：同一 IP 请求同一网站不超过 1 次/秒，避免被目标屏蔽；关闭 keep-alive（CLI 默认已遵循）。
- 参考开发者指南：<https://www.kuaidaili.com/doc/dev/tps/>；隧道错误码：<https://www.kuaidaili.com/doc/dev/tpshttpresponse/>。