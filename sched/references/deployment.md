# 部署与日常运维

## 环境要求

- Python 3.10+（项目要求 `>=3.10`）。
- 可选：cgroup v2（用于执行进程的身份/观测归因；不可用时降级，观测不足阶段减慢探索并记录限制）。
- SQLite（标准库自带，无需额外安装）。

## 安装

两种安装形态任选其一：

```bash
# 形态一：npm 全局封装（本机当前形态：/usr/local/bin/sched → cli.js → runner.py）
#   cli.js 透传参数给 runner.py，后者按 SCHED_REPO / SCHED_HOME / cwd 向上 /
#   ~/scheduler / pip 安装包的顺序定位代码仓（见 configuration.md）
npm install -g @ielym/sched        # 或已有的全局封装

# 形态二：pip 可编辑安装（原生 sched 命令）
git clone <scheduler repo>
cd scheduler
pip install -e .
python3 -m sched version       # 应输出 sched 3.0.0 (protocol v3)
```

CLI 入口：`sched`（npm 封装或 `pyproject.toml` 的 `[project.scripts]`），或直接用 `python3 -m sched`。

## 启动

```bash
python3 -m sched serve         # 前台常驻；systemd 可直接托管
```

- 单实例：`runtime/scheduler.lock` flock 保证只允许一个执行调度实例。
- SIGTERM/SIGINT 优雅停机：撤执行进程树（先协作暂停再强杀）、关库、释放锁；**生产者保持运行**（不因调度器退出被回收）。
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

## Web 控制台（固定部署规则）

`sched web` 提供 Web 控制台（只读快照 + SQLite 查询；控制操作走 commands.jsonl 通道）。**部署规则固定，不按需更改**：

1. **不启用令牌**：启动时不传 `--token`，也不设 `SCHED_WEB_TOKEN` 环境变量。
2. **绑定 0.0.0.0**：公网可访问；公网可达性另需云安全组放行入方向端口。
3. **端口固定 5555**：不得改用其他端口。

标准单元 `/etc/systemd/system/scheduler-web.service`（随 scheduler.service 一起常驻）：

```ini
[Service]
Type=simple
WorkingDirectory=/mnt/data01/projects/scheduler
Environment=SCHED_HOME=/mnt/data01/projects/scheduler
Environment=PYTHONUNBUFFERED=1
ExecStart=/usr/bin/python3 -m sched web --host 0.0.0.0 --port 5555
Restart=always
RestartSec=3
```

变更后执行 `systemctl daemon-reload && systemctl restart scheduler-web.service`。功能：总览（KPI/资源图表，时间窗下拉 1/6/12/24/48 小时、默认 24h）、任务、作业（筛选/批量重排/CSV 导出）、实时执行（每 attempt CPU/内存，取消与作业取消同语义）、作业详情（事件时间线/worker.log/检查点）。CLI 命令与 Web 控制台等效，见 SKILL.md 命令速查。