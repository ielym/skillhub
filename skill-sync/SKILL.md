---
name: skill-sync
description: 用 skill-sync 命令统一安装与同步本机所有 AI 工具的 skills，基于自有 git 仓库管理自建 skill，并把手动安装到 external_skills/ 的外部 skill 一并软连接。当用户要安装/更新/推送 skill、查看链接状态、建立或解除链接、一键同步所有 skill 到最新时使用。
version: 1.0.0
---

# skill-sync（统一安装与多端同步）

本 skill 是本机所有 AI 工具 skill 安装与同步的唯一入口；其余 skill 只承担使用功能，一般不承担安装。

配套 CLI（`skill-sync` 命令）源码在 [ielym/clihub](https://github.com/ielym/clihub)。

## 职责边界

- 只有本 skill 负责「安装 / 同步」，其它 skill 一律只描述「怎么用」。
- SKILL 与 CLI 是两个独立产物，**各自独立安装、独立更新**：更新 CLI 不会动本 SKILL，更新本 SKILL 也不会动 CLI。

## 修改 skill 的红线

> 所有 AI 工具都是通过软连接指向源仓库使用 skills 的，一处改动会影响全部工具。因此 **除非用户主动要求，否则禁止任何 AI 工具自行新增、修改或删除任何 skill（含本 skill 与 `external_skills/` 下内容）**。需要改动时，必须先由用户明确开口，再动手。

## 安装 / 更新 / 卸载 CLI

> **CLI 尚未发布到 npm registry**（`npm i -g @ielym/skill-sync` 会 404），只能从源码目录全局安装。

```bash
git clone https://github.com/ielym/clihub.git <cli 源码目录>   # 首次；已有则跳过
cd <cli 源码目录> && npm i -g .          # 全局安装，得到 skill-sync 命令

# 更新 CLI（与更新本 SKILL 无关）
cd <cli 源码目录> && git pull && npm i -g .

npm uninstall -g @ielym/skill-sync   # 卸载
```

> npm 全局命令在 PATH 里，任一终端都能直接跑 `skill-sync`；不同 AI 工具无需任何额外配置，按命令名调用即可。
> 源码目录位置自己定；改源码后重跑 `npm i -g .` 即生效。

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

| <br /> | 自建                      | 外部（社区 / 第三方）                                        |
| ------ | ----------------------- | ------------------------------------------------------ |
| 存放     | 仓库根目录（本层直接子目录）          | `external_skills/`（gitignore，不进 git）                      |
| 声明     | 目录即声明                   | 手动安装（目录即声明）                                              |
| 安装/更新  | `git pull` / `git push` | 手动下载 / `git pull`，见 [`references/external-skills.md`](./references/external-skills.md) |
| 分发     | `link` 软连接到各 AI 工具      | 同左（安装后与自建 skill 一起 link）                                 |

> 外部 skill 手动安装；[`references/external-skills.md`](./references/external-skills.md) 记录了已知外部 skill 的来源与安装方法，按需选用。

## 命令

### 源仓库

| 命令                          | 用途                                         |
| --------------------------- | ------------------------------------------ |
| `skill-sync init <目录>`      | 记录源仓库路径（写入 `~/.skill-sync.json`）           |
| `skill-sync status`         | 查看各 AI 工具的 skill（自建 + 外部）链接状态               |
| `skill-sync link [--force]` | 把自建 skill 与 `external_skills/` 下的外部 skill 软连接到所有已安装工具 |
| `skill-sync unlink <tool>`  | 解除某工具的链接（只删链接，不动源）                         |

### 同步 / 推送

| 命令                          | 用途                                          |
| --------------------------- | ------------------------------------------- |
| `skill-sync update [--force]` | **一键同步**：`git pull` 自建 skill + 重新链接所有工具。命令外最推荐用这个 |
| `skill-sync pull`           | 仅拉取自建 skill（`git pull --rebase --autostash`） |
| `skill-sync push ["说明"]`    | 提交并推送自建 skill（`git add -A && commit && push`）  |

## 外部 skill（手动安装）

流程：

1. 查 [`references/external-skills.md`](./references/external-skills.md) 选一个，按其中的说明手动安装（下载解压 / `git clone`）到 `external_skills/<名字>`
2. 分发：`skill-sync link` → 软连接到各 AI 工具
3. 更新 / 卸载：手动重新下载替换 / 删除目录，再重新 `link`

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
| Trae        | `~/.trae-cn/skills`            |
| DeepSeek Harness | `~/.dsh/skills`（Windows 为 `%USERPROFILE%\.dsh\skills`） |

父目录存在才认为该工具已安装，不会给没装的工具建空目录。

## 注意

- `external_skills/` 与其下外部 skill 的 `.env` 等敏感文件已 gitignore，不进 git；换机器按 [`references/external-skills.md`](./references/external-skills.md) 手动重装。
- `link` 遇非空目标目录默认跳过；`--force` 先备份成 `<目标>.bak-<时间戳>`。
- `unlink` 只删链接本身，源文件不受影响。
- 记不准的参数先查 `--help`，不猜。

