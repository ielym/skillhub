# 配置与参数完整参考（运维/任务作者必读）

> 本文覆盖调度器**全部可配置面**：任务侧 task.json 字段见 [contracts.md](contracts.md)，
> 本文讲运维侧 `data/settings.json`、全部 CLI 的确切行为、调度时刻语义、数据/日志布局、部署步骤。
> 所有默认值与代码根 `sched/config.py` 当前代码逐一对应。

## 1. 路径与多实例（SCHED_HOME）

| 路径 | 含义 |
| --- | --- |
| 代码根（默认 HOME） | scheduler 仓库 clone 目录（`sched` 包上一级；`SCHED_HOME` 可覆盖） |
| `$SCHED_HOME/tasks/<id>/` | 任务目录（task.json + run.py + cache/ + results/） |
| `$SCHED_HOME/data/settings.json` | 全局设置（首次启动/注册时自动生成默认值） |
| `$SCHED_HOME/data/jobs.json` | 注册表唯一真源，形如 `{"<id>": {"enabled": true}}` |
| `$SCHED_HOME/data/runtime/scheduler_state.json` | WQ 队列、cooldown/backoff、软资源容量（**禁手改**） |
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
  "soft_degrade_threshold": 3,
  "soft_degrade_window_sec": 600.0,
  "soft_degrade_cooldown_sec": 300.0,
  "hot_reload_sec": 30.0,
  "runner": {
    "kill_grace_sec": 10,
    "heartbeat_timeout_sec": 120,
    "cooldown_sec": 60,
    "grace_sec": 40,
    "max_resource_attempts": 0
  },
  "resource": {
    "window_samples": 8,
    "overshoot": 1.2,
    "memory_high_ratio": 1.5,
    "memory_max_ratio": 2.5,
    "overload_ratio": 2.0,
    "overload_sustain_sec": 60,
    "sample_interval_sec": 3,
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
| runner.cooldown_sec | 60 | success 与 preempted 后同 job 的冷却（防秒级连触发/连环抢占） |
| runner.max_resource_attempts | 0 | 资源重试封顶：**0=不设上限**（退让重试，默认）；正整数 N=第 N 次仍资源错误则转人工（止损逃生舱） |
| resource.window_samples | 8 | 画像 P95 滑窗样本数（最近 N 次正式 run） |
| resource.overshoot | 1.2 | 画像 P95 × 该系数为准出/账本预估 |
| resource.memory_high_ratio | 1.5 | run cgroup memory.high = 预估×1.5（内核节流软限） |
| resource.memory_max_ratio | 2.5 | run cgroup memory.max = 预估×2.5（硬限，超即 OOM kill） |
| resource.overload_ratio | 2.0 | 实测内存/预估 >2.0 判超限 |
| resource.overload_sustain_sec | 60 | 超限持续该秒数 → 优雅抢占（99 语义、断点续跑） |
| resource.sample_interval_sec | 3 | 监测采样周期；同时决定渐进式提交观察期 = max(2, 2×该值)=6s |
| resource.external_safety_margin_mb | 512 | 准出时给非调度器进程预留的内存（MB），防与外部进程互殴 |
| starvation_sec | 3600 | 同优先级等待超该秒数 → 饿死保护临时提权（101）参与排序 |
| preempt_exempt_sec | 60 | 被抢占任务重入队后的豁免窗口（秒），期内不再被抢 |
| data_risk_max_reschedules | 3 | 110 二刷最大自动轮数，达到后转人工 |
| soft_degrade_threshold | 3 | 软资源错误计数阈值（窗口内 101 次数） |
| soft_degrade_window_sec | 600 | 软资源错误计数窗口 |
| soft_degrade_cooldown_sec | 300 | 触发降额后的冷却时长，到期恢复登记容量 |
| hot_reload_sec | 30 | serve 重读 jobs.json/task.json 的周期；改任务配置无需重启，≤30s 生效 |
| web.enabled | false | 是否在 serve 进程内嵌 Web 管理台（FastAPI/uvicorn）；也可用 `serve --web/--no-web` 临时覆盖 |
| web.host | 127.0.0.1 | 监听地址。改成 `0.0.0.0`（公网/局域网）时强制要求 auth_token 或显式风险开关，否则 serve 拒绝启动 |
| web.port | 8799 | 管理台端口；页面 `/`，接口 `/api/*`，OpenAPI `/api/docs` |
| web.auth_token | 空 | HTTP Basic Auth 密码（用户名任意，仅校验密码，常量时间比较），保护全部页面与接口；非空即启用。**绑非回环地址的推荐做法** |
| web.allow_public_no_auth | false | 显式承认"无密码暴露公网"。仅当 host 非回环且 auth_token 为空时需要；不设此开关又改公网 host，serve 启动直接失败（防不知不觉裸奔） |

资源退避重试的**实际序列**（代码计算，不可配置）：第 1 次失败等 300s，第 2 次 600s，
第 3 次起 1200s 并维持（20 分钟封顶，不是 1 小时）；`max_resource_attempts>0` 时在第 N 次转人工。

## 3. 调度时刻语义（interval / once / manual）

- **interval 无时间窗**：首次触发时刻 = 注册生效（或 serve 启动/热加载 upsert）后**再过一个 interval**，
  不是"注册后立刻跑一次"，也不按整点对齐；之后每隔 interval 一次。
- **interval 带 start_time/end_time（可带 weekdays）**：触发点对齐到**窗口起点的 interval 网格**
  （如 08:00 起每 3600s → 08:00/09:00/…/22:00）；`end_time < start_time` 视为跨天窗
  （如 22:00–06:00）；weekdays 不填=每天，1=周一…7=周日。
- **once**：`once_at` 必须是带时区 ISO8601（如 `2026-10-03T20:00:00+08:00`）；
  **时刻已过 → 永不触发**（list 中 next 显示为空），只能重新 register 或改配置。
- **manual**：不自动触发；只能 `run <id>` 入队。注意 manual 任务**同样参与抢占/心跳/资源体系**
  （仅心跳阈值 ×2）；`contract_exempt` 的 manual 任务才不可抢占、不可自动恢复。
- 热加载保序：运行中改 task.json 不会把未到的触发时刻重置为 now+interval。
- 到点时在途实例已达 `max_instances`：`overflow=skip` 本次跳过（记 decisions 日志）；
  `queue` 照常入队排队。跳过/排队都不算失败。

## 4. CLI 完整行为（均在代码根执行：`python3 -m sched <cmd>`）

| 命令 | 确切行为与输出 | 失败情形 |
| --- | --- | --- |
| `register <id>` | 校验用户存在 → 跑五道闸 → 写 jobs.json(enabled=true)+初始画像 → 输出 `注册成功：<id>` 及每闸通过原因 | 目录/task.json 非法、用户不存在、任一闸不过：打印 `注册失败：<各闸名: 原因>`，exit 1，不写注册表 |
| `run <id>` | **只入队**（trigger=manual，状态 waiting），输出 `已入队：<run_id> (<id>, priority=<n>)`；是否/何时跑由 serve 准出 | 未注册/`ok=false`（task.json 损坏）：`触发失败：...` exit 1；**无 --dry-run**，dry 只能靠任务自己读 SCHED_DRY_RUN |
| `list` | 每行 `<id>  pri=<n> ok=<bool> next=<ISO 时刻或 ->`（先热加载，manual/过期 once 显示 `-`） | 仅读，不失败 |
| `status` | `jobs/waiting/running` 计数 + 账本 reserved/actual 内存 + 每行软资源 `soft[<name>] cap=<n> used=<n>` | 仅读 |
| `set-soft <name> <n>` | 立即设置软资源容量并持久化（n 为非负整数；0=不允许使用，未配置=无该池，任务将永远等待） | n 非整数报错 |
| `serve` | 前台常驻：单实例 flock、cgroup 自检（不可用打印 WARNING 降级运行）、热加载、触发/准出/抢占/监测四 tick（1s）；Ctrl-C 优雅停机（先 SIGTERM 等 kill_grace_sec，再 SIGKILL；在途 run 以 interrupted 断点重入队）。加 `--web` 同时启动内嵌管理台（打印 `管理台：http://...`），`--no-web` 强制不启动 | 已有实例在跑：`启动失败：已有调度器实例在运行（runtime/scheduler.lock 被占用）` exit 1 |

**没有的命令（不要找、不要自己造）**：无独立 web/ui 命令（管理台**只能内嵌在 serve 进程**，
另起 Web 进程写 scheduler_state.json 会与 serve 内存态互相覆盖）、无 unregister、
无 kill/stop 单个任务、无 run --dry-run、无改 settings 的 CLI（手编 settings.json）、
无查看 run 详情的 CLI（直接读 `data/runs/<id>.jsonl` 与日志文件，或用管理台）。
（停用任务可用管理台开关，等价于手编 jobs.json 的 enabled。）

### 4.1 Web 管理台能力与边界（serve --web）

- **只读**：总览（账本/软资源/整机容量/参数）、任务表（下次触发/ok/启用）、WQ 与在途、run 历史与
  stdout/stderr、decisions 审计流、资源画像（P95/声明/样本数）。
- **写操作全部与 CLI 等价且走同一 SchedulerService 实例**：手动触发（只入队，绝不旁路拉起进程）、
  enable/disable、set-soft、新建任务（生成最小合规骨架）、在线编辑任务文件、跑五闸注册
  （SSE 逐闸推送通过/失败原因与耗时，注册前自动执行 `chown -R <run_user>` 并把写入文件置 0644）。
- 文件编辑安全边界：仅限任务目录内 `.py/.json/.txt/.md/.conf/.yaml/.sh` 等源码类文件（单文件 ≤1MB）；
  `cache/`、`results/`、`__pycache__/` 禁止经 Web 读写；目录穿越（`..`）拒绝。
- 所有写动作落 `decisions.jsonl`（web_create_task/web_save_file/web_set_enabled…）可审计。
- **暴露面三档（按安全优先）**：
  1. 默认回环 + SSH 隧道（零额外攻击面）：`ssh -L 8799:127.0.0.1:8799 <服务器>`；
  2. 公网/局域网 + `web.auth_token`：host 改 `0.0.0.0` 并配密码，浏览器 Basic 弹窗输入（用户名任意）；
  3. 公网无密码：必须显式 `web.allow_public_no_auth=true` 否则 serve 拒绝启动——
     **管理台能在线改 .py 并注册执行（等同 RCE），此档风险自负，强烈建议同时在云安全组
     把入站 8799 限制为特定源 IP 段**，不要对 0.0.0.0/0 开放。
- 云主机还需在**安全组/防火墙**放行对应 TCP 入站端口；改 host 只解决监听，不替代安全组。
  HTTP 明文（含 Basic 密码）会经链路传输，需要保密时用反代 + TLS（nginx + 证书）。

## 5. 首次部署清单（root 执行一次）

```bash
# 1) 运行用户（默认 sched-run；多租户各自独立用户，在任务 runtime.user 指定）
useradd -r -m -s /usr/sbin/nologin sched-run

# 2) cgroup v2 嵌套控制器委派（关键！不做则硬限额静默失效，见 SKILL.md 自检命令）
mkdir -p /sys/fs/cgroup/sched
echo '+memory +cpu' > /sys/fs/cgroup/sched/cgroup.subtree_control

# 3) 任务目录权限：sched-run 需能读任务代码、写 cache/results（建议属主 sched-run 或 o+rx）
chown -R sched-run:sched-run <代码根>/tasks/<id>

# 4) 软资源容量（任务声明了 resources.soft 才需要）
python3 -m sched set-soft proxy 10

# 5) 常驻（建议 systemd 托管，ExecStart=python3 -m sched serve，重启策略 on-failure）
python3 -m sched serve --web     # 加 --web 启动内嵌管理台（默认 127.0.0.1:8799）
```

任务进程环境补充事实：降权执行时任务进程的 `HOME` 会被改成目标用户的家目录（不是 /root）；
透传白名单仅 `PATH HOME LANG TZ LC_ALL PYTHONPATH PYTHONUNBUFFERED`，PYTHONPATH 自动前置项目根；
密钥不要走 env（同机进程可读 `/proc/<pid>/environ`），放任务目录 600 权限文件。

## 6. 常见运维操作

- 改任务配置/代码：编辑 task.json/run.py → serve ≤30s 热加载（list 的 ok 变 false 即配置非法，修到 ok 自动恢复）；
  改了 `resources` 需要重新 register 才会更新画像/注册信息。
- 临时停用任务：编辑 `data/jobs.json` 把该 id 的 `enabled` 置 false（这是注册表的设计字段），
  或在管理台任务表拨动开关（两者完全等价）；在途 run 不受影响，跑完后不再触发；重新启用置回 true。
- 删除任务：按 [acceptance.md](acceptance.md) C4 的 5 步流程（jobs.json 删条目 → 删任务目录 → 删 runs 日志）。
- 任务一直 waiting：先 `status` 看账本余量与软资源 cap/used，再看 `decisions.jsonl` 尾部；
  容量未配置、资源申报超剩余、处于 backoff/cooldown 都会等待，均属正常排队语义。
- serve 重启：启动时自动把上轮在途 run 记 interrupted 并携断点重入队（contract_exempt 只记待人工）；
  残留孤儿进程组会被 kill，残留 cgroup 会被清理。
