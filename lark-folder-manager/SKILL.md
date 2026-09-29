---
name: lark-folder-manager
description: 飞书云盘目录管理与文档路由。任何"把内容生成/保存/导出/上传到飞书"的请求（docx/sheet/slides/bitable/mindnote/whiteboard，含本地 md/docx 导入）在写入前必须先经本 skill 路由到具体目录——严禁落在云盘根目录、严禁使用 --parent-position my_library。也用于列/建/移动/重命名/删除目录、给已有文档归档、在内容索引表登记。目录定义与收纳规则全部从目录管理 Base 运行时读取，不硬编码。
---

# lark-folder-manager

飞书云盘目录管理与文档路由 skill。**所有目录定义、收纳规则、表结构均从目录管理 Base 动态读取，skill 不硬编码任何具体目录或表 ID。**

## When to Use（强制触发条件，先于任何写入动作）

**只要本轮会在云盘上产生一个新对象，就必须在执行前加载本 skill 并完成路由。判断依据不是"用户有没有提文件夹"，而是"会不会落盘"。** 以下任一命中即触发：

1. 用户说"保存/导出/同步/上传到飞书"、"做成飞书文档"、"记到飞书里" 等**任何落盘意图**。
2. 准备执行**创建/导入类**命令：`docs +create`、`drive files upload`/`import`、`sheets +create`、`slides +create`、`base +create`，或本地 md/docx/xlsx → 飞书的转换导入。
3. 命令里出现 `--parent-position`，或**缺失 `--parent-token`**（两者都等价于写根目录，违规）。
4. 用户要求整理/归档/移动已有文档，或问"这个文档该放哪"。
5. 明确的目录增删改查与索引登记。

> **为什么写这么死**：这类请求的字面是"创建文档"，天然会被判给 `lark-doc` / `lark-drive` 从而绕过路由，结果文档落在根目录。
> **本 skill 与 lark-doc / lark-drive / lark-sheets 是串联关系，不是二选一：路由在前，创建在后。**

## 硬性约束（STOP 门）

0. **创建命令执行前必须能答出三件事**：目标目录是哪个？它的 `folder_token` 是多少？内容索引表是哪张？三者缺一，不得执行。
1. **禁止在云盘根目录创建任何文档**——所有文档必须放入具体目录；归属不确定的一律放兜底目录（从目录定义表的收纳规则中识别，通常名为 TEMP）。
   - **等价禁止项**：不得使用 `--parent-position my_library`（= 我的空间根目录），不得省略 `--parent-token`。这两种写法都等价于写根目录。
   - **唯一正确写法**：`--parent-token <目标目录 folder_token>`，token 从目录定义表「目录链接」字段取（形如 `/drive/folder/<token>`）。
2. 任何文档操作（创建/移动/修改）前，必须先读取目录定义表确定目标目录；操作完成后必须在对应内容索引表登记。
3. 内容索引表的表名**必须与对应的云盘一级目录名完全一致**——表名和对应关系从目录定义表的「内容索引表」字段读取，不写死。

## 入口：目录管理 Base

Base token 是 skill 唯一需要的常量，其余全部运行时读取：

- Base token：`KlZobKh0MaWyaNsSsmdcoG7CnIc`
- 默认打开目录定义表：<https://my.feishu.cn/base/KlZobKh0MaWyaNsSsmdcoG7CnIc?table=tblFGopMYHt6rdIg>

## 运行时初始化（每次执行前）

1. 列出 Base 所有表（`base +base-block-list`），拿到表名→table_id 映射。
   **纯路由场景可跳过本步**：目录定义表默认 table_id 为 `tblFGopMYHt6rdIg`，直接读它即可；只有在需要内容索引表的 table_id 时才必须列全表。降这一步的成本 = 降低绕过的概率。
2. 读取目录定义表全部记录，得到：
   - 所有目录的完整路径、层级、收纳规则、目录链接
   - 每个目录对应的内容索引表名（从「内容索引表」字段）
   - 哪些内容索引表存在（与 Base 表名交叉验证）
3. 确定兜底目录：收纳规则中含"兜底/临时/待分类/不确定"关键词的目录。

## 目录定义表字段（从 Base 读取，不写死）

| 字段 | 作用 |
|---|---|
| 目录名称 | 从云空间根起的完整路径，`/` 分隔（如 `NOTES/AIGC/arxiv`），路由匹配主键 |
| 目录层级 | 一级/二级/三级/四级及以上 |
| 父目录路径 | 上一级目录完整路径，一级目录留空 |
| 目录链接 | 云盘文件夹直达链接 |
| 收纳规则 | 用途+关键词+正反例三合一，裁决边界不清的情况 |
| 内容索引表 | 该目录文档登记到哪张内容索引表（表名=一级目录名） |
| 状态 | 启用/停用，只有启用目录参与路由 |

## 内容索引表字段（每张内容索引表同构，字段从 Base 读取）

| 字段 | 类型 | 作用 |
|---|---|---|
| 文档名称 | text | 与云盘文档标题一致 |
| 文档链接 | text(url) | 文档直达链接；token 为 URL 最后一段（如 `/docx/<token>`） |
| 文档类型 | select | 飞书文档 / 电子表格 / 多维表格 / 幻灯片 / 思维笔记 / 文件 / 其他（见类型映射表） |
| 所在目录 | text | 一级目录内的相对路径（如 `AIGC/arxiv`）；根目录直存填 `（根目录）` |
| 创建日期 | datetime | 云盘元数据中的创建时间（`yyyy-MM-dd HH:mm`） |
| 最近修改日期 | datetime | 云盘元数据中的最近修改时间（`yyyy-MM-dd HH:mm`） |
| 登记说明 | text | `YYYY-MM-DD 操作描述`，多条以分号分隔 |
| 内容摘要 | text | 文档内容简要说明，初始登记可为空 |
| 登记时间 | created_at | 系统自动生成，**不要写入** |

> **类型映射（drive type → 索引表选项）**：`docx`/`doc`→飞书文档、`sheet`→电子表格、`bitable`→多维表格、`slides`→幻灯片、`mindnote`→思维笔记、`file`→文件、`whiteboard`/`shortcut`/其他→其他。

## 路由流程（创建/移动文档前）

1. 读取目录定义表中**状态=启用**的全部记录。
2. 将文档主题（标题/描述）与各记录的「收纳规则」匹配，得到候选集。
3. 候选含多个层级时，**取层级最深的目录**（最具体优先）。
4. 同层多候选冲突时，以「收纳规则」正反例裁决。
5. 仍无法裁决或零命中 → 兜底目录。
6. 依「目录链接」执行云盘操作，依「内容索引表」完成事后登记。

## 登记流程（操作完成后）

在目标目录对应的「内容索引表」中新增或更新记录：

- 文档名称、文档链接、文档类型、所在目录、创建日期、最近修改日期
- 登记说明：`YYYY-MM-DD 操作描述`，多条以分号分隔
- 移动文档时更新原记录，不重复建档

## 全量对账（手动触发）

> **为什么需要**：内容索引表是云盘目录的影子副本。当文档在飞书 UI 中被直接重命名、移动、删除（未走本 skill）时，索引表会与云盘真实状态不一致。全量对账通过扫描云盘真实文件清单与索引表逐条比对，自动修正差异。
>
> **当前工具链限制**：`lark-cli event consume` 不支持 drive 域事件（`unknown domain: drive`），无法实时推送文件变更，因此对账只能由用户手动触发。

### 触发时机

用户明确要求执行以下操作之一时触发本流程：
- "全量对账"、"同步索引"、"检查文档变更"、"盘点索引"、"校准索引表"
- 怀疑索引表与云盘不一致，要求校准

### 核心约束

1. **匹配主键是 token，不是文档名称**。重命名后 name 会变，token 不变。从「文档链接」URL 的最后一段提取 token（形如 `https://my.feishu.cn/docx/<token>`，token 即最后一段）。
   - wiki 链接（`/wiki/<token>`）需先用 `drive +inspect --url` 解包到底层资源 token。
2. **只对账「目录层级=一级」且「状态=启用」的目录**。每个一级目录对应一张内容索引表（表名=目录名）。
3. **文件夹本身不进内容索引表**，只登记文件和在线文档（docx/sheet/bitable/slides/mindnote/whiteboard/file）。

### 对账流程

1. **读取目录定义表**，筛选「目录层级=一级」且「状态=启用」的记录，得到 `[(目录名, folder_token, 内容索引表名), ...]`。
2. **列 Base 全表**（`base +base-block-list`），建立「内容索引表名 → table_id」映射。
3. **对每个一级目录**：
   a. 从 folder_token 开始递归 `drive files list`，收集所有非 folder 子项，构建真实清单：
      `{token → {name, type, url, created_time, modified_time, rel_path}}`
      - `rel_path` = 该文件在一级目录内的相对路径（如 `AIGC/arxiv`）；直接在一级目录下填 `（根目录）`。
   b. 读取对应内容索引表全部记录，从每条记录的「文档链接」提取 token，构建：
      `{token → {record_id, 文档名称, 文档类型, 所在目录, 创建日期, 最近修改日期, 登记说明}}`
   c. 按 token 做 diff（见下方判定矩阵）。
4. **处理跨一级目录移动**：若某 token 在 A 目录的云盘清单中消失、在 B 目录中出现 → 从 A 的索引表删除该记录，在 B 的索引表新增。
5. **输出 diff 摘要**（各变更类型数量与示例），经用户确认后批量写回。

### 变更判定矩阵

| 云盘 | 索引表 | 判定 | 动作 |
|---|---|---|---|
| 有 | 无 | 新建未登记 | 在索引表新增完整记录 |
| 无 | 有 | 云盘已删除 | 默认保留记录，在「登记说明」追加 `YYYY-MM-DD 云盘已删除`；物理删除需用户单独确认 |
| 有 | 有，name 不同 | 重命名 | 更新「文档名称」，「登记说明」追加 `YYYY-MM-DD 重命名为 <新名称>` |
| 有 | 有，rel_path 不同 | 移动 | 更新「所在目录」，「登记说明」追加 `YYYY-MM-DD 移动至 <新路径>` |
| 有 | 有，modified_time 不同 | 内容修改 | 更新「最近修改日期」 |
| 有 | 有，type 不同 | 类型变更 | 更新「文档类型」，「登记说明」追加 `YYYY-MM-DD 类型变更为 <新类型>` |
| 有 | 有，全部一致 | 无变化 | 跳过 |

### 写回规则

- **新增记录**：填入 文档名称、文档链接、文档类型（按类型映射）、所在目录（rel_path）、创建日期、最近修改日期、登记说明 = `YYYY-MM-DD 对账补登`。内容摘要留空。
- **更新记录**：只更新变更字段；「登记说明」在原值后以分号追加新条目（如 `原说明; 2026-09-29 重命名为 xxx`）。
- **删除记录**：默认不物理删除，仅在「登记说明」追加删除标记；用户明确要求清理时再 `base +record-delete`。
- **批量写**：优先用 `record-batch-create` / `record-batch-update`，单次 ≤200 条；写 API 间隔 2–3 秒。

### 安全门（必须遵守）

1. **写回前必须输出 diff 摘要**（各变更类型的数量与示例），经用户确认后才执行写入。
2. **物理删除索引记录**必须单独确认，不得与更新混批。
3. **token 无法从「文档链接」提取的记录**（链接为空或格式异常），不做自动处理，列入"待人工确认"清单返回给用户。
4. 对账过程中若发现某一级目录在云盘不存在（folder_token 失效），跳过该目录并报告。

### 常用命令

```bash
# 1. 列 Base 全表（获取内容索引表名→table_id 映射）
lark-cli base +base-block-list --base-token KlZobKh0MaWyaNsSsmdcoG7CnIc --as user

# 2. 读目录定义表（取一级目录的 folder_token 与内容索引表）
lark-cli base +record-list --base-token KlZobKh0MaWyaNsSsmdcoG7CnIc --table-id tblFGopMYHt6rdIg --as user

# 3. 递归列出某一级目录全部文件（从 folder_token 开始，遇到 type=folder 继续递归）
lark-cli drive files list --params '{"folder_token":"<folder_token>","page_size":200}' --format json

# 4. 读内容索引表全部记录
lark-cli base +record-list --base-token KlZobKh0MaWyaNsSsmdcoG7CnIc --table-id <content_table_id> --page-size 200 --as user

# 5. 批量新增记录
lark-cli base +record-batch-create --base-token KlZobKh0MaWyaNsSsmdcoG7CnIc --table-id <content_table_id> --json @payload.json --as user

# 6. 批量更新记录
lark-cli base +record-batch-update --base-token KlZobKh0MaWyaNsSsmdcoG7CnIc --table-id <content_table_id> --json @payload.json --as user

# 7. 批量删除记录（需用户单独确认；--record-id 可重复传多个）
lark-cli base +record-delete --base-token KlZobKh0MaWyaNsSsmdcoG7CnIc --table-id <content_table_id> --record-id <id1> --record-id <id2> --yes --as user
```

## 知识库（wiki）挂载同样需要路由

本 skill 目录体系覆盖云盘；若目标是把文档挂进**知识库**，"先裁决、再挂载"同样适用，而且更容易漏（典型事故：文档从云盘根目录被救出来后，又被挂到知识空间的根节点）。

- `wiki +move`（云盘文档移入知识库）、`wiki +node-create`、`docs +create --parent-token <wiki 节点 token>` 都会在 wiki 产生新对象 → 触发路由。
- **禁止挂在知识空间根节点**（`parent_node_token` 为空 = 根节点，等价于根目录）。挂载前必须先确定目标父节点。
- 事后同样在内容索引表登记，「所在目录」写明空间与层级路径。

## 反例 vs 正例（最容易犯的错就在这里）

❌ **错误**：先把文档建出来，再补一句"需要的话可以移到指定文件夹"。

```bash
lark-cli docs +create --as user --doc-format markdown --title "..." --content "@./x.md" --parent-position my_library
```

已经落在根目录。事后移动只是在补救，且索引登记第一次一定会漏。

✅ **正确**：先读目录定义表裁决 → 取 folder_token → 创建时直接带上 → 登记索引。

```bash
lark-cli base +record-list --base-token KlZobKh0MaWyaNsSsmdcoG7CnIc --table-id tblFGopMYHt6rdIg --as user
lark-cli docs +create --as user --doc-format markdown --title "..." --content "@./x.md" --parent-token <folder_token>
```

## 操作后自检（四问，全为"是"才算完成）

1. 文档的父目录是具体目录，**不是根目录**？
2. 父目录与路由裁决一致（—> 取层级最深的命中目录）？
3. 内容索引表已新增/更新记录：文档名称、文档链接、文档类型、所在目录、创建日期、最近修改日期、登记说明？
4. 「所在目录」填的是**一级目录内的相对路径**（如 `股票` / `AIGC/arxiv`），不是绝对路径、也不是 `（根目录）`？

## 常用命令

```bash
# 列出 Base 所有表（获取表名→table_id 映射）
lark-cli base +base-block-list --base-token KlZobKh0MaWyaNsSsmdcoG7CnIc --as user

# 读取目录定义表（路由前必做）
lark-cli base +record-list --base-token KlZobKh0MaWyaNsSsmdcoG7CnIc --table-id <dirdef_table_id> --as user

# 列出云盘根目录（不传 --folder-token）
lark-cli drive files list --page-size 200 --as user

# 列出指定文件夹内容
lark-cli drive files list --folder-token <folder_token> --page-size 200 --as user

# 创建文件夹
lark-cli drive +create-folder --name <name> --folder-token <parent_token> --as user

# 移动文件/文件夹（注意 flag 是 --file-token，不是 --token）
lark-cli drive +move --file-token <token> --type <type> --folder-token <target_folder_token> --as user

# 重命名
lark-cli drive files patch --file-token <token> --type <type> --name <new_name> --as user

# 删除（高风险，需 --yes）
lark-cli drive +delete --file-token <token> --type <type> --yes --as user

# 向内容索引表登记文档
lark-cli base +record-batch-create --base-token KlZobKh0MaWyaNsSsmdcoG7CnIc --table-id <content_table_id> --json @payload.json --as user
```

## 注意事项

- `drive files list` 列根目录时**不要传** `--folder-token`，直接省略即可列出根目录。
- 写 API（字段/视图/记录）有限流，间隔 2–3 秒。
- PowerShell 脚本含中文时需 UTF-8 BOM；JSON payload 文件用 `@file` 传参时文件不要 BOM。
- `record-batch-create` 的 `create_records` 是**字段映射数组**，每个元素直接是 `{字段名: 值}`，**不要**再套一层 `{"fields": {...}}`（套了会报 `Cell value does not match any supported shape`）。
- 单元格取值形状：text/url → 字符串；select → `["选项"]`；datetime → `"YYYY-MM-DD HH:mm"` 字符串（不要传毫秒时间戳）。url 样式的文本字段传纯 URL 字符串即可，传对象会报错。
- 登记前用 `base +field-list` 确认真实字段类型；不要写 formula / lookup / created_at 等系统字段。
- `record-batch-update` 用 `update_records` 映射格式：`{"update_records":{"<record_id>":{"<字段名>": <值>}}}`，每条记录独立指定要更新的字段。
- 目录定义表的 table_id 默认是 `tblFGopMYHt6rdIg`，但应通过 `base-block-list` 确认。
