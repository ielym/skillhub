# aliyun-oss provider 参考

阿里云 OSS 访问凭证，按 Bucket 维度取回。

> 本文档不含任何具体业务凭证；`<bucket>` 等均为占位符，引导文档地址为固定的管理入口。

## 为什么需要引导（bootstrap）

凭证集中存放在 OSS，但读取 OSS 本身又需要一组凭证，构成引导死循环。本 provider 的解法是引入**独立信任根——飞书登录态**（与阿里云 OSS 是两套权限体系）：

```text
飞书扫码登录（每台设备一次，lark-cli）
  → 读取飞书引导文档中的 AccessKey
  → 落盘为本工具专属配置（0700/0600）
  → 凭该配置从 OSS 凭证库取回各 Bucket 凭证
```

引导过程只存在于 ielym-certification 内部；其他 CLI/skill 只调用本工具取凭证，不需要安装 lark-cli、也不感知飞书。

## 前置条件

1. **ossutil**：读取 OSS 对象的底层工具。
   - 安装与升级见官方文档 https://help.aliyun.com/zh/oss/install-ossutil2
   - 验证：`ossutil version`；升级：`ossutil update`（`-f` 免交互）
   - 不在 PATH 中时，用环境变量 `ALIYUN_OSS_OSSUTIL` 指定其路径
2. **lark-cli 并完成飞书登录**（仅引导时需要）：
   - 安装 lark-cli 后执行登录，按提示扫码授权（飞书账号需有引导文档的访问权限）
   - lark-cli 不在 PATH 时，用环境变量 `IELYM_CERT_LARK_CLI` 指定其路径

## 引导（每台设备一次）

```bash
ielym-certification bootstrap          # 拉取引导凭证并落盘
ielym-certification bootstrap --status # 查看状态（只显示掩码 AK，不输出 Secret）
ielym-certification bootstrap --force  # 重新拉取并覆盖（AK 轮换后使用）
```

- 引导文档（飞书 AIManager 目录）：<https://my.feishu.cn/docx/EQLFdZ1GWo9ttmxF1bhcQDhmnRg>
- 落盘位置：`~/.config/ielym-certification/`（`$XDG_CONFIG_HOME` 可改根目录），目录 `0700`，其中 `bootstrap.json` 与 `ossutil.config` 均为 `0600`
- 可用环境变量 `IELYM_CERT_FEISHU_DOC` 覆盖引导文档地址

引导完成后即可取回凭证，无需配置 ossutil、无需手工粘贴 AK：

```bash
ielym-certification aliyun-oss                 # 默认取回凭证库所在 Bucket 的凭证
ielym-certification aliyun-oss --bucket <bucket>
```

## OSS 凭证存放约定

```
oss://<store-bucket>/certification/aliyun-oss/<name>/<name>.json
```

- `<name>` 即 `--bucket` 指定的 Bucket 名；省略 `--bucket` 时默认取引导凭证所在的 Bucket；
- `<store-bucket>` 缺省与 `<name>` 相同，可用 `--store-bucket` 指向集中存放的 Bucket；
- 也可用 `--key` 直接指定完整对象 key，绕过模板。

## 参数

| 参数 | 说明 |
| --- | --- |
| `--bucket <name>` | 要获取凭证的 Bucket 名；省略时用引导凭证所在 Bucket |
| `--store-bucket <name>` | 凭证文件所在的 Bucket；缺省与 `--bucket` 相同 |
| `--key <object-key>` | 直接指定凭证对象 key，覆盖默认模板 |
| `-e, --endpoint` | 覆盖 OSS 访问域名（默认用引导凭证中的内网域名） |
| `--region` | 覆盖地域 ID（默认用引导凭证中的地域） |

## 环境变量

| 变量 | 作用 |
| --- | --- |
| `IELYM_CERT_FEISHU_DOC` | 覆盖飞书引导文档地址 |
| `IELYM_CERT_LARK_CLI` | lark-cli 可执行文件路径（PATH 中没有时使用） |
| `IELYM_CERT_BUCKET` | `--bucket` 的缺省值 |
| `IELYM_CERT_STORE_BUCKET` | `--store-bucket` 的缺省值 |
| `ALIYUN_OSS_OSSUTIL` | ossutil 可执行文件路径（PATH 中没有时使用） |
| `XDG_CONFIG_HOME` | 引导配置的根目录（默认 `~/.config`） |

## 用法示例

```bash
# 取回某 Bucket 的凭证（默认直接输出内容）
ielym-certification aliyun-oss --bucket <bucket>

# 带定位信息的 JSON 信封
ielym-certification aliyun-oss --bucket <bucket> --json

# 落盘（自动 600 权限）
ielym-certification aliyun-oss --bucket <bucket> --out <file>

# 列出已登记的凭证
ielym-certification aliyun-oss --list

# 凭证集中存放在另一个 Bucket
ielym-certification aliyun-oss --bucket <bucket> --store-bucket <store-bucket>

# 自定义对象 key
ielym-certification aliyun-oss --bucket <bucket> --key <object-key>
```

## 输出格式

默认输出即凭证文件的**原始文本**，可直接被 `jq` 或程序解析。

`--json` 信封（下列为 aliyun-oss 特有的定位字段）：

```json
{
  "cli": "ielym-certification",
  "provider": "aliyun-oss",
  "command": "get",
  "ok": true,
  "bucket": "<bucket>",
  "store_bucket": "<store-bucket>",
  "key": "certification/aliyun-oss/<bucket>/<bucket>.json",
  "oss_path": "oss://<store-bucket>/certification/aliyun-oss/<bucket>/<bucket>.json",
  "content": "..."
}
```

`--list --json`：

```json
{
  "cli": "ielym-certification",
  "provider": "aliyun-oss",
  "command": "list",
  "ok": true,
  "count": 1,
  "names": ["<bucket>"]
}
```

## 常用组合

```bash
# 取出某个字段
ielym-certification aliyun-oss --bucket <bucket> | jq -r '.access_key_id'

# 脚本判断凭证是否可用
if ielym-certification aliyun-oss --bucket <bucket> >/dev/null 2>&1; then
  echo "凭证可用"
else
  echo "凭证缺失或不可读"
fi
```

## 故障排查

| 现象 | 原因与处理 |
| --- | --- |
| `未找到 ossutil` | 安装 ossutil，或用 `ALIYUN_OSS_OSSUTIL` 指定其路径 |
| `未找到 lark-cli` | 引导依赖 lark-cli；安装后重新登录，或用 `IELYM_CERT_LARK_CLI` 指定路径 |
| `读取飞书引导文档失败` | lark-cli 登录态过期或无文档权限；重新扫码登录后执行 `bootstrap --force` |
| `引导文档中未找到凭证 JSON` | 文档内容被改动；恢复其中的 JSON 代码块后重新引导 |
| `尚未引导` | 该设备首次使用，先执行 `ielym-certification bootstrap` |
| `凭证不存在`（退出 2） | 对象 key 不对，或该 Bucket 尚未登记凭证 |
| `AccessDenied` / `SignatureDoesNotMatch` | 引导凭证权限不足或已轮换；确认文档为最新后 `bootstrap --force` |
| 内网 Endpoint 连不通 | 运行环境不在同地域 VPC 内，用 `-e` 指定外网 Endpoint |
