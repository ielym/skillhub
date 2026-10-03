# 配置与参数完整参考（运维/任务作者必读）

> 本文覆盖调度器**可配置面**：任务侧 task.json 字段见 [contracts.md](contracts.md)，
> 本文讲路径与数据布局、运维侧 `data/settings.json` 全参数、全部 CLI 的确切行为。
> 触发时刻与调度语义见 [scheduling.md](scheduling.md)；部署、Web 暴露与运维操作见
> [deployment.md](deployment.md)。所有默认值与代码根 `sched/config.py` 当前代码逐一对应。

## 1. 路径与多实例（SCHED_HOME）

| 路径 | 含义 |
| --- | --- |
| 代码根（默认 HOME） | scheduler 仓库 clone 目录（`sched` 包上一级；`SCHED_HOME` 可覆盖） |
| `$SCHED_HOME/tasks/<id>/` | 任务目录（task.json + run.py + cache/ + results/） |
| `$SCHED_HOME/data/settings.json` | 全局设置（首次启动时自动生成默认值） |
| `$SCHED_HOME/data/jobs.json` | 注册表唯一真源，形如 `{"<id>": {"enabled": true}}` |
| `$SCHED_HOME/data/runtime/scheduler_state.json` | WQ 队列（等待项含 not_before 最早准出时刻，**禁手改**） |
| `$SCHED_HOME/data/runtime/admission.json` | 自动上线检查状态（未通过任务的原因/尝试次数/最后指纹，自动维护，勿手改） |
| `$SCHED_HOME/data/runtime/profiles.json` | 任务资源画像（冒烟+正式 run 实测，自动更新） |
| `$SCHED_HOME/data/runtime/ledger.json` | 资源账本（运行期内存态，勿手改） |
| `$SCHED_HOME/data/runtime/active.json` | 在途 run 快照（崩溃恢复依据，勿手改） |
| `$SCHED_HOME/data/runtime/scheduler.lock` | serve 单实例 flock（残留 = 上次非正常退出，确认无 serve 后可删） |
| `$SCHED_HOME/data/runtime/decisions.jsonl` | 调度决策审计日志（enqueue/admit/preempt/retry/terminal…） |
| `$SCHED_HOME/data/runs/<id>.jsonl` | 每 run 一条终态记录（**排障第一入口**） |
| `$SCHED_HOME/data/runs/<id>/<run_id>.stdout.log` `.stderr.log` | 任务输出，单文件上限 32MB，超出截断并写 `[truncated]` |

- `SCHED_HOME` 环境变量可覆盖根目录（测试隔离用）；**生产不设置**，用默认路径。
- `ensure_layout()` 在 serve/register 时自动创建 tasks/data/runs/runtime 目录并补默认 settings.json。
- settings.json 解析失败会被静默重置为默认值并覆盖——**手改时务必保证 JSON 合法**（改后 `python3 -m json.tool` 校验）。

## 2. settings.json 全参数（data/settings.json）

```json
{
  "timezone": "Asia/Shanghai",
  "run_user": "sched-run",
  "max_log_mb": 32,
  "starvation_sec": 3600.0,
  "preempt_exempt_sec": 60.0,
  "data_risk_max_reschedules": 3,
  "hot_reload_sec": 30.0,
  "runner": {
    "kill_grace_sec": 10,
    "heartbeat_timeout_sec": 120,
    "grace_sec": 40
  },
  "resource": {
    "window_samples": 8,
    "overshoot": 1.2,
    "memory_high_ratio": 1.5,
    "memory_max_ratio": 2.5,
    "overload_ratio": 2.0,
    "overload_sustain_sec": 60,
    "sample_interval_sec": 3,
    "profile_live_interval_sec": 60,
    "external_safety_margin_mb": 512
  },
  "web": {
    "enabled": false,
    "host": "127.0.0.1",
    "port": 8799,
    "auth_token": "",
    "allow_public_no_auth": false
  }
}
```

| 参数 | 默认 | 取值含义与调整影响 |
| --- | --- | --- |
| timezone | Asia/Shanghai | IANA 时区名；所有窗口/once 计算的基准；非法值启动报错 |
| run_user | sched-run | 全局降权执行用户。**置空串 `""` = 显式禁用降权**（仅本机测试用，生产禁止）；任务级 `runtime.user` 优先于它 |
| max_log_mb | 32 | 每个 stdout/stderr 日志文件截断上限（MB） |
| runner.kill_grace_sec | 10 | **cancel 类信号**（窗口收口、serve 优雅停机、手动终止）SIGTERM→SIGKILL 宽限 |
| runner.grace_sec | 40 | **抢占** SIGTERM 后等任务保存断点退出 99 的宽限；超时 SIGKILL → preempt_failed 转人工 |
| runner.heartbeat_timeout_sec | 120 | 全局心跳超时兜底；任务 `heartbeat.timeout_sec` 可单独设更长（下限 5）；manual 触发运行时阈值 ×2 |
| resource.window_samples | 8 | 画像 P95 滑窗样本数（最近 N 次正式 run + 运行中动态采样） |
| resource.overshoot | 1.2 | 画像 P95 × 该系数为准出/账本预估 |
| resource.memory_high_ratio | 1.5 | run cgroup memory.high = 预估×1.5（内核节流软限） |
| resource.memory_max_ratio | 2.5 | run cgroup memory.max = 预估×2.5（硬限，超即 OOM kill） |
| resource.overload_ratio | 2.0 | 实测内存/预估 >2.0 判超限 |
| resource.overload_sustain_sec | 60 | 超限持续该秒数 → 优雅抢占（99 语义、断点续跑） |
| resource.sample_interval_sec | 3 | 监测采样周期；同时决定渐进式提交观察期 = max(2, 2×该值)=6s |
| resource.profile_live_interval_sec | 60 | 运行中动态画像采样落盘间隔（秒）：运行中的 run 按此节流把 cgroup 实测 CPU/内存写入画像滑窗 |
| resource.external_safety_margin_mb | 512 | 准出时给非调度器进程预留的内存（MB），防与外部进程互殴 |
| starvation_sec | 3600 | 同优先级等待超该秒数 → 饿死保护临时提权（101）参与排序 |
| preempt_exempt_sec | 60 | 被抢占任务重入队后的豁免窗口（秒），期内不再被抢 |
| data_risk_max_reschedules | 3 | 110 二刷最大自动轮数，达到后转人工 |
| hot_reload_sec | 30 | serve 重读 jobs.json/task.json、扫描新任务目录的周期；改任务配置无需重启，≤30s 生效 |
| web.enabled | false | 是否在 serve 进程内嵌 Web 管理台（FastAPI/uvicorn）；也可用 `serve --web/--no-web` 临时覆盖 |
| web.host | 127.0.0.1 | 监听地址。改成 `0.0.0.0`（公网/局域网）时强制要求 auth_token 或显式风险开关，否则 serve 拒绝启动 |
| web.port | 8799 | 管理台端口；页面 `/`，接口 `/api/*`，OpenAPI `/api/docs` |
| web.auth_token | 空 | HTTP Basic Auth 密码（用户名任意，仅校验密码，常量时间比较），保护全部页面与接口；非空即启用。**绑非回环地址的推荐做法** |
| web.allow_public_no_auth | false | 显式承认"无密码暴露公网"。仅当 host 非回环且 auth_token 为空时需要；不设此开关又改公网 host，serve 启动直接失败（防不知不觉裸奔） |

**资源错误重试 = 任务自治，调度器不设全局冷却/退避/重试上限**：资源错误（exit 100
本机固定资源、exit 101 外部资源、未分类错误）结束后，run **立即回到 WQ 排队**
（不 sleep、不退避），其它任务释放资源、下一轮准出自然再跑；重试间隔、最大尝试次数、
时效截止全部由任务在 task.json 的 `retry` 段声明（见
[contracts.md](contracts.md) §任务自治重试），任务还可在运行中用 SDK
`set_retry_hint()` 按当天情况收紧。调度器不感知、不池化外部资源（不同账号/不同协议
无法统一管理），只依据任务自报的退出码调整调度。

**任务侧责任（重要）**：隧道代理每连接换出口 IP，单连接被掐断（IncompleteRead/响应截断）是
高频瞬时故障——任务**必须先就地快速重试若干次**（每次新连接换新 IP，间隔几秒递增），连续
失败才 `sys.exit(101)` 交给调度器立即重排队；是否还需要间隔（`retry.delay_sec`）、
今天最多再试几次（`max_attempts`）、几点之后放弃（`not_after`）由任务按场景声明，
一次抖动不该拖垮节奏。
判断标准：换个连接/换个 IP 可能成功的问题，先自己重试；整类资源在一段时间内确定性不可用，
才上报 101，并用 retry 段/`set_retry_hint` 控制重试节奏与止损。

管理台**不再有「运行参数」面板**：时区固定 Asia/Shanghai（settings.json 里仍可手编），
成功冷却、资源退避 base/cap、max_resource_attempts、闸失败定时重试这些全局旋钮均已删除
——重试节奏是任务自己的契约（retry 段）。管理台只保留**任务级纯调度参数**的行内编辑
（优先级、完整 schedule、心跳超时、retry 三字段），保存立即生效；引擎内部参数需要时
手编 settings.json 后重启。

## 3. CLI 完整行为（均在代码根执行：`python3 -m sched <cmd>`）

| 命令 | 确切行为与输出 | 失败情形 |
| --- | --- | --- |
| `register <id>` | **可选的立即检查**：立刻对该任务跑五道上线检查（serve 本身会在热加载时自动检查新任务，此命令用于不想等 ≤30s 扫描）。通过则写 jobs.json(enabled=true)+初始画像，输出 `上线检查通过，已纳入调度：<id>` 及每闸结果 | 目录/task.json 非法、用户不存在、任一闸不过：打印 `上线检查未通过：<原因>`，exit 1，不写注册表 |
| `run <id>` | **立即运行一次**（trigger=manual，只入队），输出 `已加入运行队列：<run_id> (<id>, priority=<n>)`；是否/何时跑由 serve 准出。也是 `contract_exempt`（声明不可断点恢复）任务的人工触发通道 | 任务不存在/`ok=false`（task.json 损坏）：`运行失败：...` exit 1；**无 --dry-run**，dry 只能靠任务自己读 SCHED_DRY_RUN |
| `list` | 每行 `<id>  pri=<n> ok=<bool> next=<ISO 时刻或 ->`（先热加载，manual/过期 once 显示 `-`） | 仅读，不失败 |
| `status` | 任务数/等待运行/运行中计数 + 账本预留/实测内存；若有未通过上线检查的任务，逐个打印 `[未通过] <id>：<原因>` | 仅读 |
| `serve` | 前台常驻：单实例 flock、cgroup 自检（不可用打印 WARNING 降级运行）、**自动发现 `tasks/` 新任务并后台串行跑五道上线检查**（闸失败不做定时重试；失败原因可在 status/管理台/admission.json 查看，修改或删除任务文件后按新指纹自动重检）、热加载、触发/准出/抢占/监测四 tick（1s）；Ctrl-C 优雅停机（先 SIGTERM 等 kill_grace_sec，再 SIGKILL；在途 run 以 interrupted 断点重入队）。加 `--web` 同时启动内嵌管理台（打印 `管理台：http://...`），`--no-web` 强制不启动 | 已有实例在跑：`启动失败：已有调度器实例在运行（runtime/scheduler.lock 被占用）` exit 1 |

**没有的命令（不要找、不要自己造）**：无独立 web/ui 命令（管理台**只能内嵌在 serve 进程**，
另起 Web 进程写 scheduler_state.json 会与 serve 内存态互相覆盖）、无 unregister、
无 CLI 停止单个 run（用管理台队列页「停止」按钮，cancel Event→SIGTERM、断点可续）、
无 run --dry-run、无改 settings 的 CLI（手编 settings.json 后重启）、
**无任何外部资源（代理/配额等）配置命令**（不存在 set-soft 一类接口：外部资源无法统一
管理，任务用 exit 101 自分类、立即重排队并受自身 retry 段约束）、无查看 run 详情的 CLI
（直接读 `data/runs/<id>.jsonl` 与日志文件，或用管理台；管理台历史可删记录/连带日志）。
（停用任务可用管理台开关，等价于手编 jobs.json 的 enabled；想彻底移除就把任务目录移出 `tasks/`。）

Web 管理台的能力边界（导入任务/调度参数编辑/停止/历史删除，**不含文件查看编辑**）与
公网暴露三档安全模式见 [deployment.md](deployment.md) §2。
