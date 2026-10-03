# 技术契约参考（task.json / SDK / 环境变量 / 状态文件 / 错误码）

> 本文是任务作者与调度器之间的"接线手册"，与 [rules.md](rules.md) 的铁律、[gates.md](gates.md) 的闸门配套。
> 所有行为以代码根当前实现为准。路径一律相对任务目录
> （`$SCHED_WORKSPACE`，即 `tasks/<id>/`）。

## 1. task.json 字段全表（schema_version=2）

| 字段 | 类型 | 默认 | 约束与语义 |
| --- | --- | --- | --- |
| schema_version | int | 必填 | 新任务写 2；1 兼容但不新用 |
| name | str | "" | 展示名；为空时回落到 entry.file |
| description | str | "" | 说明 |
| entry.file | str | 必填 | 入口相对路径，不允许 `..`/绝对路径，必须存在 |
| entry.interpreter | str\|null | "python3" | 仅命令名（无路径无空格）；null 表示直接执行，入口须有 x 权限 |
| entry.args | str[] | [] | 命令行参数，元素必须都是字符串 |
| entry.cwd | str | "." | 相对工作目录，约束在任务目录内 |
| schedule.type | enum | "manual" | interval / once / manual |
| schedule.interval | int | 无 | interval 必填，正整数秒。无窗时首次触发=生效后再过一个 interval（非整点对齐）；带时间窗时对齐窗口起点网格，详见 [configuration.md](configuration.md) |
| schedule.once_at | str | 无 | once 必填，带时区的 ISO8601；**过去时刻上线后永不触发** |
| schedule.start_time/end_time | str | 无 | `HH:MM` 或 `HH:MM:SS`，成对出现；end<start 视为跨天 |
| schedule.weekdays | int[] | [] | 1=周一…7=周日；空=每天 |
| schedule.allow_overrun | bool | false | false=越过窗口终点立即 cancel（SIGTERM/10s）→ killed 转人工，**不自动续跑**；true=越过窗口也允许跑完 |
| schedule.max_instances | int | 1 | 1–20，同任务在途（等待+运行）实例上限 |
| schedule.overflow | enum | "skip" | skip=触发时满员直接跳过；queue=入队等待 |
| priority | int | 0 | **0–100，越大越优先**；决定准出顺序与能否抢占低优 |
| env | map | {} | string→string；黑名单键拒绝；**不得放密钥** |
| outputs.expect | str[] | [] | 交付物相对路径；run 成功但任一文件缺失 → 改判 failed |
| resources.cpu | float | 0 | 单 run 平均核数预算；超整机拒绝上线；0 且无实测=未知被拒 |
| resources.memory_mb | int | 0 | 单 run 内存上限(MB)；规则同上。**resources 只有这两个字段**；代理/VPN/配额等外部资源不申报（见 §7） |
| error_rules.resource_regex | str[] | [] | 命中（忽略大小写）异常消息→resource 分类（叠加内置资源模式） |
| error_rules.logic_regex | str[] | [] | 命中→logic 分类（优先级高于 resource 规则） |
| heartbeat.timeout_sec | int | 120 | ≥5；state 超过该秒数未更新即判卡死；manual 任务阈值 ×2 |
| smoke.mode | enum | "dry" | dry=冒烟注入 SCHED_DRY_RUN=1；real=真实执行冒烟 |
| smoke.max_runtime_sec | int | 60 | 冒烟收敛时限 |
| smoke.signal_after_sec | float | 1.5 | 闸5 起跑后多久发 SIGTERM（步骤慢的任务调大，如 3–5） |
| runtime.user | str | "sched-run" | 降权执行用户，必须已存在；空串=以调度器身份执行（仅限测试） |
| contract_exempt | bool | false | true ⇒ type 必须为 manual；不可抢占、崩溃/抢占不自动恢复 |

env 黑名单（出现即闸1 失败）：`LD_PRELOAD`、`LD_LIBRARY_PATH`、`LD_AUDIT`、`LD_DEBUG`、
`PYTHONSTARTUP`、`PYTHONINSPECT`、`BASH_ENV`、`ENV`、`IFS`、`PATH`。

## 2. 调度器注入的环境变量（任务只读）

| 变量 | 取值与用途 |
| --- | --- |
| SCHED_JOB_ID | 任务 id |
| SCHED_RUN_ID | 运行实例 id（如 `20261003T120000-a1b2c3d4`）；决定实例级状态目录；本地裸跑时缺省为 `local` |
| SCHED_TRIGGER | `manual` / `interval` / `once` / `second_pass`（110 二刷）/ `contract`（闸门期） |
| SCHED_ATTEMPT | 第几次尝试（资源退避重试递增） |
| SCHED_SCHEDULED_AT | 本次调度时刻 ISO |
| SCHED_WORKSPACE | 任务目录绝对路径，所有产物的根 |
| SCHED_DRY_RUN | `1`=冒烟/dry（禁止真实副作用）；`0`=正式 |
| SCHED_CONTRACT_PROBE | `1`=契约探针模式（SDK 自动走自检分支，任务无需处理） |
| SCHED_ERROR_RULES | task.json 错误分类正则的 JSON（SDK 自动加载） |

透传白名单（仅这些父进程环境变量进入任务）：`PATH HOME LANG TZ LC_ALL PYTHONPATH PYTHONUNBUFFERED`。
PYTHONPATH 已自动加项目根，直接 `from sched_task_sdk import SchedTask, Step, run_task` 即可。
降权执行时 `HOME` 会被改成目标运行用户的家目录（不是 /root），任务不要依赖调度器启动环境。

## 3. 任务目录文件布局（运行时约定）

```
tasks/<id>/
├── task.json                     # 声明（唯一需要手写的配置）
├── run.py                        # 入口（继承 SchedTask）
├── <业务配置>                     # 自带配置文件（密钥文件 chmod 600）
├── cache/
│   ├── runs/<run_id>/state.json  # 实例级状态：心跳/进度/last_error（SDK 写）
│   ├── resume_point.json         # 任务级断点：{"resume_point": {...}}，跨运行续跑依据
│   ├── state.json                # legacy 回退（新代码不要主动写）
│   ├── pending_skipped.jsonl     # 跳过项（skip_item 写，second_pass 消费；自动去重）
│   └── dead_letter.jsonl         # 确认不可救的数据条目
└── results/                      # 交付物（outputs.expect 在这里列）
```

- state.json 与断点均为**原子写 + flock**，可安全被心跳线程与主线程并发写；任务自己的附加文件也要原子写。
- `cache/`、`results/` 是运行时产物：不应纳入版本提交；上线检查/运行时自动创建。
- 实例隔离：同一任务多实例（max_instances>1）各写各的 `runs/<run_id>/`；断点文件任务级共享，
  因此**断点内容必须与实例无关、可被任一恢复实例消费**。

state.json 字段（SDK as_dict）：

| 字段 | 说明 |
| --- | --- |
| schema_version | 当前为 2 |
| status | running / success / preempted / failed / intentional_exit |
| current_step | 当前步名（yield 的 Step.name） |
| next_action | 自描述下一步（可选） |
| progress | 0–100 整数 |
| loop_count | 已完成步数 |
| resume_point | 断点对象（同时写 resume_point.json） |
| metrics | 自定义指标对象 |
| last_error | `{"category": "resource|logic|unclassified", "message": "..."}` |
| started_at / updated_at | ISO 时间戳；updated_at 的 mtime 即心跳 |

## 4. SDK API（sched_task_sdk）

```python
from sched_task_sdk import SchedTask, Step, run_task
from sched_task_sdk import resource, logic, Category

class MyTask(SchedTask):
    def steps(self, resume: dict):           # resume = 上次断点，首次为 {}
        start = resume.get("cursor", 0)
        for item in self.work_items(start=start):
            yield Step("process", {"id": item.id})   # 可观测步（心跳/展示）
            self.handle(item)                      # 单条异常要自己抓 → skip_item，勿炸整轮
            self.state.resume_point = {"cursor": item.id}
            self.state.flush()                     # 每步末落盘断点（抢占恢复点）

if __name__ == "__main__":
    sys.exit(run_task(MyTask()))
```

| API | 行为契约 |
| --- | --- |
| `steps(resume)` | **必须实现**的生成器；恢复时 resume 来自 cache/resume_point.json |
| `yield Step(name, payload=None)` | 声明一个可观测步；SDK 在每步自动 flush 状态并检查停止位 |
| `state.flush()` | 原子写实例状态 + 断点；每步末必须调用 |
| `state.resume_point` | dict；成功后由 SDK 清空；抢占时作为重入队凭证 |
| `dry_run` 属性 | bool，读 SCHED_DRY_RUN；dry 下所有真实副作用必须短路 |
| `skip_item(item_id, reason)` | 追加 pending_skipped（同 item 自动去重），不中断本轮 |
| `read_pending_skipped()` | 读跳过项列表；second_pass 轮（SCHED_TRIGGER）消费补跑 |
| `dead_letter(item_id, reason)` | 写死信，明确放弃 |
| `resource() / logic()` | 分类辅助字符串（"resource"/"logic"） |
| `run_task(task)` | 入口：PROBE 环境自动自检；否则运行 steps；托管 SIGTERM/SIGINT |

**⚠️ 已实测的 API 陷阱（必须遵守，否则状态造假）：**

1. **不要在 steps() 内部调用 `fail()` 后 return 来结束任务**。当前 SDK 的 `fail()` 只置状态不抛异常，
   生成器正常结束后 `run()` 末尾会**无条件 mark_success → 退出码被覆盖为 0、状态被覆盖为 success**
   （逻辑失败会被伪装成成功）。`fail()` 仅适用于不经 run_task 的特殊封装，普通任务一律不要用。
2. **逻辑错误的可靠上报方式**：在 steps 内 `raise ValueError("LOGIC: ...")`，并在 task.json
   `error_rules.logic_regex` 声明 `"LOGIC:"`（异常消息先过 logic 正则，命中即 category=logic、
   exit 1、state=failed，调度器转人工不重试）。实测：`ValueError: LOGIC: ...` → exit 1 / failed / logic。
3. **100/101/110 的可靠方式**：先 `state.mark_failed(...); state.flush()`（落分类与现场），再
   `sys.exit(101)` / `sys.exit(110)`。SystemExit 被 run() 原样透传，退出码不被覆盖。实测退出码与
   state 均正确（101→resource，110→data_risk）。
4. **意图内提前成功**（如当日不命中）直接 `return` 让生成器自然结束即可（SDK 自动 mark_success）；
   `finish(0)` 等价，但不要用 `finish(非0)`（同样会被末尾覆盖回 0）。

内置信号行为：SIGTERM/SIGINT 只置 `_stop_requested`，**不打断当前步**；下一道步边界自动
`mark_preempted()→flush→退出 99`。后台心跳线程每 30s flush 一次，保证长 IO 步不被误判卡死
（因此单步仍应避免无超时的阻塞调用——进程整体挂死时心跳也停）。

异常自动分类：`classify_exception(exc, resource_regex, logic_regex)`——先匹配 logic 正则，
再匹配资源正则（内置含 timeout/429/rate limit/connection/proxy/socket/refused/unreachable/
oom/quota/temporary 等），都不命中记 **unclassified**（调度器兜底按资源错误重试）。
任务可在 `__init__` 后给 `self.resource_regex/self.logic_regex` 赋值覆盖环境注入规则。

## 5. 退出码与终态（统一错误码协议）

| 退出码 | 含义 | 调度器终态与后继动作 |
| --- | --- | --- |
| 0 | 成功（且 outputs.expect 全部存在；缺失改判 failed） | success；进入 success 冷却（默认 60s） |
| **99** | 干净抢占：断点已保存 | preempted；冷却后**携断点自动重入队**，60s 内不再被抢 |
| **100** | 本机固定资源错误（内存/CPU/磁盘等硬资源或通用资源不足） | resource；退避后重入队，**默认无限重试**。退避序列（代码实际值）：300s→600s→1200s→2400s→封顶 3600s |
| **101** | 外部资源错误（代理/隧道失效、429 限流、API 配额、连接失败等） | 与 100 同一条退避重试路径；调度器不感知、不池化外部资源，仅按此退出码调整调度 |
| **110** | 数据风险：跳过项已落 pending_skipped | failed(data_risk)；自动以 `SCHED_TRIGGER=second_pass` 重入队，**最多 3 轮**仍 110 转人工 |
| 1 | 逻辑错误代表码 | 看 last_error.category：logic → failed 转人工；缺省/unclassified → 兜底按资源重试 |
| 137 / -9 | SIGKILL 归因 | 三态：cgroup OOM → resource 重试；调度器抢占/取消超时强杀 → preempt_failed 转人工；外部 kill → failed |
| 其他非 0 | 未知 | 有任务自报分类按分类；无自报一律按资源重试（宁重试不错杀） |

**101/110 的当前用法（SDK 未封装一键退出码）**：先写好状态/跳过项，再裸退出：

```python
# 110：本轮有跳过项，请求调度器二刷
self.skip_item(bad_id, "parse error")
self.state.mark_failed("data_risk", f"{len(ids)} items skipped")  # category 仅作记录
self.state.flush()
sys.exit(110)

# 101：外部资源失败（如代理 429 / 隧道失效 / 配额耗尽）
self.state.mark_failed("resource", "proxy 429")
self.state.flush()
sys.exit(101)
```

二刷轮写法（SCHED_TRIGGER=second_pass）：读取 pending_skipped 逐条补跑，成功后记结果/清账；
补不动的进 dead_letter，最终以 0 收尾。3 轮后仍 110 转人工，此时必须人工排查 pending_skipped。

**逻辑错误必须显式化**：`raise ValueError("LOGIC: 券面校验失败: ...")` 并在 task.json
`error_rules.logic_regex` 写 `"LOGIC:"`。未命中任何分类规则的异常（unclassified，exit 1）即便真是
逻辑 bug 也会被兜底机制当资源错误无限退避重试；这是机制倒逼，不是宽松。
（再次提醒：在 steps 里调 `self.fail(...)` 然后 return 会被覆盖成 exit 0/success，禁止这样写。）

## 6. 三大运行期契约

### 6.1 抢占/断点

- 触发条件：**严格更低优先级**在跑任务才会入选（同优先级永不互相抢占）；贪心选择最少的低优任务集合
  释放 CPU/内存缺口；被选任务 60s 豁免期内不重复被抢。
- 时序：SIGTERM → 步边界落断点 → exit 99（宽限 40s）→ 调度器记账释放 → 高优准出 → 被抢者重入队。
- 设计推论：**步长 ≤20s**（留足 flush 与宽限余量）；断点必须是"已完成位点"；续跑循环必须从断点游标开始；
- 任何一步的副作用在重放时必须幂等（upsert/带幂等键/先查后写）。

### 6.2 心跳（监测面）

- 证据：实例 state.json 的 mtime（或 updated_at）距检查时刻的秒数。
- 阈值：heartbeat.timeout_sec（≥5，默认 120；manual 触发 ×2 放宽但不豁免）。
- 超时后果：整组 cancel → killed；首次心跳超时按中断语义重入队 1 次，**连续第二次转人工**。
- SDK 任务：心跳线程 30s 自动 flush，无需手写；但主线程死锁/整进程挂起时心跳同样停——不要在步内
  做无超时的锁等待/网络等待。

### 6.3 超限退让（防打爆的运行期防线）

- cgroup 双水位：memory.high ≈ 预估×1.5（内核节流）、memory.max ≈ 预估×2.5（超限 OOM 杀）；
  cpu.max 按预估核数限制。
- 监控：实测内存 > 预估×overload_ratio(2.0) 且持续约 60s → 优雅抢占（99 语义，断点重入队），不是硬杀。
- 任务侧推论：申报要贴近真实 P95；长期超限说明申报或任务本身有问题，会反复被退让，不要指望超限运行。

## 7. 外部资源（代理隧道 / VPN / API 配额）：只按退出码调度，不做容量管理

- **为什么不统一管理**：外部资源跨账号、跨协议（IP 隧道与 VPN 无法同口径计量，别的账号占用的资源
  调度器根本感知不到），混在一起设容量池既不可信也无意义。因此 task.json **没有**这类字段，
  也没有 set-soft 之类配置命令。
- **调度器怎么应对**：任务在运行中真实遇到代理失效/429/配额耗尽/连接失败时，先 flush 现场，然后
  快速 `sys.exit(101)`；调度器按与 100 相同的指数退避（300s→600s→1200s→2400s→封顶 3600s）
  自动重入队重试，`max_resource_attempts>0` 时到次数转人工。
- **任务侧纪律（两层重试，各司其职）**：
  1. **瞬时单连接故障先就地快速重试**：隧道代理每次连接自动换出口 IP，传输中途被掐断
     （IncompleteRead、响应 JSON 截断、偶发连接重置）发生率很高且与具体 IP/连接相关。
     对这类"换个连接可能就好"的错误，任务应在**同一步骤内**重试 3~4 次（间隔 2/4/8s
     递增，每次新连接换新 IP），幂等步骤可安全重放；
  2. **连续失败才快速 101**：重试全部失败说明资源在一段时间内确定性不可用，立即 flush 后
     `sys.exit(101)`，把长节奏交给调度器退避。一次抖动就 101 = 白白等一小时，属于 bug。
  不要做的是：代理池排队、长睡眠占坑死等——占着 CPU/内存硬资源不放手更糟。
  资源的选用、换号、切换协议都由任务自身负责。
- 冒烟（dry）路径必须短路外部调用，闸3 不接受 101 退出（见 [gates.md](gates.md) 闸3）。

## 8. 调度器全局参数（data/settings.json，运维侧）

任务作者需要感知的关键默认值：`grace_sec=40`（抢占断点宽限）、`kill_grace_sec=10`（窗口收口/停机
信号宽限）、`cooldown_sec=60`、`heartbeat_timeout_sec=120`（任务级可调长、manual 运行 ×2）、
`max_resource_attempts=0`（资源错误不封顶重试）、资源退避 300→600→1200→2400s 封顶 3600s（起始/封顶可在管理台总览面板热更新）、
画像 window=8/overshoot=1.2、cgroup 水位 1.5/2.5、超限额 2.0 持续 60s 退让、
`preempt_exempt_sec=60`、二刷上限 3、自动上线检查失败冷却 `auto_admit_retry_sec=300`（改文件立即重试）、`hot_reload_sec=30`。

**全字段、取值影响、调参后果、CLI 确切行为、数据/日志布局、部署步骤** 见
[configuration.md](configuration.md)。

## 9. 给任务作者的反模式清单

- `while True: work(); sleep()` 常驻写法——会长期占资源、被抢占、且断点为空，sched 禁止此类任务。
- 把所有工作塞进一个大步（几十分钟）——抢占与心跳都会失败。
- 断点写"将要处理的位点"而非"已完成位点"——重放丢数据。
- 续跑不读 resume / 每次从 0 全量跑——闸5 可能过但交付验收必被打回。
- 捕获所有异常后 `pass` 继续——坏数据静默扩散；应 skip_item 或显式分类失败。
- dry 模式留真实写操作（发消息/写库/付费 API）——闸3 与调试纪律双重违规。
- 在任务内 import 兄弟任务目录、读他任务 cache/results——隔离铁律违规。
- 把代理/连接池排队逻辑塞进任务自己 sleep 死等——占着硬资源不让，应快速 101 交给调度器退避重试。
- 用 `contract_exempt=true` 逃避抢占——该标记只给真正无法保证数据完整性的 manual 任务。
