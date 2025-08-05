"""
文件处理工具函数
"""
import os

# 文件名无效字符 - 直接定义避免循环导入
INVALID_FILENAME_CHARS = '<>:"/\\|?*'


def clean_filename(filename: str) -> str:
    """清理文件名中的无效字符"""
    for char in INVALID_FILENAME_CHARS:
        filename = filename.replace(char, '')
    return filename


def extract_playlist_id(url: str) -> str:
    """从URL中提取歌单ID"""
    if 'music.163.com' in url or '163cn.tv' in url:
        index = url.find('id=') + 3
        return url[index:].split('&')[0]
    return url


def ensure_directory_exists(directory: str):
    """确保目录存在"""
    os.makedirs(directory, exist_ok=True)


def get_file_extension(quality: str) -> str:
    """根据音质获取文件扩展名"""
    return '.flac' if quality == 'lossless' else '.mp3'


def build_file_path(download_dir: str, song_name: str, artists: str, quality: str) -> str:
    """构建文件路径"""
    clean_song_name = clean_filename(song_name)
    clean_artists = clean_filename(artists)
    file_extension = get_file_extension(quality)
    return os.path.join(download_dir, f"{clean_song_name} - {clean_artists}{file_extension}")


def build_lyric_path(download_dir: str, song_name: str, artists: str) -> str:
    """构建歌词文件路径"""
    clean_song_name = clean_filename(song_name)
    clean_artists = clean_filename(artists)
    return os.path.join(download_dir, f"{clean_song_name} - {clean_artists}.lrc")
