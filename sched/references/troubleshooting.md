# 故障排查（troubleshooting）

## 意图没被消费

**现象**：`requests/<rid>.json` 写了很久，但 `process list` 里状态还是 `pending` 或没记录。

**排查步骤**：

1. **闸失败了？** `sched register <sid>` 看输出
   - 闸1 manifest 解析失败 → 看 Web 管理台 `error` 字段修 manifest.json
   - 闸2 契约失败 → 本地 `python3 run.py` 裸跑复现

2. **run_mode=manual 未启用？** `data/jobs.json` 里 `enabled` 应该是 true；false 时用 `sched start <sid>`

3. **账本满了？** `sched status` 看 ledger 预留；如果所有进程账本加起来接近机器上限 → 等其他任务结束 / 抢低优

4. **指纹冲突 rejected？** 看 `intents_state.json` 里 `rejected_reason`，新执行必须是新 request_id 文件

## 进程被频繁抢占

**现象**：daemon 频繁 exit 99 后又起来，反复打断业务。

**排查**：

1. **自己优先级太低**？调 manifest 的 priority（0~100，越高越不容易被抢）
2. **有高优任务在排队**？`status` 看 WQ，高优任务在等容量 → 等它起来
3. **画像太保守**？声明资源申报偏保守 → 调 resources 或等画像收敛

## 进程卡住（心跳超时）

**现象**：monitor 判定 heartbeat_kill。

**排查**：

1. SDK 心跳线程正常跑吗？state.json.heartbeat_at 有没有持续更新
2. heartbeat_timeout_sec 设得太短？manifest 里调大
3. cgroup memory.max 硬限位导致 OOM kill → exit 137？看 exit 码
4. 外部资源阻塞没超时？加 timeout 机制（别让进程一直卡在等待网络）

## 进程 OOM

**现象**：exit 137 / -9 / 审计日志 `overload_preempt`。

**排查**：

1. **声明虚低**？实际内存峰值 > 声明 × 1.5 → 上调 manifest.resources.memory_mb
2. **业务逻辑泄漏**？profile 画像持续爬升 → 修内存泄漏
3. **cgroup 硬限太严**？profile 上浮系数 overshoot 默认 1.5 → 调 settings.resource.overshoot

## 意图不重试（本来应该回退重排）

**现象**：exit 100/101 但意图直接 done，没回退 pending。

**排查**：

1. **SDK 写了 no_retry control 段？** state.json 里看 control.action（no_retry 会终结意图）
2. **SDK 写了 stop control 段？** 进程主动 stop 也会终结
3. **意图文件被删除了？** 文件消失 → 意图 done

## 被抢占后没恢复（断点丢了）

**现象**：抢占后新进程从开头跑，重做了已完成的工作。

**排查**：

1. **SDK 断点有没有保存？** 抢占前 state.json 的 resume_point 字段存在吗
2. **resume_point.json 丢了？** tasks/<id>/cache/resume_point.json 应该有最后一次保存的断点
3. **daemon 里 steps() 没循环？** 抢占后 resume → 重新进入 `while True`，应该从断点位置继续 yield

## 审计日志看不到想要的事件

**现象**：`decisions.jsonl` 里没有某次 preempt / exit_decision。

**排查**：

1. **文件没 flush？** `store.py` 是原子写 + 轮转，正常情况下立即可见
2. **路径被 `_ignore` 列表过滤了？** scanner 会跳过 `_dev/` 等目录
3. **serve 进程重启过？** 审计日志不会丢失，但重启前最后几条可能在轮转中

## 核心排查文件一览

| 文件 | 看什么 |
| --- | --- |
| `data/runtime/intents_state.json` | 每个意图的状态、指纹、run_id、rejected_reason |
| `data/runtime/decisions.jsonl` | 所有调度决策（enqueue / admit / preempt / exit） |
| `data/runtime/ledger.json` | 当前账本预留 |
| `data/runtime/profiles.json` | 资源画像 |
| `data/runtime/active.json` | 运行中进程清单 |
| `data/runs/<sid>.jsonl` | 该子任务所有运行历史 |
| `tasks/<sid>/cache/runs/<rid>/state.json` | 运行时心跳/断点/错误 |
