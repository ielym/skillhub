# 子任务模板索引（按场景复制，禁止直接把模板本体当正式任务）

> 模板位于 `assets/`，全部**已对真实 SDK 与五道闸等价流程验证通过**（probe=0 / dry 冒烟=0 /
> 非豁免模板 ckpt TERM→99→恢复=0）。使用方式：

```bash
# 1) 复制为你的任务 id（在代码根）
cp -r <skill目录>/assets/templates/<模板目录> tasks/<你的id>
# 基础骨架（最小可用）：
cp -r <skill目录>/assets/skeleton tasks/<你的id>
# 2) 改 task.json（name/description/schedule/priority/resources/…）与 run.py 业务逻辑
# 3) 放进 tasks/ 后调度器自动跑五道上线检查（或 register 立即检查），流程见 acceptance.md
```

模板之间刻意**代码复制不共享**（H5 隔离铁律）：复制后该任务与模板、其他任务再无任何依赖关系。
所有模板的 dry 模式都不产生真实副作用；`SCHED_DEMO_*` 环境变量仅为错误注入演练开关，正式逻辑里删除。

## 选型决策

| 你的场景 | 用哪个 | schedule | priority 参考 | 关键模式 |
| --- | --- | --- | --- | --- |
| 还不确定/最小起步 | [skeleton](../assets/skeleton/) | interval（示例） | 40 | 游标断点、skip→110→二刷、原子交付物 |
| 定时抓取/轮询外部 API，受代理/限流约束 | [01_interval_crawler](../assets/templates/01_interval_crawler/) | interval+时间窗+weekdays | 45 | 分页断点、外部资源错误快速 101 立即重排队（retry 段自治节奏） |
| 一次性迁移/历史回填，只跑一次 | [02_once_migration](../assets/templates/02_once_migration/) | once（未来时刻！） | 80 | ID 分片断点、逻辑错误 `LOGIC:` 转人工、幂等写 |
| 人工按需触发的大结果集导出 | [03_manual_report](../assets/templates/03_manual_report/) | manual（可抢占） | 55 | 批次断点 + append 续跑、skip/110、心跳放宽 |
| 外部原子操作，无法断点/无法重入 | [04_exempt_atomic](../assets/templates/04_exempt_atomic/) | manual + contract_exempt | 90 | **无闸5/不可抢占/崩溃不自动恢复**，极慎用 |
| 夜间大批量长计算，可被白天任务随时抢占 | [05_nightly_batch](../assets/templates/05_nightly_batch/) | interval 跨夜窗 + allow_overrun | 15 | 二维分片断点(partition,cursor)、细粒度心跳 |

## 各模板要点与必读注意

### skeleton — 最小骨架
6 个条目演示：dry 零副作用、每步 flush 断点、单条坏数据 skip→110→second_pass→dead_letter、
逻辑错误靠 `raise ValueError("LOGIC:")` + `logic_regex`、交付物原子写。
演练：`SCHED_DEMO_SKIP=1`。

### 01_interval_crawler — 定时采集
- 每"页"一个步（约 1s dry sleep 仅供闸5），断点 `{"page": n}`；`_upsert_item` 必须幂等。
- 代理/429 等外部资源问题**无需任何容量配置**：任务直接 exit 101，调度器立即重排队；
  重试间隔/次数上限/时效在 task.json `retry` 段声明（模板示例 delay_sec=300），
  不同代理账号/VPN 等由任务自己选用，调度器不感知也不混用管理。
- 资源失败演示：`SCHED_DEMO_RESERR=1` → exit 101；真实代码里网络超时要设超时、429 直接快速失败，禁止 sleep 死等。
- 二刷分支只处理 pending_skipped；补不动的进 dead_letter。

### 02_once_migration — 一次性回填
- **`once_at` 必须是未来的带时区 ISO8601**；过期=永不触发，上线前再核一次时区。
- 按 ID chunk（示例 8 行/片），断点 `{"last_id": n}`，目标写入必须 `ON CONFLICT` 幂等。
- 优先级给高（80）是因为一次性任务通常有时效；跑完后它留在注册表不再触发，确认无误后按 C4 流程清理。

### 03_manual_report — 手动导出
- manual 不是特权：可抢占、心跳阈值仅 ×2；长导出必须按批断点（`{"last_batch": n}`）。
- 首轮重建文件（表头），续跑 append 下一批 → 断点重放天然不重复行；若你的格式不支持 append，
  改成"每批一个 part 文件 + 最后合并"，同样按批次位点续跑。
- 触发：`python3 -m sched run <id>`（只入队，执行仍排队/可被抢占）。

### 04_exempt_atomic — 豁免原子任务（最高警示级）
- 闸1–4 照过、**闸5 免除**；只能 manual；不可抢占；serve 重启后**不自动恢复**、需人工确认外部状态。
- 动作必须真的短而原子（外部原子 API），`smoke.max_runtime_sec` 与预估时长匹配；
  heartbeat 已放宽到 300s。**能拆步的任务禁止用这个模板。**

### 05_nightly_batch — 夜间大批量
- 跨夜窗 23:00–08:00 + `allow_overrun=true`（跑过 8 点也不被窗口收口杀掉）。
- 低优先级 15：随时给白天任务让路；断点二维 `{"partition": p, "cursor": n}`，每条目 flush。
- dry 只跑 6 步用于过闸；真实量级 5000/分区是示例常量，按实际替换，单步耗时仍需 ≪120s 心跳。

## 模板自检（复制后、上线前）

```bash
cd tasks/<id>
export SCHED_WORKSPACE=$PWD PYTHONPATH=<代码根>
SCHED_CONTRACT_PROBE=1 SCHED_RUN_ID=probe python3 run.py            # 预期 exit 0
SCHED_DRY_RUN=1 SCHED_RUN_ID=smoke python3 run.py                 # 预期 exit 0，results/ 交付物已生成
# 非 exempt 模板再做断点演练（见 acceptance.md A2 的 kill -TERM 双终端流程）
```
