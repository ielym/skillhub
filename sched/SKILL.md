---
name: sched
description: sched 优先级抢占式任务调度器的使用规则与子任务创建规范。当用户要在 sched 上新建、注册、调试、交付一个被调度子任务，或咨询任务门禁（五道闸）、资源申报、优先级/抢占、断点续跑、错误码、软资源、验收标准时使用。
---

# sched（任务调度器使用规则与子任务创建规范）

本 skill 是在 **sched**（优先级抢占式任务调度器）上**创建、调试、注册、交付子任务**的强制规范。
目标：高优任务绝对优先执行完毕、资源有限不打爆机器、所有任务最终都能被正确执行。

**路径约定（全文统一）**：

- **代码根**：scheduler 仓库的 clone 目录（`tasks/`、`data/` 的父目录；默认取 `sched` 包所在
  目录的上一级，可用环境变量 `SCHED_HOME` 覆盖）。
- **skill 目录**：本 skill 的安装目录（模板与参考文件在其 `assets/`、`references/` 下）。

**核心理念（必须先建立认知）：**

| 维度 | sched 的规则 |
| --- | --- |
| 调度依据 | **优先级决定一切**：高优等待可抢占低优在跑任务 |
| 任务形态 | **必须有限、可断点**；禁止常驻，长任务分段提交断点 |
| 准入 | **五道闸**：静态→契约→冒烟→容量→断点，缺一不可 |
| 资源 | 必须申报 CPU/内存/软资源，cgroup 硬限 + 账本 + 画像 |
| 失败处理 | 统一错误码，资源错误退让重试、逻辑错误转人工、110 二刷 |
| 任务基类 | **强制 SDK 契约行为**：心跳、断点、99 退出、错误分类 |
| 手动任务 | 不可恢复任务只能 manual（`contract_exempt`），其余 manual 触发**同样可被抢占** |

## 适用 / 不适用

- **适用**：在代码根上创建新的被调度子任务；为已有任务改配置/排障/做交付验收；判断一个任务能否/如何纳入调度。
- **不适用**：调度器核心源码（`sched/` 包）本身的重构开发（走需求审查流程，不属于子任务创建）。
- **铁律：子任务作者只在 `tasks/<id>/` 自己的目录内工作，禁止改 `sched/` 包源码、禁止手改 `data/runtime/` 内文件。**

## 部署前置（任何注册动作之前先确认）

在代码根执行所有 CLI：`cd <代码根>`，调用形式 `python3 -m sched <cmd>`
（或使用安装好的 `sched` 命令，等价；用 `SCHED_HOME` 可指定其它调度器根）。

1. **serve 常驻**：`python3 -m sched serve`（生产建议由 systemd 托管）。`register/run` 是独立 CLI 进程，
   只写注册表与入队；**真正的运行只由 serve 的准出循环决定**。无 serve 时任务注册后不会执行。
2. **运行用户存在**：task.json 的 `runtime.user`（默认 `sched-run`）必须是系统已有用户，否则闸2起进程即失败。
   部署：`useradd -r -m -s /usr/sbin/nologin sched-run`；多使用者应各自独立系统用户，不要共用。
3. **cgroup v2 硬边界在线（关键，静默失效不报警）**：注册的冒烟实测、内存/CPU 硬限、超限退让、OOM 归因、
   画像回流全部依赖 run cgroup 内存在控制文件。注册前用下面一条命令自检（root）：

   ```bash
   d=/sys/fs/cgroup/sched/_skill_probe
   mkdir -p "$d" && test -f "$d/memory.max" && echo "cgroup OK" || echo "cgroup DEGRADED"
   rmdir "$d" 2>/dev/null
   ```

   输出 `cgroup DEGRADED` 时，不得交付资源敏感型任务；先在调度子树委派控制器后再注册：
   `echo '+memory +cpu' > /sys/fs/cgroup/sched/cgroup.subtree_control`（root，一次性，部署修复）。
   降级状态下冒烟实测峰值恒为 0，**闸4 将完全依赖任务自报内存，申报虚低即打爆机器**。

## 核心操作命令

```bash
python3 -m sched list                 # 已注册任务、ok 状态、下次触发
python3 -m sched register <id>        # 跑五道闸并注册（唯一准入入口，闸不过即拒）
python3 -m sched run <id>             # 手动入队（只入队！是否/何时跑由 serve 准出决定；无 --dry-run 选项）
python3 -m sched status               # WQ 等待数、运行数、账本预留/实测、软资源令牌
python3 -m sched set-soft <name> <n>  # 配置软资源容量（如 proxy 代理并发上限）
python3 -m sched serve                # 常驻调度循环（热加载周期 30s）
python3 -m sched serve --web          # 同时启动内嵌 Web 管理台（127.0.0.1:8799）
```

Web 管理台（`serve --web`）：总览/队列/历史日志/决策/画像只读监控，外加与 CLI 等价的
触发入队、启停、set-soft、新建任务、在线改码与**逐闸 SSE 注册**；写操作与调度循环共享同一
serve 进程（不存在独立 web 进程）。默认绑 127.0.0.1。公网暴露必须配 `web.auth_token`
（Basic Auth），或显式 `web.allow_public_no_auth=true`（等同无密码 RCE 面板，风险自负），
否则 serve 拒启动；完整能力/安全边界见 [configuration.md](references/configuration.md) §4.1。

注意：**没有**取消注册命令、**没有** kill 命令、`run` **没有** `--dry-run` 开关。清理调试任务与
dry-run 的正确姿势见下文「调试约束」与 [acceptance.md](references/acceptance.md)。

## 铁律（H1–H12，强制，违反任一条不得交付）

- **H1 唯一执行通道**：任务的每一次真实执行都必须由调度器准出触发。禁止 crontab/systemd timer/手工 `python3 run.py`
  跑正式任务、禁止任务内 fork 长驻后台、禁止任务调用 sched CLI 触发自己或别的任务。裸进程执行只允许出现在
  `_dev` 调试阶段（见「调试约束」）。
- **H2 任务必须有限且可断点**：每个 run 要能在有限时间内跑完或进入可等待状态；长流程必须切成多个步骤，
  每步落 `resume_point` 并 `flush()`；收到 SIGTERM 后在宽限期（40s）内保存断点并以 **99** 退出。
  **禁止 `while True` 常驻、禁止不可中断的长事务。**
- **H3 可抢占性只由优先级决定**：不存在、也不允许自造任何"不可抢占/豁免"开关。唯一例外是
  `contract_exempt=true`（无法保证断点数据完整性的任务），它被强制只能 `schedule.type=manual`，
  且不得用于可恢复任务来逃避抢占。
- **H4 必须走 SDK 契约**：任务继承 `sched_task_sdk.SchedTask`，实现 `steps(resume)` 生成器，入口调
  `run_task()`。不允许用裸脚本绕过契约探针/心跳/断点/错误分类行为。
- **H5 任务间完全隔离**：一任务一目录 `tasks/<id>/`；代码各自一份，**禁止跨任务 import、禁止引用他任务目录文件、
  禁止共享 cache/results/配置/可变外部资源**；跨任务输入只能是只读稳定源。宁可复制，不许共享可变物。
- **H6 资源必须如实申报**：`resources.cpu/memory_mb/soft` 必填且有依据（冒烟实测或保守上限）；声明或实测超整机
  上限、以及两者都为 0（预估未知）闸4 一律拒绝。不得靠低报抢资源——实测持续超限会被优雅抢占，OOM 会被杀并重试。
- **H7 错误必须真实分类上报**：逻辑错误在 steps 内 `raise ValueError("LOGIC: ...")` 并在 task.json
  `logic_regex` 声明 `"LOGIC:"`（exit 1 + `last_error.category=logic`，转人工不重试）；
  资源不足 `sys.exit(100/101)`、数据风险 `sys.exit(110)`（先 flush 现场），**不要在任务内 sleep 死等资源**；
  未分类异常（unclassified）一律按资源错误重试，逻辑错误不分类会被无限重试，后果作者自负。
  **注意：不要在 steps 内调用 `task.fail()` 后 return——会被 SDK 覆盖成 success（实测陷阱，见契约参考）。**
- **H8 单条坏数据不得卡死整体**：捕获单条数据异常 → `skip_item(id, reason)` 落 pending_skipped → 本轮继续；
  需要二刷时写好跳过项后以 110 退出，由调度器 `second_pass` 重入队补跑；确认无救的条目 `dead_letter()`。
- **H9 心跳义务**：运行期必须周期性更新实例级 state.json（SDK 心跳线程每 30s 自动完成）；自研非 Python 入口
  须自己写心跳。超过 `heartbeat.timeout_sec`（默认 120s）无更新即判卡死被杀。任何单步耗时不得逼近超时阈值。
- **H10 调试与正式彻底隔离**：一切调试在 `<id>_dev` 任务或本地裸进程上进行；正式任务**从不手动 run**，
  其历史中只能有 interval/once（含 second_pass 恢复）触发记录；调试完按清单清除全部痕迹。
- **H11 无密钥、可执行面最小**：task.json 的 `env` 禁止放密钥（任务进程间同机可读 `/proc/<pid>/environ`），
  密钥放任务目录内 600 权限配置文件；`env` 不得使用黑名单键（`LD_PRELOAD/PATH/...`，见契约参考）；
  入口解释器只能是命令名（不带路径），入口/cwd/产物路径不得含 `..` 或绝对路径。
- **H12 调度器源码不动、数据文件不手改**：需要修改 `sched/` 包行为时提需求，不得在任务侧 monkey-patch；
  `data/` 下除调试清理时按流程编辑 `jobs.json` 外，其余文件（scheduler_state.json、active.json、runs/*.jsonl、
  decisions.jsonl）一律禁止手工修改。

## 标准工作流（四阶段，每阶段有准入/准出）

```
阶段0 设计        → 阶段1 本地调试(_dev/裸进程) → 阶段2 注册门禁(register 五道闸) → 阶段3 交付验收
```

**阶段 0 · 设计（不写运行代码前先定 5 件事）**

1. 任务 id：`^[a-z0-9_-]{1,64}$`，不以 `_`/`.` 开头；语义化、与目录同名。
2. 调度类型与优先级：interval/once/manual；priority 0–100（越高越能抢占别人、也越早被准出）。
   按业务刚性给级，**一律禁止默认 0 凑合**：延迟可容忍的批处理 10–30，常规 40–60，强时效 70–90，
   必须尽快完成的保底任务 90+。同优先级 FIFO 排队，互不抢占。
3. 资源预算：单机内存/CPU 占用保守上限；是否使用软资源（代理并发、API QPS 配额等）及每 run 占用令牌数。
4. 断点粒度：`resume_point` 的键设计（如 `{"date": "2026-10-03", "chunk": 12}`），保证从断点重放**幂等**。
5. 错误分类表：哪些异常算资源（可重试）、哪些算逻辑（转人工）、哪些数据进 skip/二刷；写进 task.json
   `error_rules` 正则与代码显式分类。

**阶段 1 · 本地调试（不经过调度器，首选路径，零历史污染）**

在任务目录内直接以裸进程跑（SDK 自动支持这些环境变量）：

```bash
cd <代码根>/tasks/<id>_dev
export SCHED_WORKSPACE=$PWD SCHED_RUN_ID=local
# 契约自检（闸2 的同款探针）：必须 exit 0 并写出合法 state.json
SCHED_CONTRACT_PROBE=1 python3 run.py
# dry 全流程：必须跳过一切真实副作用（上传/写库/发消息/付费调用只 print）
SCHED_DRY_RUN=1 python3 run.py
# 断点演练：dry 跑起来后另开终端 kill -TERM <pid>，验证 exit 99 + resume_point 落盘，再跑一次验证幂等续跑
SCHED_DRY_RUN=1 python3 run.py
```

需要调度器介导验证（队列、准出、画像、二刷等）时才注册 `<id>_dev` 并 `python3 -m sched run <id>_dev`。
**注意 `run` 无 dry-run：会真实执行**，副作用只能靠任务代码内的自有开关（读 `SCHED_DRY_RUN` 或 _dev 专用配置）关断。
完整调试规则见 [acceptance.md](references/acceptance.md)。

**阶段 2 · 注册（五道闸，唯一准入入口）**

```bash
cd <代码根>
python3 -m sched register <id>
```

`register` 会**真实串行拉起最多 4 次任务进程**（探针→冒烟→打断→恢复），实测单任务约 10–20s
（随冒烟步数增长），且冒烟进程的内存预算取整机上限、**不感知 serve 在跑任务**——禁止在机器高负载时
并发注册多个重任务。
五道闸逐条判定标准、失败原因与修复动作极其严格，注册前必须通读：[gates.md](references/gates.md)。
闸不过时修任务后重跑 register；**严禁修改调度器代码或数据文件来"绕过"闸门。**

**阶段 3 · 交付验收（完成定义，DoD）**

正式任务只接受**调度触发**的成功作为验收证据，`manual` 记录不算。12 项验收逐条打勾、证据留存，
清单见 [acceptance.md](references/acceptance.md)（含断点/错误分类/二刷/心跳/资源复核/_dev 清理/历史洁净）。

## 任务模板（按场景选，复制后改名，禁止直接注册模板本体）

**阶段 0 先选模板再动手**，六套已验证模板的场景对照见 [templates.md](references/templates.md)：

- [assets/skeleton/](assets/skeleton/) — 最小骨架（游标断点/skip/二刷/原子交付物）
- [01_interval_crawler](assets/templates/01_interval_crawler/) — 定时采集：时间窗+软资源代理+分页断点+101/110
- [02_once_migration](assets/templates/02_once_migration/) — 一次性迁移回填：once、ID 分片、逻辑错误转人工
- [03_manual_report](assets/templates/03_manual_report/) — 手动按需导出：manual 但可抢占、批次断点续跑
- [04_exempt_atomic](assets/templates/04_exempt_atomic/) — 不可断点原子动作：exempt+manual（极慎用）
- [05_nightly_batch](assets/templates/05_nightly_batch/) — 夜间大批量：跨夜窗、低优先级、二维分片细断点

字段、退出码、状态文件、SDK API 的完整参考见 [contracts.md](references/contracts.md)；
settings.json 全参数、CLI 确切行为、调度时刻语义、部署步骤见 [configuration.md](references/configuration.md)。

## 调度语义（写代码前必须内化）

- **抢占流程**：高优等待且资源缺口无法由空闲满足 → 调度器向最低优先级在跑任务发 SIGTERM → 任务在**当前步结束后**
  保存断点退出 99 → 资源释放给高优 → 被抢任务携断点自动重入队（60s 豁免期内不再被抢）。40s 不退出才 SIGKILL，
  被判 `preempt_failed` 转人工。因此：步要短、断点要在每步末落盘、SIGTERM 只置位不强退（SDK 已托管）。
- **排队与退让**：资源不足的任务留在全局队列 WQ，不失效、不超时报废；同优 FIFO，等待超 1h 触发饿死保护。
  资源错误（100/101）自动指数退避重入队（300s→600s→1200s→2400s→封顶 3600s，默认无限重试）。
  任务侧要做的是**快速明确地失败**，把等待让给调度器，而不是占着进程死等。
- **见缝插针**：大任务暂时放不下时，能放进剩余资源的小任务会先跑。任务启动开销应尽量小、申报应尽量准。
- **手动触发不是特权**：非 exempt 的 manual 任务与自动任务遵守同一套抢占、心跳（超时阈值放宽 2 倍）、超限规则。
- **时间窗收口会终止任务且不自动续跑**：`allow_overrun=false`（默认）时，一旦运行越过窗口终点
  （`end_time`，支持跨天窗），调度器立即对进程组发 SIGTERM（cancel 宽限仅 **10s**），
  终态记 `killed` 并**转人工，不携断点自动重入队**（这是收口语义，区别于抢占的 40s+99 续跑）。
  因此运行时长不可控的任务必须设 `allow_overrun=true`，**不要用窗口收口当"兜底杀"**，
  也不要把必须跑完的任务放进明显小于其运行时长的窗口。

## 排查速查

| 现象 | 含义/处理 |
| --- | --- |
| `register` 报 gate2 契约自检失败 | 探针进程非 0 退出，或 state.json 缺 `status/current_step/schema_version/resume_point`；裸跑 `SCHED_CONTRACT_PROBE=1 python3 run.py` 复现 |
| gate3 冒烟超时 | dry 路径没在 `smoke.max_runtime_sec` 内收敛；检查死循环/网络硬等待，dry 必须无真实 IO 等待 |
| gate4 预估未知拒绝 | 声明 0 且 cgroup 实测 0；先按保守上限填 `resources.memory_mb`，并排查 cgroup 是否降级 |
| gate5 打断后不是 99 / 恢复跑失败 | 步太长、SIGTERM 后没落断点、或恢复未消费 resume_point 导致重跑；缩短步长，每步末 flush |
| run 状态 `resource` | 100/101 或未分类错误，退避中；看 `data/runs/<id>.jsonl` 的 reason 与 stderr，资源类属正常退让 |
| run 状态 `preempted` | 正常的高优先抢，断点已存，自动重入队；频繁被抢说明优先级给低了或申报偏大 |
| run 状态 `preempt_failed` | 40s 内没退出被 SIGKILL，断点未确认，转人工；必须缩短步长/优化信号响应 |
| run 状态 `failed` | 逻辑错误或交付物缺失；交付物缺失查 outputs.expect 路径（相对任务目录） |
| `killed` 且原因含心跳超时 | 单步阻塞超 heartbeat.timeout_sec；拆小步、保持 SDK 心跳（勿在心跳线程外长期阻塞 IO） |
| `status` 里 waiting 长期不动 | `status` 查账本余量/软资源令牌；容量为 0 的软资源会永久饥饿，需 `set-soft` 配置 |
| list 中任务 `ok=false` | task.json 非法或入口缺失；修复后下次热加载（≤30s）自动恢复，无需重新 register |

## 红线总表（任一触发即判定交付不合格）

1. 正式任务被手工执行/常驻/自调度，或由 cron 等调度器之外的通道触发（H1）。
2. 不可断点、SIGTERM 后不能 99 退出的任务没有标 `contract_exempt`，或可恢复任务滥用 exempt（H2/H3）。
3. 裸脚本不继承 SDK、运行期不写心跳（H4/H9）。
4. 跨任务 import/共享文件/共享配置/互相依赖产物（H5）。
5. 资源申报为 0、虚低、无依据（H6）。
6. 逻辑错误未显式分类，指望调度器重试"碰运气"（H7）。
7. 单条数据异常导致整 run 长卡或整体失败而不走 skip/110（H8）。
8. 在正式任务上调试；`_dev` 残留；正式历史出现 manual 记录（H10）。
9. task.json/env 含密钥或黑名单键；路径绝对化/含 `..`（H11）。
10. 修改 `sched/` 源码或手改 `data/runtime/` 文件以绕过门禁（H12）。
11. 注册闸未全过即宣布完成；用"我本地跑通过"代替五闸与调度触发验收。
12. cgroup 降级状态下交付资源敏感型任务，且未在交付说明中标注。

参考文件：

- [references/gates.md](references/gates.md) — 五道闸逐条判定标准、实证方法、失败修复（注册前必读）
- [references/contracts.md](references/contracts.md) — task.json 字段、SDK API（含实测陷阱）、环境变量、状态文件布局、退出码与错误分类、抢占/心跳/断点契约、软资源
- [references/configuration.md](references/configuration.md) — settings.json 全参数、CLI 确切行为与缺项、调度时刻语义、数据/日志布局、首次部署步骤
- [references/templates.md](references/templates.md) — 六套场景模板选型索引与使用要点
- [references/acceptance.md](references/acceptance.md) — 调试/注册提交/交付验收三张强制清单
- [assets/](assets/) — skeleton 与 5 个场景模板（每个含 task.json + run.py，均已验证）
