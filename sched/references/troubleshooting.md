# 排查速查

> 按现象定位含义与处理动作。任务 run 记录在 `data/runs/<id>.jsonl`，调度决策在
> `data/runtime/decisions.jsonl`，任务 stdout/stderr 在 `data/runs/<id>/` 下。

| 现象 | 含义/处理 |
| --- | --- |
| `register` 失败/管理台显示"未通过上线检查" | 对应闸门失败；自动检查的原因也在 `data/runtime/admission.json`。gate2 契约失败：探针进程非 0 退出或 state.json 缺字段，裸跑 `SCHED_CONTRACT_PROBE=1 python3 run.py` 复现；改文件保存后立即重检 |
| gate3 冒烟超时 | dry 路径没在 `smoke.max_runtime_sec` 内收敛；检查死循环/网络硬等待，dry 必须无真实 IO 等待 |
| gate4 预估未知拒绝 | 声明 0 且 cgroup 实测 0；先按保守上限填 `resources.memory_mb`，并排查 cgroup 是否降级（自检见 [deployment.md](deployment.md)） |
| gate5 打断后不是 99 / 恢复跑失败 | 步太长、SIGTERM 后没落断点、或恢复未消费 resume_point 导致重跑；缩短步长，每步末 flush |
| run 状态 `resource` | 100/101 或未分类错误，退避中；看 `data/runs/<id>.jsonl` 的 reason 与 stderr，资源类属正常退让 |
| run 状态 `preempted` | 正常的高优先抢，断点已存，自动重入队；频繁被抢说明优先级给低了或申报偏大 |
| run 状态 `preempt_failed` | 40s 内没退出被 SIGKILL，断点未确认，转人工；必须缩短步长/优化信号响应 |
| run 状态 `failed` | 逻辑错误或交付物缺失；交付物缺失查 outputs.expect 路径（相对任务目录） |
| `killed` 且原因含心跳超时 | 单步阻塞超 heartbeat.timeout_sec；拆小步、保持 SDK 心跳（勿在心跳线程外长期阻塞 IO） |
| `status` 里 waiting 长期不动 | `status` 查账本余量与未通过上线检查项；常见原因：资源申报超剩余（正常排队，等高优/在途释放）、处于 backoff/cooldown（101 外部资源错误按 300s→1h 退避，属正常等待，到点自动重试）。外部资源没有容量开关可配 |
| 新任务放进 tasks/ 后一直不出现 | serve 未运行（自动检查只在 serve 内执行）；或检查未通过——看 `status`/管理台"等待上线检查"区/admission.json 的失败原因；冷却中改一次文件即可立即重试 |
| list 中任务 `ok=false` | task.json 非法或入口缺失；修复后下次热加载（≤30s）自动恢复 |

五道闸逐条判定标准见 [gates.md](gates.md)；字段/退出码细节见 [contracts.md](contracts.md)；
调度语义见 [scheduling.md](scheduling.md)；常见运维操作见 [deployment.md](deployment.md)。
