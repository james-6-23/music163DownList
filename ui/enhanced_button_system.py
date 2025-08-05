"""
增强的按钮系统 - 优化的 Spotify 风格按钮组件
提供更好的视觉效果、交互体验和响应式设计
"""
import flet as ft
from typing import Optional, Callable, Union


class ButtonVariant:
    """按钮变体定义"""
    PRIMARY = "primary"
    SECONDARY = "secondary"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    GHOST = "ghost"
    OUTLINE = "outline"


class ButtonSize:
    """按钮尺寸定义"""
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"
    EXTRA_LARGE = "extra_large"


class EnhancedButtonSystem:
    """增强的按钮系统"""
    
    def __init__(self, theme_colors: dict):
        """
        初始化按钮系统
        
        Args:
            theme_colors: 主题颜色字典，包含各种颜色定义
        """
        self.colors = theme_colors
        
        # 按钮尺寸配置
        self.size_config = {
            ButtonSize.SMALL: {"height": 36, "text_size": 12, "padding": 16, "icon_size": 16},
            ButtonSize.MEDIUM: {"height": 44, "text_size": 14, "padding": 20, "icon_size": 18},
            ButtonSize.LARGE: {"height": 52, "text_size": 16, "padding": 24, "icon_size": 20},
            ButtonSize.EXTRA_LARGE: {"height": 60, "text_size": 18, "padding": 28, "icon_size": 22}
        }
        
        # 按钮变体颜色配置
        self.variant_config = {
            ButtonVariant.PRIMARY: {
                "bgcolor": self.colors.get("primary_color", "#1DB954"),
                "color": "#FFFFFF",
                "hover_bgcolor": "#1ED760",
                "disabled_bgcolor": "#535353",
                "border_color": None
            },
            ButtonVariant.SECONDARY: {
                "bgcolor": self.colors.get("surface_variant_color", "#282828"),
                "color": self.colors.get("text_primary_color", "#FFFFFF"),
                "hover_bgcolor": "#3E3E3E",
                "disabled_bgcolor": "#181818",
                "border_color": None
            },
            ButtonVariant.SUCCESS: {
                "bgcolor": self.colors.get("success_color", "#1DB954"),
                "color": "#FFFFFF",
                "hover_bgcolor": "#1ED760",
                "disabled_bgcolor": "#535353",
                "border_color": None
            },
            ButtonVariant.WARNING: {
                "bgcolor": self.colors.get("warning_color", "#FFA726"),
                "color": "#000000",
                "hover_bgcolor": "#FFB74D",
                "disabled_bgcolor": "#535353",
                "border_color": None
            },
            ButtonVariant.ERROR: {
                "bgcolor": self.colors.get("error_color", "#F44336"),
                "color": "#FFFFFF",
                "hover_bgcolor": "#F66356",
                "disabled_bgcolor": "#535353",
                "border_color": None
            },
            ButtonVariant.GHOST: {
                "bgcolor": "transparent",
                "color": self.colors.get("text_primary_color", "#FFFFFF"),
                "hover_bgcolor": self.colors.get("surface_variant_color", "#282828"),
                "disabled_bgcolor": "transparent",
                "border_color": None
            },
            ButtonVariant.OUTLINE: {
                "bgcolor": "transparent",
                "color": self.colors.get("primary_color", "#1DB954"),
                "hover_bgcolor": self.colors.get("primary_color", "#1DB954"),
                "hover_color": "#FFFFFF",
                "disabled_bgcolor": "transparent",
                "border_color": self.colors.get("primary_color", "#1DB954")
            }
        }

    def create_enhanced_button(
        self,
        text: str,
        on_click: Optional[Callable] = None,
        variant: str = ButtonVariant.PRIMARY,
        size: str = ButtonSize.MEDIUM,
        icon: Optional[str] = None,
        icon_position: str = "left",  # "left", "right", "only"
        width: Optional[float] = None,
        disabled: bool = False,
        loading: bool = False,
        tooltip: Optional[str] = None,
        full_width: bool = False
    ) -> ft.ElevatedButton:
        """
        创建增强的按钮
        
        Args:
            text: 按钮文本
            on_click: 点击回调函数
            variant: 按钮变体
            size: 按钮尺寸
            icon: 图标
            icon_position: 图标位置
            width: 自定义宽度
            disabled: 是否禁用
            loading: 是否显示加载状态
            tooltip: 工具提示
            full_width: 是否全宽
            
        Returns:
            ft.ElevatedButton: 增强的按钮组件
        """
        size_conf = self.size_config[size]
        variant_conf = self.variant_config[variant]
        
        # 处理加载状态
        if loading:
            disabled = True
            if icon_position == "only":
                icon = ft.Icons.REFRESH
            else:
                icon = ft.Icons.REFRESH
                text = "加载中..."
        
        # 创建按钮内容
        button_content = self._create_button_content(
            text, icon, icon_position, size_conf, loading
        )
        
        # 计算按钮宽度
        button_width = width
        if full_width:
            button_width = None  # 让容器处理全宽
        elif width is None and icon_position == "only":
            button_width = size_conf["height"]  # 正方形图标按钮
        
        # 创建按钮样式
        button_style = self._create_button_style(variant_conf, size_conf, variant)
        
        button = ft.ElevatedButton(
            content=button_content if (icon and icon_position != "left") else None,
            text=text if not (icon and icon_position != "left") else None,
            icon=icon if icon_position == "left" else None,
            on_click=on_click,
            bgcolor=variant_conf["bgcolor"],
            color=variant_conf["color"],
            disabled=disabled,
            width=button_width,
            height=size_conf["height"],
            style=button_style,
            tooltip=tooltip
        )
        
        # 如果是全宽按钮，包装在容器中
        if full_width:
            return ft.Container(
                content=button,
                width=None,
                expand=True
            )
        
        return button

    def _create_button_content(self, text: str, icon: Optional[str], icon_position: str, size_conf: dict, loading: bool):
        """创建按钮内容"""
        if not icon:
            return None
            
        icon_size = size_conf["icon_size"]
        text_size = size_conf["text_size"]
        
        # 创建图标组件
        icon_component = ft.Icon(
            icon,
            size=icon_size,
            color=None  # 继承按钮颜色
        )
        
        # 如果是加载状态，使用旋转动画
        if loading and icon == ft.Icons.REFRESH:
            icon_component = ft.ProgressRing(
                width=icon_size,
                height=icon_size,
                stroke_width=2
            )
        
        if icon_position == "only":
            return icon_component
        elif icon_position == "right":
            return ft.Row([
                ft.Text(text, size=text_size, weight=ft.FontWeight.W_600),
                ft.Container(width=8),
                icon_component
            ], alignment=ft.MainAxisAlignment.CENTER, tight=True)
        else:  # left position handled by ElevatedButton's icon parameter
            return None

    def _create_button_style(self, variant_conf: dict, size_conf: dict, variant: str):
        """创建按钮样式"""
        # 基础样式
        style = ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=size_conf["height"] // 2),
            text_style=ft.TextStyle(
                size=size_conf["text_size"],
                weight=ft.FontWeight.W_600,
                letter_spacing=0.5
            ),
            padding=ft.padding.symmetric(horizontal=size_conf["padding"]),
            elevation={"": 2, "hovered": 4, "pressed": 1},
            animation_duration=200
        )
        
        # 添加边框（如果是outline变体）
        if variant == ButtonVariant.OUTLINE and variant_conf.get("border_color"):
            style.side = {
                "": ft.BorderSide(width=1.5, color=variant_conf["border_color"]),
                "hovered": ft.BorderSide(width=1.5, color=variant_conf["border_color"])
            }
        
        # 添加悬停效果
        if variant_conf.get("hover_bgcolor"):
            style.bgcolor = {
                "": variant_conf["bgcolor"],
                "hovered": variant_conf["hover_bgcolor"],
                "disabled": variant_conf["disabled_bgcolor"]
            }
            
        if variant_conf.get("hover_color"):
            style.color = {
                "": variant_conf["color"],
                "hovered": variant_conf["hover_color"]
            }
        
        return style

    def create_button_group(self, buttons: list, spacing: float = 12, alignment=ft.MainAxisAlignment.START):
        """
        创建按钮组
        
        Args:
            buttons: 按钮列表
            spacing: 按钮间距
            alignment: 对齐方式
            
        Returns:
            ft.Row: 按钮组容器
        """
        return ft.Row(
            controls=buttons,
            spacing=spacing,
            alignment=alignment,
            wrap=True
        )

    def create_floating_action_button(
        self,
        icon: str,
        on_click: Optional[Callable] = None,
        tooltip: Optional[str] = None,
        size: float = 56,
        mini: bool = False
    ) -> ft.FloatingActionButton:
        """
        创建浮动操作按钮
        
        Args:
            icon: 图标
            on_click: 点击回调
            tooltip: 工具提示
            size: 按钮尺寸
            mini: 是否为迷你版本
            
        Returns:
            ft.FloatingActionButton: 浮动操作按钮
        """
        fab_size = 40 if mini else size
        
        return ft.FloatingActionButton(
            icon=icon,
            on_click=on_click,
            tooltip=tooltip,
            bgcolor=self.colors.get("primary_color", "#1DB954"),
            foreground_color="#FFFFFF",
            width=fab_size,
            height=fab_size,
            mini=mini
        )
