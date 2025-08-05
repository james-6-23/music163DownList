"""
下载进度管理器
"""
import threading
from typing import Dict, List, Optional, Tuple
from models.download_task import DownloadTask


class DownloadProgressManager:
    """下载进度管理器"""
    
    def __init__(self):
        self.tasks: Dict[str, DownloadTask] = {}
        self.lock = threading.Lock()

    def add_task(self, task: DownloadTask):
        """添加下载任务"""
        with self.lock:
            self.tasks[task.id] = task

    def update_task_progress(self, task_id: str, progress: float, speed: float = 0.0):
        """更新任务进度"""
        with self.lock:
            if task_id in self.tasks:
                self.tasks[task_id].progress = progress
                self.tasks[task_id].speed = speed

    def update_task_status(self, task_id: str, status: str, error_message: str = ""):
        """更新任务状态"""
        with self.lock:
            if task_id in self.tasks:
                self.tasks[task_id].status = status
                self.tasks[task_id].error_message = error_message

    def get_task(self, task_id: str) -> Optional[DownloadTask]:
        """获取指定任务"""
        with self.lock:
            return self.tasks.get(task_id)

    def get_all_tasks(self) -> List[DownloadTask]:
        """获取所有任务"""
        with self.lock:
            return list(self.tasks.values())

    def get_overall_progress(self) -> Tuple[float, float, int, int, int]:
        """
        获取总体进度
        返回: (总进度, 总速度, 完成数, 失败数, 下载中数)
        """
        with self.lock:
            if not self.tasks:
                return 0.0, 0.0, 0, 0, 0

            total_tasks = len(self.tasks)
            completed_tasks = sum(1 for task in self.tasks.values() if task.status == "completed")
            failed_tasks = sum(1 for task in self.tasks.values() if task.status == "failed")
            downloading_tasks = sum(1 for task in self.tasks.values() if task.status == "downloading")

            overall_progress = completed_tasks / total_tasks if total_tasks > 0 else 0.0
            total_speed = sum(task.speed for task in self.tasks.values() if task.status == "downloading")

            return overall_progress, total_speed, completed_tasks, failed_tasks, downloading_tasks
