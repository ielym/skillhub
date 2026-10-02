# 安装与配置详解（xray-easy）

## 1. 服务端部署（服务器上，root）

```bash
sudo xray-easy install                       # 默认 dest=www.cloudflare.com:443, 端口 443
sudo xray-easy install --dest www.apple.com  # 指定伪装站点
sudo xray-easy install --port 8443           # 端口 <1024 时安全组记得放行
```

install 内部依次完成：

1. **安装 Xray**（官方脚本）：
   ```bash
   bash -c "$(curl -L https://github.com/XTLS/Xray-install/raw/main/install-release.sh)" @ install
   ```
   生成 systemd 单元 `/etc/systemd/system/xray.service`，默认 `User=nobody` +
   `AmbientCapabilities=CAP_NET_ADMIN CAP_NET_BIND_SERVICE`（可绑定 443 特权端口）。

2. **生成 Reality 密钥对**：
   ```bash
   xray x25519
   # v26 输出（注意格式带冒号）:
   # PrivateKey: aJVO...
   # Password (PublicKey): WmWt...
   ```
   客户端要用 **Password (PublicKey)** 那行作 `pbk` 参数。

3. **生成 UUID 与 shortId**：
   ```bash
   xray uuid                 # 或 cat /proc/sys/kernel/random/uuid
   openssl rand -hex 4       # 8 位十六进制 shortId
   ```

4. **写 `/usr/local/etc/xray/config.json`**（模板）：

   ```json
   {
     "log": {"loglevel": "warning", "access": "/var/log/xray/access.log", "error": "/var/log/xray/error.log"},
     "inbounds": [{
       "listen": "0.0.0.0",
       "port": 443,
       "protocol": "vless",
       "settings": {
         "clients": [{"id": "<UUID>", "flow": "xtls-rprx-vision"}],
         "decryption": "none"
       },
       "streamSettings": {
         "network": "tcp",
         "security": "reality",
         "realitySettings": {
           "show": false,
           "dest": "www.cloudflare.com:443",
           "xver": 0,
           "serverNames": ["www.cloudflare.com"],
           "privateKey": "<PRIV>",
           "shortIds": ["<SID>"]
         }
       },
       "sniffing": {"enabled": true, "destOverride": ["http", "tls", "quic"]}
     }],
     "outbounds": [{"protocol": "freedom", "tag": "direct"}]
   }
   ```

5. **校验并启动**：`xray run -test -c config.json` → `systemctl enable --now xray`。

6. **安全组放行**：云控制台放行 TCP 443（或自定义端口）入站。

## 2. 生成客户端链接（服务器上）

```bash
sudo xray-easy link 43.110.43.207 --qr
```

输出形如：

```
vless://<UUID>@<IP>:443?encryption=none&flow=xtls-rprx-vision&security=reality&sni=www.cloudflare.com&fp=chrome&pbk=<PUB>&sid=<SID>&type=tcp&headerType=none#xray-easy
```

参数含义（客户端侧）：

| 参数 | 值 | 来源 |
| --- | --- | --- |
| UUID | vless:// 用户 id | install 生成，存 config.json |
| security | reality | 固定 |
| sni | 伪装域名 | 与服务器 dest 一致 |
| fp | chrome | utls 指纹（手机常用） |
| pbk | Reality 公钥 | 服务器私钥推导（`xray x25519 -i <priv>`） |
| sid | shortId | install 生成 |
| flow | xtls-rprx-vision | 与服务器 clients flow 一致 |

## 3. 更换伪装站点

```bash
sudo xray-easy change-dest www.apple.com
```

脚本会：校验新站点 TLS 可达（仅提示）→ 更新 config.json 的 dest/serverNames → `xray run -test` → 重启。**之后必须重新 `xray-easy link` 生成新链接导入客户端**（sni 变了，旧链接失效）。

## 4. 服务运维

```bash
sudo xray-easy status          # 服务/端口/dest/连接/错误日志
sudo xray-easy status --json   # 机器可读
sudo xray-easy restart|start|stop
sudo xray-easy log 50          # 最近 50 行 access+error
```

日志文件：`/var/log/xray/access.log`（每次成功代理的连接）、`/var/log/xray/error.log`（含 REALITY 握手失败记录）。
