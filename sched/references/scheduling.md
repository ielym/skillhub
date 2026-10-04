# 调度语义（写代码前必须内化）

> 抢占、排队、触发、SDK 自治时机的确切行为。任务设计与排障都以此为准；
> 相关参数见 [configuration.md](configuration.md)。

## 运行期调度行为

- **抢占流程**：高优等待且资源缺口无法由空闲满足 → 调度器向最低优先级在跑任务发 SIGTERM → 任务在**当前步结束后**
  保存断点退出 99 → 资源释放给高优 → 被抢任务携断点自动重入队（60s 豁免期内不再被抢）。40s 不退出才 SIGKILL，
  被判 `preempt_failed` 转人工。因此：步要短、断点要在每步末落盘、SIGTERM 只置位不强退（SDK 已托管）。
- **排队与退让**：资源不足的任务留在全局队列 WQ，不失效、不超时报废；排序键 =
  **优先级降序 → 预估运行时长升序（SJF 短作业优先）→ 入队时刻升序**。预估时长取画像
  成功 run 时长中位数（冒烟声明值兜底，无样本视为最长），让短任务在同优先级下见缝先跑；
  等待超 1h 触发饿死保护临时提权。
  资源错误（100/101/未分类）后**立即重排队**、无全局退避；任务可在 task.json `retry`
  段声明 delay_sec（等待项带 not_before，到点才参与准出）、max_attempts（到次数 giveup
  转人工）、not_after（时效过了 giveup_expired 转人工），也可运行中用 SDK
  `set_retry_hint()` 收紧。任务侧要做的是**快速明确地失败**，把等待让给调度器，
  而不是占着进程死等。
- **手动停止**：管理台队列页对运行中 run 提供「停止」（cancel Event → SIGTERM 整组，
  10s 宽限），终态 killed、**本轮不自动重排队、转人工**；区别于 serve 停机的 killed
  （断点自动重入队）和心跳超时的 killed（重入队 1 次，第二次转人工）。
- **见缝插针**：大任务暂时放不下时，能放进剩余资源的小任务会先跑。任务启动开销应尽量小、申报应尽量准。
- **手动触发不是特权**：非 exempt 的 manual 任务与自动任务遵守同一套抢占、心跳（超时阈值放宽 2 倍）、超限规则。

## 触发时刻语义（manual / auto）

【讨论二 两值模型】调度器只做**粗颗粒节流**，精确时机判断全部下放任务进程内。

- **auto**：调度器按 `interval`（秒）给机会（`next_fire = now + interval`）。
  不做任何时间窗/星期/单次时刻判定——任务收到机会后，进程内自行判断"今天该不该跑"
  （法定节假日、每月特定日期、收盘后无意义等）：
  ```python
  # 任务 steps 开头示例：
  if today in HOLIDAYS or not self._should_run(today):
      self.reschedule(delay_sec=3600)  # 写 state.retry_hint.delay_sec=3600
      return self.exit_skip()          # exit_code=102，调度器转 not_before 重排队
  ```
  `reschedule(delay_sec)` 别名 `set_retry_hint(delay_sec=...)`，`exit_skip()` 设
  state.status=success 后以 102 退出。调度器读 `state_snapshot.retry_hint.delay_sec`
  → resolve_retry 合并 → 转 WQ 等待项的 `not_before`，到点后下一轮再给机会。
  attempt **不递增**（"跳过本轮"不是"重试失败"），**不受 max_attempts/not_after 限制**。
  任务进程内纠错/回扫节奏也用 reschedule 声明，和 retry 段（处理资源错误/逻辑错误的重试）
  走同一条 resolve_retry 合并路径。
- **manual**：调度器**永不自动给机会**；只能 `run <id>` 或管理台「立即运行一次」入队。
  注意 manual 任务**同样参与抢占/心跳/资源体系**（仅心跳阈值 ×2）；
  `contract_exempt` 的 manual 任务才不可抢占、不可自动恢复。
- 热加载保序：运行中改 task.json（或 serve 重启）不会把未到的 auto 触发时刻重置为 now+interval。
- 到点时在途实例已达 `max_instances`：`overflow=skip` 本次跳过（记 decisions 日志）；
  `queue` 照常入队排队。跳过/排队都不算失败。

### 已废弃字段（讨论二移除，旧 task.json 含这些字段时静默忽略）

| 废弃字段 | 旧语义 | 新做法 |
| --- | --- | --- |
| ~~once_at~~ | 单次时刻到期触发一次 | auto + interval 或 manual，时机判断放 SDK |
| ~~start_time / end_time~~ | 每日时间窗 | 任务 SDK 内部判断窗口（可任意不规则） |
| ~~weekdays~~ | 星期生效 | 任务 SDK 内部判断（支持法定节假日日历等） |
| ~~allow_overrun~~ | 越过窗口终点终止 | 窗口收口功能整体移除，调度器不再终止窗口外运行 |

## 退出码协议（任务 ↔ 调度器）

| 退出码 | 分类 | 调度器后续 |
| --- | --- | --- |
| 0（success） | — | 成功完结，auto 类 engine 继续按 interval 算下次给机会 |
| 99（PREEMPTED） | preempted | 断点保存 → 重入队、60s 豁免期 |
| 100（RESOURCE） | resource | retry 段自治重排队 |
| 101（EXTERNAL_RESOURCE） | resource | retry 段自治重排队（外部资源指数退避节奏由 SDK delay_sec 声明）|
| **102（SKIP_SCHEDULE）** | — | **跳过本轮 N 秒后再给机会**。attempt 不递增，不受 retry.max_attempts/not_after 限制；delay_sec 来自 SDK reschedule() 或 retry.delay_sec |
| 110（DATA_RISK） | logic | data_risk 二刷闭环（有上限） |
| 137（SIGKILL） | 待归因 | 人工排查 |
| 其他非 0（含 1） | unclassified | G5 兜底按 resource 重试（倒逼显式分类）|
