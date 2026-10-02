---
name: xray-easy
description: Xray VLESS+Reality 一键部署与接入：在 Linux 云服务器上一条命令完成 Xray 安装与 Reality 服务端配置（生成密钥/UUID/写配置/启动），一条命令生成 vless 客户端链接与二维码，支持查看状态、更换伪装站点、查看日志。当 WireGuard 被 GFW/运营商封锁、需要抗封锁代理、或用户要搭建 VLESS+Reality 服务端并给手机/电脑接入时使用。
version: 1.0.0
---

# xray-easy（Xray VLESS+Reality 一键部署与接入）

把「手动装 Xray + 手写 Reality 配置 + 手拼 vless 链接」压缩为：**服务器 1 条命令部署，每台设备 1 条命令/1 次扫码接入**。

源码仓库：<https://github.com/ielym/xray-easy>（skill + CLI 一体化）。

```
┌──────────────┐  TLS TCP 443  ┌────────────────────────────────┐
│ 手机 v2rayNG │ ────────────► │ 云服务器 (Linux, root)           │
│              │  VLESS+Reality│ Xray :443 → Reality 伪装 → 出网  │
└──────────────┘   伪装成 HTTPS │ (SNI/dest = 真实站点，不可区分)   │
                               └────────────────────────────────┘
```

## 为什么用 Reality（何时选它）

- **WireGuard 默认 UDP 51820 易被 GFW/运营商端口级封锁**（实测：境外服务器 + 中国内地宽带，51820 握手永不完成，换 8443 立通——端口级封锁，非内容级）。
- **VLESS+Reality** 走 TCP 443，TLS 握手与真实 HTTPS 不可区分（SNI/dest 指向真实站点），抗封锁能力最强，是目前推荐方案。
- 客户端用 **v2rayNG**（Android）/ 任意支持 Reality 的客户端。

## 前置条件

- 服务端：任意 Linux 云主机（root 权限），脚本基于 Debian/Ubuntu 的 `apt`；Xray 官方安装脚本安装，默认 TCP 443。
- 客户端：手机安装 **v2rayNG**（APK 侧载，见 [references/client-android.md](./references/client-android.md)）。
- **唯一需要手动的一步**：云控制台安全组放行 **TCP 443 入站**（端口 <1024 同理）。

## 安装 CLI

依赖 Node.js ≥ 18 与 Bash（服务端脚本）。该包未发布到公共 npm registry，从源码目录安装：

```bash
git clone https://github.com/ielym/xray-easy.git /mnt/data01/projects/xray-easy   # 首次；已有则跳过
npm i -g /mnt/data01/projects/xray-easy/cli                                        # 得到 xray-easy 命令
```

> CLI 运行在**服务器上**（需要 root 操作 /usr/local/etc/xray/config.json 与 systemd）；源码存放在工作机。

## 快速流程

```bash
# ① 服务端（一次性，约 1 分钟；在服务器上执行）
sudo xray-easy install                              # 默认 dest=www.cloudflare.com:443
# 或指定伪装站点/端口: sudo xray-easy install --dest www.apple.com --port 8443

# ② 生成客户端链接（服务器上执行；公网IP或域名）
sudo xray-easy link 43.110.43.207 --qr              # 打印 vless:// 链接 + 生成二维码 PNG

# ③ 手机接入
#   安装 v2rayNG → 右上角 ⋮ → 「从剪贴板导入」粘贴链接 / 「扫描二维码」→ 连接
```

## 命令参考

| 命令 | 说明 | 需要 root |
| --- | --- | --- |
| `xray-easy install [--dest 站点:端口] [--port 端口] [--force]` | 装 Xray、生成 x25519 密钥/UUID/shortId、写 Reality 配置、启动（幂等） | 是 |
| `xray-easy link <公网IP或域名> [--qr]` | 生成 vless:// 客户端链接（--qr 同时输出二维码 PNG） | 是 |
| `xray-easy change-dest <站点[:端口]>` | 更换伪装站点（dest + SNI），自动重启；**换后客户端 sni 需重新导入** | 是 |
| `xray-easy status [--json]` | 服务状态、监听端口、伪装站点、443 连接、错误日志 | 是 |
| `xray-easy restart / start / stop` | 服务管理 | 是 |
| `xray-easy log [行数]` | 查看 access/error 日志（默认 30 行） | 是 |

默认值：dest `www.cloudflare.com:443`、端口 `443`、流控 `xtls-rprx-vision`、fingerprint `chrome`。

## 产物位置

| 路径 | 内容 |
| --- | --- |
| `/usr/local/etc/xray/config.json` | 服务端配置（VLESS+Reality inbound + freedom outbound） |
| `/var/log/xray/access.log` / `error.log` | 访问日志 / 错误日志（含 REALITY 握手结果） |
| `/root/xray-clients/vless-*.png` | `link --qr` 生成的二维码 |

## 设备接入

**Android（v2rayNG）**：安装 v2rayNG APK（下载源与步骤见 [references/client-android.md](./references/client-android.md)）→ 右上角 ⋮ → 从剪贴板导入 / 扫描二维码 → 选中配置 → 点击右下角圆形按钮连接。

**验证**：浏览器打开 <https://api.ipify.org>，返回**服务器公网 IP** 即隧道生效；再随便开几个网站确认 DNS 正常。

## 排障（黄金路径）

按顺序查：① 客户端是否显示已连接 → ② 服务器 `xray-easy status` 的 443 连接与错误日志 → ③ 服务器 `xray-easy log 50` 看 `REALITY: processed invalid connection` → ④ 云安全组是否放行 TCP 端口（**最常见原因**）。

| 症状 | 大概率原因 | 处理 |
| --- | --- | --- |
| 一直连不上 / 测试延迟失败 | 安全组未放行 TCP 端口 | 云控制台放行入站 |
| 显示已连接但没网 | **dest 站点拒绝 Reality 握手**（如 www.microsoft.com 的 Akamai 校验 TLS 指纹） | `change-dest` 换成 www.cloudflare.com 等宽容站点，客户端重新导入 |
| 显示已连接但没网 | 客户端链接的 sni 与服务器 dest 不一致（换过 dest） | 重新 `link` 生成新链接导入 |
| 显示已连接但没网 | 客户端 DNS 问题 | v2rayNG 设置中把 DNS 改为 223.5.5.5 / 8.8.8.8；先访问 api.ipify.org 区分 DNS 与流量问题 |
| error.log 大量 `REALITY: processed invalid connection` | Reality 握手失败：密钥/UUID/SNI 不匹配 或 dest 不通 | 核对链接参数；`change-dest` 换站点 |
| 服务启动失败 status=23 | config.json 语法/字段错误（如空 privateKey） | `xray run -test -c /usr/local/etc/xray/config.json` 定位 |

完整症状对照与协议级疑难见 [references/troubleshooting.md](./references/troubleshooting.md)。

## 注意事项

- **dest 不要选 www.microsoft.com**（Akamai CDN 会拒绝 Reality 转发来的 utls ClientHello，导致所有客户端"连上但没网"，握手日志报 `REALITY: processed invalid connection`）。推荐 www.cloudflare.com / www.apple.com / www.google.com 等对任意 TLS 指纹宽容的站点。
- `install` 幂等：已配置时再次执行只提示、不覆盖；需要重建用 `--force`（危险，**所有客户端需重新导入**）。
- `change-dest` 后客户端链接的 `sni` 参数必须同步更新，否则旧链接全部失效。
- Xray 官方 systemd 单元以 `nobody` 运行并带 `AmbientCapabilities=CAP_NET_BIND_SERVICE`，可绑定 443 等特权端口；无需额外处理。
- 服务器若在境外（阿里云美国等），中国客户端流量全程穿越 GFW——这正是 WireGuard 被端口封锁、需换 Reality 的原因；同理避免再用 UDP 51820 等"指纹"端口。
- `xray x25519` 新版输出格式为 `PrivateKey:` / `Password (PublicKey):`（带冒号），解析时两种格式都要兼容。
- 客户端链接含 UUID/PublicKey，属凭据；二维码 PNG 妥善保管，勿公开分享。
- 仅需内网互访时，可在客户端将路由改为仅隧道网段；默认全走代理（0.0.0.0/0 全局）。

安装/配置/客户端/排障的详细展开分别见：
- [references/install.md](./references/install.md)
- [references/client-android.md](./references/client-android.md)
- [references/troubleshooting.md](./references/troubleshooting.md)
