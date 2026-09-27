# skills 工作区

<br />

本仓库即 [ielym/skillhub](https://github.com/ielym/skillhub)；配套 CLI（`skill-sync` 命令）在 [ielym/clihub](https://github.com/ielym/clihub)。

## skills

| 目录            | 说明                               |
| ------------- | -------------------------------- |
| `skill-sync/` | 统一安装与多端同步入口（自建 skill + 外部 skill） |

## 两类来源

| <br /> | 自建               | 外部（社区 / 第三方）                                     |
| ------ | ---------------- | ------------------------------------------------ |
| 存放     | 本层目录下，随 git 走    | `external_skills/`，被 `.gitignore` 排除             |
| 声明     | 目录即声明            | 登记在 `skill-sync/references/external-skills.json` |
| 换机器    | `git clone` 一次到位 | `skill-sync ext install` 按清单复现                   |

## 换一台机器

```bash
git clone https://github.com/ielym/skillhub <本地目录>
cd <本地目录>
skill-sync ext install          # 按清单装外部 skills（需 clawdbot / skillhub CLI）
skill-sync link --dir <本地目录>
```

## 约定

- git 仓库、忽略规则、打包分发等在本层统一处理；各 skill 目录内不单独放 README 和 git 配置。
- 安装、多端同步统一由 `skill-sync/` 负责；其余 skill 只承担使用功能，一般不承担安装。
- 新增外部 skill：`skill-sync ext add <名字> --source clawdbot --id <作者/名字>`，再 `ext install`。

