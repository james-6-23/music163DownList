"""
基础UI组件和工具 - Spotify风格
"""
import flet as ft
from .enhanced_button_system import EnhancedButtonSystem, ButtonVariant, ButtonSize
from utils.constants import (
    PRIMARY_COLOR, SECONDARY_COLOR, SUCCESS_COLOR, ERROR_COLOR, WARNING_COLOR,
    BACKGROUND_COLOR, SURFACE_COLOR, SURFACE_VARIANT_COLOR,
    TEXT_PRIMARY_COLOR, TEXT_SECONDARY_COLOR, TEXT_DISABLED_COLOR,
    BORDER_COLOR, HOVER_COLOR
)


class BaseUI:
    """基础UI组件类 - Spotify风格"""

    def __init__(self, page: ft.Page):
        self.page = page
        # Spotify风格颜色
        self.primary_color = PRIMARY_COLOR
        self.secondary_color = SECONDARY_COLOR
        self.success_color = SUCCESS_COLOR
        self.error_color = ERROR_COLOR
        self.warning_color = WARNING_COLOR
        self.background_color = BACKGROUND_COLOR
        self.surface_color = SURFACE_COLOR
        self.surface_variant_color = SURFACE_VARIANT_COLOR
        self.text_primary_color = TEXT_PRIMARY_COLOR
        self.text_secondary_color = TEXT_SECONDARY_COLOR
        self.text_disabled_color = TEXT_DISABLED_COLOR
        self.border_color = BORDER_COLOR
        self.hover_color = HOVER_COLOR

        # 初始化增强按钮系统
        self.button_system = EnhancedButtonSystem({
            "primary_color": self.primary_color,
            "surface_variant_color": self.surface_variant_color,
            "text_primary_color": self.text_primary_color,
            "success_color": self.success_color,
            "warning_color": self.warning_color,
            "error_color": self.error_color
        })

    def show_snackbar(self, message: str, color: str):
        """显示消息提示 - Spotify风格"""
        self.page.snack_bar = ft.SnackBar(
            content=ft.Text(
                message,
                color=self.text_primary_color,
                size=14,
                weight=ft.FontWeight.W_500
            ),
            bgcolor=color,
            duration=3000,
            behavior=ft.SnackBarBehavior.FLOATING,
            margin=ft.margin.all(20),
            shape=ft.RoundedRectangleBorder(radius=12),
            elevation=8
        )
        self.page.snack_bar.open = True
        self.page.update()

    def show_loading_page(self, message="正在加载..."):
        """显示加载页面 - Spotify风格"""
        self.page.clean()
        self.page.add(
            ft.Container(
                content=ft.Column([
                    ft.Container(height=200),
                    ft.Row([
                        ft.ProgressRing(
                            width=60,
                            height=60,
                            color=self.primary_color,
                            stroke_width=4
                        ),
                    ], alignment=ft.MainAxisAlignment.CENTER),
                    ft.Container(height=30),
                    ft.Row([
                        ft.Text(
                            message,
                            size=18,
                            color=self.text_primary_color,
                            weight=ft.FontWeight.W_500
                        )
                    ], alignment=ft.MainAxisAlignment.CENTER),
                ], alignment=ft.MainAxisAlignment.CENTER),
                alignment=ft.alignment.center,
                bgcolor=self.background_color,
                expand=True
            )
        )
        self.page.update()

    def create_elevated_button(self, text: str, on_click, bgcolor=None, color=None, disabled=False, width=None, height=None, icon=None):
        """创建Spotify风格的提升按钮（保持向后兼容）"""
        button_bgcolor = bgcolor or self.primary_color
        button_color = color or self.text_primary_color

        return ft.ElevatedButton(
            text=text,
            icon=icon,
            on_click=on_click,
            bgcolor=button_bgcolor,
            color=button_color,
            disabled=disabled,
            width=width,
            height=height or 48,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=24),  # 更圆润的按钮
                text_style=ft.TextStyle(
                    size=14,
                    weight=ft.FontWeight.W_600,
                    letter_spacing=0.5
                )
            )
        )

    def create_enhanced_button(self, text: str, on_click=None, variant=ButtonVariant.PRIMARY,
                             size=ButtonSize.MEDIUM, icon=None, icon_position="left",
                             width=None, disabled=False, loading=False, tooltip=None, full_width=False):
        """创建增强的按钮（新的推荐方法）"""
        return self.button_system.create_enhanced_button(
            text=text,
            on_click=on_click,
            variant=variant,
            size=size,
            icon=icon,
            icon_position=icon_position,
            width=width,
            disabled=disabled,
            loading=loading,
            tooltip=tooltip,
            full_width=full_width
        )

    def create_button_group(self, buttons: list, spacing: float = 12, alignment=None):
        """创建按钮组"""
        return self.button_system.create_button_group(
            buttons=buttons,
            spacing=spacing,
            alignment=alignment or ft.MainAxisAlignment.START
        )

    def create_text_field(self, label: str, hint_text: str = "", width=None, multiline=False, password=False, prefix_icon=None):
        """创建Spotify风格的文本输入框"""
        return ft.TextField(
            label=label,
            hint_text=hint_text,
            width=width,
            multiline=multiline,
            password=password,
            can_reveal_password=password,
            prefix_icon=prefix_icon,
            border_radius=12,
            filled=True,
            bgcolor=self.surface_color,
            color=self.text_primary_color,
            border_color=self.border_color,
            focused_border_color=self.primary_color,
            cursor_color=self.primary_color,
            text_size=14
        )

    def create_dropdown(self, label: str, options: list, value=None, width=None, on_change=None):
        """创建Spotify风格的下拉选择框"""
        dropdown_options = [ft.dropdown.Option(key, text) for key, text in options]
        return ft.Dropdown(
            label=label,
            options=dropdown_options,
            value=value,
            width=width,
            border_radius=12,
            filled=True,
            bgcolor=self.surface_color,
            color=self.text_primary_color,
            border_color=self.border_color,
            focused_border_color=self.primary_color,
            on_change=on_change
        )

    def create_checkbox(self, label: str, value=False, on_change=None):
        """创建Spotify风格的复选框"""
        return ft.Checkbox(
            label=label,
            value=value,
            active_color=self.primary_color,
            check_color=self.background_color,
            label_style=ft.TextStyle(
                color=self.text_primary_color,
                size=14
            ),
            on_change=on_change
        )

    def create_progress_bar(self, width=None, value=0):
        """创建Spotify风格的进度条"""
        return ft.ProgressBar(
            width=width,
            value=value,
            color=self.primary_color,
            bgcolor=self.surface_variant_color,
            bar_height=6,
            border_radius=3
        )

    def create_card_container(self, content, padding=20, bgcolor=None, border_radius=16):
        """创建Spotify风格的卡片容器"""
        return ft.Container(
            content=content,
            padding=padding,
            bgcolor=bgcolor or self.surface_color,
            border_radius=border_radius,
            border=ft.border.all(1, self.border_color),
            shadow=ft.BoxShadow(
                spread_radius=0,
                blur_radius=8,
                color=ft.Colors.with_opacity(0.3, ft.Colors.BLACK),
                offset=ft.Offset(0, 4)
            )
        )

    def create_icon_button(self, icon, on_click, tooltip=None, icon_color=None, bgcolor=None, size=40):
        """创建Spotify风格的图标按钮"""
        return ft.IconButton(
            icon=icon,
            on_click=on_click,
            tooltip=tooltip,
            icon_color=icon_color or self.text_secondary_color,
            bgcolor=bgcolor,
            icon_size=20,
            width=size,
            height=size,
            style=ft.ButtonStyle(
                shape=ft.CircleBorder()
            )
        )

    def create_text(self, text, size=14, color=None, weight=None, max_lines=None):
        """创建Spotify风格的文本"""
        return ft.Text(
            text,
            size=size,
            color=color or self.text_primary_color,
            weight=weight,
            max_lines=max_lines,
            overflow=ft.TextOverflow.ELLIPSIS if max_lines else None
        )
