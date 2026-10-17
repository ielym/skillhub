# 起步代码与场景模板

模板在 `assets/` 下。所有模板为最小可运行示例，业务逻辑留白，请按真实业务填写。

| 模板 | 场景 | 文件 |
| --- | --- | --- |
| skeleton | 最小生产者 + 执行者骨架 | [assets/skeleton](../assets/skeleton) |
| 01_daily_producer | 每日定时发现（如每日抓取 T-2） | [assets/templates/01_daily_producer](../assets/templates/01_daily_producer) |
| 02_batch_backfill | 批量回溯（有限日期/ID 范围，幂等跳过已完成） | [assets/templates/02_batch_backfill](../assets/templates/02_batch_backfill) |
| 03_longtask | 长期任务（持续进展，无完成事件参与调度） | [assets/templates/03_longtask](../assets/templates/03_longtask) |

每个模板含 `task.json`、`config.json`（可选）、`producer.py`、`run.py`，自包含（不含外部依赖）。

## 起步骨架（skeleton/）

`task.json`：

```json
{ "schema_version": 1, "task_id": "my_task", "enabled": true, "priority": 50,
  "producer_entry": { "file": "producer.py", "interpreter": "python3", "args": [] },
  "executor_entry": { "file": "run.py", "interpreter": "python3", "args": [] },
  "workdir": ".",
  "recovery": { "replay": "outbox", "retain": "说明数据源保留", "replay_note": "说明遗漏识别" } }
```

`producer.py` 最小实现（见 [contracts.md](contracts.md) §7）：

```python
from sched_task_sdk import Producer, run_producer

class MyProducer(Producer):
    def discover(self, cursor):
        if cursor is not None:            # 已发布过 → 不再发布
            return cursor, []
        return {"published": True}, [{"event_id": "round-1", "business_version": "1",
                                      "input_refs": [], "idempotency_key": "k",
                                      "env": {}, "entry_args": []}]

run_producer(MyProducer(), tick_sec=60)
```

`run.py` 最小实现（见 [contracts.md](contracts.md) §8）：

```python
from sched_task_sdk import ExecutorTask, run_task

class MyExecutor(ExecutorTask):
    def execute(self):
        done = self.resume_data() or []
        for i in range(10):
            if i in done:
                continue
            # 业务处理（幂等）...
            done.append(i)
            self.checkpoint(done)                              # 落断点 + 查暂停
            self.report_progress(len(done))
        self.complete({"count": len(done)})

run_task(MyExecutor())
```

## 关键注意

- 生产者 `discover()` 返回 `(new_cursor, [publish_spec...])`；`cursor` 用于去重，不用它外推业务时间。
- 执行者 `self.checkpoint(...)` 是「落断点 + 查暂停」的统一点，务必在有界步骤边界调用。
- 有限任务必须 `self.complete(...)`；长期任务持续 `report_progress`、无需 complete。