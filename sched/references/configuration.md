# 配置、CLI 与数据/日志布局

## 代码根发现

CLI 按顺序发现代码根：`SCHED_REPO` → `SCHED_HOME` → 当前目录及各级父目录 → `~/scheduler` → 已安装 `sched` 包。

## 数据布局（SCHED_HOME，默认 sched 包父目录）

```
SCHED_HOME/
├── config.json                      # 全局配置（control 节奏参数）
├── tasks/<task_id>/
│   ├── task.json                    # 任务清单（唯一真源）
│   ├── producer.py / run.py         # 生产者入口 / 执行入口
│   ├── config.json                  # 任务业务配置（可选，自包含）
│   ├── producer_state/state.json    # 生产者游标 + 待发布记录（同一原子写）
│   ├── outbox/<job_id>.json         # 已就绪作业 JSON
│   └── receipts/<job_id>.json       # 调度器接收回执
└── runtime/
    ├── exec.db                      # SQLite 执行库（jobs/attempts/events/checkpoints/receipts/task_state）
    ├── scheduler.lock               # 单实例 flock
    ├── archive/<task_id>/           # 已接收请求归档
    ├── isolation/<task_id>/         # 异常请求隔离（相同 job_id 内容不同）
    ├── runs/<attempt_id>/           # 事件 events.jsonl / 控制 control.json / 检查点 checkpoint.json
    ├── logs/<task_id>/              # 生产者 stdout/stderr 日志
    └── status.jsonl                 # 状态日志（启动/暂停/退让/终结）
```

## config.json（全局配置）

```jsonc
{
  "schema_version": 1,
  "timezone": "Asia/Shanghai",
  "control": {
    "loop_tick_sec": 1.0,               // 主循环 + 事件消费
    "sample_interval_sec": 2.0,         // 执行资源采样
    "heartbeat_interval_sec": 5.0,      // 心跳初值
    "producer_restart_base_sec": 1.0,   // 生产者崩溃退避起点
    "producer_restart_cap_sec": 30.0,   // 生产者崩溃退避上限
    "producer_crash_reset_after_sec": 300.0,
    "start_interval_sec": 1.0,          // 全局启动间隔（错开启动防突发）
    "grow_observe_sec": 30.0,           // 扩容观察期初值
    "pause_grace_base_sec": 10.0,       // 暂停宽限节奏初值
    "pause_grace_max_sec": 60.0,
    "shortage_retry_base_sec": 5.0,     // 不足重试指数退避起点
    "shortage_retry_cap_sec": 900.0,
    "protect_deadline_sec": 300.0,      // 整轮保护截止初值
    "protect_round_backoff_sec": 60.0,  // 失败保护轮间等待
    "slow_confidence_sec": 120.0,       // 变慢判定连续证据窗口
    "recovery_probe_sec": 60.0
  }
}
```

节奏/等待/间隔是**控制节奏**，有初始值并可随运行调整，不是任务容量或资源申请。

## CLI

| 命令 | 说明 |
| --- | --- |
| `sched serve` | 常驻调度循环（前台；SIGTERM/SIGINT 优雅停机） |
| `sched status [--json]` | 全局状态（生产者 / 动态目标 / 存活 attempt / 队列 / 退让 / 保护对象） |
| `sched list [--json]` | 已加载任务 |
| `sched task validate <id>` | 校验 task.json（schema + 入口存在 + 任务目录内） |
| `sched task enable/disable <id>` | 写 task.json `enabled` |
| `sched job list [task]` | 作业清单（最近 N 条） |
| `sched job show <job_id>` | 作业 + attempts |
| `sched job cancel <job_id>` | 显式取消（运行中先撤进程树） |
| `sched attempt list [job]` | attempt 清单 |
| `sched attempt cancel <id>` | 显式取消单个 attempt |

**没有 `run` 子命令** —— 正式执行只能由调度器扫描 outbox 就绪 JSON 触发。

## 运行身份与启动协议

执行进程命令通过参数数组直接启动，不默认经 shell 解释。调度器注入：

```
SCHED_ATTEMPT_ID / SCHED_JOB_ID / SCHED_TASK_ID / SCHED_TOKEN
SCHED_RUN_DIR / SCHED_EVENT_FILE / SCHED_CONTROL_FILE / SCHED_CHECKPOINT_FILE
SCHED_WORKSPACE / SCHED_PROGRESS_SEMVER
```

执行身份 = PID + 进程启动时间 + attempt_id + 执行令牌 + cgroup/进程树归属，PID 复用不会误暂停其他进程。

## 只观测执行进程

- 准入只使用执行进程及其后代的 CPU 时间、实际驻留/cgroup 内存、I/O 计数、压力指标、OOM 证据与业务进展。
- 生产者不加入执行统计范围；不使用整机 CPU 忙碌率/整机可用内存作为日常准入门禁。
- 机器可用核数、安装内存与真实容量只作为比较尺度。
- 无法归因时标为观测不足，减慢执行探索，不以含生产者的全局指标替代。