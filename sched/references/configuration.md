# 配置、CLI 与数据/日志布局

## 代码根发现

`sched` 命令按以下顺序定位 scheduler 代码仓（需要同时包含 `sched/` 与 `sched_task_sdk/` 两个包）：

1. 环境变量 `SCHED_REPO`（显式指定代码仓根）
2. 环境变量 `SCHED_HOME`（调度器项目根，与代码仓根同构）
3. 当前工作目录及其各级父目录（在仓库内任意位置调用均可）
4. `~/scheduler`（约定的 clone 位置）
5. 已安装到解释器环境的 sched 包（`pip install -e <代码仓>`）

运行时（serve/任务进程）的 SCHED_HOME 未设置时默认 sched 包上一级目录。

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
    ├── exec.db                      # SQLite 执行库（jobs/attempts/events/checkpoints/task_state）
    ├── scheduler.lock               # 单实例 flock
    ├── snapshot.json                # serve 每轮写入的运行时快照（CLI status 优先读取）
    ├── commands.jsonl               # CLI → serve 控制命令通道（cancel 等）
    ├── commands_ack.jsonl           # serve 对控制命令的回执
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
    "feedback_interval_init_sec": 5.0,      // 业务进展节奏 EMA 初值（只服务慢检测/暂停宽限/保护窗，不参与存活）
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
    "protect_round_backoff_sec": 60.0,  // 失败保护轮间等待（起点）
    "protect_round_backoff_cap_sec": 600.0,  // 失败保护轮间等待上限（逐渐增加）
    "yield_observe_sec": 10.0,          // 保护轮每次退让后需观察的间隔
    "slow_confidence_sec": 120.0,       // 变慢判定连续证据窗口
    "recovery_probe_sec": 60.0,         // 恢复探测最小机会间隔
    "scan_batch_size": 200,             // 每任务每轮接收时间片（文件数上限）
    "heartbeat_interval_sec": 5.0,      // SDK 心跳发送间隔（注入 worker；调度器据此判活）
    "heartbeat_stale_multiplier": 6.0,  // 心跳超时 = 心跳间隔 × 该倍数（丢失该数量心跳判死）
    "resource_unhealthy_ratio": 0.9,    // 持续超过判定不健康
    "resource_healthy_ratio": 0.7,      // 持续低于判定恢复健康（滞回）
    "resource_stable_samples": 3,       // 滞回连续样本数
    "exec_mem_cap_ratio": 0.80,         // 执行内存占机器 ≥ 此值即 SHED（停新增+撤内存，单采样）
    "mem_growth_ratio": 0.05,           // 单采样区间执行内存净增占容量比例，判"快速增长"
    "observability_slow_factor": 3.0,   // 观测不足时扩容观察期放大倍数
    "task_backoff_probe_base_sec": 30.0,   // 任务全退避（EMPTY）后的首次探测间隔
    "task_backoff_probe_cap_sec": 600.0,   // 探测间隔上限（每失败一次翻倍递增）
    "recover_grace_sec": 30.0,          // 重启后旧执行进程协作退出宽限
    "cmd_ack_wait_sec": 6.0,            // CLI 控制命令等待确认超时
    "stale_pause_cooldown_sec": 60.0,  // 心跳超时/OOM/内存增长退让/保护自收缩暂停的作业恢复排队前冷却，防紧密重启循环
    "cleanup_terminal_after_sec": 604800.0  // 已完结作业（成功/取消）attempt 工件保留时长（秒）
  }
}
```

节奏/等待/间隔是**控制节奏**，有初始值并可随运行调整，不是任务容量或资源申请。

> `task.json` 不再接受任务自申报的 `feedback_interval_sec` / `max_step_sec`（以及 `progress_semver`）字段：任务反馈节奏改由调度器从实际事件间隔自统计（TaskTiming EMA 动态更新，`feedback_interval_init_sec` 仅作为该 EMA 的初始值/下限），暂停宽限与变慢观察期都基于自统计节奏推导。

## CLI

| 命令 | 说明 |
| --- | --- |
| `sched serve` | 常驻调度循环（前台；SIGTERM/SIGINT 优雅停机） |
| `sched status [--json]` | 全局状态（生产者 / 动态目标 / 存活 attempt / 队列 / 退让 / 保护对象）；serve 在线时读运行时快照显示 `serve=alive` |
| `sched list [--json]` | 已加载任务 |
| `sched task validate <id>` | 校验 task.json（schema + 入口存在 + 任务目录内） |
| `sched task enable/disable <id>` | 写 task.json `enabled` |
| `sched job list [task]` | 作业清单（最近 N 条） |
| `sched job show <job_id>` | 作业 + attempts |
| `sched job cancel <job_id> [--reason <r>]` | 显式取消（serve 在线走命令通道并等回执；离线降级直连撤进程树） |
| `sched job requeue <job_id> [--reason <r>]` | 显式重排：关闭在途/退避/阻塞 attempt 并重新排队（STARTING/RUNNING/PAUSING 拒绝）；RECOVERY_BLOCKED 人工解除入口 |
| `sched attempt list [job]` | attempt 清单 |
| `sched attempt cancel <id> [--reason <r>]` | 显式取消单个 attempt |

**没有 `run` 子命令** —— 正式执行只能由调度器扫描 outbox 就绪 JSON 触发。

## 运行身份与启动协议

执行进程命令通过参数数组直接启动，不默认经 shell 解释。调度器注入：

```
SCHED_ATTEMPT_ID / SCHED_JOB_ID / SCHED_TASK_ID / SCHED_TOKEN
SCHED_RUN_DIR / SCHED_EVENT_FILE / SCHED_CONTROL_FILE / SCHED_CHECKPOINT_FILE
SCHED_PERMIT_FILE / SCHED_WORKSPACE
```

执行身份 = PID + 进程启动时间 + attempt_id + 执行令牌 + cgroup/进程树归属，PID 复用不会误暂停其他进程。

## 只观测执行进程

- 准入只使用执行进程及其后代的 CPU 时间、实际驻留/cgroup 内存、I/O 计数、压力指标、OOM 证据与业务进展。
- 生产者不加入执行统计范围；不使用整机 CPU 忙碌率/整机可用内存作为日常准入门禁。
- 机器可用核数、安装内存与真实容量只作为比较尺度。
- 无法归因时标为观测不足，减慢执行探索，不以含生产者的全局指标替代。