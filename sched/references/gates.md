# 五道闸上线检查细则（自动准入，逐条可验证）

> 本文是调度器对 `tasks/<id>/` 新任务自动执行的五道准入闸的权威说明
> （serve 在热加载扫描时后台执行；`python3 -m sched register <id>` 可立即手动触发一次），
> 全部判定与调度器 `sched/contract.py` 实现一一对应。**任务上线前逐条自检，检查未通过时按本文对照修复。**
> 严禁通过修改调度器源码、task.json 注水、手改数据文件等任何方式应付闸门——闸是给无人值守运行上的保险。

## 0. 通则

- 上线检查只做两件事的二选一：**五道闸全过 → 写入 `data/jobs.json`（enabled=true）+ 初始画像**；任一闸不过
  → 任务**被明确拒绝纳入调度**，注册表不留 enabled 记录，失败原因进入 `data/runtime/admission.json`
  并在管理台/`status` 展示为"未通过：闸名: 原因"。
- 新任务无需任何手动动作：把任务目录放进 `tasks/`，serve 最迟一个热加载周期（≤30s）发现它并**在后台
  串行**跑闸（同一时刻只检查一个任务）；检查期间不阻塞调度主循环。也可随时 `register <id>` 或管理台
  「导入任务」立即检查（管理台导入只接受 `tasks/` 下已存在的子目录名）。
- **闸失败不做定时自动重试**：失败原因持久化后该任务挂起，只有当任务目录内文件指纹变化
  （本地修改/删除文件）时才自动重新检查——闸是上线流程的一部分，迭代节奏由创建者掌握，
  调度器不隔几分钟空跑冒烟。删掉任务目录即放弃该任务；删除后再放回同名目录会按新指纹重检。
- 五道闸全部由调度器在本机**真实拉起子进程**完成，串行执行，最多 4 次子进程：
  闸2（探针 1 次）→ 闸3（冒烟 1 次）→ 闸4（纯计算，不拉进程）→ 闸5（非 exempt 任务：打断跑 + 恢复跑 2 次）。
  加上可能的进程收尾等待，**实测单任务检查约 10–20s**（小步 dry 冒烟）；耗时随冒烟步数线性增长，
  硬上限由各闸超时决定（探针 30s、冒烟 max_runtime_sec 默认 60s、断点两次各 60s）。闸2/3/5 均有超时杀进程兜底，不会无限挂住。
- 闸期进程的运行身份：task.json `runtime.user`（默认 sched-run）；降权失败闸直接失败，**绝不静默回升 root 跑**。
- 闸期环境与正式一致地注入 `SCHED_*` 与白名单变量；**闸内子进程的 stdout/stderr 被丢弃（DEVNULL）**，
  检查只回报闸名与原因。要看错误输出，必须按本文各闸的"实证自检"命令在任务目录手工裸跑复现。
- **cgroup 降级影响闸门可信度**：闸3/闸5 的内存实测依赖 cgroup `memory.peak`。按 [deployment.md](deployment.md) §1
  自检；`cgroup DEGRADED` 时实测峰值为 0，闸4 只信申报值，闸5 不再有内存边界，上线需谨慎并在交付说明标注。
- 每个非 exempt 任务必须通过 **全部 5 道闸**；`contract_exempt=true` 任务通过 **闸1–4**（无断点能力要求，
  之后只能 manual 触发）。

## 闸1 · 静态闸 gate1_static —— task.json 与文件结构合法性

**机制**：不拉起进程。解析 `tasks/<id>/task.json`（pydantic schema 校验），校验入口与路径约束，
复核 exempt 规则。

**通过条件（必须同时满足）：**

1. 任务 id 匹配 `^[a-zA-Z0-9_-]{1,64}$` 且不以 `_`/`.` 开头，id 与目录名一致；目录存在且内含 `task.json`。
2. JSON 顶层为对象，schema_version ∈ {1, 2}（**新任务一律写 2**）。
3. `entry.file` 非空、相对路径、不含 `..`、解析后仍在任务目录内，且文件真实存在。
4. `entry.interpreter`：要么为 `null`（此时入口文件必须自带可执行权限 `os.X_OK`），要么匹配
   `^[A-Za-z0-9_.+-]+$`（**只能是命令名，不带 `/` 路径**，防止解释器劫持）。
5. `entry.cwd` 相对且不越出任务目录；`entry.args` 只能是字符串数组。
6. `outputs.expect[]` 每项相对路径、不含 `..`、不越界（文件允许暂不存在，正式 run 后校验）。
7. `priority` 为 0–100 整数；`env` 为 string→string，且**不含黑名单键**：
   `LD_PRELOAD/LD_LIBRARY_PATH/LD_AUDIT/LD_DEBUG/PYTHONSTARTUP/PYTHONINSPECT/BASH_ENV/ENV/IFS/PATH`。
8. `resources`：cpu≥0（float）、memory_mb≥0（int 非 bool）。**只有 CPU/内存两个字段**；
   代理/VPN/API 配额等外部资源既不申报也不做容量管理（见闸4 语义要点）。
9. `heartbeat.timeout_sec` 为整数且 ≥5；`schedule`（讨论二两值模型）：
   - `type` 仅 `manual` / `auto`；
   - `auto` 类型必须带正整数 `interval`（给机会的最小间隔秒数）；
   - 旧字段 `start_time/end_time/weekdays/once_at/allow_overrun` 已废弃，
     ScheduleSpec model_config extra=ignore 会静默忽略不报错，但**闸1 不再校验它们**，
     精确时机（法定节假日、每月特定日期等）由任务 SDK `reschedule(delay_sec)` + `exit_skip()`
     自行判断；
   - `max_instances` 1–20；`overflow` 仅 `skip/queue`。
10. `contract_exempt=true` ⇒ `schedule.type` 必须为 `manual`（**单向强制**；反向不成立：manual 任务
    可以且应当具备断点能力，只有真正无法保证数据完整性的任务才标 exempt）。
11. `retry` 段（可省略，省略=全默认）：`delay_sec`/`max_attempts` 为非负整数；`not_after`
    为空、合法 ISO8601 绝对时刻或每日 `HH:MM(:SS)` 之一，非法即闸1 失败。

**典型失败与修复：**

| 报错要点 | 修复 |
| --- | --- |
| `entry.file 不存在/越出任务目录/'..'` | 路径改成任务目录内相对路径；入口放任务目录里 |
| `interpreter 非法（只能是命令名）` | 写 `python3` 而非 `/usr/bin/python3` |
| `env 键在安全黑名单中` | 删除 PATH/LD_* 等键；需要自定义环境用别的键名 |
| `contract_exempt=true 只能 manual` | 改 schedule.type=manual，或去掉 exempt（能断点的任务不许用 exempt 逃避抢占） |
| `interval 必须为正整数秒` / auto 类型缺 interval | auto 类型必须填 interval（给机会的最小间隔）；manual 类型 interval 忽略 |

**反作弊约束**：闸1 只证明"声明合法"，不证明行为。不要用注释/多份 task.json 切换来糊弄上线检查；
正式运行以检查通过时同目录文件为准，热加载只重读同一路径。

## 闸2 · 契约闸 gate2_contract —— 证明任务遵守 SDK 通信契约

**机制**：以环境 `SCHED_CONTRACT_PROBE=1` 拉起入口一次，超时 30s，降权到 runtime.user 执行。
SDK 的 `run_task()` 在此环境自动走 `contract_probe()`：写一次合法 state.json 并退出 0，不产生业务副作用。

**通过条件（全部满足）：**

1. 进程退出码 **0**（30s 不退出判超时失败，随后 SIGKILL 回收）。
2. 在 `cache/runs/probe/state.json`（或 legacy `cache/state.json`）写出 JSON 对象。
3. state 对象**同时包含**四个键：`status`、`current_step`、`schema_version`、`resume_point`
   （resume_point 允许是空对象 `{}`，但键必须在；类型须可被 JSON 解析）。

**实证自检（上线前本地先跑，等价于闸2）：**

```bash
cd tasks/<id> && export SCHED_WORKSPACE=$PWD SCHED_RUN_ID=probe
SCHED_CONTRACT_PROBE=1 python3 run.py; echo "exit=$?"
cat cache/runs/probe/state.json
```

**失败排查：**

- 非 0 退出：裸跑复现，看 stderr；常见为 import 错误（PYTHONPATH 已自动加入项目根，正常 `from sched_task_sdk import ...` 即可）、
  降权用户无权读任务目录（给目录 o+rx 或改为属主用户）、入口路径错。
- state 缺字段：不要手写探针分支绕过，继承 `SchedTask` 用 `run_task()` 即自动满足；自研入口必须自己
  在探针模式写齐四字段。
- **探针模式禁止有副作用**（不得写库/发请求/产出 results）：探针会在每次上线检查时重跑。

## 闸3 · 冒烟闸 gate3_smoke —— 真实执行一轮，测量资源与收敛时间

**机制**：以 `SCHED_DRY_RUN=1`（smoke.mode=dry，默认）或 `=0`（mode=real）拉起入口，
超时 `smoke.max_runtime_sec`（默认 60s）；cgroup 预算 memory.high=0.9×整机、memory.max=整机、cpu=整机核数。
记录退出码、运行时长、cgroup CPU 秒、内存峰值。

**通过条件（全部满足）：**

1. 在 `max_runtime_sec` 内退出（超时 → SIGKILL → 闸失败）。
2. 退出码为 **0 或 99**（冒烟被资源挤压时 99 也算可接受的干净退出）；其余退出码（含 1/100/101/110/负数）一律失败。
3. dry 模式下任务必须**无真实副作用且能快速收敛**：外部写操作全部关断，只允许本地只读探查与 print；
   网络等待必须带短路超时，不允许 dry 路径等待真实配额。

**资源测量与画像：**

- 实测平均核数 = cgroup CPU 秒 ÷ 运行时长；实测内存峰值 = cgroup `memory.peak`；二者作为画像首样本，
  并在之后每次正式 run 后按 P95 滑窗（8 次）×1.2 上浮更新。
- cgroup 正常时，冒烟峰值是闸4 与准出预估的主要依据；**申报值不得低于冒烟峰值**（预估取 max(申报, 画像)）。
- dry 占用通常低于 real：若真实路径明显更重（大对象/并发），`resources` 申报必须按 real 上限额外上浮，
  不得直接抄 dry 数字。必要时用 `smoke.mode=real`（确认副作用幂等、目标安全后）。

**失败排查：**

| 现象 | 修复方向 |
| --- | --- |
| 冒烟超时 | 拆小首轮工作量；dry 路径禁用慢等待；适当调大 max_runtime_sec（上限须与调度频率匹配，不得无脑调大） |
| 退出 100/101 | dry 路径不应真碰受限资源；给网络调用加 dry 短路/模拟返回 |
| 退出 1 且无分类 | 修代码异常；兜底归类不会在闸门救你（冒烟只接受 0/99） |
| 实测峰值远高于申报 | 上调 resources.memory_mb；超整机则必须先优化内存，否则闸4 拒绝且无商量余地 |

## 闸4 · 容量闸 gate4_capacity —— 硬资源门禁（超过本机上限，拒绝加入）

**机制**：纯计算，不拉进程。输入 = 申报值（task.json resources）+ 闸3 实测峰值，对比整机 `/proc/meminfo`
与 CPU 核数。

**通过条件（按顺序全部满足）：**

1. 若 `resources.memory_mb > 0`：申报内存 **不得大于** 整机内存总量，否则拒绝
   （`声明内存 XMB > 机器上限 YMB，拒绝加入`）。
2. 若闸3 实测峰值 > 0：实测峰值 **不得大于** 整机总量，否则拒绝。
3. 预估内存（实测优先，否则申报）**不得为 0**：申报与实测都为 0 = 资源占用未知，拒绝
   （`资源预估未知（未声明且冒烟未测得），拒绝加入`）。
4. `resources.cpu` 不得大于整机 CPU 核数。

**语义要点：**

- 这是**硬门禁**：超上限的任务没有"先排队试试"的选项，必须先优化（降内存/限流/拆分数据分片），优化后等其自动重新检查（改文件立即重检）或手动 register。
- 闸4 只对比**机器上限**，不看当前空闲：即使此刻内存被占满，只要任务不超整机上限就允许上线，
  运行时排队由准出侧负责。**不要**为了"当前能立刻跑"而把申报调到当下空闲值以下。
- **外部资源不参加任何闸门，也没有容量配置**：代理隧道/VPN/API 配额等外部资源跨账号、跨协议，
  调度器无法感知真实占用，统一池化管理没有意义，因此不申报、不设上限、不排队令牌。任务在
  **正式运行中**遇到这类问题（代理失效、429、配额耗尽、连接失败）时自己快速 `sys.exit(101)`，
  调度器立即重排队，重试节奏/上限/时效由任务 `retry` 段自治；冒烟（dry）路径必须短路这类调用，
  不允许真碰外部配额（见闸3 失败排查）。
- 准出时预估还会叠加：画像 P95×overshoot(1.2)、外部进程占用余量（external_safety_margin，默认 512MB）。
  申报要给正常波动留余量，避免每次正式跑都触发超限退让。

## 闸5 · 断点闸 gate5_checkpoint —— 证明可被安全抢占、可幂等续跑（最严，非 exempt 必考）

**机制（两次真实拉起，dry 模式）：**

1. **打断跑 ckpt1**：拉起进程后 `sleep smoke.signal_after_sec`（默认 1.5s），向整个进程组发 **SIGTERM**，
   总超时 60s，到期 SIGKILL。
2. 读 `cache/runs/ckpt1/state.json` + `cache/resume_point.json` 做三项校验。
3. **恢复跑 ckpt2**：不带信号再拉起一次，超时 60s，验证能从断点正常收尾。

**通过条件（全部满足，任一不过即拒）：**

1. ckpt1 退出码 **= 99**，**或** state.status == `"preempted"`（两者满足其一）。
   退出 0（无视 SIGTERM 直接跑完）、其他码、被 SIGKILL（超时未退出）均失败。
2. **运行期心跳实证**：ckpt1 启动之后，实例级 state.json（或 legacy）的 mtime 必须在运行期间被更新过
   （容差 1s）。只在 `SCHED_CONTRACT_PROBE` 模式写一次状态、正式运行不写心跳的"伪契约任务"在此被拦。
3. ckpt1 落盘的 `resume_point` 必须是 **JSON 对象**（null/标量/数组均失败）；空对象 `{}` 仅当任务确实
   一步完成时才可接受，多步任务首次被打断就给出空断点视为不合格（无法证明续跑）。
4. ckpt2（恢复跑）退出码 **= 0**，且 state.status ∈ {`success`, `intentional_exit`}。

**作者必须额外保证（闸的观测局限，列入验收人工核对）：**

- **真续跑而非全量重跑**：闸只看到 ckpt2 成功，无法自动识别"忽略 resume_point 从头跑"。必须在 _dev 用
  日志/计数证明 ckpt2 的处理起点 = ckpt1 的 resume_point，且重放部分**幂等**（重复写不产生重复数据/重复扣费）。
- **断点粒度**：每完成一个最小工作单元立即 `self.state.resume_point = {...}; self.state.flush()`；
  断点必须覆盖"已确认完成的位点"，不得把未完成的工作记进断点。
- **信号语义**：SIGTERM 只置停止位，不打断当前步（SDK 已托管）；当前步结束后落断点→`mark_preempted()`→
  return 99。**单步必须短于 40s 宽限期**（考虑磁盘 flush 时间，建议单步 ≤20s）；天然长操作要拆成可增量的小步。
- 信号处理期间不得吞掉 SIGTERM、不得退出码造假；进程组内若拉起孙进程，由任务自己保证孙进程随组退出
  （调度器按进程组发信号）。

**实证自检（上线前在 _dev 完整演练）：**

```bash
# 终端1：dry 跑起
SCHED_DRY_RUN=1 SCHED_RUN_ID=ckpt1 python3 run.py &
# 终端2：1.5–3s 后对进程组发 TERM
kill -TERM -<pgid>      # 或 kill -TERM <pid>（单进程时等价）
# 预期：终端1 退出码 99；检查
echo $?; cat cache/resume_point.json
# 恢复跑：预期 exit 0、日志显示从断点继续而非从 0 开始
SCHED_DRY_RUN=1 SCHED_RUN_ID=ckpt2 python3 run.py; echo "exit=$?"
```

**常见失败修复：**

| 现象 | 根因/修复 |
| --- | --- |
| ckpt1 exit 0 | 信号到达时任务已经跑完（步太少/signal_after 太短）或根本没处理 SIGTERM；调大 smoke.signal_after_sec，检查信号处理器（用 SDK 即默认正确） |
| ckpt1 超时被 SIGKILL | 当前步不可中断且超过 60s；拆步；信号后不得做大量收尾 IO |
| 运行期未写 state.json | 没用 SDK 或心跳线程没启动；自研入口须自己周期写状态 |
| resume_point 不是对象/为空 | steps 中在每步末正确赋值 dict 并 flush；检查是否写到了别的路径（必须是 cache/resume_point.json 或实例 state） |
| ckpt2 失败/重跑全部数据 | steps 的 `resume` 入参没消费；起始游标错误；幂等性缺失——按断点设计重写循环 |

## 上线检查通过后的生效与画像

1. 五闸全过后写入 `data/jobs.json`（enabled=true），冒烟实测值写入 `data/runtime/profiles.json`
   初始画像；手动 register 会打印各闸结果（exempt 为 4 行），自动检查通过则只在
   decisions.jsonl 留 `auto_admit_ok` 审计记录。
2. serve 运行中：检查通过即纳入调度并出现在 `list`（无需再等热加载）。
3. `list` 核对：任务 `ok=True`、下次触发时刻正确（manual 显示 `-`）。
4. 画像会随正式 run 的实测峰值/平均核数自我修正（P95，8 次窗口）；任务数据规模显著增长后应关注
   `status` 的账本预留/实测对比，必要时更新申报（热加载即生效，也可 register 立即重跑五闸确认）。

## 闸门与调试阶段的对应关系

| 闸 | 阶段1 本地等价自检 | 失败主要归属 |
| --- | --- | --- |
| 闸1 | 肉眼/jq 审 task.json + 试 `python3 -c "import ast;ast.parse(open('run.py').read())"` | 配置/结构 |
| 闸2 | `SCHED_CONTRACT_PROBE=1 python3 run.py` + cat state | 契约接入 |
| 闸3 | `SCHED_DRY_RUN=1 python3 run.py`，计时、观察内存 | 收敛性/资源 |
| 闸4 | 对照 `free -m`、`nproc` 核算申报 | 容量规划 |
| 闸5 | 双终端 TERM→99→恢复跑演练 + 幂等性审计 | 断点设计（最易翻车，重点演练） |

**任何一闸失败后：修任务代码/配置 → 需要时重跑阶段1 等价自检 → 保存文件（调度器立即重检）
或手动 `register <id>`。不得跳过、不得靠反复触发施压。**
