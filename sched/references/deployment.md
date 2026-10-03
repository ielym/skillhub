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

总览/运行队列/历史日志/决策/画像只读监控，外加与 CLI 等价的"立即运行一次"、启停、新建任务、
在线改码；新任务的五道上线检查由 serve 自动执行，其状态（等待检查/检查中/未通过原因/下次重试
时刻）直接在页面展示。写操作与调度循环共享同一 serve 进程（不存在独立 web 进程）。默认绑 127.0.0.1。

- **只读**：总览（账本/整机容量/参数/上线检查状态）、任务表（下次触发/ok/启用）、运行队列、run 历史与
  stdout/stderr、decisions 审计流、资源画像（P95/声明/样本数）。
- **写操作全部与 CLI 等价且走同一 SchedulerService 实例**：立即运行一次（只入队，绝不旁路拉起进程）、
  enable/disable、新建任务（生成最小合规骨架并触发自动检查）、在线编辑任务文件（保存后若文件有变化
  立即重新跑上线检查，无需等待冷却）。任务通过检查纳入调度时会自动执行 `chown -R <run_user>`
  并把写入文件置 0644。
- 文件编辑安全边界：仅限任务目录内 `.py/.json/.txt/.md/.conf/.yaml/.sh` 等源码类文件（单文件 ≤1MB）；
  `cache/`、`results/`、`__pycache__/` 禁止经 Web 读写；目录穿越（`..`）拒绝。
- 所有写动作落 `decisions.jsonl`（web_create_task/web_save_file/web_set_enabled/auto_admit_ok/auto_admit_failed…）可审计。

### 暴露面三档（按安全优先）

1. 默认回环 + SSH 隧道（零额外攻击面）：`ssh -L 8799:127.0.0.1:8799 <服务器>`；
2. 公网/局域网 + `web.auth_token`：host 改 `0.0.0.0` 并配密码，浏览器 Basic 弹窗输入（用户名任意）；
3. 公网无密码：必须显式 `web.allow_public_no_auth=true` 否则 serve 拒绝启动——
   **管理台能在线改 .py 并上线执行（等同 RCE），此档风险自负，强烈建议同时在云安全组
   把入站 8799 限制为特定源 IP 段**，不要对 0.0.0.0/0 开放。

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
  未上线的新任务改文件后会**立即**重跑上线检查；已上线任务改 `resources` 后声明值热加载即生效，
  画像随后续正式 run 实测回流（也可手动 `python3 -m sched register <id>` 立即重跑一次五闸确认）。
- 临时停用任务：编辑 `data/jobs.json` 把该 id 的 `enabled` 置 false（这是注册表的设计字段），
  或在管理台任务表拨动开关（两者完全等价）；在途 run 不受影响，跑完后不再触发；重新启用置回 true。
- 删除任务：按 [acceptance.md](acceptance.md) C4 的 5 步流程（jobs.json 删条目 → 删任务目录 → 删 runs 日志）。
- 任务一直 waiting：先 `status` 看账本余量与未通过上线检查项，再看 `decisions.jsonl` 尾部；
  资源申报超剩余、处于 backoff/cooldown 都会等待，均属正常排队语义。任务因外部资源错误（101）
  等待时，按 backoff 节奏自动重试，不需要也无法手工"补容量"。
- serve 重启：启动时自动把上轮在途 run 记 interrupted 并携断点重入队（contract_exempt 只记待人工）；
  残留孤儿进程组会被 kill，残留 cgroup 会被清理。
