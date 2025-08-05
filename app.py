"""
主应用程序 - 重构后的入口文件
"""
import flet as ft
import logging
import threading
from managers.cookie_manager import CookieManager
from ui.cookie_ui import CookieUI
from ui.download_ui import DownloadUI
from ui.base_ui import BaseUI

# 设置日志
logging.basicConfig(filename='download.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')


class MusicDownloaderApp(BaseUI):
    """音乐下载器主应用程序"""
    
    def __init__(self, page: ft.Page):
        super().__init__(page)
        self.page.title = "🎵 DownList - 网易云音乐下载器"
        self.page.window_width = 1400
        self.page.window_height = 1100
        self.page.theme_mode = ft.ThemeMode.DARK  # Spotify风格深色主题
        self.page.bgcolor = self.background_color

        # 核心组件
        self.cookie_manager = CookieManager()
        self.current_view = "cookie"  # cookie 或 download

        # UI组件
        self.cookie_ui = None
        self.download_ui = None

        # 检查是否已有有效Cookie，如果有则直接进入下载页面
        self.check_existing_cookie()

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

    def show_cookie_page(self):
        """显示Cookie输入页面"""
        self.current_view = "cookie"
        if not self.cookie_ui:
            self.cookie_ui = CookieUI(self.page, self.cookie_manager, self.show_download_page)
        else:
            self.cookie_ui.reset()
        self.cookie_ui.show()

    def show_download_page(self):
        """显示下载页面"""
        self.current_view = "download"
        if not self.download_ui:
            self.download_ui = DownloadUI(self.page, self.cookie_manager, self.show_cookie_page)
        self.download_ui.show()


def main(page: ft.Page):
    """应用程序入口点"""
    MusicDownloaderApp(page)


if __name__ == "__main__":
    ft.app(target=main)
