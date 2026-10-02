---
name: wireguard-easy
description: WireGuard 一键部署与接入：在 Linux 云服务器上一条命令完成服务端部署，按设备名一条命令生成客户端配置与二维码，并支持查看隧道状态、移除设备、导出 Windows 一键连接脚本。当用户要搭建 WireGuard / VPN 服务端、给电脑或手机添加接入、查看握手与流量状态、排查连不上或连上没网、或更换服务器迁移时使用。
---

# wireguard-easy（WireGuard 一键部署与接入）

把「手动部署 WireGuard 服务端 + 逐台配置客户端」压缩为：**服务器 1 条命令部署，每台设备 1 条命令 / 1 次扫码接入**。

上游脚本仓库：<https://github.com/ielym/wireguard-easy>（CLI 已内置该仓库的服务端脚本与客户端一键脚本）。

```
┌──────────────┐   UDP 51820    ┌────────────────────────────────┐
│ Windows/手机  │ ─────────────► │ 云服务器 (Linux, root)          │
│ 10.0.0.2     │  WireGuard 隧道 │ wg0: 10.0.0.1/24               │
└──────────────┘                │ NAT(MASQUERADE) → 互联网        │
                                └────────────────────────────────┘
```

## 前置条件

- 服务端：任意 Linux 云主机（root 权限），脚本基于 Debian/Ubuntu 的 `apt`；隧道默认 UDP 51820 / 网段 10.0.0.0/24。
- 客户端：始终使用 **WireGuard 官方客户端/App**（Windows 客户端、Android / iOS App），本方案只负责部署与发配置。
- **唯一需要手动的一步**：在云控制台安全组放行 **UDP 51820 入站**，否则客户端握手无响应（最常见故障）。

## 安装 CLI

依赖 Node.js ≥ 18 与 Bash（服务端脚本）。该包未发布到公共 npm registry，从源码目录安装：

```bash
git clone https://github.com/ielym/clihub.git <cli 源码目录>   # 首次；已有则跳过
npm i -g <cli 源码目录>/wireguard-easy                          # 得到 wireguard-easy 命令
```

## 快速流程

```bash
# ① 服务端（一次性，约 1 分钟）
sudo wireguard-easy install vpn.example.com          # 或公网 IP

# ② 添加设备（每台一条）
sudo wireguard-easy add-client laptop
sudo wireguard-easy add-client phone-xiaomi

# ③ 设备接入
#   Windows: wireguard-easy windows ./wg-client   → 放入 .conf → 管理员运行 onekey-connect.bat
#   手机    : wireguard-easy qr phone-xiaomi        → 用 WireGuard App 扫终端/图片二维码
```

## 命令参考

| 命令 | 说明 | 需要 root |
| --- | --- | --- |
| `wireguard-easy install <公网IP或域名> [端口] [网段] [--force]` | 部署服务端：装 WireGuard、生成密钥、写配置、开转发、开机自启（幂等） | 是 |
| `wireguard-easy add-client <设备名> [隧道IP]` | 加设备：生成密钥对、分配隧道 IP、登记并与持久化、生成 `.conf` 与二维码 | 是 |
| `wireguard-easy list-clients` | 列出运行中的 peer 与已生成的客户端文件 | 是 |
| `wireguard-easy remove-client <设备名或公钥>` | 移除设备：热移除 peer + 从 `wg0.conf` 删除条目 + 清理客户端文件 | 是 |
| `wireguard-easy status [--json]` | 查看服务状态、接口信息、各 peer 的握手/流量、已登记设备 | 否（非 root 读不到 wg 详情） |
| `wireguard-easy qr <设备名>` | 在终端渲染该设备的二维码（同时给出 PNG 路径） | 否 |
| `wireguard-easy conf <设备名>` | 打印该设备的客户端配置 `.conf` 内容 | 否 |
| `wireguard-easy windows [输出目录]` | 导出 Windows 一键连接脚本（`onekey-connect.bat` / `.ps1`） | 否 |

默认值：端口 `51820`、网段 `10.0.0.0/24`（服务端隧道地址 `10.0.0.1`）、客户端 DNS `223.5.5.5`、`AllowedIPs = 0.0.0.0/0`（全局代理）、`PersistentKeepalive = 25`。

## 产物位置

| 路径 | 内容 |
| --- | --- |
| `/etc/wireguard/server.key` / `server.pub` | 服务端密钥对（私钥 600） |
| `/etc/wireguard/wg0.conf` | 服务端配置（含各 `[Peer]`，热添加的同时持久化，重启不丢） |
| `/etc/wireguard/public_endpoint` | install 时传入的公网 IP/域名，供 add-client 自动填 Endpoint |
| `/root/wireguard-clients/<设备名>.conf` / `.key` / `.pub` / `.png` | 客户端配置、密钥对、二维码 |

## 设备接入

**Windows**：`wireguard-easy windows ./wg-client` 导出脚本 → 把客户端 `.conf` 重命名为 `wireguard-client.conf` 放入同目录 → 右键「以管理员身份运行」`onekey-connect.bat`（自动装官方客户端 → 导入隧道 → 启动连接）。

**Android / iOS**：安装官方 WireGuard App → `+` → 扫描二维码（`wireguard-easy qr <设备名>` 可在终端直接扫）或「从文件导入」`.conf` → 打开开关。

**验证**：客户端 `ping 10.0.0.1` 通，浏览器访问 <https://api.ipify.org> 返回服务器公网 IP。

Android 侧详细说明（官方 APK 侧载源、常见问题）见 [references/client-android.md](./references/client-android.md)。

## 排障（黄金路径）

按顺序查：① `ping 10.0.0.1` 能否通 → ② 服务端 `wg show wg0` 的 `latest handshake` 是否增长 → ③ 服务端 `tcpdump -i eth0 -nn 'udp port 51820'` 有无入站包 → ④ 云安全组是否放行 UDP 51820（**最常见原因**）。

| 症状 | 大概率原因 | 处理 |
| --- | --- | --- |
| 一直 Handshake in progress | 安全组未放行 UDP 51820 | 云控制台放行入站 |
| 一直 Handshake in progress | Endpoint 填成内网 IP | 改公网 IP/域名 |
| 一直 Handshake in progress | 服务端 wg0 未运行 | `systemctl start wg-quick@wg0` |
| 连上但无法上网 | 服务端 `ip_forward=0` 或 NAT 规则缺失 | 查 `/etc/sysctl.d/99-wireguard.conf`、`iptables -t nat -S POSTROUTING` |
| 连接时通时断 | 公网 IP 是 NAT 后的（家用宽带） | 改用域名 + 端口转发 |
| 只有部分设备能连 | 隧道 IP 冲突 | `wg show wg0 allowed-ips` 查重 |

完整症状对照与协议级疑难见 [references/troubleshooting.md](./references/troubleshooting.md)。

## 更换服务器

判断原则：**服务端私钥变不变，决定客户端要不要全部重做。**

- 策略 A（推荐，影响最小）：新机 `install` → 覆盖旧机 `/etc/wireguard/server.key` → 追加旧 `[Peer]` 段 → 安全组放行 → 每台客户端只改 `Endpoint` 一行。
- 策略 B（最干净）：新机 `install` → 逐台 `add-client` 重新生成并重新导入。

完整步骤与检查清单见 [references/migration.md](./references/migration.md)。

## 注意事项

- 所有服务端操作需 root；`/root/wireguard-clients/*.key` 与 `.conf` 含私钥，妥善保管。
- `install` 幂等：已运行时再次执行只提示状态、不覆盖密钥；需要重建用 `--force`（危险，会导致所有客户端需重新导入）。
- `add-client` 同名设备重复执行会重建该设备密钥与配置。
- 隧道默认是全局代理（`AllowedIPs = 0.0.0.0/0`）；只要内网互通需自行改客户端 `AllowedIPs`。
- CLI 内置的脚本版本已修复上游两处问题：首个客户端添加时被 `set -e` 中断、设备名被追加 `-` 后缀。若直接使用上游仓库脚本，需自行打补丁。