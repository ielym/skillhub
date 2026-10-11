# 部署与日常运维

## 环境要求

- Python 3.10+（项目要求 `>=3.10`）。
- 可选：cgroup v2（用于执行进程的身份/观测归因；不可用时降级，观测不足阶段减慢探索并记录限制）。
- SQLite（标准库自带，无需额外安装）。

## 安装

```bash
git clone <scheduler repo>
cd scheduler
pip install -e .
python3 -m sched list          # 应为 sched (v3)
```

CLI（Node 薄封装 `sched`）定位代码仓；或直接用 `python3 -m sched`。

## 启动

```bash
python3 -m sched serve         # 前台常驻；systemd 可直接托管
```

- 单实例：`runtime/scheduler.lock` flock 保证只允许一个执行调度实例。
- SIGTERM/SIGINT 优雅停机：撤执行进程树（先协作暂停再强杀）、停生产者、关库、释放锁。
- 仅重启调度器默认保持生产者运行；显式整套服务关闭由外部生命周期管理（如 systemd stop），关闭过程依赖生产者持久化进度与事件源回放。

## systemd 示例

```ini
[Service]
WorkingDirectory=/path/to/scheduler
ExecStart=/usr/bin/python3 -m sched serve
Environment=SCHED_HOME=/path/to/scheduler
Restart=on-failure
```

## 数据库与文件系统

- SQLite 执行库与锁放在**验证过语义的本机文件系统**。共享挂载可存任务 JSON；未经验证不可依赖共享挂载上的 SQLite WAL、文件锁或远端文件通知。
- `outbox`/`producer_state` 在任务目录内，走原子写 + fsync 目录。

## 日常

- `sched status` 每轮关注：生产者存活、动态目标 vs 存活 attempt、退让集合、保护对象、队列长度（观测值非上限）。
- 资源监控记执行范围实测消耗/趋势/观测缺失；发现延迟、接收→启动延迟、暂停与检查点耗时、保护改善与无效退让。
- 日志可轮转，但不得删除未完成任务所需的状态/检查点/去重依据。

## 公开暴露（无）

v3 无内嵌 Web 管理台；全部操作走 CLI。