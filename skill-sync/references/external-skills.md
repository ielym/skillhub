# 外部 skills（手动安装）

外部（社区 / 第三方）skill 由用户手动选择安装。本文记录每个外部 skill 的来源与安装方式，按需选用。

## 约定

- 安装位置：源仓库 `external_skills/<名字>/`（已被 `.gitignore` 排除，不进 git）。
- 目录内须包含 `SKILL.md`（或其子目录包含），安装后执行 `skill-sync link`，即可与自建 skill 一起软链接到所有 AI 工具。
- 更新：按各自来源手动重新下载 / `git pull` 替换；替换前注意保留目录里的 `.env` / `.env.*` 等本地密钥文件。
- 卸载：删除 `external_skills/<名字>` 目录后重新执行 `skill-sync link`（各工具侧的链接会显示为独立目录，可手动删除）。

## 已知外部 skill

### lark 官方 skills（larksuite/cli）

- 来源（git 仓库，`skills/` 目录）：https://github.com/larksuite/cli
- 本地已验证版本：main @ `72579c8`（仅供参考；以各 skill `SKILL.md` 的 `version` 为准）
- 本地共 24 个 `lark-*` skill（含 `lark-shared` 基础依赖）；仓库另有 4 个 0 KB 兼容 stub（`lark-minutes` / `lark-note` / `lark-vc` / `lark-vc-agent`，纯转发到 `lark-meeting`），不安装
- 依赖：`lark-cli` 二进制（`npx @larksuite/cli@latest install` 全局安装）+ 应用配置与登录（`lark-cli config init`、`lark-cli auth login --recommend`）
- 说明：飞书 / Lark 官方全功能套件——消息、云文档、云盘、多维表格、表格、幻灯片、日历、邮件、任务、会议、Wiki、审批、OKR、画板等
- 注意：skill 之间有相对引用（如 `../lark-shared/SKILL.md`），必须保持同层兄弟目录结构，不能单独挪动某个 lark skill

安装 / 更新（PowerShell 示例，在源仓库根目录执行）：

```powershell
# 1. sparse 克隆（只拉 skills/ 目录）
git clone --filter=blob:none --sparse --depth 1 https://github.com/larksuite/cli.git "$env:TEMP\lark-cli-repo"
git -C "$env:TEMP\lark-cli-repo" sparse-checkout set skills

# 2. 复制全部 lark-* skill（跳过 4 个兼容 stub；-Force 覆盖即为更新）
$skip = 'lark-minutes','lark-note','lark-vc','lark-vc-agent'
Get-ChildItem "$env:TEMP\lark-cli-repo\skills" -Directory |
  Where-Object { $skip -notcontains $_.Name } |
  ForEach-Object { Copy-Item $_.FullName "external_skills\$($_.Name)" -Recurse -Force }

# 3. 分发到各 AI 工具
skill-sync link
```

Unix（bash）示例：

```bash
git clone --filter=blob:none --sparse --depth 1 https://github.com/larksuite/cli.git /tmp/lark-cli-repo
git -C /tmp/lark-cli-repo sparse-checkout set skills
skip="lark-minutes lark-note lark-vc lark-vc-agent"
for d in /tmp/lark-cli-repo/skills/*/; do
  name=$(basename "$d")
  [[ " $skip " == *" $name "* ]] || cp -r "$d" "external_skills/$name"
done
skill-sync link
```

卸载单个 lark skill：删除对应 `external_skills/lark-<名字>` 目录后重新 `skill-sync link`；整组卸载同理（注意 `lark-shared` 被其他 lark skill 引用，整组卸载时一并删除）。
