# aliyun-oss 命令参考

> 本文档不含任何具体路径与凭证，`<file>`、`<dir>`、`<bucket>` 等均为占位符，使用时替换为实际值。

## 一、命令总览

| 命令 | 别名 | 作用 | 关键参数 |
| --- | --- | --- | --- |
| `buckets` | — | 列出所有 Bucket | — |
| `ls` | `list` | 列出 Bucket 或对象 | `path`、`-r/--recursive` |
| `exists` | `check` | 判断对象是否存在（存在退出 0，不存在 1） | `path` |
| `stat` | — | 查看对象元数据 | `path` |
| `upload` | `up`、`put` | 上传文件/目录到 OSS | `source`、`target`(可选)、`-r` |
| `download` | `down`、`get` | 下载 OSS 对象 | `source`、`target`(可选)、`-r` |
| `cp` | — | 通用拷贝，自动识别方向，支持 OSS↔OSS | `source`、`target`、`-r` |
| `sync` | — | 增量同步目录 | `source`、`target`、`--delete` |
| `rm` | `delete`、`del` | 删除对象 | `path`、`-r` |
| `du` | — | 统计 Bucket/目录用量 | `path`(可选) |
| `presign` | `sign`、`url` | 生成签名 URL | `path`、`--timeout 秒`、`--expires 时长` |
| `info` | — | 显示环境与凭证来源状态（不含密钥） | — |

通用选项（所有子命令均可加）：

| 选项 | 说明 |
| --- | --- |
| `-e, --endpoint` | 覆盖 OSS 访问域名（默认用 ielym-certification 返回的内网域名） |
| `--region` | 覆盖地域 ID（默认取 ielym-certification 返回的地域） |
| `--json` | 以 JSON 信封输出结果 |

## 二、环境变量

| 变量 | 作用 |
| --- | --- |
| `ALIYUN_OSS_BUCKET` | 默认 Bucket；`upload` 省略 target 或只给 Bucket 根时，自动拼成 `oss://<bucket>/temp/<文件名>`（禁止上传到根目录） |
| `ALIYUN_OSS_OSSUTIL` | ossutil 可执行文件的绝对路径（PATH 中没有时使用） |
| `ALIYUN_OSS_CERTIFICATION_BIN` | ielym-certification 可执行文件的绝对路径（PATH 中没有时使用） |

## 三、凭证

凭证**统一由 ielym-certification 提供**，本 CLI 不接受也不读取任何其他认证方式（不读 ossutil 配置文件、不读 AK 环境变量）：

- 每次执行自动向 ielym-certification 取回对应 Bucket 的凭证，一次性注入底层调用，不落盘；
- 首次在一台设备上使用若提示未引导，按 ielym-certification skill 完成一次性引导；
- 手动查看原始凭证：`ielym-certification aliyun-oss --bucket <bucket>`。

## 四、判断对象是否存在

```bash
# 方式 1：CLI 封装（推荐，语义清晰）
aliyun-oss exists oss://<bucket>/report.pdf     # 打印 true/false，退出码 0/1
aliyun-oss exists oss://<bucket>/report.pdf --json

# 方式 2：ossutil 原生
ossutil stat oss://<bucket>/report.pdf          # 存在 → 退出 0 并打印元数据
                                                # 不存在 → 404 NoSuchKey，退出 2
# 方式 3：列举后看数量
ossutil ls oss://<bucket>/<prefix>/             # 看输出末尾 Object Number
```

说明：`exists`/`stat` 针对**单个对象**；`stat` 对目录前缀无效（目录是逻辑概念，请用 `ls`）。

## 五、输出格式

默认透传 ossutil 的可读输出。加 `--json` 输出信封：

```json
{
  "cli": "aliyun-oss",
  "command": "ls",
  "ok": true,
  "exit_code": 0,
  "elapsed_s": 0.031,
  "endpoint": null,
  "region": null,
  "command_line": ["ossutil", "ls", "oss://<bucket>/<prefix>/", "-r"],
  "data": "..."
}
```

`exists` 的信封形如：

```json
{
  "cli": "aliyun-oss",
  "command": "exists",
  "path": "oss://<bucket>/<key>",
  "exists": false,
  "exit_code": 1
}
```

## 六、典型工作流

```bash
# 0) 先确认环境与 Bucket
aliyun-oss info
aliyun-oss buckets

# 上传路径规则：目标必须带至少一级目录前缀（oss://<bucket>/<dir>/...），
# 禁止直接传到根目录；未指定前缀时默认使用 temp/（oss://<bucket>/temp/...）。

# 1) 上传单个文件
aliyun-oss upload <file> oss://<bucket>/reports/report.pdf

# 2) 上传整个目录（自动递归）
aliyun-oss upload <dir>/ oss://<bucket>/dataset/

# 3) 查看 / 判断是否存在
aliyun-oss ls oss://<bucket>/dataset/ -r
aliyun-oss exists oss://<bucket>/dataset/part-000.parquet

# 4) 下载（目录需 -r）
aliyun-oss download oss://<bucket>/dataset/ <dir> -r

# 5) 增量同步（仅传输新增/变更）
aliyun-oss sync <dir>/ oss://<bucket>/dataset/

# 6) 生成临时下载链接（公网分享务必指定外网域名）
aliyun-oss presign oss://<bucket>/reports/report.pdf --timeout 3600 -e oss-cn-<region>.aliyuncs.com

# 7) 清理
aliyun-oss rm oss://<bucket>/dataset/ -r
```

## 七、成本要点

| 项目 | 说明 |
| --- | --- |
| 上传 | **不产生流量费**（上行免费），仅极低的请求费 |
| 下载（内网 Endpoint） | 同地域 ECS ↔ OSS，**免流量费** |
| 下载（外网 Endpoint） | 按**外网流出流量**计费，是主要开销；量大时考虑 CDN 或资源包 |
| 存储 | 标准存储适合频繁访问；长期不取可降到低频/归档（降冷后下载有**取回费用**，且有最低存储时长） |

结论：**客户端与 Bucket 同地域时，用内网 Endpoint 是最省的方式**。

## 八、故障排查

| 现象 | 原因与处理 |
| --- | --- |
| `未找到 ossutil` | 安装 ossutil，或用环境变量 `ALIYUN_OSS_OSSUTIL` 指定其绝对路径 |
| `凭证获取失败（ielym-certification）` / 提示未引导 | 该设备尚未完成一次性引导，按 ielym-certification skill 的说明执行引导 |
| `AccessDenied` / `SignatureDoesNotMatch` | 凭证内容有误或 RAM 权限不足；在 ielym-certification 侧核对或轮换凭证 |
| `NoSuchBucket` | Bucket 名写错，或 Endpoint 地域与 Bucket 地域不匹配 |
| `exists` 报错而非返回 false | 非 404 类错误（如权限/网络）同样返回 false，需看 `--json` 的 stderr 区分 |
| 内网 Endpoint 连不通 | 客户端不在同地域 VPC 内；改用外网 Endpoint |
| 签名 URL 在浏览器打不开 | URL 是用内网 Endpoint 生成的，仅 VPC 内可用；改用外网域名重新生成 |