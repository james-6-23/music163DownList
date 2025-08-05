"""
下载任务数据模型
"""
from dataclasses import dataclass
from typing import Dict


@dataclass
class DownloadTask:
    """下载任务数据类"""
    id: str
    track: Dict
    quality: str
    download_lyrics: bool
    download_dir: str
    status: str = "pending"  # pending, downloading, completed, failed, paused
    progress: float = 0.0
    speed: float = 0.0
    error_message: str = ""
    file_path: str = ""
