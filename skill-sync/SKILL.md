---
name: skill-sync
description: 用 skill-sync 命令统一安装与同步本机所有 AI 工具的 skills，管理自建 skill 与外部 skill（按 external-skills.json 清单安装到 external_skills 并软连接）。当用户要查看链接状态、建立或解除链接、安装外部 skill、拉取或推送 skill 源仓库时使用。
version: 1.0.0
---

# skill-sync（统一安装与多端同步入口）

本 skill 是本机所有 AI 工具 skill 安装与同步的唯一入口；其余 skill 只承担使用功能，一般不承担安装。

配套 CLI（`skill-sync` 命令）源码在 [ielym/clihub](https://github.com/ielym/clihub)。

## 职责边界

- 只有本 skill 负责「安装 / 同步」，其它 skill 一律只描述「怎么用」。
- skill 分两类来源，存放与声明方式不同。

## 两类 skill

| <br /> | 自建               | 外部（社区 / 第三方）                          |
| ------ | ---------------- | ------------------------------------- |
| 存放     | 仓库根目录（本层直接子目录）   | `external_skills/`（gitignore，不进 git）  |
| 声明     | 目录即声明            | 登记在 `references/external-skills.json` |
| 换机器    | `git clone` 一次到位 | `skill-sync ext install` 按清单复现        |

## 外部 skill 清单

清单文件：[`references/external-skills.json`](./references/external-skills.json)。每条字段：

- 必填 `name`（目录名）、`source`（来源类型）；`id` / `url` / `version` / `note` 按来源取用。
- `source` 支持 `clawdbot` / `skillhub` / `git`。clawdbot 与 skillhub 用 `install <id> --dir …` 装；git 用 `clone <url>` 装。

用 `skill-sync ext add …` 登记，或直接编辑 JSON。

## 命令

### 链接与同步

| 命令                          | 用途                                         |
| --------------------------- | ------------------------------------------ |
| `skill-sync status`         | 查看各 AI 工具的自建 + 外部 skill 链接状态               |
| `skill-sync link [--force]` | 把自建 skill 与 `external_skills/` 软连接到所有已安装工具 |
| `skill-sync unlink <tool>`  | 解除某工具的链接（只删链接，不动源）                         |
| `skill-sync install <名字>`   | 用 `skillhub` 把技能装到源仓库（自动补 `--dir`）         |
| `skill-sync pull`           | 拉取远端最新（`git pull --rebase --autostash`）    |
| `skill-sync push ["说明"]`    | 提交并推送（`git add -A && commit && push`）      |

### 外部 skill

| 命令                                            | 用途                                     |
| --------------------------------------------- | -------------------------------------- |
| `skill-sync ext list`                         | 查看清单与安装状态                              |
| `skill-sync ext add <名字> [--source <类型>] ...` | 登记一个外部 skill（参数按来源，见下）                 |
| `skill-sync ext install [名字]`                 | 按清单安装到 `external_skills/<名字>`（省略名字则全部） |

`ext add` 参数按 `--source` 区分：

- `--source clawdbot --id <作者/名字> [--version v]`
- `--source skillhub [--version v] [--note 说明]`
- `--source git --url <仓库地址> [--version v]`

## 安装外部 skill 流程

1. 登记：`skill-sync ext add feishu-docs --source clawdbot --id stevenlikewatermelon/feishu-docs --version 1.1.1`
2. 安装：`skill-sync ext install [名字]` → 落到 `external_skills/<名字>`
3. 分发：`skill-sync link` → `external_skills/<名字>` 软连接到各 AI 工具

## 源仓库解析优先级

按序取第一个可用：

1. `--dir <path>` 显式指定
2. 环境变量 `SKILLS_HUB`
3. `~/.skill-sync.json` 里的 `hub` 字段（`link` 时自动写入）
4. 默认 `~/.workbuddy/skills`

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

## 注意

- `external_skills/` 与其下外部 skill 的 `.env` 等敏感文件已 gitignore，不进 git；换机器靠 `ext install` 复现。
- `link` 遇非空目标目录默认跳过；`--force` 先备份成 `<目标>.bak-<时间戳>`。
- `unlink` 只删链接本身，源文件不受影响。
- 外部 skill 带 `node_modules` 时只提交源码，新机器进入目录自行 `npm install`。
- 记不准的参数先查 `--help`，不猜。

