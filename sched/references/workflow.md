# 标准流程（workflow）

## 阶段 0 设计

**产物**（必须先想清楚，否则进不了阶段 1）：

- [ ] 子任务 id（字母数字下划线短横，≤ 64 位）
- [ ] run_mode：auto（注册即消费意图）/ manual（显式 start 后消费）
- [ ] priority（0~100）
- [ ] resources（CPU / 内存，声明值作为初次准入下界）
- [ ] kind：daemon（常驻）/ oneshot（一次跑完）
- [ ] 意图策略：
  - 场景一（每天 1 个）：`run.py` 用 `DaemonTask` + SDK `emit_intent` 每天早上写一个新意图，或用单个 daemon 直接在 `steps()` 里跑
  - 场景二（2 天大任务 + 每天跑）：`controller.py` 作为驱动，按天 `emit_intent(kind="oneshot")`
- [ ] 资源外部依赖：代理/VPN/API 配额——按 100/101 退出码自分类，意图 lifetime.retry 自治
- [ ] 错误分类规则：哪些是 resource（可重试），哪些是 logic（转人工）

**模板选择**（`assets/templates/`）：

| 模板 | 场景 |
| --- | --- |
| `daemon` | 单进程常驻循环；一个意图配一个 daemon；场景一 |
| `multi_process_driver` | 驱动进程按需 emit_intent；场景二 |
| `once_migration` | 一次性迁移任务；one-shot |

## 阶段 1 本地裸进程调试

**目录建议**：`tasks/<id>/_dev/` 里放临时调试脚本，正式 run.py 不进。

跑法：

```bash
# 裸进程（不走调度器）
SCHED_WORKSPACE=tasks/<id> SCHED_RUN_ID=dev-1 python3 tasks/<id>/run.py
```

**必做演练**：

- [ ] 正常跑通：exit 0
- [ ] 断点：让 run.py 跑起来，kill -TERM，然后恢复跑，确认从断点续起（不重做）
- [ ] 资源错误：模拟代理断（exit 101），确认重试
- [ ] 进度可见：跑的过程中 stdout 有实时输出（`flush=True`），state.json 的 progress 在推进（H13）

## 阶段 2 上线（双闸自动检查）

1. 放入 `tasks/<id>/`：至少 manifest.json + run.py
2. 若 run_mode=auto → 调度器热加载到就开检（30s）；也可手动：
   ```bash
   python3 -m sched register <id>
   ```
3. 闸全部通过 → jobs.json 启用，调度器开始扫描 requests/
4. 闸失败 → Web 管理台或 `sched status` 看原因，修 manifest/run.py 后自动重检

## 阶段 3 跑通意图流程

**必做**：

- [ ] 创建 requests/ 目录
- [ ] 至少一个意图文件（或驱动进程能 `emit_intent`）
- [ ] 跑通 scan → admit → run → exit 完整链路
- [ ] 跑通被抢占恢复（kill -TERM 主进程，确认 exit 99 后续跑）
- [ ] 跑通 `no_retry` / `request_stop` / `reschedule` 三条控制协议

## 阶段 4 交付验收

**清单**：见 [acceptance.md](acceptance.md)（全部强制清单 A–G，任何一项未勾都不得交付）。
