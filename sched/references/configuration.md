# 配置（configuration）

## 数据/运行目录（SCHED_HOME）

- 默认：`sched` 包上一级目录（clone 根）
- 环境变量覆盖：`SCHED_HOME=/some/path`
- 所有路径相对 SCHED_HOME：

| 路径 | 用途 |
| --- | --- |
| `tasks/<subtask_id>/` | 子任务目录（manifest.json + run.py + requests/ + cache/ + results/） |
| `data/jobs.json` | 注册表（enabled 开关） |
| `data/settings.json` | 全局 Settings 覆盖（可选） |
| `data/runtime/scheduler_state.json` | WQ 快照 |
| `data/runtime/intents_state.json` | 意图消费状态 |
| `data/runtime/scheduler.lock` | 单实例 flock |
| `data/runtime/active.json` | 运行中进程清单 |
| `data/runtime/decisions.jsonl` | 审计日志（enqueue_intent / admit_intent / preempt / exit_decision） |
| `data/runtime/profiles.json` | 资源画像（声明 + 运行中动态采样） |
| `data/runtime/ledger.json` | 账本 |
| `data/runs/<subtask_id>.jsonl` | 运行历史（exit_code / start / finished / 归因） |
| `data/runs/<subtask_id>/<run_id>.stdout.log` | 该次运行 stdout（管理台 tail 实时看进度） |
| `data/runs/<subtask_id>/<run_id>.stderr.log` | 该次运行 stderr |

## 全局 Settings（`data/settings.json`）

```jsonc
{
  "timezone": "Asia/Shanghai",
  "run_user": "",                       // 空=当前用户；manifest.runtime.user 优先覆盖
  "runner": {
    "kill_grace_sec": 10,               // 取消/停止场景 SIGTERM → SIGKILL 宽限（秒）
    "heartbeat_timeout_sec": 120,       // 全局心跳超时兜底；manifest.heartbeat.timeout_sec 可覆盖（下限 5）
    "grace_sec": 40                     // 抢占场景 SIGTERM → SIGKILL 宽限（秒）
  },
  "resource": {
    "overshoot": 1.2,                   // 画像上浮系数（P95 ×1.2）
    "sample_interval_sec": 3,           // cgroup 采样周期
    "profile_live_interval_sec": 60,    // 运行中动态画像落盘间隔
    "external_safety_margin_mb": 512     // MemAvailable 安全垫
  },
  "web": { "port": 8765, "host": "127.0.0.1" },
  "preempt_exempt_sec": 60,             // 进程启动后抢占保护期（秒）
  "starvation_sec": 60,                 // 饿死看门狗阈值（60s 等待 → 提权到 101 级）
  "hot_reload_sec": 30                  // serve 扫描新任务/重载 manifest 周期
}
```

Settings 合并顺序（后者覆盖前者）：

1. config.py 内默认值
2. `data/settings.json`（SCHED_HOME 下；缺失时自动写默认值）

## 任务级 manifest

见 [contracts.md](contracts.md) —— manifest.json 是任务唯一清单，双闸自动从它读取。

## 意图文件（v1）

每个新执行 = `tasks/<id>/requests/<request_id>.json`（append-only），schema 见 [contracts.md](contracts.md)。

## CLI

```bash
python3 -m sched list                  # 已上线子任务、ok 状态、优先级、资源预估
python3 -m sched register <id>        # 立即跑双闸上线检查
python3 -m sched start <id>           # 启用 run_mode=manual 的子任务（置 enabled=true）
python3 -m sched status                # 子任务数、WQ、运行中、账本、意图消费状态
python3 -m sched process list [sid]   # 子任务的意图清单 + 运行进程
python3 -m sched process stop <sid> <rid>     # 终止运行中意图（把意图文件重命名 .bak 标记"消失"→ 调度器 cancel 进程并置 done）
python3 -m sched process no-retry <sid> <rid> # 不再重试（同样标记意图消失 → 终结）
python3 -m sched clear                 # 清空全部调度状态（注册表/WQ/意图/运行历史）
python3 -m sched clear --delete-requests # 同时清空所有子任务 requests/ 意图文件（保留任务代码）
python3 -m sched serve                 # 常驻调度循环（自动发现新子任务、热加载 30s）
python3 -m sched serve --web           # 同时启动内嵌 Web 管理台（默认 127.0.0.1:8765）
```

> `process stop` / `no-retry` 是"硬路径"：两者都把意图文件改名 `.bak`，让调度器在扫描时认为意图消失，从而取消运行进程并把意图置 `done`（区别只在记录原因文本）。它们**不**直接发 SIGTERM、也不写 state.json control 段；正常终止请用 SDK `request_stop()` / `no_retry()`（见 [contracts.md](contracts.md)）。

没有 `run` 子命令——**正式执行只能由调度器扫描意图触发**。

## 启动协议（环境变量注入）

调度器拉起每个意图时注入：`SCHED_SUBTASK_ID` / `SCHED_REQUEST_ID` / `SCHED_RUN_ID` / `SCHED_CONFIG` / `SCHED_TRIGGER`（`auto|retry|resume|second_pass`）/ `SCHED_ATTEMPT` / `SCHED_SCHEDULED_AT` / `SCHED_WORKSPACE` / `SCHED_ERROR_RULES`（manifest 配了 error_rules 时）。

子任务进程用这些 env 判断自己是不是被调度器正确拉起的。

## 资源硬限（cgroup v2）

调度器自动为每个运行中进程创建子 cgroup，硬限：

- `memory.high` = 预估 × 1.5（软限节流）
- `memory.max` = 预估 × 2.5（硬兜底，超限 OOM kill → exit 137）
- CPU：`cpu.max` = 预估 CPU × 配额窗口

## 心跳与超时

- SDK `SchedTask` 自动维护 state.json.heartbeat_at / updated_at
- `runner.heartbeat_timeout_sec`（默认 120s）：超时 → 心跳超时判定 → 整组终止
- `manifest.heartbeat.timeout_sec` 可单任务覆盖（下限 5s）
