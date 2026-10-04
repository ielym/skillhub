"""模板 02：once_migration（一次性）。

跑完自然 exit 0，意图自动 done，不再守护。
若中途被抢占 → exit 99 → 同意图续跑（断点恢复）。
"""

import sys
from sched_task_sdk import OneshotTask, run_task


class OnceMigration(OneshotTask):

    def steps(self):
        # 有限迭代：每个 item 是一个要迁移的单元
        items = load_items_to_migrate()
        for i, item in enumerate(items):
            self.save_checkpoint({"next_index": i, "last_id": item.id})
            yield item

    def process_step(self, item):
        try:
            migrate_item(item)
        except Exception as e:
            self.state.error("resource", f"迁移失败 item={item.id}: {e}")
            sys.exit(100)


def load_items_to_migrate():
    raise NotImplementedError("实现加载迁移单元逻辑")


def migrate_item(item):
    raise NotImplementedError("实现单个单元迁移逻辑")


if __name__ == "__main__":
    run_task(OnceMigration(name="once_migration"))
