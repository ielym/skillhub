---
name: aliyun-oss
description: 阿里云 OSS 对象存储操作 CLI。当用户需要上传、下载、列举、删除、同步 OSS 文件，判断对象是否存在，或生成签名 URL、查看 Bucket 用量时使用。底层调用 ossutil，同地域可用内网 Endpoint 免流量费。
---

# aliyun-oss（阿里云 OSS 操作 CLI）

用一条 `aliyun-oss` 命令完成 OSS 的上传、下载、列举、删除、同步、存在性判断、签名 URL 与用量统计，底层调用 ossutil；凭证统一由 **ielym-certification** 取回。

以下示例中 `<file>`、`<dir>`、`<bucket>` 均为占位符，使用时替换为实际值。

## 前置条件与安装

### 1. 安装 ossutil

ossutil 是阿里云官方命令行工具，支持 Windows / Linux / macOS（x86 与 arm）。安装方式二选一：

- **推荐**：按官方文档下载对应平台的 ossutil 2.0 压缩包 —— <https://help.aliyun.com/zh/oss/install-ossutil2>
- **直接下载**：Linux x86\_64 形如
  `https://gosspublic.alicdn.com/ossutil/v2/<version>/ossutil-<version>-linux-amd64.zip`
  （其他平台把文件名后缀换成 `-mac-arm64`、`-windows-amd64` 等）

解压后完成下面任意一步即可：

1. 把其中的 `ossutil` 可执行文件放入 PATH 中的任意目录（Linux/macOS 需先 `chmod +x`）；
2. 或保留其原位置，设置环境变量 `ALIYUN_OSS_OSSUTIL` 指向该文件。

验证与升级：

```bash
ossutil version        # 能打印版本号即安装成功
ossutil update         # 升级到最新版（加 -f 免交互确认）
```

### 2. 安装本 CLI

依赖 Node.js ≥ 18 与 Python ≥ 3.10（CLI 为 Node 薄封装 + Python 实现）。该包未发布到公共 npm registry，从源码目录安装：

```bash
npm i -g <cli-source-dir>
```

安装后用 `aliyun-oss --help` 确认命令可用。

### 3. 凭证

凭证**统一由 ielym-certification 提供**：本 CLI 每次执行自动取回对应 Bucket 的凭证并一次性注入底层调用，无需配置 AccessKey、环境变量或任何 ossutil 配置文件，也不要手工粘贴密钥。

首次在一台设备上使用时，若命令提示未引导，按 **ielym-certification** skill 的说明完成一次性引导即可（每台设备一次），之后本 CLI 直接可用。

手动查看某 Bucket 的原始凭证：

```bash
ielym-certification aliyun-oss --bucket <bucket>
```

用 `aliyun-oss info` 检查 ossutil 与凭证来源是否就绪（该命令不会打印密钥）。

## 常用命令

```bash
aliyun-oss info                                  # 查看环境与配置
aliyun-oss buckets                               # 列出所有 Bucket
aliyun-oss ls oss://my-bucket/data/              # 列出对象（-r 递归）
aliyun-oss exists oss://my-bucket/a.pdf          # 判断对象是否存在（存在 0，不存在 1）
aliyun-oss stat oss://my-bucket/a.pdf            # 查看对象元数据
aliyun-oss upload <file> oss://my-bucket/        # 上传文件
aliyun-oss upload <dir>/ oss://my-bucket/        # 上传目录（自动递归）
aliyun-oss download oss://my-bucket/a.pdf <dir>  # 下载文件（-r 下载目录）
aliyun-oss rm oss://my-bucket/old/a.txt          # 删除对象（-r 删除目录）
aliyun-oss sync <dir>/ oss://my-bucket/data/     # 增量同步
aliyun-oss du oss://my-bucket/                   # 统计用量
aliyun-oss presign oss://my-bucket/a.png --timeout 3600   # 生成签名 URL
```

加 `--json` 输出结构化信封，便于程序化消费。完整参数与输出格式见 [references/commands.md](references/commands.md)。

判断对象是否存在用 `exists`，退出码即结论，适合脚本判断；等价的原生命令是 `ossutil stat`（存在退出 0，不存在 404/NoSuchKey 退出 2）：

```bash
if aliyun-oss exists oss://my-bucket/report.pdf; then echo "已存在"; else echo "不存在"; fi
```

注意 `exists` 只判断**单个对象**；判断「前缀下是否有对象」用 `aliyun-oss ls oss://<bucket>/<prefix>/` 后看 `Object Number`。

## 必须遵守的规则

使用本 CLI 时必须遵守：

1. **同地域必须走内网 Endpoint**。客户端与 Bucket 同地域时（例如 ECS 与 Bucket 在同一地域），必须使用内网域名（形如 `oss-cn-<region>-internal.aliyuncs.com`，即 ielym-certification 返回的 `endpoints.internal`），通过环境变量 `ALIYUN_OSS_ENDPOINT` 注入；上传、下载、同步都不得改用外网 Endpoint。
2. **只有确需公网时才用外网域名**。仅当要生成公网可访问的签名链接、或客户端确实不在同地域 VPC 内时，才显式指定外网 Endpoint。
3. **不得随意降冷存储**。频繁访问的内容必须留在标准存储；长期不取的文件在降冷（低频/归档）前，必须先确认取回费用与最低存储时长。

依据：上传不产生流量费，而下载走公网会按「外网流出流量」计费，是同地域场景下最主要的开销。

## 注意事项

- **`presign`** **生成的 URL 使用当前 Endpoint**：若默认走内网，产物形如 `https://<bucket>.oss-cn-<region>-internal.aliyuncs.com/...`，**只能在 VPC 内访问**；要分享到公网，请显式指定外网域名：`aliyun-oss presign oss://<bucket>/<key> -e oss-cn-<region>.aliyuncs.com`。
- `rm -r` 与 `sync --delete` 会批量删除，执行前先用 `ls -r` 确认范围。
- Bucket 名可用环境变量 `ALIYUN_OSS_BUCKET` 设为默认，`upload` 省略 target 时自动拼接。

