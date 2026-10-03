# 标准工作流（四阶段，每阶段有准入/准出）

```
阶段0 设计        → 阶段1 本地调试(_dev/裸进程) → 阶段2 注册门禁(register 五道闸) → 阶段3 交付验收
```

每阶段的强制打勾清单见 [acceptance.md](acceptance.md)（A/B/C 三张准入门），本文讲每阶段做什么、
关键判据是什么。**上一阶段未全部打勾，不得进入下一阶段。**

## 阶段 0 · 设计（不写运行代码前先定 5 件事）

1. 任务 id：`^[a-z0-9_-]{1,64}$`，不以 `_`/`.` 开头；语义化、与目录同名。
2. 调度类型与优先级：interval/once/manual；priority 0–100（越高越能抢占别人、也越早被准出）。
   按业务刚性给级，**一律禁止默认 0 凑合**：延迟可容忍的批处理 10–30，常规 40–60，强时效 70–90，
   必须尽快完成的保底任务 90+。同优先级 FIFO 排队，互不抢占。
3. 资源预算：单机内存/CPU 占用保守上限；是否使用软资源（代理并发、API QPS 配额等）及每 run 占用令牌数。
4. 断点粒度：`resume_point` 的键设计（如 `{"date": "2026-10-03", "chunk": 12}`），保证从断点重放**幂等**。
5. 错误分类表：哪些异常算资源（可重试）、哪些算逻辑（转人工）、哪些数据进 skip/二刷；写进 task.json
   `error_rules` 正则与代码显式分类。

**先选模板再动手**：六套已验证模板的场景对照、选型决策表与各模板注意事项见
[templates.md](templates.md)（最小骨架 [assets/skeleton/](../assets/skeleton/) 与
[assets/templates/](../assets/templates/) 下 5 个场景模板）。复制后改名，禁止直接注册模板本体。

## 阶段 1 · 本地调试（不经过调度器，首选路径，零历史污染）

在任务目录内直接以裸进程跑（SDK 自动支持这些环境变量）：

```bash
cd <代码根>/tasks/<id>_dev
export SCHED_WORKSPACE=$PWD SCHED_RUN_ID=local
# 契约自检（闸2 的同款探针）：必须 exit 0 并写出合法 state.json
SCHED_CONTRACT_PROBE=1 python3 run.py
# dry 全流程：必须跳过一切真实副作用（上传/写库/发消息/付费调用只 print）
SCHED_DRY_RUN=1 python3 run.py
# 断点演练：dry 跑起来后另开终端 kill -TERM <pid>，验证 exit 99 + resume_point 落盘，再跑一次验证幂等续跑
SCHED_DRY_RUN=1 python3 run.py
```

需要调度器介导验证（队列、准出、画像、二刷等）时才注册 `<id>_dev` 并 `python3 -m sched run <id>_dev`。
**注意 `run` 无 dry-run：会真实执行**，副作用只能靠任务代码内的自有开关（读 `SCHED_DRY_RUN` 或 _dev 专用配置）关断。
调试期逐项自检与错误注入要求见 [acceptance.md](acceptance.md) 清单 A。

## 阶段 2 · 注册（五道闸，唯一准入入口）

```bash
cd <代码根>
python3 -m sched register <id>
```

`register` 会**真实串行拉起最多 4 次任务进程**（探针→冒烟→打断→恢复），实测单任务约 10–20s
（随冒烟步数增长），且冒烟进程的内存预算取整机上限、**不感知 serve 在跑任务**——禁止在机器高负载时
并发注册多个重任务。

五道闸逐条判定标准、失败原因与修复动作极其严格，注册前必须通读：[gates.md](gates.md)。
闸不过时修任务后重跑 register；**严禁修改调度器代码或数据文件来"绕过"闸门。**

## 阶段 3 · 交付验收（完成定义，DoD）

正式任务只接受**调度触发**的成功作为验收证据，`manual` 记录不算。12 项验收逐条打勾、证据留存，
清单见 [acceptance.md](acceptance.md)（含断点/错误分类/二刷/心跳/资源复核/_dev 清理/历史洁净）。
