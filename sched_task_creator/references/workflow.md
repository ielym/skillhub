# 子任务开发流程（四阶段）

## 阶段 0 设计

定清楚之后才开始写：

- **id**：`<domain>_<variant>`，字母数字下划线短横，不与现有任务冲突。
- **优先级**：数字越大越优先（默认作业继承任务优先级）。
- **生产者发现逻辑**：什么事件触发、稳定事件标识是什么、业务版本怎么定、如何幂等（同一事件重放得到同一 job_id）。
- **执行者断点与进展**：一个作业的单元是什么，进度怎么归一化，断点数据存什么，幂等键是什么。
- **数据源可回放性**：数据源保留多久、如何重放、如何识别遗漏（写进 task.json `recovery`）。
- **选模板**：daily 生产者 / 批量回溯 / 长期任务，见 [templates.md](templates.md)。

## 阶段 1 本地裸进程调试（`_dev`）

在任务目录外建 `_dev/`，直接跑生产者和执行者，验证业务逻辑：

```bash
SCHED_WORKSPACE=$PWD/_dev SCHED_TASK_ID=my_task SCHED_DEV=1 python3 producer.py
SCHED_DEV=1 SCHED_EVENT_FILE=/tmp/ev.jsonl SCHED_CHECKPOINT_FILE=/tmp/cp.json \
  SCHED_CONTROL_FILE=/tmp/ctl.json SCHED_WORKSPACE=$PWD/_dev python3 run.py
```

必须演练：**断点恢复**（中途 SIGTERM 后重启续跑）+ **协作暂停**（收暂停命令后安全退出）。

## 阶段 2 放入 `tasks/<id>/`，调度器自动守护

```
tasks/<id>/
├── task.json        # 清单（producer_entry / executor_entry / priority / recovery）
├── producer.py      # 生产者（继承 Producer）
├── run.py           # 执行者（继承 ExecutorTask）
└── config.json      # 业务配置（可选）
```

```bash
sched task validate <id>   # 离线校验 task.json
sched serve                # 起调度：自动守护生产者，接收 outbox → 存执行库 → 平缓拉起执行进程
sched status               # 看生产者存活、动态目标、队列
sched job show <job_id>    # 看作业状态与 attempt
```

## 阶段 3 跑通完整流程 + 恢复演练

1. 生产者发布就绪 JSON → `sched job list` 出现 QUEUED。
2. 调度器拉起执行进程 → RUNNING → 进展事件递增。
3. 有限任务完成 → SUCCEEDED；长期任务持续进展参与观测。
4. 演练：`sched job cancel` / 高优保护退让，验证 PAUSING→PAUSED 与断点续跑。
5. 演练：制造资源不足（断网/限流）→ exit 75 → BACKOFF → 恢复后继续。

## 阶段 4 交付验收

只认「调度触发成功」的交付。见 [acceptance.md](acceptance.md)。