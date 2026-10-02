# Android 手机接入（xray-easy · v2rayNG）

## 一、安装 v2rayNG APK

> 手机上安装 v2rayNG 是最常见的卡点（Play 商店需要翻墙）。优先用侧载：

1. 在能上网的机器上把 APK 放到服务器，再用手机浏览器直接下载（服务器已开 HTTP 服务时最方便）：
   ```bash
   # 服务器上（假设 80 端口有 HTTP 服务，目录 /root/wg-apk）
   cd /root/wg-apk
   curl -sL -o v2rayNG-arm64.apk \
     https://github.com/2dust/v2rayNG/releases/latest/download/v2rayNG_2.2.6_arm64-v8a.apk
   ```
   手机浏览器打开 `http://<服务器IP>/v2rayNG-arm64.apk` 下载安装。
2. 若安装报"解析包错误"：换成 `armeabi-v7a` 版本（老 32 位手机）。
3. 版本获取：<https://github.com/2dust/v2rayNG/releases/latest>（下载 `arm64-v8a` / `armeabi-v7a` 的 `.apk`，不要 fdroid 版无妨，均可）。

## 二、导入配置（二选一）

**方式 A：从剪贴板导入（最快）**

1. 复制服务器 `xray-easy link <IP>` 输出的整行 `vless://...`
2. v2rayNG → 右上角 ⋮ → **从剪贴板导入** → 自动生成配置

**方式 B：扫描二维码**

1. 服务器 `sudo xray-easy link <IP> --qr` 生成 PNG（`/root/xray-clients/vless-*.png`）
2. 把 PNG 传到手机 / 工作机查看 → v2rayNG → 右上角 ⋮ → **扫描二维码**

## 三、连接与验证

1. 选中新配置 → 点击右下角圆形按钮（变绿 = 已连接）
2. 打开浏览器访问 <https://api.ipify.org> → 显示**服务器公网 IP** = 隧道生效
3. 再开几个网站确认 DNS 正常

## 四、常见问题

| 症状 | 处理 |
| --- | --- |
| 一直转圈连不上 / 测试延迟失败 | 服务器安全组是否放行 TCP 443；链接 IP 是否公网 |
| 显示已连接但网页全打不开 | ① 先访问 api.ipify.org：能开 = DNS 问题，不能开 = 流量没通 |
| 显示已连接、ipify 能开但网站打不开 | **DNS 问题**：v2rayNG 设置 → 点当前配置 → DNS → 改为 `223.5.5.5`（或 8.8.8.8） |
| 换过 dest 后旧配置失效 | 需重新 `xray-easy link` 导入新链接（sni 变了） |
| 测速/大文件很慢 | 服务器本身是境外小水管；换大带宽或就近地区 |

## 五、注意事项

- **同一时刻只开一个代理**：使用 v2rayNG 时关闭 WireGuard App 的开关，避免双隧道冲突。
- 全局代理下，手机 DNS 若走局域网地址（如 192.168.1.1）会被隧道转发到服务器侧不可达，表现为"连上没网"——优先在 v2rayNG 里显式指定公网 DNS（223.5.5.5）。
- v2rayNG 的"测试配置"（底部测延迟）能通不代表网页能开，最终以浏览器访问为准。
