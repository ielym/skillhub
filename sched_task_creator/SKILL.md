---
name: sched_task_creator
description: sched 调度器上创建新子任务的完整规范与流程。当用户要新建、开发、调试、交付一个被守护子任务（producer.py/run.py/task.json/outbox 协议），或咨询任务创建的规则/契约/模板/铁律（H1-H14、外部资源纪律 R1-R9、检查点真实性 C1-C2）时使用。调度器本身的操作、部署、排障走 sched skill。
---

# sched_task_creator（子任务创建规范）

## 核心定位

在 sched 调度器上从零创建一个被守护子任务。子任务由两部分组成：

1. **生产者**（`producer.py`，常驻）：发现业务事件，把就绪 JSON 发布到 `outbox/`
2. **执行者**（`run.py`，受调度器管理）：处理作业单元，断点恢复 + 进展上报 + 幂等提交

**路径约定（全文统一）**：

- **代码根**：scheduler 仓库 clone 目录（`tasks/`、`runtime/`、`config.json` 的父目录；默认 `sched` 包上一级，环境变量 `SCHED_HOME` 覆盖）
- **任务目录**：`tasks/<task_id>/`，子任务的全部代码与数据都在此目录内
- **本 skill 目录**：模板在 `assets/`，细则在 `references/`

## 三层规则体系

创建任务需要遵守的规则分三层，全部定义在 [rules.md](references/rules.md)：

| 层 | 编号 | 管什么 |
| --- | --- | --- |
| 协议铁律 | H1–H14 | 执行通道、生产/执行分离、稳定标识、无丢失发布、SDK 契约、断点/幂等、边界 |
| 外部资源纪律 | R1–R9 | 不预设限制、不做任务间协调、资源错误 2 次有限重试后立即上浮（上限/间隔固定常量）、上浮信息完整（错误类型+资源标识）、严禁凭证、空结果即业务事实、触发窗口余量、响应读取总时长上限、禁止吞掉 |
| 检查点真实性 | C1–C2 | 只在真实进展后落检查点、异常分支不保存未变化断点 |

## 关键设计事实（决定任务代码长什么样）

- **调度器不设上限**：没有写死的最大并发/排队上限/资源申请；调度器观测实测消耗平缓扩容（冷启动 1 个，逐步 +1）
- **外部资源匿名**：任务用什么资源、任务间是否共用资源，任何层都不建模；资源不足统一 exit 75，调度器按任务独立退避（步降→验证→全退避探测→逐个放回）
- **任务自治边界**：任务吸收瞬时抖动（单次外部操作最多 2 次固定短间隔重试，重试落日志），持续故障立即上浮（错误类型+资源标识）；退避、重排、并发调整全部归调度器——不在任务里做调度器的事
- **退出码语义**：0 = 成功（必须先 `complete()` 提交完成记录）；75 = 资源不足（资源类错误，可恢复退让）；其他非 0 = 业务失败

## 路由：我要做什么 → 看哪个文件

| 你的问题 / 任务 | 必读文件 |
| --- | --- |
| 从零做一个子任务，按什么流程走 | [workflow.md](references/workflow.md) + [acceptance.md](references/acceptance.md) |
| 哪些事绝对不能做 / 交付红线 | [rules.md](references/rules.md)（H1–H14 + R1–R9 + C1–C2 + 红线总表） |
| task.json / 就绪 JSON / 事件 / 退出码 / SDK 接口怎么写 | [contracts.md](references/contracts.md) |
| 起步代码（骨架 / 场景模板） | [templates.md](references/templates.md) + [assets/](assets/) |
| 调度器怎么调度（动态扩容/保护/退避/按任务资源退避） | sched skill 的 scheduling.md（理解行为即可，规则由调度器侧维护） |

## 标准流程一句话

**阶段 0 设计**（定 id / 优先级 / 稳定事件标识 / 断点与幂等键 / 触发窗口余量，选模板）→ **阶段 1 `_dev` 裸进程调试**（必须演练断点恢复 + 协作暂停 + 资源不足）→ **阶段 2 放入 `tasks/<id>/`**（`sched task validate` → serve 自动守护）→ **阶段 3 跑通完整发布→执行→完成 + 暂停/不足演练** → **阶段 4 只认调度触发成功的交付验收**。

## 目录结构（交付物）

```
tasks/<task_id>/
├── task.json        # 清单：入口/优先级/recovery（唯一真源）
├── producer.py      # 生产者（继承 SDK Producer）
├── run.py           # 执行者（继承 SDK ExecutorTask）
├── config.json      # 业务配置（或 config/ 按日期分文件）
├── outbox/          # 就绪 JSON（生产者发布，调度器消费）
├── cache/           # 业务缓存
├── receipts/        # 提交回执（幂等核实）
└── producer_state/  # 生产者游标（无丢失发布）
```

## 模板选择

| 模板 | 适用 | 位置 |
| --- | --- | --- |
| 骨架 | 最小可运行示例（学习协议用） | [assets/skeleton/](assets/skeleton/) |
| 每日任务 | 按日触发、逐项幂等处理（含外部请求纪律与空结果处理示范） | [assets/templates/01_daily_producer/](assets/templates/01_daily_producer/) |
| 批量回溯 | 存量数据补齐（单元完成即结束） | [assets/templates/02_batch_backfill/](assets/templates/02_batch_backfill/) |
| 长期任务 | 持续输入持续处理、无完成事件 | [assets/templates/03_longtask/](assets/templates/03_longtask/) |

## 边界

- 本 skill 只管 `tasks/<id>/` 内的代码；调度器核心（`sched/` 包）的重构开发不在范围内
- 调度器的部署、CLI 操作、排障、Web 控制台：走 sched skill
- 铁律：子任务作者只在 `tasks/<id>/` 自己的目录内工作，禁止改 `sched/` 包源码、禁止手改 `runtime/` 内文件
