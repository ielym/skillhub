---
name: ielym-certification
description: 统一权限凭证获取 CLI 的入口与路由。当用户需要获取某个服务的访问凭证或认证信息、列出已登记的凭证清单、或询问如何取用某类权限凭证时使用。命令形如 ielym-certification 后接 provider 名，provider 可扩展，各 provider 的用法见 references 目录下对应文档。
---

# ielym-certification（统一权限凭证获取 CLI）

按 **provider（权限提供方）** 维度取回各类服务的访问凭证。本 skill 只负责**路由**与**基础使用说明**，各权限的具体参数与示例见 `references/` 下对应文档。

## 基础用法

```
ielym-certification bootstrap        # 一次性引导（为凭证库准备信任根；细节见 provider 文档）
ielym-certification bootstrap --status   # 查看引导状态（不输出密钥）
ielym-certification providers        # 列出已支持的 provider
ielym-certification <provider> ...   # 调用某个 provider 取回凭证
```

`<provider>` 是第一个位置参数，由 CLI 自动发现，无需注册。

部分 provider 在取回凭证前需要**一次性引导（bootstrap）**：每台设备执行一次，为凭证读取准备信任根；引导方式因 provider 而异，统一入口是 `ielym-certification bootstrap`，具体前置条件见对应 provider 的参考文档。其他工具只调用本 CLI 取凭证，不感知引导过程。

通用参数（所有 provider 均可用）：

| 参数 | 说明 |
| --- | --- |
| `--json` | 输出 JSON 信封（含 provider、定位信息、`content`） |
| `--out <file>` | 把凭证内容写入文件，权限自动设为 `600` |
| `--list` | 列出该 provider 下已登记的资源名 |
| `-v, --version` | 打印版本 |

- 默认（不加 `--json` / `--out`）把凭证内容**直接写到 stdout**，可直接被程序解析。
- 退出码：`0` 成功；`1` 参数或环境错误；`2` 目标凭证不存在；`130` 用户中断。

## 权限路由

| provider | 说明 | 参考文档 |
| --- | --- | --- |
| `aliyun-oss` | 阿里云 OSS 访问凭证（按 Bucket 维度） | [references/aliyun-oss.md](references/aliyun-oss.md) |
| `api-key` | 第三方服务 API Key / Token（按服务名维度，如 artificial-analysis） | [references/api-key.md](references/api-key.md) |

新增 provider 时，在本表补一行，并在 `references/` 下补一份同名文档。

## 扩展新 provider

1. 在 CLI 的 `providers/` 包内新增一个 `BaseProvider` 子类：设置 `name` / `summary`，实现 `add_arguments()` 与 `fetch()`（需支持 `--list` 时再实现 `list_names()`）；
2. 注册表与入口**无需改动**，CLI 会自动发现；
3. 补一份 `references/<provider>.md`，并在上面的路由表登记。

## 注意事项

- 取回凭证默认**不在本地留存副本**（`--out` 落盘时自动设为 `600` 权限）；唯一的本地留存是 bootstrap 的引导配置，写在专属配置目录，目录 `0700`、文件 `0600`，不与其他工具共享。
- 取回的内容通常含明文密钥，**不要写进日志、不要提交进仓库**。
- 各 provider 的依赖与前置条件不同，见其对应的参考文档。