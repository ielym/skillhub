# 调度语义（scheduling）

## 主循环（每 tick ≈ 1s）

```
  ① scan:  遍历已注册子任务 → 扫 requests/ 目录
     ├── 新文件 → 意图 pending，入 WQ
     ├── 文件指纹变化 → rejected（append-only 违规）
     └── 运行中意图文件消失 → 发 cancel

  ② admit: WQ 按「优先级 ↓ → 同优先级（无画像数据: round-robin 轮转 / 有数据: SJF 短作业优先）→ FIFO」排序
           admission_scan 虚拟账本判定 → 准出 → reserve → 拉起进程

  ③ control: 运行中进程轮询 state.json control 段
     ├── action=stop → 发 SIGTERM → 意图终结
     ├── action=no_retry → 记录，退出后终结
     └── action=reschedule(N) → not_before=N 秒后回队

  ④ preempt: 高优等待 & 账本不足
             贪心选最低优运行进程 → SIGTERM（exit 99 → 同意图续跑）

  ⑤ monitor: 心跳超时 / 超限 → heartbeat_kill 或 overload_preempt

  ⑥ finalize: 进程退出
     ├── exit_code + control 段 → ExitDecision
     ├── 终结（done） vs 续跑/重试同意图
     └── 画像更新
```

## 退出后决策（control.decide_from_exit）

| exit_code | control | → ExitDecision |
| --- | --- | --- |
| 0 | 任意 | terminal, done |
| 99 | 任意 | non-terminal, resume（回退 pending 续跑） |
| 100/101 | 任意 | non-terminal, retry（回退 pending 等待，不记失败） |
| 100/101 | no_retry | terminal, done |
| 102 | 任意 | non-terminal, skip（稍后重排） |
| 110 | 任意 | non-terminal, second_pass（简化重入队） |
| 其他非 0 | 任意 | non-terminal, retry（兜底按资源，回退 pending） |
| 其他非 0 | no_retry | terminal, done |

## 抢占

- **无豁免**：所有低优进程（含 daemon）都可被抢占
- 抢占触发：`preempt_exempt_sec=60` 保护期（启动后 60s 内不被抢）
- 抢占流程：SIGTERM → 期待 exit 99 → 同意图重入队
- 抢占后账本释放 → 原高优任务下一轮准出

## 排队

- **优先级（priority 字段，0~100）**：高优绝对优势
- **同优先级**：无画像数据时 round-robin（每个 subtask 轮转一人一个）；有画像数据后 SJF（预估短的先）
- **同时长 FIFO**：先入队者先
- **饿死看门狗**：`starvation_sec=60`（60s 等待）→ 提权到 101 级（钳制值域上限一级）

## 重试自治

- **同意图重试**（资源错误/抢占后）：回退 pending 等待，`lifetime.retry.backoff_base_sec` 固定退避防热循环；不设失败上限（永不放弃）
- **新执行 = 新意图**：驱动进程按需 `emit_intent()` 写新文件

## 资源协调

- **账本**：所有在运行进程的 `est_cpu` / `est_mem_mb` 汇总，`estimate_job(profile, declared, overshoot=1.2)` 上浮
- **容量**：机器总量（物理内存 / CPU 核心）
- **cgroup v2 硬限**：memory.high = 预估 × 1.5（软限节流）、memory.max = 预估 × 2.5（硬兜底）
- **画像采样**：运行中持续动态采样（60s 间隔），滑窗 8 次 P95（无冒烟）
- **外部感知**：MemAvailable - margin（默认 512MB）不足时退让等待
