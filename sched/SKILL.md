---
name: sched
description: 本地定时任务调度器的使用与运维入口。当用户需要创建/注册/启停/取消注册定时任务（间隔、时间窗+星期限定、一次性、仅手动）、按自定义规则调度（复杂日期/条件由任务内部判断，interval 宽频唤醒 + state.json 上报）、查看某次执行的进度与日志、手动立即执行或终止任务、查看执行历史、导出 CSV、或排查任务状态/调度问题时使用。所有定时任务统一放在调度器根目录的 tasks/ 下，通过 sched CLI 或 Web UI 管理。
---

# sched（本地定时任务调度器）

常驻单进程调度器（FastAPI + APScheduler）+ Web UI + CLI，统一管理一批各自独立的定时任务。

**核心理念**：调度器只定义**固定接口协议**，不关心任务内部实现。任务不 import 调度器代码，
只靠 `task.json` 声明 + 环境变量 + 约定文件（`cache/state.json`、`cache/execution.log`、
`cache/blocked.md`、`results/`）与调度器握手。

**注册模型**：**纯手动**。调度器不扫描目录、不生成任何文件、不自动发现新任务。
任务目录由用户/子任务自行创建，创建好后用 `sched job new <id>` / Web UI「注册任务」显式注册，
调度器才认它。取消注册后刷新动作不会让它复活。

## 定位调度器根目录

本文所有路径都相对**调度器根目录**。根目录不写死在文档里，按下面的方式取得：

```bash
sched status          # 输出的第一行「根目录」即调度器根目录
```

CLI 的解析顺序：`--home` 参数 → 环境变量 `SCHED_HOME` → `sched init` 记录的用户级配置文件 → 内置默认值。
任务进程内可直接读环境变量 `SCHED_HOME` / `SCHED_WORKSPACE`（后者是任务目录的绝对路径）。

## Web UI 地址

**不要手工拼地址**，CLI 会按当前监听配置自动算好：监听 `0.0.0.0` 时换成浏览器能直连的地址
（优先环境变量 `SCHED_PUBLIC_HOST`，其次云厂商元数据里的 EIP，最后才退回内网 IP）；
只监听回环时保持 `127.0.0.1`。地址里不带 token，直接打开即可用（鉴权默认关闭）。

云主机上务必用这里给出的公网地址 —— 直接报内网 IP（如 `172.31.x.x`）用户是打不开的。
若公网地址仍打不开，依次查：云安全组是否放行该端口 → 用 SSH 隧道
（本地执行 `ssh -L 8787:127.0.0.1:8787 <user>@<公网IP>` 后开 `http://127.0.0.1:8787/`）。

```bash
sched status            # 输出中的「Web UI」一行即完整地址
sched status --json     # 字段 web_url
sched start             # 启动成功后也会打印该地址
```

因此：**启动服务之后、以及任何查看/排查任务的需求中，都应把这条 Web UI 地址一并给用户**，
而不是只回执行结果。

## 目录与形态

| 项 | 位置（相对根目录） |
| --- | --- |
| 任务目录 | `tasks/<任务id>/` —— **约定目录，所有定时任务都放这里（任务自己创建）** |
| 数据（无 SQL） | `data/`：`settings.json`、`jobs.json`（注册表）、`runtime/active.json`、`runs/*.jsonl` |
| Web UI | `web/` |
| CLI 源码 | `cli/`（安装后得到全局命令 `sched`） |
| 部署 | `deploy/`（systemd 单元 + 安装脚本） |
| Web UI 地址 | 由 `sched status` 打印（见上文「Web UI 地址」） |
| 服务托管 | systemd 单元 `scheduler.service`（`Restart=always`） |

## 安装 / 启动

在调度器根目录下执行：

```bash
# 一键：装依赖 + 初始化 + 装 CLI + 装 systemd 单元并启动
sudo bash deploy/install.sh

# CLI 改了源码要重装（npm 是复制而非软链，不重装不生效）
npm i -g ./cli
```

服务控制：`sched start | stop | restart | status`（有 systemd 时走 systemd，否则 pidfile 模式）。

## 常用命令

```bash
sched status                            # 服务状态 + Web UI 地址 + 每个任务的下次触发
sched job ls                            # 任务列表（含调度、优先级、启用、上次结果）
sched job new <id>                      # 注册已存在的 tasks/<id>/ 目录（不生成文件）
sched job show <id>                     # 详情：调度 / 优先级 / 下次触发 / 任务侧 state.json
sched job enable|disable <id>
sched job rm <id> [--purge]             # 取消注册；历史与日志默认同步删除，--purge 连任务目录一起删
sched run <id>                          # 立即执行（手动触发，CLI/API 专用，Web 无此按钮）
sched run <id> --dry-run                # 调试模式：注入 SCHED_DRY_RUN=1，任务必须跳过所有真实副作用，历史标记 DRY
sched runs [--job X] [--status Y] [-n 50]
sched log <run_id> [--stream stderr] [--tail 100] [-f]
sched kill <run_id>                     # 终止某次 run；传 job_id 则终止该任务全部在途 run
sched task-state <id>                   # 任务侧 cache/state.json
sched reload                            # 刷新已注册项（只刷新 jobs.json 里的，不扫描新目录）
sched export runs [--job X] [--output f.csv]
```

加 `--json` 输出原始 JSON；`--home` / `--url` / `--token` 可覆盖连接参数。

## 写一个任务（注册制）

**调度器不生成任务骨架、不预置 cache/。目录与文件全部自己建。**

1. 自建目录：`mkdir -p tasks/daily_stock && touch tasks/daily_stock/run.py`
2. 写 `task.json`——**只写调度器需要的字段**：

```json
{
  "schema_version": 1,
  "name": "每日行情",
  "entry": { "file": "run.py", "interpreter": "python3", "args": [] },
  "schedule": { "type": "interval", "interval": 300 },
  "outputs": { "expect": ["results/quotes.csv"] }
}
```

3. 注册：`sched job new daily_stock`（目录不存在或 task.json 非法会直接报错）
4. `sched reload` 刷新已注册项，再 `sched run daily_stock` 验证

`schedule.type`：`interval`（秒，可选叠加时间窗+星期）/ `once`（ISO8601）/ `manual`（仅手动）。

### `interval` 的时间窗叠加（可选）

`interval` 带 `start_time` + `end_time` 时变成「星期 + 时间窗」内的定时，
适合「每周一至周五 09:15–17:21 之间按某频率跑」。触发点从当天窗口起点对齐
（不是从启动时刻算起），窗口外/非指定星期静默不触发。
**窗口同时是「允许运行的时间范围」**：窗口一过，仍在跑的在途运行会被立即终止（记 `killed`，
原因「窗口结束，终止在途运行」）；不想被收口就设 `allow_overrun: true`。

```json
{
  "schedule": {
    "type": "interval",
    "interval": 300,
    "start_time": "09:15",
    "end_time": "17:21",
    "weekdays": [1, 2, 3, 4, 5],
    "allow_overrun": false
  }
}
```

- `interval`：正整数秒，必填
- `start_time` / `end_time`：`HH:MM` 或 `HH:MM:SS`，**必须成对出现**；都不填 = 全天运行
- `weekdays`：`1`(周一)…`7`(周日) 数组；省略或空 = 每天
- `allow_overrun`：默认 `false` = 窗口到点终止在途；置 `true` = 允许在途跑完
- **跨天窗口**：`end_time` 早于 `start_time` 表示窗口延伸到次日。如 `15:30–06:00` = 当天 15:30 到次日 06:00；
  星期归属按**窗口起点所在的那一天**判断（周三 15:30 开的窗口跑到周四 06:00，算周三）。
  人话显示会带上「次日」，如 `每周一至五 15:30–次日 06:00 每 30 分钟`

常见配法（改 `schedule` 即可）：

| 需求 | `schedule` |
| --- | --- |
| 工作日 09:15–15:00 内每 5 分钟，超 15:00 收口终止在途 | `{"type":"interval","interval":300,"start_time":"09:15","end_time":"15:00","weekdays":[1,2,3,4,5]}` |
| 15:30 到次日 06:00 之间可执行（跨天） | `{"type":"interval","interval":null→不可省略，interval 必填","start_time":"15:30","end_time":"06:00","weekdays":[]}` |
| 每天每 5 分钟一次 | `{"type":"interval","interval":300}` |
| 仅手动触发 | `{"type":"manual"}` |

> 注意：合并后的 `interval` 类型要求 `interval` 必填（正整数秒）。旧文档里「interval 省略 =
> 窗口起点只触发一次」的语义已随 `interval_window` 类型的删除而移除；需要"窗口起点跑一次"时，
> 直接用宽间隔（如 `interval` 取一个足够大的秒数）或由任务内部自行控制。

### 自定义调度模式（复杂日期/条件规则）

调度器**只负责按固定间隔唤醒**，复杂规则（偶数日、1 月偶数 + 2 月仅 28 号、节假日跳过等）
**全部由任务内部自行判断**——这是架构方向（任务三/四已确定），调度器不再增加任何日期表达式。

**两种落地形态，按任务性质选：**

| 形态 | 适用 | 调度配置 | 执行历史 |
| --- | --- | --- | --- |
| **自循环常驻**（推荐） | 要一直推进、要保状态的"长时监督"任务 | 宽频 `interval` + `max_instances=1` + `overflow=skip`（看门狗） | **始终只有一条**在途记录，唤醒全部被跳过 |
| 宽频唤醒 + 任务内自检 | 一次性逻辑、需要"进程消失"换取隔离（日期命中才跑等） | 宽频 `interval` | 每次命中一条 |

**形态一：自循环常驻** —— 任务入口启动一次后在后台 `while True` 自行循环，**永不主动退出**；
调度器的 `interval` 只是看门狗：任务在跑时每次唤醒都被跳过（不产生新历史），只有进程意外退出
（崩溃/被杀/服务重启）后，下一次唤醒才把它重新拉起：

```json
{ "schedule": { "type": "interval", "interval": 60, "max_instances": 1, "overflow": "skip" } }
```

```python
# tasks/<id>/run.py —— 自循环常驻
import random, time
count = 0
while True:
    time.sleep(random.uniform(1, 5))  # 节奏由任务自己控制
    count += 1
    print(f"第 {count} 次执行", flush=True)
    write_state(count)                # 写 cache/state.json 上报（loop_count 递增）
```

**形态二：宽频唤醒 + 任务内自检** —— 任务入口每次被拉起后先自检规则，不命中立即正常退出
（exit 0，不算失败）：

```json
{ "schedule": { "type": "interval", "interval": 300 } }
```

```python
# tasks/<id>/run.py
import datetime, sys
def should_run(d: datetime.date) -> bool:
    # 任意复杂规则：偶数日、按月区分、节假日……
    if d.month == 1 and d.day % 2 == 0: return True
    if d.month == 2 and d.day == 28: return True
    return False
if not should_run(datetime.date.today()):
    sys.exit(0)  # 不命中：正常退出，不落失败记录
# ……命中后的真实工作……
```

命中后任务自循环推进，每轮写 `cache/state.json` 上报进度（字段见下「任务侧契约」），
Web UI 实时展示当前步骤/进度/下一步动作；`sched run <id>` 或 Web「立即执行」可随时手动
验证任务内的规则判断。

要点与边界：

- **没有 `timeout_sec` / `retry` / `queue_cap`**：任务跑多久由任务自己决定（直到完成或被终止），
  调度器不设单次超时、不自动重试；队列无限
- **并发控制**（`schedule` 里配，任意类型皆可，interval 最常用）：
  - `max_instances`：整数 1~20，默认 1。**最大同时运行的实例数**。1 = 串行（默认），N = 最多 N 个并行
  - `overflow`：`skip`（默认）| `queue`。实例数到上限时**新触发**怎么处理：
    - `skip` = 直接跳过丢弃（本次触发不留任何记录，不影响「下次触发」）
    - `queue` = 进 FIFO 队列排队，等有 worker 空了再跑（跑完一个接一个）
  - 行为表（以「间隔 1 秒、任务本身跑 1 小时」为例）：

    | `max_instances` | `overflow` | 任务跑 1 小时期间每秒触发的下场 |
    | --- | --- | --- |
    | 1 | `skip` | 第 1 秒启动，之后每秒触发全部跳过，直到跑完 |
    | 1 | `queue` | 第 1 秒启动，之后每秒触发全部排队，跑完一个接一个执行 |
    | 3 | `skip` | 第 1/2/3 秒启动 3 个并行，之后每秒触发跳过，直到有空位 |
    | 3 | `queue` | 始终有 ≤3 个并行，多的排队 |

  - **任务进程永远不会被调度器"重启/杀掉"来赶新触发**；每次触发只是产生一个执行请求，
    由上面两项决定「跳过 / 排队 / 并行启动」。任务跑 1 小时就是 1 小时，调度器不切碎它。
    唯一会终止在途运行的是：人工终止、`interval` 时间窗到点收口（`allow_overrun=false`）、服务重启
  - 并发数上限 20 是硬边界（防止误配拉爆资源）
  - **手动触发（`sched run` / Web「立即执行」）同样遵守并发上限**：满了且 `overflow=skip` 时
    会返回/提示「并发已满，本次触发已跳过」，不会静默丢
- `priority`：整数，默认 `0`，**数值越大越优先**。只在**多个任务同一时刻被触发**时决定谁先启动；
  任务之间本来就并行（各自独立线程/队列），优先级不抢占、不影响已在跑的任务。
  **优先级与调度都写在 `task.json`**，Web UI 任务详情页「编辑调度」弹窗里直接改，保存即写入
  task.json 立即生效；没有独立的覆盖机制（`overrides` 已整体移除）
- **任务自己的业务参数不写进 task.json**（比如抓什么关键词、股票代码），放任务目录内自己的文件
  （如 `config.json`），由任务自己读取

### 任务侧契约（回传即文件，任务自己写）

以下文件都在**任务目录**内：

| 文件 | 作用 |
| --- | --- |
| `cache/state.json` | 进度快照（自定义调度靠它上报每轮进度）：`status` / `current_step` / `progress`(0-100) / `next_action` / `loop_count` / `last_error` / `updated_at` |
| `cache/execution.log` | 心跳日志，每行 `时间戳 \| 轮询序号 \| 当前步骤 \| 状态变化 \| 下次动作` |
| `cache/blocked.md` | 无法完成的子任务及影响范围 |
| `results/` | 交付物；`outputs.expect` 里列的文件缺失则判 `failed` |

**进度回调接口**：任务运行中自行写 `cache/state.json`（这是任务向调度器/前端"回传"状态的唯一
通道）；Web UI 与 CLI 通过 `GET /api/jobs/{id}/task-state` / `sched task-state <id>` 读取，
前端任务页每 5s、run 页每 2s 轮询刷新。`updated_at` 用于判断"任务是否还在推进"。

环境变量：`SCHED_JOB_ID` / `SCHED_RUN_ID` / `SCHED_TRIGGER` / `SCHED_ATTEMPT` /
`SCHED_SCHEDULED_AT` / `SCHED_WORKSPACE` / `SCHED_HOME` / `SCHED_DRY_RUN`（`1` = 调试 dry-run，见下节）。

退出码 `0` = 成功，非 `0` = 失败。调度器**不解析** stdout/stderr，原样落盘到
`data/runs/<job_id>/<run_id>.{stdout,stderr}.log`。

### 调试 / 开发 与 正式任务 的严格隔离（dry-run 协议）

**背景**：创建定时任务时的验证/调试若直接在正式任务上执行，会污染正式任务的执行历史
（出现莫名其妙的 `manual` 记录），且若任务在调试时触发了真实副作用（OSS 上传、写库、发消息、
付费调用等）——这些往往不可清理或要花钱。因此调试必须与正式运行**彻底隔离**。

**四条铁律**（创建/维护任何定时任务时强制遵守）：

1. **调试绝不直接跑正式任务**。任何需要运行验证的场景——无论 dry-run 还是真实代码——都在
   独立调试任务上做：id 用 `<id>_dev` 后缀，独立目录、独立注册，与正式任务互不干扰。
   正式任务**从不手动触发**，历史里只有调度触发的记录。
   （`sched run <id> --dry-run` 仍可用，但会在正式任务历史留一条 `manual DRY`；为保持正式历史
   绝对干净，首选在 `<id>_dev` 上跑。）

2. **dry-run 模式下任务代码必须跳过一切真实副作用**。任务进程读取环境变量
   `SCHED_DRY_RUN`：`1` = 调试模式。此时**不允许**做任何对外写入——OSS 上传、数据库写、
   发消息、付费 API 调用等一律只 `print` 将要执行的动作，绝不真正执行。任务入口应显式判断：

   ```python
   import os
   DRY = os.environ.get("SCHED_DRY_RUN") == "1"
   if DRY:
       print(f"[dry-run] 将上传 {path} -> oss://bucket/x", flush=True)
       # return  # 或走仅校验逻辑，绝不真正上传
   else:
       upload_to_oss(path, "oss://bucket/x")
   ```

3. **调试结束后彻底清除，不留任何痕迹**。调试产生的 run 记录、stdout/stderr 日志、
   调试任务目录，全部删除：
   ```bash
   sched job rm <id> --purge         # 正式任务：注册 + 任务目录 + 历史与日志（如已建 _dev 调试任务）
   sched job rm <id>_dev --purge     # _dev 调试任务：同上，验证完即删
   ```
   删除语义（见上「常用命令」）：历史与日志默认同步删除；`--purge` 连任务目录一起删。
   目标状态：正式任务历史中**只有**正式触发，没有调试产生的 manual。

4. **dry-run 的 run 在历史中明确标记 `DRY`**。`sched run <id> --dry-run` 启动的 run，
   其触发列显示为 `manual DRY`（CLI 与 Web UI 均如此），与正式触发一眼可辨；
   调试结束后按铁律 3 清除，正常情况不会残留。

**判定顺序**（创建定时任务时）：

```
静态检查通过（语法/清单/配置） → 需要运行验证？
   ├─ 只需验证"逻辑正确、不产生副作用" → 建 <id>_dev 任务，在 _dev 上 sched run --dry-run（单次，不重复）
   ├─ 需跑真实代码但不想污染正式任务 → 建 <id>_dev 调试任务跑真实代码 → 验证后 --purge 清除
   └─ 都不需要 → 直接等正式调度首次执行（唯一一次真实副作用 = 最终结果）
验证后立即清理调试产物（_dev 任务 --purge），再交付。
```

### 状态机

```
queued → running → success | failed | killed | interrupted
timeout —— 保留状态值：仅用于兼容历史数据，新代码不再产生
```

- `failed`：退出码非 0 / 交付物缺失 / 无法拉起入口
- `killed`：人工终止；或 interval 时间窗到点收口
- `interrupted`：调度器重启/停止，在途进程被回收

### 前端行为（Web UI）

- 调度逻辑醒目展示：任务列表「调度」列 + 任务详情「调度规则」卡片（自然语言 + 下次触发）
- 执行历史分页：任务详情页与执行历史页均支持分页
- 不展示 task.json / execution.log / blocked.md 原文（cache/state.json 解析后展示进度）
- 「立即执行」按钮**只在 `manual`（仅手动）类型显示**：任务详情页「调度规则」卡片右上角；
  interval / once 有自动调度，不显示该按钮（手动触发仍可用 CLI `sched run <id>`）
- 「编辑调度」弹窗（标题「编辑调度与优先级」）可改类型/间隔/窗口/星期/优先级，保存即写 task.json
- 任务列表无"在途运行=N"计数徽标（在途信息只在总览页「运行中/排队中」区块）

## 排查

| 现象 | 处理 |
| --- | --- |
| 任务标「清单错误」 | 已注册条目的目录缺失或 task.json 非法；`sched job show <id>` 看详情，修复后 `sched reload` |
| `failed(missing_output)` | `outputs.expect` 的文件未产出 |
| `killed` | 被手动终止，或窗口到点收口（`allow_overrun` 可避免） |
| `interrupted` | 服务重启，在途 run 被回收（正常现象，不影响历史） |
| 服务日志 | `journalctl -u scheduler.service -f` |
| CLI 改了不生效 | 在调度器根目录下重装：`npm i -g ./cli` |
| Web UI 打不开 | `sched status` 取公网地址；查云安全组放行；或 SSH 隧道 |

## 红线

- **不要改 `uvicorn --workers`**：多 worker 会让同一任务被重复触发。
- 任务目录**必须**在 `tasks/` 下，任务 id = 目录名，且**必须显式注册**才会被调度。
- 不要在任务代码里 import 调度器模块；只用环境变量与约定文件。
- 任务的业务参数由任务自己管理，不要塞进 `task.json`。
- 不要手工改 `data/jobs.json` 之外的调度器内部文件；取消注册用 `sched job rm`。
