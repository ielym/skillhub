# 契约与协议（task.json / 就绪 JSON / 事件 / 退出码 / 暂停 / 检查点）

## 1. task.json（任务清单，唯一真源）

位于 `tasks/<task_id>/task.json`。**不包含**运行数量上限、排队上限、资源申请、生产者限额。

```json
{
  "schema_version": 1,
  "task_id": "arxiv_daily_llm",
  "enabled": true,
  "priority": 60,
  "producer_entry": { "file": "producer.py", "interpreter": "python3", "args": [], "cwd": "." },
  "executor_entry": { "file": "run.py", "interpreter": "python3", "args": [], "cwd": "." },
  "workdir": ".",
  "progress_semver": "1.0.0",
  "recovery": { "replay": "outbox", "retain": "OSS 永久保留", "replay_note": "以日期为稳定事件标识" }
}
```

| 字段 | 说明 |
| --- | --- |
| `task_id` | 稳定任务标识，必须与目录名一致，字母数字下划线短横，1-64 位，不以 `_`/`.` 开头 |
| `enabled` | 启用状态；禁用后调度器不再守护其生产者 |
| `priority` | 数字越大越优先；作业默认继承任务优先级 |
| `producer_entry` | 生产者入口（常驻）；`interpreter` 只能是命令名（不带路径），`file` 必须在任务目录内 |
| `executor_entry` | 执行入口；命令通过参数数组直接启动，不默认经 shell 解释 |
| `workdir` | 工作目录（相对任务目录） |
| `progress_semver` | 进展指标语义版本（业务进展语义版本号） |
| `recovery` | 生产者恢复方式说明（数据源如何重放、保留多久、如何识别遗漏） |

优先级：数字越大越优先。作业默认继承所属任务优先级；业务可在任务授权范围内设置作业级优先级，避免执行程序自行改变全局优先级。

## 2. 就绪 JSON（outbox）

生产者在 `tasks/<task_id>/outbox/<job_id>.json` 发布就绪 JSON。JSON 的出现即表示已就绪，不设业务等待时间。

```json
{
  "schema_version": 1,
  "job_id": "arxiv_daily_llm-<32hex>",
  "task_id": "arxiv_daily_llm",
  "entry_args": [],
  "workdir": ".",
  "input_refs": ["config/daily/2026-10-09.json"],
  "idempotency_key": "LLM:2026-10-09",
  "progress_semver": "1.0.0",
  "env": { "SCHED_CONFIG": "config/daily/2026-10-09.json" }
}
```

| 字段 | 说明 |
| --- | --- |
| `job_id` | 唯一作业标识：由 `job_id_of(task_id, 事件标识, 业务版本)` 确定（SDK 提供）。相同事件重放得到相同 job_id |
| `entry_args` | 入口参数数组（追加到 executor_entry.args 之后） |
| `input_refs` | 必要业务输入引用（如配置文件相对路径） |
| `idempotency_key` | 稳定幂等键 |
| `env` | 安全业务环境参数（**不含**外部资源清单/账号/凭证/资源申请） |

**不携带**外部资源清单，**不携带** CPU/内存/IO 资源申请，**不携带**最大运行/排队数量。

## 3. 执行事件（worker → 调度器）

worker 把事件以 JSON 行追加到 `SCHED_EVENT_FILE`（`runtime/runs/<attempt_id>/events.jsonl`），字段含 `seq`（单调递增）、`kind`、`at` 及事件专属字段。调度器按 `(attempt_id, seq)` 去重。

事件种类：

| kind | 含义 | 关键字段 |
| --- | --- | --- |
| `started` | 已启动（身份握手） | `name`, `progress_semver` |
| `heartbeat` | 进程存活 | — |
| `progress` | 业务推进 | `completed_units`（单调递增）、`has_unfinished`、`stage`、`metric_semver`、`work_units` |
| `external_shortage` | 统一外部不足 | `reason` |
| `control_ack` | 控制确认 | `command_id` |
| `checkpoint` | 检查点已提交 | `commit_seq`、`input_ref` |
| `completed` | 完成（含完成记录） | `record` |

- 心跳说明存活，进展说明推进，**两者分开**。
- 进展必须给单调递增已完成单元数 + 当前未完成工作是否存在 + 业务处理阶段 + 指标语义版本；可另给有效处理耗时/在途时长/工作量计数。
- 等待新输入、业务自行等待、正在处理但没有推进必须区分。
- 业务允许内部重试，但每次外部不足都应及时报 `external_shortage`，不能吞掉失败只发心跳。

## 4. 退出码

| 退出码 | 含义 | 调度器动作 |
| --- | --- | --- |
| **0** | 成功（**必须已提交完成记录 `completed` 事件**） | SUCCEEDED |
| **75** | 统一外部不足 | BACKOFF，到期探测 |
| 其他非 0 | 业务/未知失败 | FAILED（可见回执，不静默删除） |

- 退出 0 但无完成记录 → RECOVERING（待核实，不重复启动）。
- 统一不足事件与随后 75 属于同一失败轮次，不重复收缩。
- 业务逻辑错误**不得**冒充统一不足；永久外部失败若也统一报不足，调度器保持可见并降低探测频率，不因固定重试次数放弃。

## 5. 协作暂停（控制通道）

调度器把暂停命令写入 `SCHED_CONTROL_FILE`（`runtime/runs/<attempt_id>/control.json`）：

```json
{ "command_id": "...", "action": "pause", "job_id": "...", "attempt_id": "...",
  "token": "...", "reason": "高优先级保护退让", "deadline": "ISO" }
```

worker 确认后：停止新工作 → 让当前有界步骤结束或安全取消 → **原子提交检查点** → 发 `control_ack` + `checkpoint` 事件 → 正常退出。调度器由自身发起的 PAUSING 意图识别为 PAUSED，不依赖特殊退出码，也**不默认用 SIGSTOP**。

- 暂停宽限按业务反馈间隔/进行中步骤时长/历史检查点耗时推导，不足以分阶段 TERM→KILL，靠上个已提交检查点 + 幂等执行恢复。
- 生产者**永远不进入**执行暂停流程。

## 6. 检查点

worker 周期提交检查点（不只在收到暂停时）。检查点原子写入 `SCHED_CHECKPOINT_FILE`：

```json
{ "format_version": 1, "input_ref": "<job_id>", "business_version": "1",
  "progress": null, "commit_seq": 7, "data": { "done_ids": [...] }, "saved_at": "ISO" }
```

- 调度器不理解业务检查点内容，也不代替任务恢复业务进度。
- 业务先提交结果，再把完成位置推进到检查点；外部写入与本地进度不能原子提交时，用稳定幂等键 + 可核实提交记录。
- 重复执行未确认单元不得产生重复有效结果（幂等）。

## 7. 生产者协议（SDK `Producer`）

生产者常驻进程，环境变量 `SCHED_TASK_ID` + `SCHED_WORKSPACE`。目录：

- `producer_state/state.json`：`{cursor, unacked}` —— 发现游标与待发布记录，同一原子写。
- `outbox/`：已就绪作业 JSON。
- `receipts/`：调度器回执（`<job_id>.json`）。

流程：

1. 发现一个业务事件后，先把（稳定事件标识 + 输入引用 + 业务版本 + 待发布作业记录）持久化，再推进发现游标（同一事务/原子写）。
2. `publish_all()`：写临时文件 → fsync → 同文件系统原子 rename → fsync 目录，成功后才标记已发布。
3. 未收到接收确认的作业保持可重放；收到回执后清理待发布副本，保留游标与去重记录。
4. 重启时 `replay` 未确认记录并补扫；数据源不支持回放则必须在 `recovery` 说明保留期/回放方式/遗漏识别。

SDK 入口：

```python
from sched_task_sdk import Producer, run_producer, job_id_of

class MyProducer(Producer):
    def discover(self, cursor):          # 返回 (new_cursor, [publish_spec...])
        ...
        return new_cursor, [{"event_id": ..., "business_version": "1",
                             "input_refs": [...], "idempotency_key": ...,
                             "env": {...}, "entry_args": [...]}]

run_producer(MyProducer(), tick_sec=300)
```

## 8. 执行者 SDK（`ExecutorTask`）

```python
from sched_task_sdk import ExecutorTask, run_task

class MyExecutor(ExecutorTask):
    def execute(self):
        done = (self.resume_data() or {}).get("done_ids", [])   # 断点恢复
        for item in work_items:
            do_item(item)                                        # 幂等
            done.append(item.key)
            self.checkpoint({"done_ids": done})                  # 落断点 + 检查暂停
            self.report_progress(len(done), has_unfinished=True, stage="process", work_units=len(done))
        self.complete({"count": len(done)})                      # 完成

run_task(MyExecutor())
```

关键 API：

- `self.checkpoint(data)`：原子提交检查点 + 发 `checkpoint` 事件 + 检查暂停（收到则抛 `PauseRequested`）。
- `self.report_progress(completed_units, has_unfinished, stage, ...)`：发进展事件。
- `self.report_shortage(reason)`：报统一外部不足（抛 `Shortage` → exit 75）。
- `self.complete(record)`：提交完成记录（发 `completed` 事件）。
- `self.resume_data()`：读最近检查点的业务数据。

注入环境变量：`SCHED_ATTEMPT_ID / SCHED_JOB_ID / SCHED_TASK_ID / SCHED_TOKEN / SCHED_RUN_DIR / SCHED_EVENT_FILE / SCHED_CONTROL_FILE / SCHED_CHECKPOINT_FILE / SCHED_WORKSPACE / SCHED_PROGRESS_SEMVER`。