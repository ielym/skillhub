# 场景模板选择指南（templates）

模板在 `assets/templates/` 下，每个模板一个目录，包含：

- `run.py` — 业务入口（继承 SDK 基类）
- `manifest.json` — 子任务清单（schema_version=3）
- 可选：`requests/` 示例意图文件

| 模板 | 场景 | kind | 说明 |
| --- | --- | --- | --- |
| `daemon` | 单进程常驻循环 | daemon | 每天 1 个、每小时 1 个、持续监控类；一个意图 = 一个 daemon；内部 `while True` + 断点 |
| `multi_process_driver` | 驱动进程按需 emit_intent | 混合型 | 大任务 + 日更并行、多粒度；一个意图 = 一个 oneshot；由 `controller.py` 驱动写新意图 |
| `once_migration` | 一次性迁移 | oneshot | 跑完自然退出；daemon/oneshot 选哪个取决于"跑完了要不要继续守护" |

## 模板一：daemon（单进程常驻）

适合场景：
- 每天抓一次当天论文
- 每小时同步一次数据镜像
- 持续监控某个指标，异常时告警

特点：
- 一个意图 = 一个 `DaemonTask` 常驻循环
- `steps()` 里 `while True`：跑一次业务逻辑 → 落断点 → `yield`
- 进程退出靠 SDK 调用（`request_stop` / `exit`）或被高优抢占

## 模板二：multi_process_driver（驱动进程按需起）

适合场景：
- 一个 2 天大任务（长期跑，被抢占后续跑）
- 每天额外抓当天的（每天一个新意图）
- 多粒度并发（不同资源需求/不同意图类型的多个进程）

特点：
- 一个意图 = 一个 oneshot（`OneshotTask`）有限迭代
- 驱动进程（`controller.py`）作为 daemon，在正确时机 `emit_intent()` 写新意图
- 不同请求配置不同的 `resources`（优先级唯一来自 manifest，意图不可覆盖）
- **新执行 = 新 request_id**，调度器天然可回溯不同时期的执行方式

## 模板三：once_migration（一次性）

适合场景：
- 迁移脚本（跑完就结束，不需要守护）
- 一次性数据修复任务

特点：
- 一个意图 = 一个 oneshot
- 跑完 exit 0 就 done，不需要守护
- 如果希望"跑完自动再次跑" → 用 daemon 或 multi_process_driver

## 模板通用字段

| manifest 字段 | 推荐值 | 说明 |
| --- | --- | --- |
| run_mode | auto | 注册即消费意图；manual 适合需要显式运维启动的场景 |
| priority | 20~60 | 高优 80+ 会抢占低优 |
| resources | cpu=0.1~1, memory_mb=64~2048 | 如实申报；运行后按画像动态调 |
| runtime.user | sched-run | 部署用户；本地开发可空 |

| 意图 lifetime.retry 字段 | 推荐值 | 说明 |
| --- | --- | --- |
| backoff_base_sec | 5 | 初始退避 |
| backoff_cap_sec | 300 | 封顶 |
| not_after | "" | 空=无绝对截止 |

**所有模板默认已内置 H13 进度日志**（启动/每步/结束 `print(..., flush=True)` + `enter_step` 写 progress）——复制后保留这些输出，替换业务函数即可，不要删掉日志。
