# 契约：manifest + 意图文件 + 退出码 + control 段 + SDK

## manifest.json（schema_version=3）

子任务清单——调度器注册与双闸准入的唯一真源。**不含调度时机/间隔/并发开关**。

```jsonc
{
  "schema_version": 3,
  "name": "arxiv_daily",              // 必须：字母数字下划线短横，1-64 位
  "description": "每天抓当天论文；大任务与日更并行",
  "run_mode": "auto",                 // auto=注册即消费意图；manual=显式 start 后消费
  "entry": {
    "file": "run.py",                 // 必须：相对任务目录，禁止 ".." 与绝对路径
    "interpreter": "python3",         // 可为 null（要求 run.py 有可执行权限）
    "args": [],
    "cwd": "."
  },
  "priority": 40,                     // 0~100；唯一优先级来源（意图文件不可覆盖）
  "resources": {                      // 基线，意图可覆盖
    "cpu": 0.5,
    "memory_mb": 512
  },
  "error_rules": {                    // 选填：闸2 错误分类辅助
    "resource_regex": [],
    "logic_regex": ["LOGIC:"]
  },
  "heartbeat": { "timeout_sec": 120 },
  "runtime": { "user": "sched-run" }  // 可空 = 以当前用户执行
}
```

### manifest 校验（闸1 静态）

- schema_version **必须等于** 3（否则拒绝）
- entry.file **必须存在** 且在任务目录内（禁止 `..`、绝对路径）
- entry.interpreter 只能是命令名（禁 `/usr/bin/python3` 这种完整路径）
- priority 在 0~100 之间
- run_mode 只能是 `auto` 或 `manual`
- heartbeat.timeout_sec ≥ 5

### 入口覆盖：意图文件里的 entry

意图文件可以**覆盖** manifest 的 entry（多进程场景下不同进程用不同入口）：

```json
"entry": { "file": "controller.py", "interpreter": "python3", "args": [], "cwd": "." }
```

## 意图文件（schema_version=1，写入 `tasks/<id>/requests/<request_id>.json`）

**不可变、append-only**：写后不改、不自行删；新执行 = 新 `request_id` 文件。

```jsonc
{
  "schema_version": 1,
  "request_id": "2026-10-04-0001",     // 文件名 = request_id
  "kind": "daemon",                     // daemon | oneshot
  "config": "config/2026-10-04.json",   // 相对任务目录，--config 传入；可空
  "entry": { ... },                     // 可选覆盖 manifest.entry
  "resources": { "cpu": 0.5, "memory_mb": 512 },  // 可选覆盖（覆盖声明值；画像仍动态校准）
  "lifetime": {
    "completion": "indefinite",        // terminal=oneshot 默认；indefinite=daemon 默认
    "retry": {
      "backoff_base_sec": 5,           // 资源不足回退 pending 的固定退避（防热循环）
      "backoff_cap_sec": 300           // 封顶
    }
  }
}
```

### 启动协议（调度器注入）

调度器拉起每个意图时，向进程环境注入：

| 环境变量 | 含义 |
| --- | --- |
| `SCHED_SUBTASK_ID` | 子任务 id |
| `SCHED_REQUEST_ID` | request_id |
| `SCHED_RUN_ID` | run_id（调度器生成的 UUID 风格） |
| `SCHED_CONFIG` | 意图的 config 字段 |
| `SCHED_TRIGGER` | auto | retry | resume | second_pass |
| `SCHED_ATTEMPT` | 第几次尝试（1 起） |
| `SCHED_SCHEDULED_AT` | ISO8601 调度时间 |
| `SCHED_WORKSPACE` | 任务目录绝对路径 |

调度器执行：`python3 <entry.file> --config <config>`（interpreter 为 null 时直接执行 entry.file）。

## 退出码协议（协议 A2）

| 退出码 | 含义 | 调度器动作 |
| --- | --- | --- |
| 0 | 成功完成 | 意图 `done`，不重启 |
| **99** | **抢占/停止，断点已保存** | 同意图续跑（回退 pending） |
| **100/101** | **本机/外部资源不足** | 回退 pending 等待，固定退避，不记失败 |
| **102** | 任务判定当前不该跑 | 跳过本轮，稍后重排 |
| **110** | 数据风险（跳过项已写 pending_skipped） | 可选二刷（简化为重入队） |
| 其他非 0 | **兜底按资源错误** | 回退 pending（倒逼正确分类） |
| **137/-9** | SIGKILL | 归因后按资源回退 pending |

## state.json control 段（协议 B2：运行时异步指令）

SDK 把 `control` 段写入 `tasks/<id>/cache/runs/<run_id>/state.json`（或 legacy `cache/state.json`），调度器每 tick 轮询：

```json
{
  "control": {
    "action": "stop | no_retry | reschedule",
    "delay_sec": 0,
    "reason": ""
  }
}
```

| action | 含义 | 调度器动作 |
| --- | --- | --- |
| `stop` | 进程请求结束 | 发 SIGTERM → 进程落断点 → 意图终结 |
| `no_retry` | 进程声明不再自动重试 | 非 0 退出时直接终结（覆盖 lifetime.retry） |
| `reschedule(N)` | 稍后再给机会 | 同意图入队，`not_before = now + N 秒` |

## 意图消费状态（`data/runtime/intents_state.json`）

```json
{
  "<subtask_id>": {
    "<request_id>": {
      "status": "pending | running | done | archived | rejected",
      "fingerprint": "<16位哈希片段>",
      "run_id": "20261004T120000-abcdef12",
      "first_seen": "2026-10-04T12:00:00+08:00",
      "finished_at": "",
      "rejected_reason": ""
    }
  }
}
```

状态机：

```
  [新文件] → pending → running → done/archived
                                ↑
                     退出码 99   │
                       续跑 ──→ pending → ...
                                
  文件改写 → rejected（违规，需手动处理）
  文件消失 → done（意图终结）
```

## SDK（sched_task_sdk）

### 核心基类

```python
from sched_task_sdk import SchedTask, OneshotTask, DaemonTask

class MyTask(DaemonTask):
    def steps(self):
        while True:             # daemon 无限迭代
            data = fetch_data()
            self.save_checkpoint({"cursor": data.cursor})  # 落断点
            yield data          # 业务处理一个"步骤"
            # 被抢占后从 resume_point 恢复
```

### 控制 API

```python
task = MyTask()
task.run()                    # 主循环

# 运行中按需调：
task.request_stop("大任务已完成")    # 意图终结，不再续跑
task.no_retry("别再跑了")           # 退出后不自动重试
task.reschedule(300)                 # 5 分钟后再给机会

# 新意图（驱动进程场景）：
task.emit_intent(config="config/2026-10-05.json",
                 kind="oneshot",
                 resources={"cpu": 0.2, "memory_mb": 128})
# → 返回新 request_id
```

### state.json 字段（SDK 写，调度器读）

```json
{
  "schema_version": 1,
  "current_step": "抓取论文 page=2",
  "progress": 0.4,
  "heartbeat_at": "2026-10-04T16:18:00+08:00",
  "updated_at": "2026-10-04T16:18:00+08:00",
  "resume_point": { ... },
  "last_error": { "category": "resource", "message": "代理 429" },
  "control": { "action": "none" }
}
```

### 外部资源退出码约定（SDK 辅助）

```python
try:
    data = fetch_via_proxy()
except Exception as e:
    task.state.error("resource", f"代理故障：{e}")
    sys.exit(101)   # 外部资源错误
```

`lifetime.retry.backoff_base_sec=5` → 资源不足回退 pending 的固定退避（不记失败，永不放弃）。
