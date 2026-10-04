"""模板 01：daemon（常驻循环）。

适合每天一次、每小时一次、持续监控类。一个意图 = 一个 DaemonTask。
进程退出靠 SDK request_stop() 或被高优抢占。
被抢占后自动从断点恢复，不重做已完成工作。
"""

import sys
import time
from datetime import datetime
from sched_task_sdk import DaemonTask, run_task


class DailyCrawler(DaemonTask):

    def steps(self):
        while True:
            today = datetime.now().strftime("%Y-%m-%d")
            # 落断点："我已经处理了今天的"
            self.save_checkpoint({"date": today, "cursor": None})
            yield today
            # 下一次循环
            time.sleep(60 * 60)   # 或 24h；也可由 request_stop 提前结束

    def process_step(self, day: str):
        try:
            papers = fetch_arxiv(day)   # 业务函数
            save_to_db(papers)           # 落库
        except Exception as e:
            self.state.error("resource", f"抓取失败：{e}")
            sys.exit(101)   # 外部资源错误，调度器自动 retry


def fetch_arxiv(day: str):
    raise NotImplementedError("实现你自己的抓取逻辑")


def save_to_db(papers):
    raise NotImplementedError("实现你自己的落库逻辑")


if __name__ == "__main__":
    run_task(DailyCrawler(name="arxiv_daily"))
