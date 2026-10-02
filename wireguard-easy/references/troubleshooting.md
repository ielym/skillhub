# 排障手册（wireguard-easy）

## 排查顺序（黄金路径）

1. **客户端能否 ping 通服务端**：`ping 10.0.0.1`（通 = 隧道建立）
2. **握手是否成功**：服务端 `wg show wg0` → 看 `latest handshake` 是否有值且在增长（也可 `wireguard-easy status`）
3. **UDP 是否可达**：服务端抓包 `tcpdump -i eth0 -nn 'udp port 51820'`，客户端发起连接时有无入站包
4. **安全组/防火墙**：云控制台是否放行 UDP 51820 入站（**最常见原因**）

## 症状 → 原因对照

| 症状 | 大概率原因 | 处理 |
|---|---|---|
| 一直 Handshake in progress | 安全组未放行 UDP 51820 | 云控制台放行 |
| 一直 Handshake in progress | Endpoint 填成内网 IP | 填公网 IP/域名 |
| 一直 Handshake in progress | 服务端 wg0 未运行 | `systemctl start wg-quick@wg0` |
| 连上但无法上网 | AllowedIPs 不是 0.0.0.0/0 | 改客户端 AllowedIPs |
| 连上但无法上网 | 服务端 ip_forward=0 | `sysctl net.ipv4.ip_forward=1`（/etc/sysctl.d/99-wireguard.conf） |
| 连上但无法上网 | NAT 规则缺失 | `iptables -t nat -S POSTROUTING` 检查 MASQUERADE |
| 连接时通时断 | 公网 IP 是 NAT 后的（家用宽带） | 改用域名 + 端口转发；客户端保持 PersistentKeepalive |
| 只有部分设备能连 | 隧道 IP 冲突 | `wg show wg0 allowed-ips` 查重 |
| 重启服务器后 peer 丢失 | wg0.conf 未持久化 | `add-client` 已自动持久化；手工加 peer 需手动写 conf |
| 客户端导入报 Invalid name | conf 文件名/隧道名含非法字符 | 用 `[a-zA-Z0-9_-]` 命名 |

## 服务器命令速查

```bash
systemctl status wg-quick@wg0        # 服务状态
wg show wg0                          # peers / handshake / 流量
wireguard-easy status                # 同上（结构化视图）
wireguard-easy list-clients          # peers + 客户端文件
ip -brief addr show wg0              # 隧道地址
iptables -t nat -S POSTROUTING       # NAT 规则
tcpdump -i eth0 -nn 'udp port 51820' # 抓包看入站
journalctl -u wg-quick@wg0 -n 50     # 服务日志
```

## 客户端命令速查

```bash
# Windows（管理员 PowerShell）
ping 10.0.0.1
curl.exe -s https://api.ipify.org      # 应返回服务器公网 IP

# 手机
浏览器打开 https://api.ipify.org       # 同上
```

## 协议级疑难（上游项目已踩过的坑）

- **云安全组未放行** = 私网端点秒通、公网端点无响应（服务器抓包可见出站不见入站）
- **WireGuard KDF 是 HMAC-BLAKE2s256**：自研握手实现时 mac1 正确但无响应，多半是 KDF 链路错
- **AppArmor**：`wg set ... private-key` 只能读 `/etc/wireguard/` 下的密钥，`/tmp` 会 fopen 拒绝
- **Ubuntu 24.04+ 无 `/etc/sysctl.conf`**：转发配置写 `/etc/sysctl.d/`

## 上游脚本已修复的两处问题（本 CLI 内置版本已修复）

| 问题 | 现象 | 根因 | 修复 |
|---|---|---|---|
| 首个客户端添加失败 | `add-client.sh` 在全新服务器上无任何输出即退出；只残留 `<设备名>.key/.pub` | `set -euo pipefail` 下 `grep -oE` 无匹配返回 1，赋值语句失败导致脚本中断 | 该管道追加 `\|\| true` |
| 设备名被追加 `-` | 生成 `laptop-.conf`，按 `laptop` 移除时找不到设备 | `echo "$NAME" \| tr -c 'a-zA-Z0-9_-' '-'` 把 `echo` 的换行也转成了 `-` | 改用 `printf '%s' "$NAME" \| LC_ALL=C tr ...` |