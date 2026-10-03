# 部署与运维指南

> 面向部署/运维：serve 常驻、运行用户、cgroup v2 硬边界、Web 管理台暴露安全、
> 首次部署清单与日常运维操作。参数全集见 [configuration.md](configuration.md)。

## 1. 部署前置（任何任务上线之前先确认）

在代码根执行所有 CLI：`cd <代码根>`，调用形式 `python3 -m sched <cmd>`
（或使用安装好的 `sched` 命令，等价；用 `SCHED_HOME` 可指定其它调度器根）。

1. **serve 常驻**：`python3 -m sched serve`（生产建议由 systemd 托管）。任务目录放进 `tasks/` 后，
   由 serve 在热加载时自动跑五道上线检查并纳入调度；`run` 只是往运行队列加一次触发。
   **真正的运行只由 serve 的准出循环决定**。无 serve 时任务不会被检查、也不会执行。
2. **运行用户存在**：task.json 的 `runtime.user`（默认 `sched-run`）必须是系统已有用户，否则闸2起进程即失败。
   部署：`useradd -r -m -s /usr/sbin/nologin sched-run`；多使用者应各自独立系统用户，不要共用。
   以 root 启动 serve 时，上线检查通过会自动把任务目录 chown 给该用户，无需手工 chown。
3. **cgroup v2 硬边界在线（关键，静默失效不报警）**：上线检查的冒烟实测、内存/CPU 硬限、超限退让、OOM 归因、
   画像回流全部依赖 run cgroup 内存在控制文件。任务上线前用下面一条命令自检（root）：

   ```bash
   d=/sys/fs/cgroup/sched/_skill_probe
   mkdir -p "$d" && test -f "$d/memory.max" && echo "cgroup OK" || echo "cgroup DEGRADED"
   rmdir "$d" 2>/dev/null
   ```

   输出 `cgroup DEGRADED` 时，不得交付资源敏感型任务；先在调度子树委派控制器后再让任务上线：
   `echo '+memory +cpu' > /sys/fs/cgroup/sched/cgroup.subtree_control`（root，一次性，部署修复）。
   降级状态下冒烟实测峰值恒为 0，**闸4 将完全依赖任务自报内存，申报虚低即打爆机器**。

## 2. Web 管理台（serve --web）

总览/运行队列/历史日志/决策/画像监控，外加与 CLI 等价的"立即运行一次"、启停、**导入任务**、
纯调度参数行内编辑、运行中「停止」、历史删除；新任务的五道上线检查由 serve 自动执行，
其状态（等待检查/检查中/未通过原因）直接在页面展示。写操作与调度循环共享同一 serve 进程
（不存在独立 web 进程）。默认绑 127.0.0.1。

- **只读**：总览（账本/整机容量/上线检查状态；**无"运行参数"面板**，时区固定
  Asia/Shanghai，冷却/退避/重试上限等全局旋钮已删除）、任务表（下次触发/ok/启用，
  interval 以人话展示）、运行队列（等待项含触发来源、第几次尝试、not_before 最早准出
  时刻、上次失败原因；运行中项含实测 CPU 核数/内存）、run 历史与 stdout/stderr、
  decisions 审计流、资源画像（P95/声明/样本数/成功时长中位数）。
- **写操作全部与 CLI 等价且走同一 SchedulerService 实例**：
  - 立即运行一次（只入队，绝不旁路拉起进程；队列中标注"手动运行"，来源为管理台/`sched run`）；
  - enable/disable；
  - **导入任务**：按 `tasks/` 下已存在的子目录名导入本地**已验证**任务（不做在线建码/骨架
    生成），导入即同步跑五道闸；目录不存在 404、闸失败 400、已注册 409；
  - **调度参数行内编辑**：仅白名单字段（priority、完整 schedule、heartbeat.timeout_sec、
    retry 三字段），写 task.json（0644、保属主）后立即生效（WQ 优先级即时重排）；
  - **停止运行中 run**：cancel Event → SIGTERM 整组（10s 宽限），killed 转人工、本轮不
    自动重排队（断点保留，可再手动触发续跑）；
  - **删除历史**：弹窗二选一——仅删 jsonl 记录，或连带删 `data/runs/<job>/<run_id>.
    {stdout,stderr}.log`；运行中的 run 拒删（409）。
- **管理台不提供任务文件查看/编辑**：所有代码与 task.json 变更都在本地完成、经热加载/
  指纹变化生效（闸失败也只在文件变化后重检）。
- 所有写动作落 `decisions.jsonl`（web_import_task/web_update_job_config/manual_cancel/
  web_delete_run/web_set_enabled/auto_admit_ok/auto_admit_failed…）可审计。

### 暴露面三档（按安全优先）

1. 默认回环 + SSH 隧道（零额外攻击面）：`ssh -L 8799:127.0.0.1:8799 <服务器>`；
2. 公网/局域网 + `web.auth_token`：host 改 `0.0.0.0` 并配密码，浏览器 Basic 弹窗输入（用户名任意）；
3. 公网无密码：必须显式 `web.allow_public_no_auth=true` 否则 serve 拒绝启动——
   **管理台可触发/停止任务、改调度参数、导入本地任务、删历史，虽不能在线改代码，但仍可
   干扰生产运行，此档风险自负，强烈建议同时在云安全组把入站 8799 限制为特定源 IP 段**，
   不要对 0.0.0.0/0 开放。

云主机还需在**安全组/防火墙**放行对应 TCP 入站端口；改 host 只解决监听，不替代安全组。
HTTP 明文（含 Basic 密码）会经链路传输，需要保密时用反代 + TLS（nginx + 证书）。

## 3. 首次部署清单（root 执行一次）

```bash
# 1) 运行用户（默认 sched-run；多租户各自独立用户，在任务 runtime.user 指定）
useradd -r -m -s /usr/sbin/nologin sched-run

# 2) cgroup v2 嵌套控制器委派（关键！不做则硬限额静默失效，见本文 §1 自检命令）
mkdir -p /sys/fs/cgroup/sched
echo '+memory +cpu' > /sys/fs/cgroup/sched/cgroup.subtree_control

# 3) 任务目录权限：以 root 跑 serve 时，上线检查通过会自动 chown -R <runtime.user>；
#    非 root 启动则需自行保证任务代码可读、cache/results 可写（属主 sched-run 或 o+rx）
chown -R sched-run:sched-run <代码根>/tasks/<id>

# 4) 常驻（建议 systemd 托管，ExecStart=python3 -m sched serve，重启策略 on-failure）
python3 -m sched serve --web     # 加 --web 启动内嵌管理台（默认 127.0.0.1:8799）
# 之后把任务目录放进 tasks/ 即可：serve ≤30s 内自动跑五道上线检查，无需任何注册/资源配置命令
```

任务进程环境补充事实：降权执行时任务进程的 `HOME` 会被改成目标用户的家目录（不是 /root）；
透传白名单仅 `PATH HOME LANG TZ LC_ALL PYTHONPATH PYTHONUNBUFFERED`，PYTHONPATH 自动前置项目根；
密钥不要走 env（同机进程可读 `/proc/<pid>/environ`），放任务目录 600 权限文件。

## 4. 常见运维操作

- 改任务配置/代码：编辑 task.json/run.py → serve ≤30s 热加载（list 的 ok 变 false 即配置非法，修到 ok 自动恢复）。
  未上线的新任务改文件后按**新指纹**重跑上线检查（闸失败不做定时重试，只认文件变化）；
  已上线任务改 `resources` 后声明值热加载即生效，
  画像随后续正式 run 实测回流（也可手动 `python3 -m sched register <id>` 立即重跑一次五闸确认）。
  纯调度参数（priority/schedule/heartbeat/retry）也可直接在管理台任务行内编辑、立即生效。
- 临时停用任务：编辑 `data/jobs.json` 把该 id 的 `enabled` 置 false（这是注册表的设计字段），
  或在管理台任务表拨动开关（两者完全等价）；在途 run 不受影响，跑完后不再触发；重新启用置回 true。
- 删除任务：按 [acceptance.md](acceptance.md) C4 的 5 步流程（jobs.json 删条目 → 删任务目录 → 删 runs 日志）。
  仅删单条 run 的历史记录/日志可用管理台历史区删除按钮（二选一：只删 jsonl / 连带日志文件）。
- 任务一直 waiting：先 `status` 看账本余量与未通过上线检查项，再看 `decisions.jsonl` 尾部；
  资源申报超剩余、等待项 not_before 未到（任务 retry.delay_sec）都会等待，均属正常排队语义。
  队列里消失且历史末条是 giveup/giveup_expired = 已按任务 max_attempts/not_after 转人工，
  去历史查原因后人工处理；外部资源没有也无法手工"补容量"开关。
- serve 重启：启动时自动把上轮在途 run 记 interrupted 并携断点重入队（contract_exempt 只记待人工）；
  残留孤儿进程组会被 kill，残留 cgroup 会被清理。
