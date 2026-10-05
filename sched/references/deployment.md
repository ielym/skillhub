# 部署（deployment）

## 首次部署

### 1. 准备 cgroup v2

```bash
# 确认已启用
stat -fc %T /sys/fs/cgroup   # 应该显示 cgroup2fs
# 如果是 v1，切换内核参数 systemd.unified_cgroup_hierarchy=1
```

### 2. 委派当前用户对 cgroup 的写权限

```bash
# 创建 sched 子树
sudo mkdir /sys/fs/cgroup/sched 2>/dev/null || true
# 让当前用户可写
sudo chown -R $(whoami) /sys/fs/cgroup/sched/ 2>/dev/null || \
  sudo tee /sys/fs/cgroup/cgroup.subtree_control >/dev/null <<< "+cpu +memory"
```

### 3. 安装 sched（Python 3.10+）

```bash
cd /mnt/data01/projects/scheduler
pip install -e .   # 开发模式
```

### 4. 验证

```bash
python3 -m sched status   # 应该显示 0 个子任务，账本为空
```

### 5. 作为 systemd 服务常驻（可选）

```ini
[Unit]
Description=sched daemon
After=network.target

[Service]
Type=simple
User=sched-run
Environment=SCHED_HOME=/mnt/data01/projects/scheduler
ExecStart=/usr/bin/python3 -m sched serve --web
Restart=on-failure
RestartSec=5s
# cgroup 委派：systemd 管理的 cgroup 下再挂 sched 子树
Delegate=yes
CPUAccounting=yes
MemoryAccounting=yes

[Install]
WantedBy=multi-user.target
```

## Web 管理台

默认 `127.0.0.1:8765`（只监听 localhost）。需要暴露到公网：

1. 修改 `data/settings.json` 的 `web.host` 为 `0.0.0.0`
2. **加反向代理 + basic auth**（nginx / traefik / cloudflare tunnel 任选）
3. 禁止直接暴露到公网（管理台有进程停止/终止能力）

## 日常运维

| 操作 | 命令 |
| --- | --- |
| 查看所有子任务状态 | `python3 -m sched status` |
| 查看意图消费状态 | `python3 -m sched process list` |
| 终止运行中进程 | `python3 -m sched process stop <sid> <rid>`（硬路径，见 configuration.md） |
| 标记不再重试 | `python3 -m sched process no-retry <sid> <rid>`（硬路径，见 configuration.md） |
| 注册/上线检查 | `python3 -m sched register <id>` 或 Web「注册本地任务」 |
| 清空全部调度状态 | `python3 -m sched clear [--delete-requests]` 或 Web「清空全部」（建议先停服务） |
| 手动触发 manual 模式子任务 | `python3 -m sched start <id>` |
| 查看审计日志 | `tail -f data/runtime/decisions.jsonl` |
| 查看运行历史 | `ls -lt data/runs/*.jsonl` |

## 热重载

- **30s 周期**（`hot_reload_sec`）自动扫描 `tasks/` 目录新子任务 + 重载 manifest
- 改 manifest 或 run.py 后≤30s 生效，**无需重启 serve**
- 意图文件随时写入，调度器扫描到立即入队

## 备份建议

- `data/runtime/intents_state.json`：意图消费状态（核心，建议每日快照）
- `data/runtime/profiles.json`：资源画像（运行中动态采样重建）
- `data/jobs.json`：注册表（丢了重放 manifest 即可）
- **不要**定期清 `data/runtime/decisions.jsonl` ——这是完整审计日志
