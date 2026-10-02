# Android 手机接入（wireguard-easy）

## 方式一：扫码（推荐，最快）

1. 服务器上执行：
   ```bash
   sudo wireguard-easy add-client phone-你的设备名
   ```
2. 终端渲染二维码：`wireguard-easy qr phone-你的设备名`（也可用生成的 PNG：`/root/wireguard-clients/phone-xxx.png`）
3. 手机安装官方 WireGuard App → **+** → **扫描二维码** → 命名保存 → 打开开关

## 方式二：文件导入

`wireguard-easy conf phone-xxx > phone-xxx.conf` 取回配置（或直接把 `/root/wireguard-clients/phone-xxx.conf` 传到手机）→ WireGuard App → **+** → **从文件或存档导入**。

## 官方 APK 获取

- **官方唯一侧载源**（推荐）：<https://download.wireguard.com/android-client/>
  目录页会列出最新 `com.wireguard.android-<版本>.apk`，直接下载
- Google Play：搜索 "WireGuard"（`com.wireguard.android`）
- 不要从第三方 APK 站点下载

## 验证

连接后开关变绿，可打开浏览器访问 <https://api.ipify.org>，显示服务器公网 IP 即隧道生效。

## 常见问题

- **一直 Handshake in progress**：检查服务器安全组是否放行 UDP 51820、Endpoint 是否填了公网 IP/域名
- **连上但没网**：检查客户端 `AllowedIPs` 是否 `0.0.0.0/0`、`DNS` 是否有值（223.5.5.5）
- **iOS**：同为官方 App（App Store "WireGuard"），扫码或从文件导入 `.conf`，步骤一致。