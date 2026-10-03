# 强制规则（铁律 H1–H12 与红线总表）

> 这是 sched 上一切任务工作的**强制规范**：违反任一条铁律不得交付；触碰任一红线即判定
> 交付不合格。流程与清单见 [workflow.md](workflow.md) 与 [acceptance.md](acceptance.md)。

## 铁律（H1–H12，强制，违反任一条不得交付）

- **H1 唯一执行通道**：任务的每一次真实执行都必须由调度器准出触发。禁止 crontab/systemd timer/手工 `python3 run.py`
  跑正式任务、禁止任务内 fork 长驻后台、禁止任务调用 sched CLI 触发自己或别的任务。裸进程执行只允许出现在
  `_dev` 调试阶段（见 [workflow.md](workflow.md)「调试约束」）。
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
