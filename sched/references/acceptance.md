# 调试 · 提交 · 完成 三张强制清单（含约束与验收标准）

> 每张清单都是**准入门**：上一阶段未全部打勾，不得进入下一阶段。证据（命令输出、文件内容、run 记录）
> 必须真实取自当前环境，禁止以"代码里应该没问题""之前跑通过"代替。所有命令在代码根
> （见 SKILL.md 路径约定）或其任务目录内执行。

---

## 清单 A · 调试准入与过程约束（阶段0–1）

### A0 开调之前（设计冻结）

- [ ] 任务 id 合法（`^[a-zA-Z0-9_-]{1,64}$`，非 `_/.` 开头），目录名与 id 一致。
- [ ] 调度类型、interval/窗口、`priority`（按 [workflow.md](workflow.md) 阶段0 分级建议，非默认 0）已定。
- [ ] 资源预算有数字：CPU 核数、内存 MB（来源标注：实测/保守估算）；外部依赖清单
      （代理/VPN/第三方 API 配额等）及对应的错误分类（这些走 101，不做容量申报，见 A0 错误分类表）。
- [ ] 断点字典设计已定：键、粒度（建议单步 ≤20s 工作量）、重放幂等方案。
- [ ] 错误分类表已定：哪些异常 resource（100/101）、哪些 logic（fail）、哪些数据 skip/110/dead_letter。
- [ ] 确认任务有限、可断点。若本质上是"不可中断且无法保证数据完整"的工作，
      只能按 `contract_exempt` + manual 设计，并在交付说明中写明影响（不可抢占、异常后需人工介入）。

### A1 目录与代码（复制骨架后填实）

- [ ] 目录 `tasks/<id>_dev/`（调试一律 `_dev` 后缀），内含 task.json、run.py；不建在其他任务目录内。
- [ ] 入口继承 `SchedTask`，`steps(resume)` 从断点游标开始；每工作单元末 `resume_point=...; flush()`。
- [ ] `SCHED_DRY_RUN=1` 路径**零真实副作用**：上传/写库/发消息/付费调用全部短路为 print/模拟返回。
- [ ] 单条数据异常被局部捕获并 `skip_item`，不炸整轮；无裸 `except: pass` 吞异常。
- [ ] 无 `while True` 常驻；无任务内自触发/自调度；无跨任务 import/读他任务文件。
- [ ] task.json 无黑名单 env 键、无密钥、无绝对路径/`..`；解释器为命令名。
- [ ] 密钥（若有）放任务目录内独立配置文件且 `chmod 600`，代码做缺失时显式报错。

### A2 本地裸进程调试（不经调度器，零历史污染）

```bash
cd <代码根>/tasks/<id>_dev
export SCHED_WORKSPACE=$PWD SCHED_RUN_ID=local
# 1) 契约探针：exit=0，state 含 status/current_step/schema_version/resume_point
SCHED_CONTRACT_PROBE=1 python3 run.py; echo "probe_exit=$?"
cat cache/runs/local/state.json 2>/dev/null || cat cache/state.json
# 2) dry 全流程：exit=0，计时收敛，无真实副作用
SCHED_DRY_RUN=1 python3 run.py; echo "dry_exit=$?"
# 3) 断点演练（两条命令之间在另一终端对进程组发 kill -TERM）
SCHED_DRY_RUN=1 SCHED_RUN_ID=ckpt1 python3 run.py   # 预期退出码 99
cat cache/resume_point.json                          # 断点内容=已完成位点
SCHED_DRY_RUN=1 SCHED_RUN_ID=ckpt2 python3 run.py   # 预期 exit=0 且从断点继续
```

- [ ] 探针 exit=0 且四字段齐全（等价闸2）。
- [ ] dry 全流程 exit=0、在预期时长内收敛、副作用全部关断（逐条核对外部写动作清单）。
- [ ] **断点演练**：TERM 后退出码 99；resume_point 非空且是已完成位点；恢复跑日志/产物证明
      **从断点继续、无重复处理**（幂等）；最终 success。
- [ ] **错误注入**（至少各演一次）：模拟资源异常（拔网/错误代理/临时改限流）→ 任务以 100/101 快速退出、
      不死等；模拟逻辑异常 → `raise ValueError("LOGIC: ...")`（配合 logic_regex）以 exit 1 +
      state.last_error.category=logic 退出；喂一条坏数据 → skip_item 落 pending_skipped 且本轮继续；
      需要二刷时落跳过项后以 110 退出。
- [ ] 心跳：观察 dry 运行期间 `cache/runs/<run_id>/state.json` 的 mtime 每 ≤30s 刷新（SDK 自动）；
      最长自然步耗时显著小于 heartbeat.timeout_sec。
- [ ] 日志量可控：单 run stdout/stderr 不产生无界输出（调度器侧每文件截断 32MB，但作者仍应控量）。

### A3 调试期间约束（红线复述）

- [ ] 不在正式任务目录调试；不手工触发正式任务。
- [ ] 需要调度器介导（队列/准出/二刷/画像）时才把任务放进 `tasks/<id>_dev/`（调度器会自动跑
      五道上线检查，也可 `register <id>_dev` 立即检查）；`run <id>_dev` 是**真实执行**，
      副作用开关已由代码保证关断或目标为安全测试资源。
- [ ] 机器高负载时不放入新任务/不跑 register（闸门会串行拉起最多 4 个进程，冒烟预算取整机内存）。
- [ ] 闸失败只改任务，不改 `sched/` 源码、不手改 `data/runtime/`。

---

## 清单 B · 上线提交门禁（阶段2）

### B1 上线前最终自检

- [ ] cgroup 自检输出 `cgroup OK`（命令见 [deployment.md](deployment.md) §1）；若 DEGRADED：已评估申报可信度并在
      交付说明标注，资源敏感型任务暂缓交付。
- [ ] runtime.user 在目标机存在（默认 sched-run）；多使用者使用各自独立用户。
- [ ] 正式 task.json 字段全部显式填实：priority、schedule、resources（非 0、有依据）、heartbeat、
      smoke、error_rules、runtime.user；`contract_exempt` 明确取舍；**`retry` 段（delay_sec/
      max_attempts/not_after）按任务时效与止损要求显式设计**，不盲目用默认值（默认=立即重排、
      不放弃、无时效）。
- [ ] `resources.memory_mb` ≥ dry/real 冒烟观测峰值；CPU 申报 ≥ 观测平均核数；申报均不超整机
      （`free -m`、`nproc`）。task.json 中**只有 CPU/内存**——代理/配额等外部资源不写任何容量字段。
- [ ] 外部资源失败路径已设计：识别错误（代理失效/429/配额/连接失败）后快速 `sys.exit(101)`，
      任务内不 sleep 死等，调度器立即重排队、按任务 retry 段控制节奏。
- [ ] 清单 A 全部打勾。

### B2 上线（五道闸，自动执行；无需手动注册）

把任务目录放到 `tasks/<id>/`（从 `_dev` 改名/复制为正式 id），serve 最迟 30s 内自动开检；
不想等可手动立即检查：

```bash
cd <代码根>
python3 -m sched register <id>
```

- [ ] 5 道闸（exempt 为 4 道）全部通过；未通过时按 [gates.md](gates.md) 在本地修复并保存文件
      （指纹变化即自动重检；闸失败不做定时重试），或修复后重跑 register/管理台「导入任务」。
- [ ] 通过后 `python3 -m sched list` 中该任务 `ok=True`；auto 任务 `next_run_at` 正确。
  自动检查的未通过原因可在 `sched status`、管理台"等待上线检查"区或 `data/runtime/admission.json` 看到。
- [ ] serve 未运行时任务不会被检查：确认交付时 serve 的启动方式（systemd/`serve` 命令）。

### B3 提交约束（配置与代码卫生）

- [ ] 只提交任务代码与 task.json；`cache/`、`results/` 运行时产物不提交（保持干净工作区）。
- [ ] 不向任务目录放与本任务无关的文件；不修改其他任务任何文件（隔离铁律）。
- [ ] **不提交对 `sched/` 调度器源码的改动**；如确有调度器缺陷需求，走独立变更流程：
      先把既有代码/配置推送远端 git 再改，不得借子任务交付夹带。
- [ ] 不手工改 `data/jobs.json` 来"上线"任务；准入只能由五道闸自动检查或 register 命令完成。

---

## 清单 C · 完成定义（DoD，阶段3 交付验收）

### C1 正式调度触发成功（唯一有效的成功证据）

- [ ] 任务由 **serve 按 schedule 触发**（auto 类型由 engine 按 interval 给机会；manual 类任务由 `run` 或管理台「立即运行一次」入队后经准出执行），
      终态 `success`（或 `schedule_skip` — 任务自治时机判断"当前不该跑"、SDK reschedule 重排队）、退出码 0 或 102。
- [ ] `outputs.expect` 所列文件全部真实存在且内容非空、格式正确、无占位符。
- [ ] run 记录完整：`data/runs/<id>.jsonl` 有对应记录，started/finished/duration 合理，
      账本 est_mem/est_cpu 与观测同量级（`status` 对照 reserved vs actual）。
- [ ] **正式历史无 manual 调试记录**（manual 类型任务除外，其 trigger 本就是 manual；
      auto 任务的历史可能有 auto/schedule_skip/second_pass）。

```bash
# 历史洁净核对（不应出现调试期的 manual 触发，_dev 任务不应出现在正式列表）
python3 -m sched list
grep -h '"job_id"' data/runs/<id>.jsonl | tail -5   # 或直接读 jsonl 核对 trigger 字段
```

### C2 恢复与容错能力（取 _dev 证据，正式任务不做破坏演练）

- [ ] 抢占恢复：_dev 上 TERM→99→断点→恢复跑 success 的证据留存（输出/日志），重放幂等已核对。
- [ ] 资源退让：资源错误注入后 run 落 `resource` 并**立即重入队**（无全局退避）、最终成功
      （资源持续不足时持续排队属预期）；等待期间任务未被终止、未丢失。
- [ ] retry 段行为：`delay_sec>0` 时等待项带 not_before、到点才准出；`max_attempts=N` 时
      第 N 次仍失败落 giveup 转人工；`not_after`（绝对/每日时刻）过期落 giveup_expired；
      新计划触发后尝试计数重新从 1 开始。可用故障注入在 _dev 上逐项验证。
- [ ] 外部资源退让（如任务依赖代理/第三方 API）：故障注入后任务以 101 快速退出、run 落 `resource`
      并按 retry 段立即/延时重入队、最终成功（或到上限/时效转人工，属预期）；等待期间任务未被
      终止、未丢失。调度器不为这类资源设容量，不存在"配额开关"。
- [ ] 数据风险（如有跳过面）：110 → `second_pass` 重入队 → pending_skipped 被消费补跑 → success；
      无法补跑的条目已 dead_letter；连续 3 轮仍 110 的转人工路径已知悉。
- [ ] 逻辑错误：注入逻辑异常时落 `failed`（不重试），等待人工，不产生脏数据。
- [ ] 崩溃恢复认知：serve 重启时在途 run 记 interrupted 并自动携断点重入队（exempt 任务不自动恢复，
      需人工处理）——交付说明中已告知运维。

### C3 资源与稳定性

- [ ] 正式首跑后画像更新正常（`data/runtime/profiles.json` 中该任务样本增长，实测峰值非 0；
      若恒为 0，先查 cgroup 委派，不得带疑交付）。
- [ ] 内存实测峰值 < memory.max（预估×2.5），无 OOM；未观察到持续超限退让；如有偏差已调整 task.json 申报。
- [ ] 单步耗时/心跳留有安全余量（最长步 ≪ heartbeat.timeout_sec，且 ≪40s 抢占宽限）。
- [ ] 时间窗任务：窗口边界行为已确认（allow_overrun 取舍符合业务；不会因窗口收口造成意外中断损失）。
- [ ] max_instances/overflow 与触发频率匹配，不产生无意义的 skip 洪峰或无限 WQ 堆积。

### C4 清理与移交

- [ ] `_dev` 调试任务彻底清除（**CLI 无取消注册命令**，按下列顺序手工清理）：
      1. 若 serve 在跑：先把 `data/jobs.json` 里该条目的 `enabled` 置 false（≤30s 生效，停止自动触发），
         然后进行第 2 步（热加载会在条目删除后移除）；
      2. 编辑 `data/jobs.json` 删除 `<id>_dev` 整个条目（**唯一允许手工编辑的 data 文件**，改前可备份）；
      3. 删除 `tasks/<id>_dev/` 整个目录；
      4. 删除 `data/runs/<id>_dev.jsonl` 与 `data/runs/<id>_dev/` 日志目录；
      5. ≤30s 后 `list` 确认 _dev 消失、WQ 中无其残留排队项。
      严禁手改 `scheduler_state.json` / `active.json` / `*.jsonl` 来"清理"。
- [ ] 任务目录无 cache/results 调试残留（或已确认为正式首跑产物）。
- [ ] 交付说明（向需求方/运维口头或工单均可）至少包含：调度节奏、优先级与理由、资源申报数字与依据、
      外部资源依赖与 101 失败处理（用什么账号/协议由任务自负；retry 段的间隔/上限/时效取值与理由）、
      断点/幂等设计、错误分类与二刷策略、exempt 与否、cgroup 状态、已知风险/阻塞项。
- [ ] 运维侧确认：serve 常驻方式、sched-run 用户、settings 参数无人为乱改。

### C5 一票否决项（出现任一，不予验收）

1. 五道闸未全过，或靠改调度器/改数据/假探针绕过。
2. 正式成功证据来自手工执行而非调度触发（manual 类型除外）。
3. 抢占后不能从断点幂等续跑（含"全量重跑但恰好结果相同"）。
4. 资源申报为 0/虚低/无依据，或 cgroup DEGRADED 且未标注。
5. 单条坏数据可卡死/击穿整任务，无 skip/隔离手段。
6. 正式历史混入 manual 调试记录，或 _dev 任务/目录/日志残留。
7. 任务常驻、自调度、跨任务共享、密钥入 task.json，任一红线被触碰。
8. 交付物缺失/占位/为空却报成功；交付说明缺关键信息或阻塞项未标注。
