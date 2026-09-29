# skills 工作区

<br />

本仓库即 [ielym/skillhub](https://github.com/ielym/skillhub)；配套 CLI（`skill-sync` 命令）在 [ielym/clihub](https://github.com/ielym/clihub)。

## skills

| 目录            | 说明                                       |
| ------------- | ---------------------------------------- |
| `skill-sync/` | 统一安装与多端同步入口（自建 skill + 手动安装的外部 skill）     |
| `lark-folder-manager/` | 飞书云盘目录管理与文档路由：基于目录管理 Base 路由文档、登记索引、管理文件夹 |

## 两类来源

| <br /> | 自建                | 外部（社区 / 第三方）                                        |
| ------ | ----------------- | ---------------------------------------------------- |
| 存放     | 本层目录下，随 git 走     | `external_skills/`，被 `.gitignore` 排除                  |
| 声明     | 目录即声明             | 手动安装（目录即声明）                                          |
| 换机器    | `git clone` 一次到位  | 按 [`skill-sync/references/external-skills.md`](./skill-sync/references/external-skills.md) 手动重装 |

## 换一台机器

```bash
npm i -g @ielym/skill-sync        # 装 CLI（全局命令，任一终端可用）
git clone https://github.com/ielym/skillhub <本地目录>
skill-sync init <本地目录>          # 记录源仓库位置
skill-sync link                  # 软连接自建 skill；外部 skill 按文档手动安装后一并 link
```

## 约定

- git 仓库、忽略规则、打包分发等在本层统一处理；各 skill 目录内不单独放 README 和 git 配置。
- 安装、多端同步统一由 `skill-sync/` 负责；其余 skill 只承担使用功能，一般不承担安装。
- 外部 skill 手动安装：来源与安装方法记录在 [`skill-sync/references/external-skills.md`](./skill-sync/references/external-skills.md)，按需选用。

