"""
下载核心逻辑模块
"""
import os
import time
import logging
import requests
from typing import Dict, Any
from models.download_task import DownloadTask
from managers.download_manager import DownloadProgressManager
from api.netease_api import name_v1, url_v1, lyric_v1
from core.metadata import add_metadata
from utils.file_utils import build_file_path, build_lyric_path, clean_filename


class DownloadCore:
    """下载核心逻辑"""
    
    def __init__(self, progress_manager: DownloadProgressManager):
        self.progress_manager = progress_manager
        self.is_downloading = False
        self.is_paused = False

    def set_download_state(self, is_downloading: bool, is_paused: bool = False):
        """设置下载状态"""
        self.is_downloading = is_downloading
        self.is_paused = is_paused

    def download_single_task(self, task: DownloadTask, cookies: Dict[str, str]):
        """下载单个任务"""
        try:
            # 更新任务状态为下载中
            self.progress_manager.update_task_status(task.id, "downloading")

            song_id = str(task.track['id'])
            song_name = task.track['name']

            # 清理文件名中的无效字符
            clean_song_name = clean_filename(song_name)
            clean_artists = clean_filename(task.track['artists'])
            clean_album = clean_filename(task.track['album'])

            # 获取歌曲信息
            song_info = name_v1(song_id)['songs'][0]
            cover_url = song_info['al'].get('picUrl', '')

            # 获取下载链接
            url_data = url_v1(song_id, task.quality, cookies)
            if not url_data.get('data') or not url_data['data'][0].get('url'):
                self.progress_manager.update_task_status(task.id, "failed", "VIP限制或音质不可用")
                logging.warning(f"无法下载 {song_name}，可能是 VIP 限制或音质不可用")
                return

            song_url = url_data['data'][0]['url']
            file_path = build_file_path(task.download_dir, clean_song_name, clean_artists, task.quality)
            task.file_path = file_path

            # 检查文件是否已存在
            if os.path.exists(file_path):
                self.progress_manager.update_task_status(task.id, "completed")
                logging.info(f"{song_name} 已存在，跳过下载")
                return

            # 下载文件
            self._download_file_with_progress(song_url, file_path, task.id)

            # 添加元数据
            file_extension = '.flac' if task.quality == 'lossless' else '.mp3'
            add_metadata(file_path, clean_song_name, clean_artists, clean_album, cover_url, file_extension)

            # 下载歌词
            if task.download_lyrics:
                self._download_lyrics(song_id, clean_song_name, clean_artists, task.download_dir, cookies)

            # 更新任务状态为完成
            self.progress_manager.update_task_status(task.id, "completed")
            logging.info(f"成功下载：{song_name}")

        except Exception as e:
            self.progress_manager.update_task_status(task.id, "failed", str(e))
            logging.error(f"下载 {task.track['name']} 失败：{str(e)}")

    def _download_file_with_progress(self, url: str, file_path: str, task_id: str):
        """带进度更新的文件下载"""
        session = requests.Session()
        retries = requests.adapters.Retry(total=3, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
        session.mount('http://', requests.adapters.HTTPAdapter(max_retries=retries))
        session.mount('https://', requests.adapters.HTTPAdapter(max_retries=retries))

        response = session.get(url, stream=True, timeout=10)
        response.raise_for_status()

        total_size = int(response.headers.get('content-length', 0))
        downloaded_size = 0
        start_time = time.time()

        with open(file_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk and self.is_downloading and not self.is_paused:
                    f.write(chunk)
                    downloaded_size += len(chunk)

                    # 计算进度和速度
                    if total_size > 0:
                        progress = downloaded_size / total_size
                        elapsed = time.time() - start_time
                        speed = downloaded_size / elapsed / 1024 if elapsed > 0 else 0

                        # 更新任务进度
                        self.progress_manager.update_task_progress(task_id, progress, speed)

                elif self.is_paused:
                    # 暂停时等待
                    while self.is_paused and self.is_downloading:
                        time.sleep(0.1)
                elif not self.is_downloading:
                    # 取消下载
                    break

    def _download_lyrics(self, song_id: str, song_name: str, artists: str, download_dir: str, cookies: Dict[str, str]):
        """下载歌词"""
        try:
            lyric_data = lyric_v1(song_id, cookies)
            lyric = lyric_data.get('lrc', {}).get('lyric', '')
            if lyric:
                lyric_path = build_lyric_path(download_dir, song_name, artists)
                with open(lyric_path, 'w', encoding='utf-8') as f:
                    f.write(lyric)
                logging.info(f"已下载歌词：{song_name}")
        except Exception as lyric_error:
            logging.warning(f"下载歌词失败：{song_name}，错误：{str(lyric_error)}")
