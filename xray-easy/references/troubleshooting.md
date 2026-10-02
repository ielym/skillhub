# 排障手册（xray-easy）

> 本文基于一次真实生产故障整理：WireGuard 在境外服务器被 GFW/运营商端口级封锁，迁移到 VLESS+Reality 过程中踩过的所有坑。按症状自顶向下排查。

## 0. 排障黄金路径

```
客户端"连不上" ──► ① 安全组放行 TCP 端口？ ── 未放行 → 放行
                │
                └─ ② 服务器 xray-easy log 50
                     error.log 有 REALITY 记录？
                     ├─ 无记录 → 请求根本没到服务器（安全组/防火墙/端口）
                     └─ 有记录 →
                          "processed invalid connection" → 见 §3 Reality 握手失败
                          正常连接记录 → 见 §4 连上但没网
```

## 1. 显示"已连接"但实际没网 —— 先分清 DNS 还是流量

**决定性测试**：浏览器访问 <https://api.ipify.org>（纯 IP 站点，无 DNS 依赖）。

| 结果 | 结论 | 处理 |
| --- | --- | --- |
| 能显示服务器 IP | 流量通，纯 DNS 问题 | 见 §2 |
| 打不开 | 流量没通 | 见 §3 / §4 |

## 2. 连上但没网（DNS 问题）

- 症状：ipify 能开、普通网站打不开；或全部打不开但服务器日志有正常连接记录。
- 原因：客户端把 DNS 查询也走代理转发，而客户端配置的 DNS 是**局域网地址**（如 192.168.1.1 / 路由器），服务器侧不可达 → 解析失败。
- 处理：v2rayNG → 点当前配置 → DNS → 改为公网 DNS `223.5.5.5` 或 `8.8.8.8`；或让代理只代理流量、DNS 走本机（v2rayNG 设置里调整）。

## 3. Reality 握手失败 —— "REALITY: processed invalid connection"

**日志特征**（`/var/log/xray/error.log`）：

```
REALITY: processed invalid connection from <客户端IP>: handshake did not complete successfully
```

**这是"显示已连接但没网"的最常见服务端原因**：TCP 连接建立（所以客户端显示"已连接"），但 Reality 层握手未完成，隧道实际不存在。

逐一核对：

| 检查项 | 方法 | 说明 |
| --- | --- | --- |
| dest 站点是否"宽容" | `curl -sI https://<dest>` 可达 ≠ 可作 dest | **www.microsoft.com 的 Akamai 会拒绝 utls 指纹的 ClientHello**，导致全部客户端握手失败（实测）。换 `www.cloudflare.com` / `www.apple.com` / `www.google.com` |
| 密钥对是否匹配 | `xray x25519 -i <服务端私钥>` 得到的公钥 == 客户端 pbk | 不匹配 → 100% 失败 |
| sni 是否一致 | 客户端链接 sni == 服务器 serverNames | 换过 dest 没重新导链接 = 常见原因 |
| shortId 是否一致 | 客户端 sid ∈ 服务器 shortIds | 不匹配 → 失败 |
| flow 是否一致 | 两边都 `xtls-rprx-vision` 或都无 | 不一致 → 失败 |

**调试技巧（强烈推荐）**：在服务器上跑一个**客户端模式** xray 实例自测，与手机完全解耦：

```bash
# 服务器上：写客户端配置，连自己的公网 IP
cat > /root/xray-client-test/config.json <<'EOF'
{ "log": {"loglevel": "warning"},
  "inbounds": [{"listen": "127.0.0.1", "port": 10808, "protocol": "socks", "settings": {"udp": true}}],
  "outbounds": [{"protocol": "vless", "settings": {"vnext": [{"address": "<服务器公网IP>", "port": 443,
      "users": [{"id": "<UUID>", "encryption": "none", "flow": "xtls-rprx-vision"}]}]},
    "streamSettings": {"network": "tcp", "security": "reality",
      "realitySettings": {"serverName": "<SNI>", "fingerprint": "chrome", "publicKey": "<PUB>", "shortId": "<SID>"}}}]
}
EOF
nohup /usr/local/bin/xray run -c /root/xray-client-test/config.json > /tmp/ct.log 2>&1 &
curl -s --max-time 12 --socks5-hostname 127.0.0.1:10808 https://api.ipify.org
```

- 返回服务器 IP → 服务端配置正确，问题在手机端（DNS/链接参数）
- 失败 → 服务端配置问题，看 error.log 定位

## 4. 服务端配置校验失败 / 启动失败

| 现象 | 原因 | 处理 |
| --- | --- | --- |
| `systemctl status xray` 显示 exit status=23 | config.json 语法或字段错误 | `xray run -test -c /usr/local/etc/xray/config.json` 看具体报错 |
| `empty "privateKey"` | x25519 密钥没写进配置 | 重新 install 或手动补 privateKey（注意 xray x25519 输出格式：v26 为 `PrivateKey:` / `Password (PublicKey):` 带冒号） |
| 启动成功但不监听端口 | 端口被占 / 权限 | `ss -tlnp \| grep :443`；nobody 用户绑特权端口需 `AmbientCapabilities=CAP_NET_BIND_SERVICE`（官方 unit 已含） |

## 5. WireGuard 被封锁的判别（为什么换 Reality）

真实案例：境外服务器（阿里云美国）+ 中国内地宽带（联通北京）。

| 证据 | 结论 |
| --- | --- |
| 同一服务器、同一 51820 端口，其他设备（笔记本/旧手机）历史握手成功 | 服务器与端口本身正常 |
| 手机当前链路在 51820 上握手永不完成：initiation 到达服务器、92B 响应离开服务器、type-4 永不出现 | 服务器→手机的 UDP 回包被中间链路丢弃 |
| 同服务器换 UDP 8443，同手机立通 | **端口级封锁**（51820 被针对性封锁，非内容级——相同 WireGuard 内容在 8443 可通） |
| 服务器 IP 归属地在美国（AS45102 Alibaba US）、手机在中国（AS4808 联通） | 流量全程穿越 GFW |

**判别流程**：同一客户端换端口（如 8443）能通 ⇒ 端口级封锁 ⇒ WireGuard 类 UDP 指纹端口不可靠 ⇒ 迁移 VLESS+Reality（TCP 443 抗封锁）。或直接用 Reality 一劳永逸。

## 6. 端口 <1024 绑定时权限拒绝（AppArmor）

现象：`ip link set mtu 1420 up dev wg1` 报 Permission denied；dmesg 显示 `apparmor profile=wg-quick//ip ... capability net_bind_service denied`。

- 根因：Ubuntu AppArmor 的 wg-quick profile 拒绝非 root 网络管理进程绑定特权端口（<1024）。
- 处理：WireGuard 侧换高位端口（8443 等）；Xray 侧无此问题（官方 unit 已带 `AmbientCapabilities`，且无 AppArmor profile 约束）。

## 7. 客户端参数逐项对照表

| 客户端参数 | 必须等于 |
| --- | --- |
| address / port | 服务器公网 IP 与监听端口 |
| uuid | config.json clients[0].id |
| security | reality |
| sni | config.json realitySettings.serverNames[0] |
| pbk | `xray x25519 -i <config privateKey>` 输出的 Password (PublicKey) |
| sid | config.json realitySettings.shortIds[0] |
| flow | config.json clients[0].flow（一般 xtls-rprx-vision） |
