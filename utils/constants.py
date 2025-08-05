"""
常量定义 - Spotify风格配色
"""
import flet as ft

# Spotify风格主题颜色
PRIMARY_COLOR = "#1DB954"  # Spotify绿色
SECONDARY_COLOR = "#1ED760"  # 亮绿色
BACKGROUND_COLOR = "#121212"  # 深黑色背景
SURFACE_COLOR = "#181818"  # 卡片背景
SURFACE_VARIANT_COLOR = "#282828"  # 悬停状态
TEXT_PRIMARY_COLOR = "#FFFFFF"  # 主要文本
TEXT_SECONDARY_COLOR = "#B3B3B3"  # 次要文本
TEXT_DISABLED_COLOR = "#535353"  # 禁用文本
SUCCESS_COLOR = "#1DB954"  # 成功状态（绿色）
ERROR_COLOR = "#E22134"  # 错误状态（红色）
WARNING_COLOR = "#FFA500"  # 警告状态（橙色）
BORDER_COLOR = "#2A2A2A"  # 边框颜色
HOVER_COLOR = "#2A2A2A"  # 悬停颜色

# 音质选项
QUALITY_OPTIONS = [
    ("standard", "标准音质"),
    ("exhigh", "极高音质"),
    ("lossless", "无损音质"),
    ("hires", "Hi-Res"),
    ("sky", "沉浸环绕声"),
    ("jyeffect", "高清环绕声"),
    ("jymaster", "超清母带")
]

# 排序选项
SORT_OPTIONS = [
    ("default", "默认顺序"),
    ("name", "按歌曲名"),
    ("artist", "按艺术家"),
    ("album", "按专辑")
]

# 文件名无效字符
INVALID_FILENAME_CHARS = '<>:"/\\|?*'

# 默认设置
DEFAULT_DOWNLOAD_DIR = "C:\\"
DEFAULT_CONCURRENT_DOWNLOADS = 3
DEFAULT_QUALITY = "standard"
