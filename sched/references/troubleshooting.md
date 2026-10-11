# 排查手册

## 看状态

```bash
sched status                # 生产者存活 / 队列 / 存活 attempt / 动态目标 / 退让 / 保护对象
sched list                  # 任务与优先级
sched job list <task>       # 该任务作业
sched job show <job_id>     # 作业状态 + attempts + reason
sched attempt list <job>    # attempt 历史（exit_code / status）
```

## 常见症状

| 症状 | 排查 |
| --- | --- |
| 作业一直 QUEUED 不启动 | 是否达动态目标（`status` 的 scale 段）；是否在退让/冷却；是否资源观测接近饱和；`attempt list` 看是否已有存活 attempt 未退出 |
| 作业 BACKOFF 反复 | 执行者持续报 `external_shortage`：看 `job show` reason；日志在 `runtime/logs/<task>/`；确认不足可恢复而非永久（永久失败不应报不足） |
| 作业 FAILED | 业务逻辑错误或未知失败：看 stdout/stderr 与 attempt reason；修复后由生产者重放或重发新作业 |
| 生产者反复崩溃 | `status` 的 producers crash 计数；日志 `runtime/logs/<task>/producer.stderr.log`；崩溃退避在一次次加长 |
| 暂暂停后恢复重跑已完成工作 | 检查检查点是否周期提交、幂等键是否稳定；`runtime/runs/<attempt_id>/checkpoint.json` |
| 有孤儿进程 | 取消/暂停后进程树是否确认退出（cgroup 内 `cgroup.procs`）；重启接管会核实身份 |
| RECOVERING 卡住 | 退出 0 但无 `completed` 记录；确认执行者 `complete()` 被调用；或显式取消 |

## 关键文件位置

- 执行事件：`runtime/runs/<attempt_id>/events.jsonl`
- 暂停命令：`runtime/runs/<attempt_id>/control.json`
- 检查点：`runtime/runs/<attempt_id>/checkpoint.json`
- 状态日志：`runtime/status.jsonl`
- 审计（接收/隔离）：`runtime/isolation/`、`runtime/archive/`

## 数据清理（仅调试，建议先停服务）

- 清空全部调度状态：删除 `runtime/exec.db` 与各任务 `outbox/`、`producer_state/`（谨慎：会丢游标与未完成作业记录）。
- 单作业重置：`sched job cancel <job_id>` 后由生产者按稳定标识重放。