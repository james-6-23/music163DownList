"""
Cookie输入页面UI组件 - Spotify风格
"""
import flet as ft
import time
import threading
from ui.base_ui import BaseUI
from managers.cookie_manager import CookieManager


class CookieUI(BaseUI):
    """Cookie输入页面UI - Spotify风格"""
    
    def __init__(self, page: ft.Page, cookie_manager: CookieManager, on_success_callback):
        super().__init__(page)
        self.cookie_manager = cookie_manager
        self.on_success_callback = on_success_callback
        self.init_components()

    def init_components(self):
        """初始化UI组件 - Spotify风格"""
        # 标题组件
        self.cookie_title = ft.Text(
            "🎵 DownList",
            size=56,
            weight=ft.FontWeight.BOLD,
            color=self.primary_color,
            text_align=ft.TextAlign.CENTER
        )
        self.cookie_subtitle = ft.Text(
            "网易云音乐无限下载器",
            size=24,
            color=self.text_secondary_color,
            text_align=ft.TextAlign.CENTER,
            weight=ft.FontWeight.W_400
        )
        self.cookie_description = ft.Text(
            "请输入您的网易云音乐 MUSIC_U Cookie 以开始使用",
            size=16,
            color=self.text_secondary_color,
            text_align=ft.TextAlign.CENTER
        )

        # Cookie输入框 - Spotify风格
        self.cookie_input = ft.TextField(
            label="MUSIC_U Cookie",
            hint_text="请输入完整的MUSIC_U Cookie值",
            width=700,
            multiline=True,
            min_lines=4,
            max_lines=6,
            password=True,
            can_reveal_password=True,
            border_radius=16,
            filled=True,
            bgcolor=self.surface_color,
            color=self.text_primary_color,
            border_color=self.border_color,
            focused_border_color=self.primary_color,
            cursor_color=self.primary_color,
            text_size=14
        )

        # 帮助文本 - Spotify风格
        self.cookie_help_text = ft.Text(
            "💡 如何获取Cookie：\n\n"
            "1. 打开浏览器，访问 music.163.com 并登录\n"
            "2. 按F12打开开发者工具，切换到Application/存储标签\n"
            "3. 在Cookies中找到MUSIC_U，复制其值\n"
            "4. 将值粘贴到上方输入框中\n\n"
            "⚠️ 注意：建议使用有黑胶VIP的账号以获得更好的下载体验",
            size=14,
            color=self.text_secondary_color,
            text_align=ft.TextAlign.LEFT,
            weight=ft.FontWeight.W_400
        )

        # 验证按钮 - 增强的 Spotify 风格
        self.validate_button = self.create_enhanced_button(
            text="🔐 验证并继续",
            on_click=self.validate_cookie,
            variant="primary",
            size="large",
            icon=ft.Icons.SECURITY,
            width=280,
            tooltip="验证Cookie并进入下载页面"
        )

        # 辅助操作按钮
        self.clear_button = self.create_enhanced_button(
            text="清空",
            on_click=self.clear_cookie_input,
            variant="ghost",
            size="medium",
            icon=ft.Icons.CLEAR,
            tooltip="清空输入框"
        )

        self.help_button = self.create_enhanced_button(
            text="获取帮助",
            on_click=self.show_help_dialog,
            variant="outline",
            size="medium",
            icon=ft.Icons.HELP_OUTLINE,
            tooltip="查看Cookie获取教程"
        )

        # 状态显示 - Spotify风格
        self.validation_status = ft.Text(
            "",
            size=16,
            weight=ft.FontWeight.W_500,
            text_align=ft.TextAlign.CENTER
        )
        self.validation_progress = ft.ProgressRing(
            visible=False,
            width=28,
            height=28,
            color=self.primary_color,
            stroke_width=3
        )

    def show(self):
        """显示Cookie输入页面 - Spotify风格"""
        self.page.clean()

        # Spotify风格背景
        background_container = ft.Container(
            width=self.page.window_width,
            height=self.page.window_height,
            gradient=ft.LinearGradient(
                begin=ft.alignment.top_center,
                end=ft.alignment.bottom_center,
                colors=[self.background_color, "#0D1117"]
            )
        )

        # Spotify风格主卡片容器
        main_card = ft.Container(
            content=ft.Column([
                # 标题区域
                ft.Container(
                    content=ft.Column([
                        self.cookie_title,
                        ft.Container(height=16),
                        self.cookie_subtitle,
                        ft.Container(height=12),
                        self.cookie_description,
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    padding=ft.padding.only(top=50, bottom=40)
                ),

                # 输入区域
                ft.Container(
                    content=ft.Column([
                        self.cookie_input,
                        ft.Container(height=32),
                        # 辅助按钮组
                        self.create_button_group([
                            self.clear_button,
                            self.help_button
                        ], spacing=16, alignment=ft.MainAxisAlignment.CENTER),

                        ft.Container(height=16),

                        # 主要操作按钮
                        ft.Row([
                            self.validate_button,
                            ft.Container(width=24),
                            self.validation_progress
                        ], alignment=ft.MainAxisAlignment.CENTER),
                        ft.Container(height=20),
                        self.validation_status,
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    padding=24
                ),

                # 帮助信息卡片 - Spotify风格
                self.create_card_container(
                    content=self.cookie_help_text,
                    padding=32,
                    bgcolor=self.surface_variant_color,
                    border_radius=20
                )
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=24),
            width=850,
            bgcolor=self.surface_color,
            border_radius=24,
            padding=40,
            shadow=ft.BoxShadow(
                spread_radius=0,
                blur_radius=32,
                color=ft.Colors.with_opacity(0.4, ft.Colors.BLACK),
                offset=ft.Offset(0, 16)
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

    def validate_cookie(self, e):
        """验证Cookie有效性"""
        cookie_text = self.cookie_input.value.strip()
        if not cookie_text:
            self.validation_status.value = "❌ 请输入Cookie"
            self.validation_status.color = self.error_color
            self.page.update()
            return

        # 显示验证中状态 - 增强的 Spotify 风格
        self.validation_progress.visible = True
        self.validation_status.value = "🔄 正在验证Cookie..."
        self.validation_status.color = self.primary_color

        # 更新按钮为加载状态
        self.validate_button = self.create_enhanced_button(
            text="验证中...",
            variant="primary",
            size="large",
            loading=True,
            disabled=True,
            width=280
        )
        self.page.update()

        # 在后台线程中验证Cookie
        def validate_in_background():
            try:
                self.cookie_manager.set_cookie(cookie_text)
                is_valid, message = self.cookie_manager.validate_cookie()

                # 更新UI
                self.validation_progress.visible = False

                # 恢复按钮正常状态
                self.validate_button = self.create_enhanced_button(
                    text="🔐 验证并继续",
                    on_click=self.validate_cookie,
                    variant="primary",
                    size="large",
                    icon=ft.Icons.SECURITY,
                    width=280,
                    tooltip="验证Cookie并进入下载页面"
                )

                if is_valid:
                    self.validation_status.value = f"✅ {message}"
                    self.validation_status.color = self.success_color
                    self.page.update()

                    # 保存Cookie并切换到下载页面
                    self.cookie_manager.save_cookie()
                    time.sleep(1)  # 让用户看到成功消息
                    self.on_success_callback()
                else:
                    self.validation_status.value = f"❌ {message}"
                    self.validation_status.color = self.error_color
                    self.page.update()

            except Exception as ex:
                self.validation_progress.visible = False
                self.validate_button.disabled = False
                self.validation_status.value = f"❌ 验证失败：{str(ex)}"
                self.validation_status.color = self.error_color
                self.page.update()

        # 启动验证线程
        validation_thread = threading.Thread(target=validate_in_background, daemon=True)
        validation_thread.start()

    def clear_cookie_input(self, e):
        """清空Cookie输入框"""
        self.cookie_input.value = ""
        self.validation_status.value = ""
        self.validation_progress.visible = False
        self.validate_button.disabled = False
        self.page.update()
        self.show_snackbar("📝 输入框已清空", self.text_secondary_color)

    def show_help_dialog(self, e):
        """显示Cookie获取帮助对话框"""
        help_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("🔍 Cookie获取详细教程", size=20, weight=ft.FontWeight.BOLD),
            content=ft.Container(
                content=ft.Column([
                    ft.Text("详细步骤：", size=16, weight=ft.FontWeight.W_600),
                    ft.Container(height=12),
                    ft.Text("1. 打开Chrome或Edge浏览器", size=14),
                    ft.Text("2. 访问 https://music.163.com", size=14),
                    ft.Text("3. 登录您的网易云音乐账号", size=14),
                    ft.Text("4. 按F12键打开开发者工具", size=14),
                    ft.Text("5. 点击Application标签", size=14),
                    ft.Text("6. 在左侧找到Cookies > music.163.com", size=14),
                    ft.Text("7. 找到MUSIC_U项，复制Value值", size=14),
                    ft.Text("8. 将复制的值粘贴到输入框中", size=14),
                ], spacing=8),
                width=400,
                height=300
            ),
            actions=[
                self.create_enhanced_button(
                    text="我知道了",
                    on_click=lambda _: self.page.close(help_dialog),
                    variant="primary",
                    size="medium"
                )
            ]
        )
        self.page.open(help_dialog)

    def reset(self):
        """重置Cookie输入"""
        self.cookie_input.value = ""
        self.validation_status.value = ""
        self.validation_progress.visible = False
        self.validate_button.disabled = False
