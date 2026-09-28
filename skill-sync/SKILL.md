---
name: skill-sync
description: 用 skill-sync 命令统一安装与同步本机所有 AI 工具的 skills，管理自建 skill 与外部 skill（按 external-skills.json 清单从 git/url 安装到 external_skills 并软连接）。当用户要安装/更新/推送 skill、查看链接状态、建立或解除链接、一键同步所有 skill 到最新时使用。
version: 1.0.0
---

# skill-sync（统一安装与多端同步）

本 skill 是本机所有 AI 工具 skill 安装与同步的唯一入口；其余 skill 只承担使用功能，一般不承担安装。

配套 CLI（`skill-sync` 命令）源码在 [ielym/clihub](https://github.com/ielym/clihub)。

## 职责边界

- 只有本 skill 负责「安装 / 同步」，其它 skill 一律只描述「怎么用」。
- SKILL 与 CLI 是两个独立产物，**各自独立安装、独立更新**：更新 CLI 不会动本 SKILL，更新本 SKILL 也不会动 CLI。

## 安装 / 更新 / 卸载 CLI

> **CLI 尚未发布到 npm registry**（`npm i -g @ielym/skill-sync` 会 404），只能从源码目录全局安装。

```bash
git clone https://github.com/ielym/clihub.git <cli 源码目录>   # 首次；已有则跳过
cd <cli 源码目录> && npm i -g .          # 全局安装，得到 skill-sync 命令

# 更新 CLI（与更新本 SKILL 无关）
cd <cli 源码目录> && git pull && npm i -g .

npm uninstall -g @ielym/skill-sync   # 卸载
```

> npm 全局命令在你的 PATH 里，任一终端都能直接跑 `skill-sync`；不同 AI 工具无需任何额外配置，按命令名调用即可。
> 本机实际安装位置：`D:\projects\cli_packages\skill-sync`（源码 + `npm i -g .`），改源码后重跑 `npm i -g .` 即生效。

## 源仓库（Skill 原始目录）位置

所有 AI 工具都只通过软连接（Windows junction / Unix symlink）指向源仓库，**不在工具目录放副本**——改一处，处处生效。

按序取第一个可用：

1. `--dir <path>` 显式指定（临时覆盖）
2. 环境变量 `SKILLS_HUB`
3. `~/.skill-sync.json` 里的 `hub` 字段（`init` / `link` 时自动写入）

```bash
skill-sync init <源仓库目录>   # 记录一次，之后所有命令默认用它
skill-sync link --dir <目录>   # 或临时指定
```

未配置且未用 `--dir` 时，命令会报错并提示 `init`，不会闷头用错目录。

## 两类 skill

| <br /> | 自建               | 外部（社区 / 第三方）                          |
| ------ | ---------------- | ------------------------------------- |
| 存放     | 仓库根目录（本层直接子目录）   | `external_skills/`（gitignore，不进 git）  |
| 声明     | 目录即声明            | 登记在 `references/external-skills.json` |
| 更新     | `git pull` / `git push` | 按来源 `git pull` 或重新下载替换            |

## 命令

### 源仓库

| 命令                        | 用途                                  |
| ------------------------- | ----------------------------------- |
| `skill-sync init <目录>`     | 记录源仓库路径（写入 `~/.skill-sync.json`）   |
| `skill-sync status`       | 查看各 AI 工具的自建 + 外部 skill 链接状态      |
| `skill-sync link [--force]` | 把自建 skill 与 `external_skills/` 软连接到所有已安装工具 |
| `skill-sync unlink <tool>` | 解除某工具的链接（只删链接，不动源）                  |

### 同步 / 推送

| 命令                      | 用途                                            |
| ----------------------- | --------------------------------------------- |
| `skill-sync update [--force]` | **一键同步**：`git pull` 自建 + 更新外部 skill + 重新链接所有工具。命令外最推荐用这个 |
| `skill-sync pull`       | 仅拉取自建 skill（`git pull --rebase --autostash`）   |
| `skill-sync push ["说明"]` | 提交并推送自建 skill（`git add -A && commit && push`）  |
| `skill-sync install <名字> --source git|url --url <地址>` | 登记并安装一个外部 skill（等价于 ext add + ext install + link） |

### 外部 skill

| 命令                                               | 用途                                          |
| ------------------------------------------------ | ------------------------------------------- |
| `skill-sync ext list`                            | 查看清单与安装状态                                   |
| `skill-sync ext add <名字> --source git|url --url <地址> [--version v]` | 登记一个外部 skill                                |
| `skill-sync ext install [名字]`                    | 安装到 `external_skills/<名字>`；已装则更新；装完自动 link |

## 外部 skill 清单

清单文件：[`references/external-skills.json`](./references/external-skills.json)。每条字段：

- 必填 `name`（目录名）、`source`（来源类型）、`url`。
- `source` 支持两种，都是 CLI 直连、不依赖任何其它 CLI：
  - `git`：`clone <url>` 首次安装，已装则 `git pull` 更新。
  - `url`：下载一个 zip/tar 到临时目录解压后替换；更新即重新下载替换，并自动保留旧目录里的 `.env` / `.env.*` 密钥文件。
- `version` / `note` 为可选说明，`git` 来源安装后可用 `version` 指定 checkout。

用 `skill-sync ext add …`（或 `install`）登记，也可直接编辑 JSON。

## 安装外部 skill 流程

1. 登记：`skill-sync ext add feishu-docs --source url --url https://…/download?slug=feishu-docs`
2. 安装：`skill-sync ext install` → 落到 `external_skills/<名字>`（已装则更新）
3. 分发：自动执行 `link` → 软连接到各 AI 工具

## 支持的 AI 工具及 skills 目录

| 工具          | skills 目录                      |
| ----------- | ------------------------------ |
| WorkBuddy   | `~/.workbuddy/skills`          |
| Claude Code | `~/.claude/skills`             |
| Cursor      | `~/.cursor/skills`             |
| Windsurf    | `~/.codeium/windsurf/skills`   |
| Codex       | `~/.codex/skills`              |
| Gemini CLI  | `~/.gemini/skills`             |
| Antigravity | `~/.gemini/antigravity/skills` |
| QoderWork   | `~/.qoderwork/skills`          |

父目录存在才认为该工具已安装，不会给没装的工具建空目录。

## 注意

- `external_skills/` 与其下外部 skill 的 `.env` 等敏感文件已 gitignore，不进 git；换机器靠 `ext install` 复现。
- `url` 来源更新是「整体替换」，已内置保留 `.env` / `.env.*`，其余本地改动会被覆盖。
- `link` 遇非空目标目录默认跳过；`--force` 先备份成 `<目标>.bak-<时间戳>`。
- `unlink` 只删链接本身，源文件不受影响。
- 外部 skill 带 `node_modules` 时只提交源码，新机器进入目录自行 `npm install`。
- 记不准的参数先查 `--help`，不猜。