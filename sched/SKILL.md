---
name: sched
description: sched 优先级抢占式任务调度器的使用规则与子任务创建规范。当用户要在 sched 上新建、上线、调试、交付一个被调度子任务，或咨询任务门禁（五道闸）、资源申报、优先级/抢占、断点续跑、错误码、外部资源退避、验收标准时使用。
---

# sched（任务调度器）

## 能力介绍

sched 是常驻单进程的本地任务调度器：高优任务可抢占低优在跑任务、任务必须可断点续跑、
任务放进 `tasks/` 后经五道契约闸**自动准入**、本机资源经 cgroup v2 硬限 + 账本 + 画像防打爆，
并自带零构建 Web 管理台。无外部服务依赖（不用数据库、不用 APScheduler）。

本 skill 是在 sched 上**创建、调试、上线、交付子任务**的规范入口，也是所有调度器使用问题
的路由入口。**核心目标：高优任务绝对优先执行完毕、资源有限不打爆机器、所有任务最终都能被正确执行。**

**路径约定（全文统一）**：

- **代码根**：scheduler 仓库的 clone 目录（`tasks/`、`data/` 的父目录；默认取 `sched` 包所在
  目录的上一级，可用环境变量 `SCHED_HOME` 覆盖）。
- **skill 目录**：本 skill 的安装目录（模板与参考文件在其 `assets/`、`references/` 下）。

**核心理念**：

| 维度 | sched 的规则 |
| --- | --- |
| 调度依据 | **优先级决定一切**：高优等待可抢占低优在跑任务 |
| 任务形态 | **必须有限、可断点**；禁止常驻，长任务分段提交断点 |
| 准入 | **五道闸自动检查**：静态→契约→冒烟→容量→断点，缺一不可；放入 tasks/ 即自动开检，无需手动注册 |
| 资源 | 必须如实申报 CPU/内存，cgroup 硬限 + 账本 + 画像；代理/VPN/配额等外部资源**不做统一管理**，任务按退出码 101 自分类，调度器退避重试 |
| 失败处理 | 统一错误码，资源错误退让重试、逻辑错误转人工、110 二刷 |
| 任务基类 | **强制 SDK 契约行为**：心跳、断点、99 退出、错误分类 |
| 手动任务 | 不可恢复任务只能 manual（`contract_exempt`），其余 manual 触发**同样可被抢占** |

## 适用 / 不适用

- **适用**：在代码根上创建新的被调度子任务；为已有任务改配置/排障/做交付验收；判断一个任务能否/如何纳入调度。
- **不适用**：调度器核心源码（`sched/` 包）本身的重构开发（走需求审查流程，不属于子任务创建）。
- **铁律：子任务作者只在 `tasks/<id>/` 自己的目录内工作，禁止改 `sched/` 包源码、禁止手改 `data/runtime/` 内文件。**

## 命令速查

均在代码根执行（或用等价的 `sched` 命令）；确切行为与失败情形见 [configuration.md](references/configuration.md)。

```bash
python3 -m sched list                 # 已上线任务、ok 状态、下次触发
python3 -m sched register <id>        # 立即跑一次五道上线检查（常规无需使用：放进 tasks/ 后自动检查）
python3 -m sched run <id>             # 立即运行一次（只入队！是否/何时跑由 serve 准出决定；无 --dry-run）
python3 -m sched status               # 任务数、等待运行/运行中、账本预留/实测、未通过上线检查项
python3 -m sched serve                # 常驻调度循环（自动发现新任务并跑上线检查，热加载周期 30s，单实例互斥）
python3 -m sched serve --web          # 同时启动内嵌 Web 管理台（默认 127.0.0.1:8799）
```

注意：**没有** kill 命令、`run` **没有** `--dry-run` 开关；任务想停用就移出 `tasks/`
或把 `data/jobs.json` 中对应条目 `enabled` 置 false。外部资源（代理隧道/VPN/API 配额）
没有任何配置命令——由任务在运行中按错误码自分类（见下）。

## 路由：我要做什么 → 看哪个文件

| 你的问题 / 任务 | 必读文件 |
| --- | --- |
| 从零做一个任务，按什么流程走 | [workflow.md](references/workflow.md)（四阶段流程）+ [acceptance.md](references/acceptance.md)（三张强制清单） |
| 哪些事绝对不能做 / 交付红线 | [rules.md](references/rules.md)（铁律 H1–H12 + 红线总表） |
| 上线检查（五道闸）不过，怎么修 | [gates.md](references/gates.md)（五道闸逐条判定与修复，上线前必读） |
| task.json 怎么写、SDK 怎么用、退出码/状态文件 | [contracts.md](references/contracts.md) |
| settings 参数、CLI 确切行为、数据/日志布局 | [configuration.md](references/configuration.md) |
| 抢占/排队/退避/时间窗/触发时刻怎么算 | [scheduling.md](references/scheduling.md) |
| 首次部署、cgroup 委派自检、Web 公网暴露、日常运维 | [deployment.md](references/deployment.md) |
| 任务跑挂了 / 状态异常怎么排查 | [troubleshooting.md](references/troubleshooting.md) |
| 找起步代码（骨架/场景模板） | [templates.md](references/templates.md) + [assets/](assets/) |

## 铁律索引（H1–H12，违反任一条不得交付）

1. **H1 唯一执行通道**：正式执行只能由调度器准出触发，禁止 cron/手工跑/任务自触发。
2. **H2 有限且可断点**：禁常驻；SIGTERM 后 40s 内存断点、exit 99。
3. **H3 抢占只由优先级决定**：唯一例外 `contract_exempt`（强制 manual）。
4. **H4 必走 SDK 契约**：继承 `SchedTask`，禁裸脚本绕过探针/心跳/断点/分类。
5. **H5 任务间完全隔离**：一任务一目录，禁跨任务 import/共享可变物。
6. **H6 资源如实申报**：CPU/内存必填且有依据，虚低申报闸4 拒绝；外部资源（代理/配额等）无法统一申报与管理，靠 101 错误码退让。
7. **H7 错误真实分类**：逻辑错误显式报（转人工），资源错误 100/101 快速失败，不死等。
8. **H8 单条坏数据不卡死整体**：skip_item → 110 二刷 → dead_letter。
9. **H9 心跳义务**：周期写 state.json（SDK 每 30s），超时 120s 判卡死。
10. **H10 调试与正式隔离**：只在 `_dev`/裸进程调试，正式历史无 manual 记录。
11. **H11 无密钥、执行面最小**：密钥走 600 权限文件；禁黑名单 env 键与绝对/`..` 路径。
12. **H12 源码不动、数据不手改**：仅调试清理时按流程编辑 jobs.json。

全文（含每条的细节与原因）见 [rules.md](references/rules.md)。

## 标准流程一句话

**阶段 0 设计**（定 id/优先级/资源/断点/错误分类，选模板）→ **阶段 1 本地 `_dev` 裸进程调试**
（探针/dry/断点演练）→ **阶段 2 放入 `tasks/<id>/`，调度器自动跑五道闸上线**（失败在管理台/status
看原因，改文件立即重试；也可手动 `register <id>` 立即检查）→ **阶段 3 只认调度触发成功的交付验收**。
详见 [workflow.md](references/workflow.md)，每阶段打勾清单见 [acceptance.md](references/acceptance.md)。
