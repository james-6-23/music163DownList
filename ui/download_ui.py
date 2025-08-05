"""
下载页面UI组件 - Spotify风格
"""
import flet as ft
import os
import threading
import logging
import uuid
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Set, Dict, Any
from ui.base_ui import BaseUI
from models.download_task import DownloadTask
from managers.download_manager import DownloadProgressManager
from managers.cookie_manager import CookieManager
from api.netease_api import playlist_detail
from core.downloader import DownloadCore
from utils.constants import QUALITY_OPTIONS, SORT_OPTIONS, DEFAULT_CONCURRENT_DOWNLOADS
from utils.file_utils import extract_playlist_id, ensure_directory_exists


class DownloadUI(BaseUI):
    """下载页面UI - Spotify风格"""
    
    def __init__(self, page: ft.Page, cookie_manager: CookieManager, on_reset_cookie_callback):
        super().__init__(page)
        self.cookie_manager = cookie_manager
        self.on_reset_cookie_callback = on_reset_cookie_callback
        
        # 数据状态
        self.download_dir = "C:\\"
        self.tracks = []
        self.selected_songs: Set[int] = set()
        self.filtered_tracks = []
        self.current_sort = "default"
        
        # 下载管理
        self.download_progress_manager = DownloadProgressManager()
        self.download_core = DownloadCore(self.download_progress_manager)
        self.max_concurrent_downloads = DEFAULT_CONCURRENT_DOWNLOADS
        self.thread_pool = None
        self.download_futures = []
        self.progress_update_timer = None
        
        self.init_components()

    def init_components(self):
        """初始化UI组件 - Spotify风格"""
        # 输入组件 - Spotify风格
        self.url_input = self.create_text_field(
            "🎵 歌单链接",
            "请输入网易云音乐歌单链接",
            width=600,
            prefix_icon=ft.Icons.LINK
        )

        self.quality_dropdown = self.create_dropdown(
            "🎧 音质选择",
            QUALITY_OPTIONS,
            value="standard",
            width=220
        )

        self.lyrics_checkbox = self.create_checkbox("📝 下载歌词", value=False)
        
        # 并发控制 - Spotify风格
        self.concurrent_slider = ft.Slider(
            min=1,
            max=8,
            divisions=7,
            value=3,
            label="并发数: {value}",
            width=220,
            active_color=self.primary_color,
            inactive_color=self.surface_variant_color,
            thumb_color=self.primary_color,
            on_change=self.on_concurrent_change
        )
        self.concurrent_text = self.create_text(
            "🚀 并发下载: 3 个线程",
            size=14,
            color=self.text_secondary_color
        )
        
        # 按钮组件 - Spotify风格
        self.dir_button = self.create_elevated_button(
            "📁 选择目录",
            self.select_directory,
            bgcolor=self.surface_variant_color,
            color=self.text_primary_color,
            icon=ft.Icons.FOLDER_OPEN
        )
        self.dir_text = self.create_text(
            f"📂 下载目录: {self.download_dir}",
            size=14,
            color=self.text_secondary_color
        )

        self.parse_button = self.create_elevated_button(
            "🔍 解析歌单",
            self.parse_playlist,
            icon=ft.Icons.SEARCH
        )

        self.download_all_button = self.create_elevated_button(
            "⬇️ 下载全部",
            self.start_download,
            disabled=True,
            icon=ft.Icons.DOWNLOAD
        )

        self.download_selected_button = self.create_elevated_button(
            "⬇️ 下载选中",
            self.download_selected,
            disabled=True,
            bgcolor=self.success_color,
            icon=ft.Icons.DOWNLOAD_FOR_OFFLINE
        )

        self.pause_button = self.create_elevated_button(
            "⏸️ 暂停",
            self.pause_download,
            disabled=True,
            bgcolor=self.warning_color,
            icon=ft.Icons.PAUSE
        )

        self.resume_button = self.create_elevated_button(
            "▶️ 继续",
            self.resume_download,
            disabled=True,
            bgcolor=self.success_color,
            icon=ft.Icons.PLAY_ARROW
        )

        self.cancel_button = self.create_elevated_button(
            "❌ 取消",
            self.cancel_download,
            disabled=True,
            bgcolor=self.error_color,
            icon=ft.Icons.CANCEL
        )

        self.reset_cookie_button = self.create_elevated_button(
            "🔑 重设Cookie",
            self.reset_cookie,
            bgcolor=self.surface_variant_color,
            color=self.text_secondary_color,
            icon=ft.Icons.REFRESH
        )
        
        # 进度显示组件 - Spotify风格
        self.total_progress = self.create_progress_bar(width=800)
        self.total_progress_text = self.create_text(
            "📊 总进度: 0/0",
            size=18,
            weight=ft.FontWeight.W_600
        )
        self.speed_text = self.create_text(
            "🚀 下载速度: 0 KB/s",
            size=14,
            color=self.text_secondary_color
        )
        self.status_text = self.create_text(
            "📋 状态: 等待开始",
            size=14,
            color=self.text_secondary_color
        )
        
        # 搜索和筛选组件 - Spotify风格
        self.search_input = self.create_text_field(
            "🔍 搜索歌曲",
            "输入歌曲名或艺术家名称",
            width=320,
            prefix_icon=ft.Icons.SEARCH
        )
        self.search_input.on_change = self.on_search_change

        self.sort_dropdown = self.create_dropdown(
            "📊 排序方式",
            SORT_OPTIONS,
            value="default",
            width=180,
            on_change=self.on_sort_change
        )
        
        # 选择控制组件 - Spotify风格
        self.select_all_checkbox = self.create_checkbox(
            "全选",
            on_change=self.on_select_all_change
        )

        self.invert_selection_button = ft.TextButton(
            "反选",
            on_click=self.invert_selection,
            style=ft.ButtonStyle(
                color=self.primary_color
            )
        )

        self.selection_status_text = self.create_text(
            "已选择 0/0 首歌曲",
            size=14,
            color=self.text_secondary_color
        )
        
        # 歌曲列表
        self.song_list = ft.ListView(
            expand=True,
            spacing=2,
            padding=ft.padding.all(10),
            auto_scroll=False
        )
        
        # 下载任务列表
        self.download_tasks_list = ft.ListView(
            expand=True,
            spacing=8,
            padding=10
        )

    def show(self):
        """显示下载页面 - Spotify风格"""
        self.page.clean()

        # Spotify风格标题栏
        header = ft.Container(
            content=ft.Row([
                ft.Row([
                    ft.Icon(ft.Icons.MUSIC_NOTE, color=self.primary_color, size=32),
                    ft.Container(width=12),
                    ft.Text(
                        "DownList",
                        size=28,
                        weight=ft.FontWeight.BOLD,
                        color=self.text_primary_color
                    ),
                ]),
                ft.Container(expand=True),
                self.reset_cookie_button
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            padding=ft.padding.symmetric(horizontal=24, vertical=16),
            bgcolor=self.surface_color,
            border=ft.border.only(bottom=ft.BorderSide(1, self.border_color)),
            shadow=ft.BoxShadow(
                spread_radius=0,
                blur_radius=8,
                color=ft.Colors.with_opacity(0.2, ft.Colors.BLACK),
                offset=ft.Offset(0, 2)
            )
        )

        # Spotify风格输入配置区域
        config_section = self.create_card_container(
            ft.Column([
                ft.Row([
                    self.url_input,
                    ft.Container(width=16),
                    self.parse_button
                ], alignment=ft.MainAxisAlignment.CENTER),
                ft.Container(height=20),
                ft.Row([
                    self.quality_dropdown,
                    ft.Container(width=20),
                    self.lyrics_checkbox,
                    ft.Container(width=20),
                    self.dir_button
                ], alignment=ft.MainAxisAlignment.CENTER),
                ft.Container(height=16),
                self.dir_text,
                ft.Container(height=16),
                ft.Row([
                    self.concurrent_text,
                    ft.Container(width=20),
                    self.concurrent_slider
                ], alignment=ft.MainAxisAlignment.CENTER)
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            padding=24
        )

        # Spotify风格下载控制区域
        control_section = self.create_card_container(
            ft.Row([
                # 选择控制
                ft.Column([
                    self.create_text(
                        "选择控制",
                        size=16,
                        weight=ft.FontWeight.BOLD,
                        color=self.primary_color
                    ),
                    ft.Container(height=12),
                    ft.Row([
                        self.select_all_checkbox,
                        ft.Container(width=8),
                        self.invert_selection_button,
                        ft.Container(width=16),
                        self.selection_status_text
                    ], spacing=0)
                ], horizontal_alignment=ft.CrossAxisAlignment.START),

                ft.Container(expand=True),

                # 下载按钮
                ft.Column([
                    self.create_text(
                        "下载操作",
                        size=16,
                        weight=ft.FontWeight.BOLD,
                        color=self.primary_color
                    ),
                    ft.Container(height=12),
                    ft.Row([
                        self.download_selected_button,
                        ft.Container(width=12),
                        self.download_all_button,
                        ft.Container(width=12),
                        self.pause_button,
                        ft.Container(width=12),
                        self.resume_button,
                        ft.Container(width=12),
                        self.cancel_button
                    ])
                ], horizontal_alignment=ft.CrossAxisAlignment.END)
            ]),
            padding=24
        )

        # Spotify风格进度显示区域
        progress_section = self.create_card_container(
            ft.Column([
                ft.Row([
                    self.total_progress_text,
                    ft.Container(expand=True),
                    self.speed_text,
                    ft.Container(width=24),
                    self.status_text
                ]),
                ft.Container(height=16),
                self.total_progress
            ]),
            padding=20
        )

        # 歌曲列表区域
        song_list_section = self.create_song_list_section()

        # Spotify风格主要内容区域
        main_content = ft.Container(
            content=ft.Column([
                config_section,
                ft.Container(height=16),
                control_section,
                ft.Container(height=16),
                progress_section,
                ft.Container(height=16),
                song_list_section
            ], scroll=ft.ScrollMode.AUTO),
            padding=ft.padding.all(20),
            expand=True,
            bgcolor=self.background_color
        )

        # Spotify风格页面布局
        self.page.add(
            ft.Column([
                header,
                main_content
            ], expand=True, spacing=0)
        )
        self.page.update()

    def create_song_list_section(self):
        """创建歌曲列表区域 - Spotify风格"""
        # Spotify风格搜索和排序控制栏
        search_bar = ft.Container(
            content=ft.Row([
                self.search_input,
                ft.Container(width=20),
                self.sort_dropdown,
                ft.Container(expand=True),
                self.create_text(
                    "🎵 歌曲列表",
                    size=18,
                    weight=ft.FontWeight.BOLD,
                    color=self.primary_color
                )
            ]),
            padding=ft.padding.symmetric(horizontal=20, vertical=16),
            bgcolor=self.surface_variant_color,
            border_radius=ft.border_radius.only(top_left=16, top_right=16)
        )

        # Spotify风格列表头部
        list_header = ft.Container(
            content=ft.Row([
                ft.Container(width=50),  # 复选框列
                ft.Container(width=70),  # 封面列
                ft.Container(
                    content=self.create_text(
                        "歌曲名",
                        size=14,
                        weight=ft.FontWeight.BOLD,
                        color=self.text_secondary_color
                    ),
                    width=220
                ),
                ft.Container(
                    content=self.create_text(
                        "艺术家",
                        size=14,
                        weight=ft.FontWeight.BOLD,
                        color=self.text_secondary_color
                    ),
                    width=180
                ),
                ft.Container(
                    content=self.create_text(
                        "专辑",
                        size=14,
                        weight=ft.FontWeight.BOLD,
                        color=self.text_secondary_color
                    ),
                    width=180
                ),
                ft.Container(
                    content=self.create_text(
                        "状态",
                        size=14,
                        weight=ft.FontWeight.BOLD,
                        color=self.text_secondary_color
                    ),
                    width=100
                ),
                ft.Container(width=120)  # 操作列
            ]),
            padding=ft.padding.symmetric(horizontal=20, vertical=12),
            bgcolor=self.surface_color,
            border=ft.border.only(bottom=ft.BorderSide(1, self.border_color))
        )

        # Spotify风格歌曲列表容器
        song_list_container = ft.Container(
            content=self.song_list,
            expand=True,
            bgcolor=self.surface_color
        )

        return ft.Container(
            content=ft.Column([
                search_bar,
                list_header,
                song_list_container
            ], spacing=0),
            border_radius=16,
            border=ft.border.all(1, self.border_color),
            expand=True,
            shadow=ft.BoxShadow(
                spread_radius=0,
                blur_radius=8,
                color=ft.Colors.with_opacity(0.2, ft.Colors.BLACK),
                offset=ft.Offset(0, 4)
            )
        )

    def on_concurrent_change(self, e):
        """并发数量变化处理"""
        self.max_concurrent_downloads = int(e.control.value)
        self.concurrent_text.value = f"🚀 并发下载: {self.max_concurrent_downloads} 个线程"
        self.page.update()

    def on_search_change(self, e):
        """搜索内容变化处理"""
        search_text = e.control.value.lower().strip()
        self.filter_and_sort_tracks(search_text, self.current_sort)

    def on_sort_change(self, e):
        """排序方式变化处理"""
        self.current_sort = e.control.value
        search_text = self.search_input.value.lower().strip() if self.search_input.value else ""
        self.filter_and_sort_tracks(search_text, self.current_sort)

    def filter_and_sort_tracks(self, search_text="", sort_by="default"):
        """筛选和排序歌曲"""
        if not self.tracks:
            return

        # 筛选
        if search_text:
            self.filtered_tracks = [
                track for track in self.tracks
                if search_text in track['name'].lower() or
                   search_text in track['artists'].lower() or
                   search_text in track['album'].lower()
            ]
        else:
            self.filtered_tracks = self.tracks.copy()

        # 排序
        if sort_by == "name":
            self.filtered_tracks.sort(key=lambda x: x['name'].lower())
        elif sort_by == "artist":
            self.filtered_tracks.sort(key=lambda x: x['artists'].lower())
        elif sort_by == "album":
            self.filtered_tracks.sort(key=lambda x: x['album'].lower())
        # default 保持原顺序

        # 更新显示
        self.update_song_list()
        self.update_selection_status()

    def on_select_all_change(self, e):
        """全选/取消全选处理"""
        if e.control.value:
            # 全选当前筛选的歌曲
            for track in self.filtered_tracks:
                self.selected_songs.add(track['id'])
        else:
            # 取消全选
            self.selected_songs.clear()

        self.update_song_list()
        self.update_selection_status()

    def invert_selection(self, e):
        """反选处理"""
        current_filtered_ids = {track['id'] for track in self.filtered_tracks}

        # 计算反选结果
        new_selection = set()
        for track_id in current_filtered_ids:
            if track_id not in self.selected_songs:
                new_selection.add(track_id)

        # 保留不在当前筛选中的选择
        for track_id in self.selected_songs:
            if track_id not in current_filtered_ids:
                new_selection.add(track_id)

        self.selected_songs = new_selection
        self.update_song_list()
        self.update_selection_status()

    def update_selection_status(self):
        """更新选择状态显示"""
        total_count = len(self.tracks)
        selected_count = len(self.selected_songs)

        self.selection_status_text.value = f"已选择 {selected_count}/{total_count} 首歌曲"

        # 更新全选复选框状态
        if selected_count == 0:
            self.select_all_checkbox.value = False
        elif selected_count == len(self.filtered_tracks):
            self.select_all_checkbox.value = True
        else:
            self.select_all_checkbox.value = None  # 部分选择状态

        # 更新下载按钮状态
        self.download_selected_button.disabled = selected_count == 0

        self.page.update()

    def on_song_selection_change(self, e, track_id):
        """单首歌曲选择状态变化"""
        if e.control.value:
            self.selected_songs.add(track_id)
        else:
            self.selected_songs.discard(track_id)

        self.update_selection_status()

    def select_directory(self, e):
        """选择下载目录"""
        dialog = ft.FilePicker(on_result=self.on_directory_picked)
        self.page.overlay.append(dialog)
        self.page.update()
        dialog.get_directory_path()

    def on_directory_picked(self, e: ft.FilePickerResultEvent):
        """目录选择回调"""
        if e.path:
            self.download_dir = e.path
            self.dir_text.value = f"📂 下载目录: {self.download_dir}"
            self.page.update()

    def reset_cookie(self, e):
        """重新设置Cookie"""
        self.on_reset_cookie_callback()

    def parse_playlist(self, e):
        """解析歌单"""
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
                playlist_id = extract_playlist_id(url)
                playlist_info = playlist_detail(playlist_id, cookies)

                if playlist_info['status'] != 200:
                    self.parse_button.disabled = False
                    self.parse_button.text = "🔍 解析歌单"
                    self.show_snackbar(f"❌ 歌单解析失败：{playlist_info['msg']}", self.error_color)
                    self.page.update()
                    logging.error(f"歌单解析失败：{playlist_info['msg']}")
                    return

                self.tracks = playlist_info['playlist']['tracks']
                self.filtered_tracks = self.tracks.copy()  # 初始化筛选列表
                self.selected_songs.clear()  # 清空选择
                self.update_song_list()

                self.total_progress_text.value = f"📊 总进度: 0/{len(self.tracks)}"
                self.download_all_button.disabled = False
                self.parse_button.disabled = False
                self.parse_button.text = "🔍 解析歌单"
                self.update_selection_status()

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

        tracks_to_show = self.filtered_tracks if hasattr(self, 'filtered_tracks') and self.filtered_tracks else self.tracks

        for i, track in enumerate(tracks_to_show):
            # Spotify风格交替背景色
            bg_color = self.surface_color if i % 2 == 0 else self.surface_variant_color

            # Spotify风格复选框
            checkbox = self.create_checkbox(
                "",
                value=track['id'] in self.selected_songs,
                on_change=lambda e, track_id=track['id']: self.on_song_selection_change(e, track_id)
            )

            # Spotify风格封面图片
            cover_image = ft.Container(
                content=ft.Image(
                    src=track['picUrl'] if track['picUrl'] else "https://via.placeholder.com/56x56?text=No+Image",
                    width=56,
                    height=56,
                    fit=ft.ImageFit.COVER,
                    border_radius=8
                ),
                width=56,
                height=56,
                shadow=ft.BoxShadow(
                    spread_radius=0,
                    blur_radius=4,
                    color=ft.Colors.with_opacity(0.3, ft.Colors.BLACK),
                    offset=ft.Offset(0, 2)
                )
            )

            # Spotify风格歌曲信息
            song_name = ft.Container(
                content=self.create_text(
                    track['name'],
                    size=15,
                    weight=ft.FontWeight.W_500,
                    max_lines=2
                ),
                width=220,
                padding=ft.padding.symmetric(horizontal=12)
            )

            artist_name = ft.Container(
                content=self.create_text(
                    track['artists'],
                    size=14,
                    color=self.text_secondary_color,
                    max_lines=1
                ),
                width=180,
                padding=ft.padding.symmetric(horizontal=12)
            )

            album_name = ft.Container(
                content=self.create_text(
                    track['album'],
                    size=14,
                    color=self.text_secondary_color,
                    max_lines=1
                ),
                width=180,
                padding=ft.padding.symmetric(horizontal=12)
            )

            # 状态图标
            status_icon = self.get_song_status_icon(track['id'])

            # Spotify风格下载按钮
            download_button = self.create_icon_button(
                icon=ft.Icons.DOWNLOAD,
                on_click=lambda e, track_data=track: self.download_single_song(track_data),
                tooltip="下载此歌曲",
                icon_color=self.primary_color,
                size=44
            )

            # Spotify风格行容器
            song_row = ft.Container(
                content=ft.Row([
                    ft.Container(content=checkbox, width=50),
                    ft.Container(content=cover_image, width=70),
                    song_name,
                    artist_name,
                    album_name,
                    ft.Container(content=status_icon, width=100, alignment=ft.alignment.center),
                    ft.Container(content=download_button, width=120, alignment=ft.alignment.center)
                ], alignment=ft.MainAxisAlignment.START),
                padding=ft.padding.symmetric(horizontal=20, vertical=12),
                bgcolor=bg_color,
                border=ft.border.only(bottom=ft.BorderSide(1, self.border_color)),
                on_hover=lambda e, row_bg=bg_color: self.on_song_row_hover(e, row_bg),
                border_radius=8
            )

            self.song_list.controls.append(song_row)

        self.page.update()

    def get_song_status_icon(self, track_id):
        """获取歌曲状态图标"""
        # 检查是否在下载任务中
        for task in self.download_progress_manager.get_all_tasks():
            if task.track['id'] == track_id:
                if task.status == "downloading":
                    return ft.Icon(ft.Icons.DOWNLOAD, color=self.primary_color, size=20)
                elif task.status == "completed":
                    return ft.Icon(ft.Icons.CHECK_CIRCLE, color=self.success_color, size=20)
                elif task.status == "failed":
                    return ft.Icon(ft.Icons.ERROR, color=self.error_color, size=20)
                elif task.status == "pending":
                    return ft.Icon(ft.Icons.PENDING, color=ft.Colors.GREY_400, size=20)

        return ft.Icon(ft.Icons.MUSIC_NOTE, color=ft.Colors.GREY_400, size=20)

    def on_song_row_hover(self, e, original_bg):
        """Spotify风格歌曲行悬停效果"""
        if e.data == "true":
            e.control.bgcolor = self.hover_color
        else:
            e.control.bgcolor = original_bg
        self.page.update()

    def download_single_song(self, track):
        """下载单首歌曲"""
        if self.download_core.is_downloading:
            self.show_snackbar("⚠️ 请等待当前下载完成", self.warning_color)
            return

        # 临时设置选择状态
        original_selection = self.selected_songs.copy()
        self.selected_songs = {track['id']}

        # 开始下载
        self.download_selected(None)

        # 恢复选择状态
        self.selected_songs = original_selection
        self.update_selection_status()

    def download_selected(self, e):
        """下载选中的歌曲"""
        if not self.selected_songs:
            self.show_snackbar("❌ 请先选择要下载的歌曲", self.error_color)
            return

        try:
            self.cookie_manager.read_cookie()
        except Exception as ex:
            self.show_snackbar(f"❌ {str(ex)}", self.error_color)
            logging.error(str(ex))
            return

        # 获取选中的歌曲
        selected_tracks = [track for track in self.tracks if track['id'] in self.selected_songs]

        if not selected_tracks:
            self.show_snackbar("❌ 未找到选中的歌曲", self.error_color)
            return

        self._start_download_process(selected_tracks, is_selected_only=True)

    def start_download(self, e):
        """开始下载全部歌曲"""
        if not self.tracks:
            self.show_snackbar("❌ 请先解析歌单", self.error_color)
            return

        try:
            self.cookie_manager.read_cookie()
        except Exception as ex:
            self.show_snackbar(f"❌ {str(ex)}", self.error_color)
            logging.error(str(ex))
            return

        self._start_download_process(self.tracks, is_selected_only=False)

    def _start_download_process(self, tracks_to_download: List[Dict[str, Any]], is_selected_only: bool):
        """启动下载进程"""
        # 更新UI状态
        self.download_selected_button.disabled = True
        self.download_all_button.disabled = True
        self.pause_button.disabled = False
        self.cancel_button.disabled = False
        self.download_core.set_download_state(True, False)

        # 清空之前的下载任务
        self.download_progress_manager = DownloadProgressManager()
        self.download_core = DownloadCore(self.download_progress_manager)
        self.download_core.set_download_state(True, False)
        self.download_tasks_list.controls.clear()

        # 启动多线程下载
        self._start_multithreaded_download(tracks_to_download, is_selected_only)

        # 启动进度更新定时器
        self._start_progress_timer()

    def _start_multithreaded_download(self, tracks_to_download: List[Dict[str, Any]], is_selected_only: bool):
        """启动多线程下载"""
        def download_worker():
            try:
                # 获取歌单信息
                cookies = self.cookie_manager.parse_cookie()
                playlist_id = extract_playlist_id(self.url_input.value.strip())
                playlist_info = playlist_detail(playlist_id, cookies)

                if playlist_info['status'] != 200:
                    self.show_snackbar(f"❌ 歌单解析失败：{playlist_info['msg']}", self.error_color)
                    return

                playlist_name = playlist_info['playlist']['name']
                if is_selected_only:
                    playlist_name += " (选中歌曲)"

                download_dir = os.path.join(self.download_dir, playlist_name)
                ensure_directory_exists(download_dir)

                # 创建下载任务
                tasks = []
                for track in tracks_to_download:
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
                self._create_download_task_ui(tasks)

                # 使用线程池执行下载
                self.thread_pool = ThreadPoolExecutor(max_workers=self.max_concurrent_downloads)
                self.download_futures = []

                for task in tasks:
                    if not self.download_core.is_downloading:
                        break
                    future = self.thread_pool.submit(self.download_core.download_single_task, task, cookies)
                    self.download_futures.append(future)

                # 等待所有任务完成
                for future in as_completed(self.download_futures):
                    if not self.download_core.is_downloading:
                        break

                # 下载完成处理
                if self.download_core.is_downloading and not self.download_core.is_paused:
                    self._on_download_complete(playlist_name)

            except Exception as ex:
                self.show_snackbar(f"❌ 下载失败：{str(ex)}", self.error_color)
                logging.error(f"下载失败：{str(ex)}")
            finally:
                self._cleanup_download()

        # 启动下载线程
        download_thread = threading.Thread(target=download_worker, daemon=True)
        download_thread.start()

    def _create_download_task_ui(self, tasks: List[DownloadTask]):
        """创建下载任务UI"""
        for task in tasks:
            task_card = self._create_task_card(task)
            self.download_tasks_list.controls.append(task_card)
        self.page.update()

    def _create_task_card(self, task: DownloadTask):
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

    def _start_progress_timer(self):
        """启动进度更新定时器"""
        def update_progress():
            while self.download_core.is_downloading:
                if not self.download_core.is_paused:
                    self._update_ui_progress()
                time.sleep(0.5)  # 每0.5秒更新一次

        self.progress_update_timer = threading.Thread(target=update_progress, daemon=True)
        self.progress_update_timer.start()

    def _update_ui_progress(self):
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
            self._update_task_cards()

            self.page.update()
        except Exception as e:
            logging.error(f"更新UI进度失败：{str(e)}")

    def _update_task_cards(self):
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
        self.download_core.set_download_state(True, True)
        self.pause_button.disabled = True
        self.resume_button.disabled = False
        self.status_text.value = "📋 状态: 已暂停"
        self.page.update()
        logging.info("下载已暂停")

    def resume_download(self, e):
        """继续下载"""
        self.download_core.set_download_state(True, False)
        self.pause_button.disabled = False
        self.resume_button.disabled = True
        self.status_text.value = "📋 状态: 下载中"
        self.page.update()
        logging.info("下载已继续")

    def cancel_download(self, e):
        """取消下载"""
        self.download_core.set_download_state(False, False)
        self._cleanup_download()

        # 重置UI状态
        self.download_all_button.disabled = len(self.tracks) == 0
        self.download_selected_button.disabled = len(self.selected_songs) == 0
        self.pause_button.disabled = True
        self.resume_button.disabled = True
        self.cancel_button.disabled = True

        self.total_progress.value = 0
        self.total_progress_text.value = "📊 总进度: 0/0"
        self.speed_text.value = "🚀 下载速度: 0 KB/s"
        self.status_text.value = "📋 状态: 已取消"

        # 清空任务列表
        self.download_tasks_list.controls.clear()
        from managers.download_manager import DownloadProgressManager
        self.download_progress_manager = DownloadProgressManager()

        self.page.update()
        self.show_snackbar("❌ 下载已取消", self.warning_color)
        logging.info("下载已取消")

    def _cleanup_download(self):
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

    def _on_download_complete(self, playlist_name: str):
        """下载完成处理"""
        self.download_core.set_download_state(False, False)

        # 获取最终统计
        _, _, completed, failed, _ = self.download_progress_manager.get_overall_progress()

        # 更新UI状态
        self.download_all_button.disabled = False
        self.download_selected_button.disabled = len(self.selected_songs) == 0
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
