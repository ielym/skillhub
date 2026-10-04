# 验收清单（acceptance）

交付前必须全部打勾；任何没打勾的都是阻塞项。

## 清单 A：双闸上线通过

- [ ] 闸1 静态通过（manifest schema 合法）
- [ ] 闸2 契约通过（dry 跑通、exit 0）
- [ ] `data/jobs.json` 中对应条目 `enabled=true`
- [ ] 管理台 Web 或 `sched status` 里子任务 `ok=true`

## 清单 B：端到端链路

- [ ] scan 到新意图 → 入队 pending
- [ ] admission_scan 判定可准出 → admit
- [ ] runner 拉起进程 → exit 0 → 意图 `done`
- [ ] 进程 exit 100 → 意图 `pending`（retry）+ 退避
- [ ] kill -TERM 运行中进程 → exit 99 → 意图 `pending`（resume）
- [ ] SDK `request_stop()` → 意图 `done`
- [ ] SDK `no_retry()` → 进程退出后不再 retry
- [ ] 意图文件改写（指纹变）→ rejected
- [ ] 意图文件消失 → done

## 清单 C：运行画像

- [ ] 首次运行后资源消耗被 cgroup 动态采样记录（运行几次后画像收敛）
- [ ] 资源画像写入 `data/runtime/profiles.json`
- [ ] 运行历史记录落盘 `data/runs/<subtask_id>.jsonl`（exit_code、start/finished 时间）
- [ ] 决策审计落盘 `data/runtime/decisions.jsonl`（enqueue_intent / admit_intent / preempt / exit_decision）

## 清单 D：资源协调正确

- [ ] 高优等待 + 低优运行 + 账本满 → 抢占低优
- [ ] 抢占后账本释放 → 高优下一轮准出
- [ ] 抢占者 60s 保护期 → 不被再抢
- [ ] 同优先级不互相抢占

## 清单 E：安全与合规

- [ ] 密钥不在 manifest/state.json/日志里
- [ ] 所有入口文件路径相对任务目录（无 `..`、无绝对路径）
- [ ] 外部 env 黑名单键（LD_PRELOAD 等）未注入
- [ ] `chmod 600` 密钥文件

## 清单 F：可恢复 / 可回溯

- [ ] 被抢占进程 exit 99 后，断点文件存在且包含已完成位点
- [ ] 同意图续跑后从断点继续（不重复已完成工作）
- [ ] 不同时期的执行方式（新意图文件）天然可回溯
- [ ] `data/runtime/intents_state.json` 完整保留历史状态
