# 契约与协议（task.json / 就绪 JSON / 事件 / 退出码 / 暂停 / 检查点）

## 1. task.json（任务清单，唯一真源）

位于 `tasks/<task_id>/task.json`。**不包含**运行数量上限、排队上限、资源申请、生产者限额。

```json
{
  "schema_version": 1,
  "task_id": "arxiv_daily_llm",
  "enabled": true,
  "priority": 60,
  "producer_entry": { "file": "producer.py", "interpreter": "python3", "args": [] },
  "executor_entry": { "file": "run.py", "interpreter": "python3", "args": [] },
  "workdir": ".",
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
| `job_priority_cap` | 可选。作业级优先级授权上限（≤ 任务优先级，只能收窄）；缺省 = 任务优先级。作业 priority 超出被钳制到该上限 |
| `recovery` | 生产者恢复方式说明（数据源如何重放、保留多久、如何识别遗漏） |

入口对象（`producer_entry`/`executor_entry`）统一支持可选 `cwd` 字段：入口工作目录（相对任务目录，必须落在任务目录内；缺省 `.`；就绪请求的 `workdir` 在此基础上再解析）。

优先级：数字越大越优先。作业默认继承所属任务优先级；业务可在任务授权范围内（`job_priority_cap`，缺省即任务优先级）设置作业级优先级，避免执行程序自行改变全局优先级。

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
  "env": { "SCHED_CONFIG": "config/daily/2026-10-09.json" }
}
```

| 字段 | 说明 |
| --- | --- |
| `job_id` | 唯一作业标识：由 `job_id_of(task_id, 事件标识, 业务版本)` 确定（SDK 提供）。相同事件重放得到相同 job_id |
| `entry_args` | 入口参数数组（追加到 executor_entry.args 之后） |
| `input_refs` | 必要业务输入引用（如配置文件相对路径） |
| `idempotency_key` | 稳定幂等键（**必填非空**：缺失/空串的请求按无效载荷隔离；SDK 对未显式提供的 spec 以稳定事件标识兜底） |
| `schema_version` | 协议版本（**必填**：缺失的请求按无效载荷隔离） |
| `priority` | 可选。作业级优先级（数字越大越优先），但**不得高于任务授权上限**（`job_priority_cap`，缺省=任务优先级；超出被钳制，避免执行程序自行改变全局优先级）；未提供时继承任务优先级 |
| `env` | 安全业务环境参数（**不含**外部资源清单/账号/凭证/资源申请；接收端对疑似凭证键名告警） |

**不携带**外部资源清单，**不携带** CPU/内存/IO 资源申请，**不携带**最大运行/排队数量。

`job_id_of` 实现算法（SDK `producer.py`）：

```python
digest = sha256(f"{task_id}\0{event_id}\0{business_version}".encode()).hexdigest()[:32]
job_id = f"{task_id}-{digest}"
```

即事件标识与业务版本以 `\0` 分隔拼接后取 sha256 前 32 位十六进制，最终 job_id = `f"{task_id}-{digest}"`。同一 (task_id, event_id, business_version) 重放/补扫得到同一 job_id，是全链路幂等去重的依据。

## 3. 执行事件（worker → 调度器）

worker 把事件以 JSON 行追加到 `SCHED_EVENT_FILE`（`runtime/runs/<attempt_id>/events.jsonl`），字段含 `seq`（单调递增）、`kind`、`at` 及事件专属字段。调度器按 `(attempt_id, seq)` 去重。

事件种类：

| kind | 含义 | 关键字段 |
| --- | --- | --- |
| `started` | 已启动（身份握手） | `name`（可选，纯可观测） |
| `progress` | 业务推进 | `completed_units`（必填，单调递增） |
| `error` | 错误（含资源不足） | `reason`（必填：错误类型 + 资源标识） |
| `done` | 成功完成（含完成记录） | `record`（可选） |
| `ack` | 确认调度命令 | `command_id`（必填） |

- 每行事件自带 `job_id` / `attempt_id` 归属字段（SDK 从注入环境自动携带），脱离 run_dir 也能定位来源。

- 存活改由**调度器自观测**（进程树 + CPU + 事件间隔）。
- 进展必须给单调递增已完成单元数（`completed_units`）；耗时与资源消耗由调度器自统计，任务不预估。
- 断点是**任务可选实践**：调度器不规定文件名/格式/提交时机/存在性，仅提供 run_dir 空间；若任务写了断点文件，调度器原样透传（便利而非强制），恢复正确性由任务幂等提交兜底。
- `name` 字段由任务业务在构造执行者时自己命名（如 `ExecutorTask(name=f"arxiv_fetch_{topic}_{date}")`），纯可观测，调度器不消费决策。
- **资源错误有限重试纪律（R3/R9）**：单次外部操作（一次请求/一次 CLI 调用）失败后原地重试最多 2 次（固定短间隔 3s，重试落日志，仅过滤瞬时抖动），仍失败立即把错误连同错误类型与资源标识一起上浮（`error` 事件 + exit 75），由调度器统一决定退避与并发调整。重试上限与间隔为固定常量，禁止无界/递增重试；禁止兜底、降级、跳过等吞掉行为。

## 4. 退出码

| 退出码 | 含义 | 调度器动作 |
| --- | --- | --- |
| **0** | 成功（**必须已提交完成记录 `done` 事件**） | SUCCEEDED |
| **75** | 资源不足（资源类错误，可恢复退让） | BACKOFF，到期探测 |
| 其他非 0 | 业务/未知失败 | FAILED（可见回执，不静默删除） |

- **错误分类靠退出码，不靠事件 type**：75 是 `error` 的一种（资源类），不是独立事件类型；业务失败 = 其他非 0 退出码。
- 退出 0 但无完成记录 → RECOVERING（待核实，不重复启动）。
- 75 与随后同轮的资源类 `error` 事件属于同一失败轮次，任务退避只步降一次。
- 业务逻辑错误**不得**冒充资源不足；永久外部失败若也报 75，调度器保持可见并降低探测频率，不因固定重试次数放弃。
- **reason 归因信息**：`error`/退出原因必须携带错误类型（异常类名/HTTP 状态码）与资源标识（URL/主机），供调度器与运维归因；SDK 只做不可见字符清理、空白压缩与长度截断（300 字符），不剥除错误指纹。凭证/账号类敏感信息禁止写入。
- **启动许可门**：worker 发 `started` 后须等待 `SCHED_PERMIT_FILE`（`runtime/runs/<attempt_id>/permit.json`，含匹配的 attempt_id）才产生业务副作用；等待被中断或超时按资源不足（75）退让，不误判业务失败。
- **显式完成**：`execute()` 正常返回不等于完成——必须显式 `complete()` 提交完成记录；退出 0 无完成记录由调度器按"待核实"处理。

## 5. 协作暂停（控制通道）

调度器把暂停命令写入 `SCHED_CONTROL_FILE`（`runtime/runs/<attempt_id>/control.json`）：

```json
{ "command_id": "...", "action": "pause", "job_id": "...", "attempt_id": "...",
  "token": "...", "reason": "高优先级保护退让", "deadline": "ISO" }
```

worker 确认后：停止新工作 → 让当前有界步骤结束或安全取消 → **保存断点（若有）** → 发 `ack` 事件 → 正常退出。调度器由自身发起的 PAUSING 意图识别为 PAUSED，不依赖特殊退出码，也**不默认用 SIGSTOP**。

- 暂停命令**自带目标 attempt 身份**（`attempt_id`/`token`）：worker 校验与本进程注入身份一致才确认；不一致（调度器已换发新 attempt、控制文件是残留旧命令）一律忽略，防止旧命令误杀新 attempt。
- 本 attempt 继承了上一 attempt 的检查点但尚未自己提交过时，确认暂停前先把继承数据按本 attempt 身份重提交一次（否则检查点挂在旧 attempt 名下，恢复后会从零重放）。
- 业务里的长等待必须用 `wait_interruptible()`（小步睡眠 + 检查暂停）替代死 `sleep`，收到暂停立即在安全边界响应。

- 暂停宽限按调度器自统计的事件间隔（TaskTiming EMA）/进行中步骤时长/历史检查点耗时推导，不足以分阶段 TERM→KILL，靠上个已提交检查点 + 幂等执行恢复。
- 宽限超时后的强撤在调度器主循环内**非阻塞**分阶段推进（TERM → 到期 SIGKILL/cgroup.kill → 不可中断 D 态按未知退出码兜底收尾），单个卡死 worker 不会冻结控制平面（快照/命令/事件/准入）。
- 生产者**永远不进入**执行暂停流程。

## 6. 检查点

worker 若选择使用断点，可周期提交检查点（不只在收到暂停时）。检查点原子写入 `SCHED_CHECKPOINT_FILE`：

```json
{ "format_version": 1, "input_ref": "<job_id>", "business_version": "1",
  "progress": { "done": 12, "total": 40 }, "commit_seq": 7,
  "checksum": "<sha256[:32]>", "data": { "done_ids": [...] }, "saved_at": "ISO" }
```

- `progress` 建议给 `{"done": N, "total": M}` 结构的进展指标（业务语义自定，但须与 `progress` 事件的口径一致）——动态扩容凭真实进展证据决策，不只看提交编号。
- `checksum` 由 SDK 自动计算（业务数据规范化 JSON 的 sha256 前 32 位）；读回校验不一致（磁盘损坏/半写被外部替换）时丢弃断点并大声告警，宁可从零重放也不带病恢复。无 checksum 的旧检查点后向兼容。
- 调度器不理解业务检查点内容，也不代替任务恢复业务进度。
- 跨 attempt 继承：重试/暂停恢复/重启重放的新 attempt 启动前，调度器把该作业最近一次已提交检查点整体复制进新 run_dir；worker 启动时经 `resume_data()` 恢复，`commit_seq` 从恢复点继续递增。
- 业务先提交结果，再把完成位置推进到检查点；外部写入与本地进度不能原子提交时，用稳定幂等键 + 可核实提交记录。
- 重复执行未确认单元不得产生重复有效结果（幂等）。

## 7. 生产者协议（SDK `Producer`）

生产者常驻进程，环境变量 `SCHED_TASK_ID` + `SCHED_WORKSPACE`。目录：

- `producer_state/state.json`：`{cursor, unacked, conflicted}` —— 发现游标、待发布记录与冲突隔离账，同一原子写。
- `outbox/`：已就绪作业 JSON。
- `receipts/`：调度器回执（`<job_id>.json`）。

流程：

1. 发现一个业务事件后，先把（稳定事件标识 + 输入引用 + 业务版本 + 待发布作业记录）持久化，再推进发现游标（同一事务/原子写）。
2. `publish_all()`：写临时文件 → fsync → 同文件系统原子 rename → fsync 目录，成功后才标记已发布。
3. 未收到接收确认的作业保持可重放；仅当回执 `status == "received"` 才清理待发布副本（`conflict` / `invalid` 回执表示请求被隔离，移入 `conflicted` 账停止重发、留待人工处理），保留游标与去重记录。
4. 重启时 `replay` 未确认记录并补扫；数据源不支持回放则必须在 `recovery` 说明保留期/回放方式/遗漏识别。
   - **重叠回放是任务级契约**：SDK 每轮只把当前 cursor 交给 `discover()`；"从已确认游标以前的重叠范围重新检查"（数据源支持时）由各任务的 `discover()` 自行实现，依靠稳定 job_id 幂等去重，框架不强制。

SDK 入口：

```python
from sched_task_sdk import Producer, run_producer, job_id_of

class MyProducer(Producer):
    def discover(self, cursor):          # 返回 (new_cursor, [publish_spec...])
        ...
        return new_cursor, [{"event_id": ..., "business_version": "1",
                             "input_refs": [...], "idempotency_key": ...,
                             "env": {...}, "entry_args": [...],
                             "subdir": "2026/10"}]   # 可选：outbox 分目录
                                                      #（大规模任务，设计第二节）
run_producer(MyProducer(), tick_sec=300)
```

- `idempotency_key` 未显式提供时，SDK 以稳定事件标识兜底（同一事件重放得到同一键），保证全链路非空。
- `subdir`（可选）指定 outbox 内的相对子目录（不得含 `..`/绝对路径）；正式 JSON 仍是纯协议载荷（分目录信息不进入请求本体），接收端递归扫描分目录。
- 持续不足退出（`report_shortage` → exit 75）前，SDK 会把已有断点数据按本 attempt 身份重提交一次（设计第六节 L101）。

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
            self.report_progress(len(done))
        self.complete({"count": len(done)})                      # 完成（发 done 事件）

run_task(MyExecutor())
```

关键 API：

- `self.checkpoint(data)`：原子提交检查点（写 checkpoint.json）+ 检查暂停（收到则抛 `PauseRequested`）。
- `self.report_progress(completed_units)`：发进展事件。
- `self.report_shortage(reason)`：资源不足 → 抛 `Shortage` → exit 75。
- `self.complete(record)`：提交完成记录（发 `done` 事件）。
- `self.resume_data()`：读最近检查点的业务数据。跨 attempt 有效：重试/暂停恢复/重启重放产生新 attempt 时，调度器会先把该作业最近一次已提交检查点复制进新 run_dir，再拉起进程，故断点不丢。

注入环境变量：`SCHED_ATTEMPT_ID / SCHED_JOB_ID / SCHED_TASK_ID / SCHED_TOKEN / SCHED_RUN_DIR / SCHED_EVENT_FILE / SCHED_CONTROL_FILE / SCHED_CHECKPOINT_FILE / SCHED_PERMIT_FILE / SCHED_WORKSPACE`。
