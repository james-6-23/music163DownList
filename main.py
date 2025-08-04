import flet as ft
import os
import requests
import json
import urllib.parse
from random import randrange
from hashlib import md5
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from mutagen.mp3 import MP3
from mutagen.easyid3 import EasyID3
from mutagen.id3 import ID3, APIC
from mutagen.flac import FLAC
from PIL  import Image
import io
import time
import threading
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from queue import Queue
from dataclasses import dataclass
from typing import Optional, Dict, List
import uuid

# 设置日志
logging.basicConfig(filename='download.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# 下载任务数据类
@dataclass
class DownloadTask:
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

# 下载进度管理器
class DownloadProgressManager:
    def __init__(self):
        self.tasks: Dict[str, DownloadTask] = {}
        self.lock = threading.Lock()

    def add_task(self, task: DownloadTask):
        with self.lock:
            self.tasks[task.id] = task

    def update_task_progress(self, task_id: str, progress: float, speed: float = 0.0):
        with self.lock:
            if task_id in self.tasks:
                self.tasks[task_id].progress = progress
                self.tasks[task_id].speed = speed

    def update_task_status(self, task_id: str, status: str, error_message: str = ""):
        with self.lock:
            if task_id in self.tasks:
                self.tasks[task_id].status = status
                self.tasks[task_id].error_message = error_message

    def get_task(self, task_id: str) -> Optional[DownloadTask]:
        with self.lock:
            return self.tasks.get(task_id)

    def get_all_tasks(self) -> List[DownloadTask]:
        with self.lock:
            return list(self.tasks.values())

    def get_overall_progress(self) -> tuple:
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

# Cookie 管理
class CookieManager:
    def __init__(self, cookie_file='cookie.txt'):
        self.cookie_file = cookie_file
        self.cookie_text = None

    def set_cookie(self, cookie_text):
        """设置Cookie文本"""
        self.cookie_text = cookie_text.strip()

    def read_cookie(self):
        """读取Cookie，优先使用内存中的Cookie"""
        if self.cookie_text:
            return self.cookie_text
        try:
            with open(self.cookie_file, 'r', encoding='utf-8') as f:
                return f.read().strip()
        except FileNotFoundError:
            raise Exception("未找到 cookie.txt，请运行 qr_login.py 获取 Cookie")

    def parse_cookie(self):
        """解析Cookie为字典格式"""
        cookie_text = self.read_cookie()
        if not cookie_text:
            raise Exception("Cookie为空，请输入有效的MUSIC_U Cookie")

        # 如果只是MUSIC_U值，自动添加前缀
        if '=' not in cookie_text:
            cookie_text = f"MUSIC_U={cookie_text}"

        cookie_ = [item.strip().split('=', 1) for item in cookie_text.split(';') if item and '=' in item]
        return {k.strip(): v.strip() for k, v in cookie_}

    def save_cookie(self):
        """保存Cookie到文件"""
        if self.cookie_text:
            try:
                with open(self.cookie_file, 'w', encoding='utf-8') as f:
                    f.write(self.cookie_text)
                logging.info("Cookie已保存到文件")
            except Exception as e:
                logging.error(f"保存Cookie失败：{str(e)}")

    def validate_cookie(self):
        """验证Cookie有效性"""
        try:
            cookies = self.parse_cookie()
            # 使用用户信息API验证Cookie
            return self._test_cookie_validity(cookies)
        except Exception as e:
            logging.error(f"Cookie验证失败：{str(e)}")
            return False, str(e)

    def _test_cookie_validity(self, cookies):
        """通过API测试Cookie有效性"""
        try:
            # 使用用户信息API测试
            url = "https://music.163.com/api/nuser/account/get"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.164 NeteaseMusicDesktop/2.10.2.200154',
                'Referer': 'https://music.163.com/',
            }
            response = requests.post(url, headers=headers, cookies=cookies, timeout=10)
            response.raise_for_status()
            result = response.json()

            if result.get('code') == 200 and result.get('account'):
                user_info = result.get('profile', {})
                username = user_info.get('nickname', '未知用户')
                return True, f"验证成功！欢迎 {username}"
            else:
                return False, "Cookie无效或已过期"
        except requests.RequestException as e:
            return False, f"网络请求失败：{str(e)}"
        except Exception as e:
            return False, f"验证过程出错：{str(e)}"

# 网易云音乐 API 函数
def post(url, params, cookies):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.164 NeteaseMusicDesktop/2.10.2.200154',
        'Referer': '',
    }
    cookies = {'os': 'pc', 'appver': '', 'osver': '', 'deviceId': 'pyncm!', **cookies}
    try:
        response = requests.post(url, headers=headers, cookies=cookies, data={"params": params}, timeout=10)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        logging.error(f"POST 请求失败：{url}，错误：{str(e)}")
        raise

def hash_hex_digest(text):
    return ''.join(hex(d)[2:].zfill(2) for d in md5(text.encode('utf-8')).digest())

def url_v1(id, level, cookies):
    url = "https://interface3.music.163.com/eapi/song/enhance/player/url/v1"
    AES_KEY = b"e82ckenh8dichen8"
    config = {"os": "pc", "appver": "", "osver": "", "deviceId": "pyncm!", "requestId": str(randrange(20000000, 30000000))}
    payload = {'ids': [id], 'level': level, 'encodeType': 'flac', 'header': json.dumps(config)}
    if level == 'sky':
        payload['immerseType'] = 'c51'
    url2 = urllib.parse.urlparse(url).path.replace("/eapi/", "/api/")
    digest = hash_hex_digest(f"nobody{url2}use{json.dumps(payload)}md5forencrypt")
    params = f"{url2}-36cd479b6b5-{json.dumps(payload)}-36cd479b6b5-{digest}"
    padder = padding.PKCS7(algorithms.AES(AES_KEY).block_size).padder()
    padded_data = padder.update(params.encode()) + padder.finalize()
    cipher = Cipher(algorithms.AES(AES_KEY), modes.ECB())
    encryptor = cipher.encryptor()
    enc = encryptor.update(padded_data) + encryptor.finalize()
    params = ''.join(hex(d)[2:].zfill(2) for d in enc)
    return json.loads(post(url, params, cookies))

def name_v1(id):
    url = "https://interface3.music.163.com/api/v3/song/detail"
    data = {'c': json.dumps([{"id": id, "v": 0}])}
    try:
        response = requests.post(url, data=data, timeout=5)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        logging.error(f"获取歌曲信息失败：{id}，错误：{str(e)}")
        raise

def lyric_v1(id, cookies):
    url = "https://interface3.music.163.com/api/song/lyric"
    data = {'id': id, 'cp': 'false', 'tv': '0', 'lv': '0', 'rv': '0', 'kv': '0', 'yv': '0', 'ytv': '0', 'yrv': '0'}
    try:
        response = requests.post(url, data=data, cookies=cookies, timeout=5)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        logging.error(f"获取歌词失败：{id}，错误：{str(e)}")
        raise

def playlist_detail(playlist_id, cookies):
    url = 'https://music.163.com/api/v6/playlist/detail'
    data = {'id': playlist_id}
    headers = {'User-Agent': 'Mozilla/5.0', 'Referer': 'https://music.163.com/'}
    try:
        response = requests.post(url, data=data, headers=headers, cookies=cookies, timeout=10)
        response.raise_for_status()
        result = response.json()
        if result.get('code') != 200:
            return {'status': result.get('code'), 'msg': '歌单解析失败'}
        playlist = result.get('playlist', {})
        info = {
            'status': 200,
            'playlist': {
                'id': playlist.get('id'),
                'name': playlist.get('name'),
                'tracks': []
            }
        }
        track_ids = [str(t['id']) for t in playlist.get('trackIds', [])]
        for i in range(0, len(track_ids), 100):
            batch_ids = track_ids[i:i+100]
            song_data = {'c': json.dumps([{'id': int(sid), 'v': 0} for sid in batch_ids])}
            song_resp = requests.post('https://interface3.music.163.com/api/v3/song/detail', 
                                    data=song_data, headers=headers, cookies=cookies, timeout=10)
            song_result = song_resp.json()
            for song in song_result.get('songs', []):
                info['playlist']['tracks'].append({
                    'id': song['id'],
                    'name': song['name'],
                    'artists': '/'.join(artist['name'] for artist in song['ar']),
                    'album': song['al']['name'],
                    'picUrl': song['al'].get('picUrl', '')  # 使用 picUrl，默认为空字符串
                })
        return info
    except requests.RequestException as e:
        logging.error(f"歌单解析失败：{playlist_id}，错误：{str(e)}")
        return {'status': 500, 'msg': str(e)}

# 主程序
class MusicDownloaderApp:
    def __init__(self, page: ft.Page):
        self.page = page
        self.page.title = "🎵 DownList - 网易云音乐下载器"
        self.page.window_width = 1200
        self.page.window_height = 800
        self.page.theme_mode = ft.ThemeMode.LIGHT
        self.page.bgcolor = ft.Colors.GREY_50

        # 核心组件
        self.cookie_manager = CookieManager()
        self.download_dir = "C:\\"
        self.tracks = []
        self.current_view = "cookie"  # cookie 或 download

        # 多线程下载相关
        self.max_concurrent_downloads = 3
        self.thread_pool: Optional[ThreadPoolExecutor] = None
        self.download_progress_manager = DownloadProgressManager()
        self.is_downloading = False
        self.is_paused = False
        self.download_futures = []

        # UI更新定时器
        self.progress_update_timer = None

        # 主题颜色
        self.primary_color = ft.Colors.BLUE_600
        self.secondary_color = ft.Colors.BLUE_100
        self.success_color = ft.Colors.GREEN_600
        self.error_color = ft.Colors.RED_600
        self.warning_color = ft.Colors.ORANGE_600

        # 初始化UI组件
        self.init_cookie_ui()
        self.init_download_ui()

        # 检查是否已有有效Cookie，如果有则直接进入下载页面
        self.check_existing_cookie()

    def init_cookie_ui(self):
        """初始化Cookie输入页面UI组件"""
        # Cookie输入页面组件
        self.cookie_title = ft.Text(
            "🎵 DownList",
            size=48,
            weight=ft.FontWeight.BOLD,
            color=self.primary_color,
            text_align=ft.TextAlign.CENTER
        )
        self.cookie_subtitle = ft.Text(
            "网易云音乐无限下载器",
            size=20,
            color=ft.Colors.GREY_600,
            text_align=ft.TextAlign.CENTER
        )
        self.cookie_description = ft.Text(
            "请输入您的网易云音乐 MUSIC_U Cookie 以开始使用",
            size=16,
            color=ft.Colors.GREY_700,
            text_align=ft.TextAlign.CENTER
        )

        self.cookie_input = ft.TextField(
            label="MUSIC_U Cookie",
            hint_text="请输入完整的MUSIC_U Cookie值",
            width=700,
            multiline=True,
            min_lines=3,
            max_lines=5,
            password=True,
            can_reveal_password=True,
            border_radius=12,
            filled=True,
            bgcolor=ft.Colors.WHITE,
            border_color=self.primary_color,
            focused_border_color=self.primary_color,
            text_size=14
        )

        self.cookie_help_text = ft.Text(
            "💡 如何获取Cookie：\n"
            "1. 打开浏览器，访问 music.163.com 并登录\n"
            "2. 按F12打开开发者工具，切换到Application/存储标签\n"
            "3. 在Cookies中找到MUSIC_U，复制其值\n"
            "4. 将值粘贴到上方输入框中\n\n"
            "⚠️ 注意：建议使用有黑胶VIP的账号以获得更好的下载体验",
            size=13,
            color=ft.Colors.GREY_600,
            text_align=ft.TextAlign.LEFT
        )

        self.validate_button = ft.ElevatedButton(
            "🔐 验证并继续",
            on_click=self.validate_cookie,
            width=220,
            height=50,
            bgcolor=self.primary_color,
            color=ft.Colors.WHITE,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=25),
                elevation=3
            )
        )

        self.validation_status = ft.Text("", size=15, weight=ft.FontWeight.W_500)
        self.validation_progress = ft.ProgressRing(
            visible=False,
            width=24,
            height=24,
            color=self.primary_color
        )

    def init_download_ui(self):
        """初始化下载页面UI组件"""
        # 输入区域组件
        self.url_input = ft.TextField(
            label="🎵 歌单链接",
            hint_text="请输入网易云音乐歌单链接",
            width=600,
            border_radius=10,
            filled=True,
            bgcolor=ft.Colors.WHITE,
            border_color=self.primary_color
        )

        self.quality_dropdown = ft.Dropdown(
            label="🎧 音质选择",
            options=[
                ft.dropdown.Option("standard", "标准音质"),
                ft.dropdown.Option("exhigh", "极高音质"),
                ft.dropdown.Option("lossless", "无损音质"),
                ft.dropdown.Option("hires", "Hi-Res"),
                ft.dropdown.Option("sky", "沉浸环绕声"),
                ft.dropdown.Option("jyeffect", "高清环绕声"),
                ft.dropdown.Option("jymaster", "超清母带")
            ],
            value="standard",
            width=200,
            border_radius=10,
            filled=True,
            bgcolor=ft.Colors.WHITE
        )

        self.lyrics_checkbox = ft.Checkbox(
            label="📝 下载歌词",
            value=False,
            active_color=self.primary_color
        )

        self.concurrent_slider = ft.Slider(
            min=1,
            max=8,
            divisions=7,
            value=3,
            label="并发数: {value}",
            width=200,
            active_color=self.primary_color,
            on_change=self.on_concurrent_change
        )
        self.concurrent_text = ft.Text("🚀 并发下载: 3 个线程", size=14)

        # 按钮组件
        self.dir_button = ft.ElevatedButton(
            "📁 选择目录",
            on_click=self.select_directory,
            bgcolor=self.secondary_color,
            color=self.primary_color,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8))
        )
        self.dir_text = ft.Text(f"📂 下载目录: {self.download_dir}", size=14, color=ft.Colors.GREY_700)

        self.parse_button = ft.ElevatedButton(
            "🔍 解析歌单",
            on_click=self.parse_playlist,
            bgcolor=self.primary_color,
            color=ft.Colors.WHITE,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8))
        )

        self.download_button = ft.ElevatedButton(
            "⬇️ 开始下载",
            on_click=self.start_download,
            disabled=True,
            bgcolor=self.success_color,
            color=ft.Colors.WHITE,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8))
        )

        self.pause_button = ft.ElevatedButton(
            "⏸️ 暂停",
            on_click=self.pause_download,
            disabled=True,
            bgcolor=self.warning_color,
            color=ft.Colors.WHITE,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8))
        )

        self.resume_button = ft.ElevatedButton(
            "▶️ 继续",
            on_click=self.resume_download,
            disabled=True,
            bgcolor=self.success_color,
            color=ft.Colors.WHITE,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8))
        )

        self.cancel_button = ft.ElevatedButton(
            "❌ 取消",
            on_click=self.cancel_download,
            disabled=True,
            bgcolor=self.error_color,
            color=ft.Colors.WHITE,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8))
        )

        self.reset_cookie_button = ft.ElevatedButton(
            "🔑 重设Cookie",
            on_click=self.reset_cookie,
            bgcolor=ft.Colors.GREY_400,
            color=ft.Colors.WHITE,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8))
        )

        # 进度显示组件
        self.total_progress = ft.ProgressBar(
            width=800,
            value=0,
            color=self.primary_color,
            bgcolor=ft.Colors.GREY_200,
            bar_height=8,
            border_radius=4
        )
        self.total_progress_text = ft.Text("📊 总进度: 0/0", size=16, weight=ft.FontWeight.W_500)

        self.speed_text = ft.Text("🚀 下载速度: 0 KB/s", size=14, color=ft.Colors.GREY_700)
        self.status_text = ft.Text("📋 状态: 等待开始", size=14, color=ft.Colors.GREY_700)

        # 歌曲列表
        self.song_list = ft.GridView(
            expand=True,
            runs_count=3,
            max_extent=350,
            child_aspect_ratio=1.2,
            spacing=10,
            run_spacing=10,
            padding=10
        )

        # 下载任务列表
        self.download_tasks_list = ft.ListView(
            expand=True,
            spacing=8,
            padding=10
        )

    def on_concurrent_change(self, e):
        """并发数量变化处理"""
        self.max_concurrent_downloads = int(e.control.value)
        self.concurrent_text.value = f"🚀 并发下载: {self.max_concurrent_downloads} 个线程"
        self.page.update()

    def check_existing_cookie(self):
        """检查是否已有有效的Cookie"""
        try:
            # 尝试读取现有Cookie
            existing_cookie = self.cookie_manager.read_cookie()
            if existing_cookie and existing_cookie.strip():
                # 在后台验证Cookie
                def validate_existing():
                    try:
                        is_valid, message = self.cookie_manager.validate_cookie()
                        if is_valid:
                            # Cookie有效，直接进入下载页面
                            self.show_download_page()
                        else:
                            # Cookie无效，显示Cookie输入页面
                            self.show_cookie_page()
                    except:
                        # 验证失败，显示Cookie输入页面
                        self.show_cookie_page()

                # 先显示加载页面
                self.show_loading_page("正在验证现有Cookie...")
                validation_thread = threading.Thread(target=validate_existing, daemon=True)
                validation_thread.start()
            else:
                # 没有现有Cookie，显示输入页面
                self.show_cookie_page()
        except:
            # 读取失败，显示Cookie输入页面
            self.show_cookie_page()

    def show_loading_page(self, message="正在加载..."):
        """显示加载页面"""
        self.page.clean()
        self.page.add(
            ft.Container(
                content=ft.Column([
                    ft.Container(height=200),
                    ft.Row([
                        ft.ProgressRing(width=50, height=50),
                    ], alignment=ft.MainAxisAlignment.CENTER),
                    ft.Container(height=20),
                    ft.Row([
                        ft.Text(message, size=16, color=ft.Colors.GREY_700)
                    ], alignment=ft.MainAxisAlignment.CENTER),
                ], alignment=ft.MainAxisAlignment.CENTER),
                alignment=ft.alignment.center
            )
        )
        self.page.update()

    def show_cookie_page(self):
        """显示Cookie输入页面"""
        self.current_view = "cookie"
        self.page.clean()

        # 创建渐变背景
        background_container = ft.Container(
            width=self.page.window_width,
            height=self.page.window_height,
            gradient=ft.LinearGradient(
                begin=ft.alignment.top_center,
                end=ft.alignment.bottom_center,
                colors=[ft.Colors.BLUE_50, ft.Colors.WHITE]
            )
        )

        # 主卡片容器
        main_card = ft.Container(
            content=ft.Column([
                # 标题区域
                ft.Container(
                    content=ft.Column([
                        self.cookie_title,
                        ft.Container(height=10),
                        self.cookie_subtitle,
                        ft.Container(height=5),
                        self.cookie_description,
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    padding=ft.padding.only(top=40, bottom=30)
                ),

                # 输入区域
                ft.Container(
                    content=ft.Column([
                        self.cookie_input,
                        ft.Container(height=25),
                        ft.Row([
                            self.validate_button,
                            ft.Container(width=15),
                            self.validation_progress
                        ], alignment=ft.MainAxisAlignment.CENTER),
                        ft.Container(height=15),
                        self.validation_status,
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    padding=20
                ),

                # 帮助信息卡片
                ft.Container(
                    content=self.cookie_help_text,
                    padding=25,
                    bgcolor=ft.Colors.WHITE,
                    border_radius=15,
                    border=ft.border.all(1, ft.Colors.GREY_200),
                    shadow=ft.BoxShadow(
                        spread_radius=1,
                        blur_radius=10,
                        color=ft.Colors.with_opacity(0.1, ft.Colors.BLACK),
                        offset=ft.Offset(0, 4)
                    ),
                    width=700
                )
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            width=800,
            bgcolor=ft.Colors.WHITE,
            border_radius=20,
            padding=30,
            shadow=ft.BoxShadow(
                spread_radius=2,
                blur_radius=20,
                color=ft.Colors.with_opacity(0.15, ft.Colors.BLACK),
                offset=ft.Offset(0, 8)
            )
        )

        # 页面布局
        self.page.add(
            ft.Stack([
                background_container,
                ft.Container(
                    content=main_card,
                    alignment=ft.alignment.center,
                    expand=True
                )
            ])
        )
        self.page.update()

    def show_download_page(self):
        """显示下载页面"""
        self.current_view = "download"
        self.page.clean()

        # 创建标题栏
        header = ft.Container(
            content=ft.Row([
                ft.Row([
                    ft.Icon(ft.Icons.MUSIC_NOTE, color=self.primary_color, size=32),
                    ft.Container(width=10),
                    ft.Text("DownList", size=28, weight=ft.FontWeight.BOLD, color=self.primary_color),
                ]),
                ft.Container(expand=True),
                self.reset_cookie_button
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            padding=ft.padding.symmetric(horizontal=20, vertical=15),
            bgcolor=ft.Colors.WHITE,
            border_radius=ft.border_radius.only(bottom_left=15, bottom_right=15),
            shadow=ft.BoxShadow(
                spread_radius=1,
                blur_radius=5,
                color=ft.Colors.with_opacity(0.1, ft.Colors.BLACK),
                offset=ft.Offset(0, 2)
            )
        )

        # 输入配置卡片
        input_card = ft.Container(
            content=ft.Column([
                ft.Text("🎵 歌单配置", size=18, weight=ft.FontWeight.BOLD, color=self.primary_color),
                ft.Container(height=15),
                ft.Row([
                    self.url_input,
                    ft.Container(width=15),
                    self.parse_button
                ], alignment=ft.MainAxisAlignment.CENTER),
                ft.Container(height=15),
                ft.Row([
                    self.quality_dropdown,
                    ft.Container(width=20),
                    self.lyrics_checkbox,
                    ft.Container(width=20),
                    self.dir_button
                ], alignment=ft.MainAxisAlignment.CENTER),
                ft.Container(height=10),
                self.dir_text,
                ft.Container(height=15),
                ft.Row([
                    self.concurrent_text,
                    ft.Container(width=20),
                    self.concurrent_slider
                ], alignment=ft.MainAxisAlignment.CENTER)
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            padding=25,
            bgcolor=ft.Colors.WHITE,
            border_radius=15,
            border=ft.border.all(1, ft.Colors.GREY_200),
            shadow=ft.BoxShadow(
                spread_radius=1,
                blur_radius=8,
                color=ft.Colors.with_opacity(0.08, ft.Colors.BLACK),
                offset=ft.Offset(0, 4)
            )
        )

        # 控制按钮卡片
        control_card = ft.Container(
            content=ft.Column([
                ft.Text("🎮 下载控制", size=18, weight=ft.FontWeight.BOLD, color=self.primary_color),
                ft.Container(height=15),
                ft.Row([
                    self.download_button,
                    ft.Container(width=10),
                    self.pause_button,
                    ft.Container(width=10),
                    self.resume_button,
                    ft.Container(width=10),
                    self.cancel_button
                ], alignment=ft.MainAxisAlignment.CENTER)
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            padding=25,
            bgcolor=ft.Colors.WHITE,
            border_radius=15,
            border=ft.border.all(1, ft.Colors.GREY_200),
            shadow=ft.BoxShadow(
                spread_radius=1,
                blur_radius=8,
                color=ft.Colors.with_opacity(0.08, ft.Colors.BLACK),
                offset=ft.Offset(0, 4)
            )
        )

        # 进度显示卡片
        progress_card = ft.Container(
            content=ft.Column([
                ft.Text("📊 下载进度", size=18, weight=ft.FontWeight.BOLD, color=self.primary_color),
                ft.Container(height=15),
                self.total_progress_text,
                ft.Container(height=8),
                self.total_progress,
                ft.Container(height=15),
                ft.Row([
                    self.speed_text,
                    ft.Container(expand=True),
                    self.status_text
                ])
            ]),
            padding=25,
            bgcolor=ft.Colors.WHITE,
            border_radius=15,
            border=ft.border.all(1, ft.Colors.GREY_200),
            shadow=ft.BoxShadow(
                spread_radius=1,
                blur_radius=8,
                color=ft.Colors.with_opacity(0.08, ft.Colors.BLACK),
                offset=ft.Offset(0, 4)
            )
        )

        # 创建标签页
        tabs = ft.Tabs(
            selected_index=0,
            animation_duration=300,
            tabs=[
                ft.Tab(
                    text="🎵 歌曲预览",
                    content=ft.Container(
                        content=self.song_list,
                        padding=10,
                        bgcolor=ft.Colors.WHITE,
                        border_radius=15
                    )
                ),
                ft.Tab(
                    text="📋 下载任务",
                    content=ft.Container(
                        content=self.download_tasks_list,
                        padding=10,
                        bgcolor=ft.Colors.WHITE,
                        border_radius=15
                    )
                )
            ],
            expand=True
        )

        # 页面布局
        self.page.add(
            ft.Column([
                header,
                ft.Container(height=20),
                ft.Row([
                    ft.Column([
                        input_card,
                        ft.Container(height=15),
                        control_card,
                        ft.Container(height=15),
                        progress_card
                    ], expand=True)
                ], expand=True),
                ft.Container(height=20),
                tabs
            ], expand=True),
        )
        self.page.update()

    def validate_cookie(self, e):
        """验证Cookie有效性"""
        cookie_text = self.cookie_input.value.strip()
        if not cookie_text:
            self.validation_status.value = "❌ 请输入Cookie"
            self.validation_status.color = ft.Colors.RED
            self.page.update()
            return

        # 显示验证中状态
        self.validation_progress.visible = True
        self.validation_status.value = "🔄 正在验证Cookie..."
        self.validation_status.color = ft.Colors.BLUE
        self.validate_button.disabled = True
        self.page.update()

        # 在后台线程中验证Cookie
        def validate_in_background():
            try:
                self.cookie_manager.set_cookie(cookie_text)
                is_valid, message = self.cookie_manager.validate_cookie()

                # 更新UI
                self.validation_progress.visible = False
                self.validate_button.disabled = False

                if is_valid:
                    self.validation_status.value = f"✅ {message}"
                    self.validation_status.color = ft.Colors.GREEN
                    self.page.update()

                    # 保存Cookie并切换到下载页面
                    self.cookie_manager.save_cookie()
                    time.sleep(1)  # 让用户看到成功消息
                    self.show_download_page()
                else:
                    self.validation_status.value = f"❌ {message}"
                    self.validation_status.color = ft.Colors.RED
                    self.page.update()

            except Exception as ex:
                self.validation_progress.visible = False
                self.validate_button.disabled = False
                self.validation_status.value = f"❌ 验证失败：{str(ex)}"
                self.validation_status.color = ft.Colors.RED
                self.page.update()

        # 启动验证线程
        validation_thread = threading.Thread(target=validate_in_background, daemon=True)
        validation_thread.start()

    def reset_cookie(self, e):
        """重新设置Cookie"""
        self.cookie_input.value = ""
        self.validation_status.value = ""
        self.show_cookie_page()

    def select_directory(self, e):
        dialog = ft.FilePicker(on_result=self.on_directory_picked)
        self.page.overlay.append(dialog)
        self.page.update()
        dialog.get_directory_path()

    def on_directory_picked(self, e: ft.FilePickerResultEvent):
        if e.path:
            self.download_dir = e.path
            self.dir_text.value = f"下载目录: {self.download_dir}"
            self.page.update()

    def parse_playlist(self, e):
        url = self.url_input.value.strip()
        if not url:
            self.show_snackbar("❌ 请输入歌单 URL", self.error_color)
            return

        # 显示解析中状态
        self.parse_button.disabled = True
        self.parse_button.text = "🔄 解析中..."
        self.page.update()

        def parse_in_background():
            try:
                cookies = self.cookie_manager.parse_cookie()
                playlist_id = self.extract_playlist_id(url)
                playlist_info = playlist_detail(playlist_id, cookies)

                if playlist_info['status'] != 200:
                    self.parse_button.disabled = False
                    self.parse_button.text = "🔍 解析歌单"
                    self.show_snackbar(f"❌ 歌单解析失败：{playlist_info['msg']}", self.error_color)
                    self.page.update()
                    logging.error(f"歌单解析失败：{playlist_info['msg']}")
                    return

                self.tracks = playlist_info['playlist']['tracks']
                self.update_song_list()

                self.total_progress_text.value = f"📊 总进度: 0/{len(self.tracks)}"
                self.download_button.disabled = False
                self.parse_button.disabled = False
                self.parse_button.text = "🔍 解析歌单"

                self.show_snackbar(f"✅ 成功解析歌单：{playlist_info['playlist']['name']}，共 {len(self.tracks)} 首歌曲", self.success_color)
                self.page.update()
                logging.info(f"成功解析歌单：{playlist_info['playlist']['name']}，共 {len(self.tracks)} 首歌曲")

            except Exception as ex:
                self.parse_button.disabled = False
                self.parse_button.text = "🔍 解析歌单"
                self.show_snackbar(f"❌ 解析失败：{str(ex)}", self.error_color)
                self.page.update()
                logging.error(f"解析歌单失败：{str(ex)}")

        # 启动解析线程
        parse_thread = threading.Thread(target=parse_in_background, daemon=True)
        parse_thread.start()

    def update_song_list(self):
        """更新歌曲列表显示"""
        self.song_list.controls.clear()
        for i, track in enumerate(self.tracks):
            # 创建歌曲卡片
            song_card = ft.Container(
                content=ft.Column([
                    # 封面图片
                    ft.Container(
                        content=ft.Image(
                            src=track['picUrl'] if track['picUrl'] else "https://via.placeholder.com/150x150?text=No+Image",
                            width=120,
                            height=120,
                            fit=ft.ImageFit.COVER,
                            border_radius=8
                        ),
                        alignment=ft.alignment.center
                    ),
                    ft.Container(height=8),
                    # 歌曲信息
                    ft.Container(
                        content=ft.Column([
                            ft.Text(
                                track['name'],
                                size=14,
                                weight=ft.FontWeight.BOLD,
                                max_lines=2,
                                overflow=ft.TextOverflow.ELLIPSIS,
                                text_align=ft.TextAlign.CENTER
                            ),
                            ft.Text(
                                track['artists'],
                                size=12,
                                color=ft.Colors.GREY_600,
                                max_lines=1,
                                overflow=ft.TextOverflow.ELLIPSIS,
                                text_align=ft.TextAlign.CENTER
                            ),
                            ft.Text(
                                track['album'],
                                size=11,
                                color=ft.Colors.GREY_500,
                                max_lines=1,
                                overflow=ft.TextOverflow.ELLIPSIS,
                                text_align=ft.TextAlign.CENTER
                            )
                        ], spacing=2),
                        padding=ft.padding.symmetric(horizontal=8)
                    )
                ], spacing=0),
                padding=15,
                bgcolor=ft.Colors.WHITE,
                border_radius=12,
                border=ft.border.all(1, ft.Colors.GREY_200),
                shadow=ft.BoxShadow(
                    spread_radius=1,
                    blur_radius=4,
                    color=ft.Colors.with_opacity(0.1, ft.Colors.BLACK),
                    offset=ft.Offset(0, 2)
                ),
                on_hover=self.on_song_card_hover
            )
            self.song_list.controls.append(song_card)

    def on_song_card_hover(self, e):
        """歌曲卡片悬停效果"""
        if e.data == "true":
            e.control.shadow = ft.BoxShadow(
                spread_radius=2,
                blur_radius=8,
                color=ft.Colors.with_opacity(0.15, ft.Colors.BLACK),
                offset=ft.Offset(0, 4)
            )
            e.control.border = ft.border.all(1, self.primary_color)
        else:
            e.control.shadow = ft.BoxShadow(
                spread_radius=1,
                blur_radius=4,
                color=ft.Colors.with_opacity(0.1, ft.Colors.BLACK),
                offset=ft.Offset(0, 2)
            )
            e.control.border = ft.border.all(1, ft.Colors.GREY_200)
        self.page.update()

    def show_snackbar(self, message: str, color: str):
        """显示消息提示"""
        self.page.snack_bar = ft.SnackBar(
            content=ft.Text(message, color=ft.Colors.WHITE),
            bgcolor=color,
            duration=3000
        )
        self.page.snack_bar.open = True
        self.page.update()

    def extract_playlist_id(self, url):
        if 'music.163.com' in url or '163cn.tv' in url:
            index = url.find('id=') + 3
            return url[index:].split('&')[0]
        return url

    def start_download(self, e):
        if not self.tracks:
            self.show_snackbar("❌ 请先解析歌单", self.error_color)
            return

        try:
            self.cookie_manager.read_cookie()
        except Exception as ex:
            self.show_snackbar(f"❌ {str(ex)}", self.error_color)
            logging.error(str(ex))
            return

        # 更新UI状态
        self.download_button.disabled = True
        self.pause_button.disabled = False
        self.cancel_button.disabled = False
        self.is_downloading = True
        self.is_paused = False

        # 清空之前的下载任务
        self.download_progress_manager = DownloadProgressManager()
        self.download_tasks_list.controls.clear()

        # 启动多线程下载
        self.start_multithreaded_download()

        # 启动进度更新定时器
        self.start_progress_timer()

    def start_multithreaded_download(self):
        """启动多线程下载"""
        def download_worker():
            try:
                # 获取歌单信息
                cookies = self.cookie_manager.parse_cookie()
                playlist_id = self.extract_playlist_id(self.url_input.value.strip())
                playlist_info = playlist_detail(playlist_id, cookies)

                if playlist_info['status'] != 200:
                    self.show_snackbar(f"❌ 歌单解析失败：{playlist_info['msg']}", self.error_color)
                    return

                playlist_name = playlist_info['playlist']['name']
                download_dir = os.path.join(self.download_dir, playlist_name)
                os.makedirs(download_dir, exist_ok=True)

                # 创建下载任务
                tasks = []
                for track in self.tracks:
                    task = DownloadTask(
                        id=str(uuid.uuid4()),
                        track=track,
                        quality=self.quality_dropdown.value,
                        download_lyrics=self.lyrics_checkbox.value,
                        download_dir=download_dir
                    )
                    tasks.append(task)
                    self.download_progress_manager.add_task(task)

                # 创建任务UI
                self.create_download_task_ui(tasks)

                # 使用线程池执行下载
                self.thread_pool = ThreadPoolExecutor(max_workers=self.max_concurrent_downloads)
                self.download_futures = []

                for task in tasks:
                    if not self.is_downloading:
                        break
                    future = self.thread_pool.submit(self.download_single_task, task)
                    self.download_futures.append(future)

                # 等待所有任务完成
                for future in as_completed(self.download_futures):
                    if not self.is_downloading:
                        break

                # 下载完成处理
                if self.is_downloading and not self.is_paused:
                    self.on_download_complete(playlist_name)

            except Exception as ex:
                self.show_snackbar(f"❌ 下载失败：{str(ex)}", self.error_color)
                logging.error(f"下载失败：{str(ex)}")
            finally:
                self.cleanup_download()

        # 启动下载线程
        download_thread = threading.Thread(target=download_worker, daemon=True)
        download_thread.start()

    def create_download_task_ui(self, tasks: List[DownloadTask]):
        """创建下载任务UI"""
        for task in tasks:
            task_card = self.create_task_card(task)
            self.download_tasks_list.controls.append(task_card)
        self.page.update()

    def create_task_card(self, task: DownloadTask):
        """创建单个任务卡片"""
        track = task.track

        # 状态图标
        status_icon = ft.Icon(ft.Icons.PENDING, color=ft.Colors.GREY_400, size=20)

        # 进度条
        progress_bar = ft.ProgressBar(
            value=0,
            width=200,
            height=6,
            color=self.primary_color,
            bgcolor=ft.Colors.GREY_200,
            border_radius=3
        )

        # 速度文本
        speed_text = ft.Text("等待中...", size=12, color=ft.Colors.GREY_600)

        task_card = ft.Container(
            content=ft.Row([
                # 封面图片
                ft.Container(
                    content=ft.Image(
                        src=track['picUrl'] if track['picUrl'] else "https://via.placeholder.com/50x50?text=No+Image",
                        width=50,
                        height=50,
                        fit=ft.ImageFit.COVER,
                        border_radius=6
                    )
                ),
                ft.Container(width=15),
                # 歌曲信息
                ft.Column([
                    ft.Text(
                        track['name'],
                        size=14,
                        weight=ft.FontWeight.BOLD,
                        max_lines=1,
                        overflow=ft.TextOverflow.ELLIPSIS
                    ),
                    ft.Text(
                        f"{track['artists']} - {track['album']}",
                        size=12,
                        color=ft.Colors.GREY_600,
                        max_lines=1,
                        overflow=ft.TextOverflow.ELLIPSIS
                    )
                ], spacing=2, expand=True),
                ft.Container(width=15),
                # 进度信息
                ft.Column([
                    ft.Row([status_icon, speed_text], spacing=8),
                    progress_bar
                ], spacing=5, horizontal_alignment=ft.CrossAxisAlignment.END)
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            padding=15,
            bgcolor=ft.Colors.WHITE,
            border_radius=10,
            border=ft.border.all(1, ft.Colors.GREY_200),
            data=task.id  # 存储任务ID用于更新
        )

        return task_card

    def download_single_task(self, task: DownloadTask):
        """下载单个任务"""
        try:
            # 更新任务状态为下载中
            self.download_progress_manager.update_task_status(task.id, "downloading")

            song_id = str(task.track['id'])
            song_name = task.track['name']
            cookies = self.cookie_manager.parse_cookie()

            # 清理文件名中的无效字符
            invalid_chars = '<>:"/\\|?*'
            clean_song_name = song_name
            clean_artists = task.track['artists']
            clean_album = task.track['album']

            for char in invalid_chars:
                clean_song_name = clean_song_name.replace(char, '')
                clean_artists = clean_artists.replace(char, '')
                clean_album = clean_album.replace(char, '')

            # 获取歌曲信息
            song_info = name_v1(song_id)['songs'][0]
            cover_url = song_info['al'].get('picUrl', '')

            # 获取下载链接
            url_data = url_v1(song_id, task.quality, cookies)
            if not url_data.get('data') or not url_data['data'][0].get('url'):
                self.download_progress_manager.update_task_status(task.id, "failed", "VIP限制或音质不可用")
                logging.warning(f"无法下载 {song_name}，可能是 VIP 限制或音质不可用")
                return

            song_url = url_data['data'][0]['url']
            file_extension = '.flac' if task.quality == 'lossless' else '.mp3'
            file_path = os.path.join(task.download_dir, f"{clean_song_name} - {clean_artists}{file_extension}")
            task.file_path = file_path

            # 检查文件是否已存在
            if os.path.exists(file_path):
                self.download_progress_manager.update_task_status(task.id, "completed")
                logging.info(f"{song_name} 已存在，跳过下载")
                return

            # 下载文件
            self.download_file_with_progress(song_url, file_path, task.id)

            # 添加元数据
            self.add_metadata(file_path, clean_song_name, clean_artists, clean_album, cover_url, file_extension)

            # 下载歌词
            if task.download_lyrics:
                try:
                    lyric_data = lyric_v1(song_id, cookies)
                    lyric = lyric_data.get('lrc', {}).get('lyric', '')
                    if lyric:
                        lyric_path = os.path.join(task.download_dir, f"{clean_song_name} - {clean_artists}.lrc")
                        with open(lyric_path, 'w', encoding='utf-8') as f:
                            f.write(lyric)
                        logging.info(f"已下载歌词：{song_name}")
                except Exception as lyric_error:
                    logging.warning(f"下载歌词失败：{song_name}，错误：{str(lyric_error)}")

            # 更新任务状态为完成
            self.download_progress_manager.update_task_status(task.id, "completed")
            logging.info(f"成功下载：{song_name}")

        except Exception as e:
            self.download_progress_manager.update_task_status(task.id, "failed", str(e))
            logging.error(f"下载 {task.track['name']} 失败：{str(e)}")

    def download_file_with_progress(self, url: str, file_path: str, task_id: str):
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
                        self.download_progress_manager.update_task_progress(task_id, progress, speed)

                elif self.is_paused:
                    # 暂停时等待
                    while self.is_paused and self.is_downloading:
                        time.sleep(0.1)
                elif not self.is_downloading:
                    # 取消下载
                    break

    def start_progress_timer(self):
        """启动进度更新定时器"""
        def update_progress():
            while self.is_downloading:
                if not self.is_paused:
                    self.update_ui_progress()
                time.sleep(0.5)  # 每0.5秒更新一次

        self.progress_update_timer = threading.Thread(target=update_progress, daemon=True)
        self.progress_update_timer.start()

    def update_ui_progress(self):
        """更新UI进度显示"""
        try:
            # 获取总体进度
            overall_progress, total_speed, completed, failed, downloading = self.download_progress_manager.get_overall_progress()

            # 更新总进度
            self.total_progress.value = overall_progress
            self.total_progress_text.value = f"📊 总进度: {completed}/{len(self.tracks)} (失败: {failed})"
            self.speed_text.value = f"🚀 总速度: {total_speed:.1f} KB/s"
            self.status_text.value = f"📋 状态: 下载中 ({downloading} 个活跃任务)"

            # 更新任务卡片
            self.update_task_cards()

            self.page.update()
        except Exception as e:
            logging.error(f"更新UI进度失败：{str(e)}")

    def update_task_cards(self):
        """更新任务卡片显示"""
        for card in self.download_tasks_list.controls:
            task_id = card.data
            task = self.download_progress_manager.get_task(task_id)
            if task:
                # 获取卡片中的组件
                row = card.content
                progress_column = row.controls[3]  # 进度信息列
                status_row = progress_column.controls[0]  # 状态行
                progress_bar = progress_column.controls[1]  # 进度条

                status_icon = status_row.controls[0]
                speed_text = status_row.controls[1]

                # 更新状态图标和文本
                if task.status == "pending":
                    status_icon.name = ft.Icons.PENDING
                    status_icon.color = ft.Colors.GREY_400
                    speed_text.value = "等待中..."
                    speed_text.color = ft.Colors.GREY_600
                elif task.status == "downloading":
                    status_icon.name = ft.Icons.DOWNLOAD
                    status_icon.color = self.primary_color
                    speed_text.value = f"{task.speed:.1f} KB/s"
                    speed_text.color = self.primary_color
                    progress_bar.value = task.progress
                elif task.status == "completed":
                    status_icon.name = ft.Icons.CHECK_CIRCLE
                    status_icon.color = self.success_color
                    speed_text.value = "已完成"
                    speed_text.color = self.success_color
                    progress_bar.value = 1.0
                elif task.status == "failed":
                    status_icon.name = ft.Icons.ERROR
                    status_icon.color = self.error_color
                    speed_text.value = "失败"
                    speed_text.color = self.error_color
                    progress_bar.value = 0

    def pause_download(self, e):
        """暂停下载"""
        self.is_paused = True
        self.pause_button.disabled = True
        self.resume_button.disabled = False
        self.status_text.value = "📋 状态: 已暂停"
        self.page.update()
        logging.info("下载已暂停")

    def resume_download(self, e):
        """继续下载"""
        self.is_paused = False
        self.pause_button.disabled = False
        self.resume_button.disabled = True
        self.status_text.value = "📋 状态: 下载中"
        self.page.update()
        logging.info("下载已继续")

    def cancel_download(self, e):
        """取消下载"""
        self.is_downloading = False
        self.is_paused = False
        self.cleanup_download()

        # 重置UI状态
        self.download_button.disabled = False
        self.pause_button.disabled = True
        self.resume_button.disabled = True
        self.cancel_button.disabled = True

        self.total_progress.value = 0
        self.total_progress_text.value = "📊 总进度: 0/0"
        self.speed_text.value = "🚀 下载速度: 0 KB/s"
        self.status_text.value = "📋 状态: 已取消"

        # 清空任务列表
        self.download_tasks_list.controls.clear()
        self.download_progress_manager = DownloadProgressManager()

        self.page.update()
        self.show_snackbar("❌ 下载已取消", self.warning_color)
        logging.info("下载已取消")

    def cleanup_download(self):
        """清理下载资源"""
        try:
            if self.thread_pool:
                self.thread_pool.shutdown(wait=False)
                self.thread_pool = None

            # 取消所有未完成的futures
            for future in self.download_futures:
                future.cancel()
            self.download_futures.clear()

        except Exception as e:
            logging.error(f"清理下载资源失败：{str(e)}")

    def on_download_complete(self, playlist_name: str):
        """下载完成处理"""
        self.is_downloading = False

        # 获取最终统计
        _, _, completed, failed, _ = self.download_progress_manager.get_overall_progress()

        # 更新UI状态
        self.download_button.disabled = False
        self.pause_button.disabled = True
        self.resume_button.disabled = True
        self.cancel_button.disabled = True

        self.total_progress.value = 1.0
        self.speed_text.value = "🚀 下载速度: 0 KB/s"
        self.status_text.value = f"📋 状态: 完成 (成功: {completed}, 失败: {failed})"

        self.page.update()

        # 显示完成消息
        if failed == 0:
            self.show_snackbar(f"🎉 歌单 {playlist_name} 下载完成！", self.success_color)
        else:
            self.show_snackbar(f"⚠️ 歌单 {playlist_name} 下载完成，{failed} 首歌曲失败", self.warning_color)

        logging.info(f"歌单 {playlist_name} 下载完成，成功: {completed}, 失败: {failed}")





    def add_metadata(self, file_path, title, artist, album, cover_url, file_extension):
        try:
            if file_extension == '.flac':
                audio = FLAC(file_path)
                audio['title'] = title
                audio['artist'] = artist
                audio['album'] = album
                if cover_url:
                    cover_response = requests.get(cover_url, timeout=5)
                    cover_response.raise_for_status()
                    image = Image.open(io.BytesIO(cover_response.content))
                    image = image.convert('RGB')  # 将图像转换为 RGB 模式，避免 RGBA 问题
                    image = image.resize((300, 300))
                    img_byte_arr = io.BytesIO()
                    image.save(img_byte_arr, format='JPEG')
                    img_data = img_byte_arr.getvalue()
                    from mutagen.flac import Picture
                    picture = Picture()
                    picture.type = 3  # 封面图片类型
                    picture.mime = 'image/jpeg'
                    picture.desc = 'Front Cover'
                    picture.data = img_data
                    audio.add_picture(picture)
                audio.save()
            else:  # MP3 格式
                audio = MP3(file_path, ID3=EasyID3)
                audio['title'] = title
                audio['artist'] = artist
                audio['album'] = album
                audio.save()
                if cover_url:
                    cover_response = requests.get(cover_url, timeout=5)
                    cover_response.raise_for_status()
                    image = Image.open(io.BytesIO(cover_response.content))
                    image = image.convert('RGB')  # 将图像转换为 RGB 模式，避免 RGBA 问题
                    image = image.resize((300, 300))
                    img_byte_arr = io.BytesIO()
                    image.save(img_byte_arr, format='JPEG')
                    img_data = img_byte_arr.getvalue()
                    audio = ID3(file_path)
                    audio.add(APIC(mime='image/jpeg', data=img_data))
                    audio.save()
            logging.info(f"成功嵌入元数据：{file_path}")
        except Exception as e:
            logging.error(f"嵌入元数据失败：{file_path}，错误：{str(e)}")

def main(page: ft.Page):
    MusicDownloaderApp(page)

if __name__ == "__main__":
    ft.app(target=main)