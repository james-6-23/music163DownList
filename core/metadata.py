"""
元数据处理模块
"""
import io
import logging
import requests
from PIL import Image
from mutagen.mp3 import MP3
from mutagen.easyid3 import EasyID3
from mutagen.id3 import ID3, APIC
from mutagen.flac import FLAC


def add_metadata(file_path: str, title: str, artist: str, album: str, cover_url: str, file_extension: str):
    """为音频文件添加元数据"""
    try:
        if file_extension == '.flac':
            _add_flac_metadata(file_path, title, artist, album, cover_url)
        else:  # MP3 格式
            _add_mp3_metadata(file_path, title, artist, album, cover_url)
        logging.info(f"成功嵌入元数据：{file_path}")
    except Exception as e:
        logging.error(f"嵌入元数据失败：{file_path}，错误：{str(e)}")


def _add_flac_metadata(file_path: str, title: str, artist: str, album: str, cover_url: str):
    """为FLAC文件添加元数据"""
    audio = FLAC(file_path)
    audio['title'] = title
    audio['artist'] = artist
    audio['album'] = album
    
    if cover_url:
        cover_data = _download_and_process_cover(cover_url)
        if cover_data:
            from mutagen.flac import Picture
            picture = Picture()
            picture.type = 3  # 封面图片类型
            picture.mime = 'image/jpeg'
            picture.desc = 'Front Cover'
            picture.data = cover_data
            audio.add_picture(picture)
    
    audio.save()


def _add_mp3_metadata(file_path: str, title: str, artist: str, album: str, cover_url: str):
    """为MP3文件添加元数据"""
    audio = MP3(file_path, ID3=EasyID3)
    audio['title'] = title
    audio['artist'] = artist
    audio['album'] = album
    audio.save()
    
    if cover_url:
        cover_data = _download_and_process_cover(cover_url)
        if cover_data:
            audio = ID3(file_path)
            audio.add(APIC(mime='image/jpeg', data=cover_data))
            audio.save()


def _download_and_process_cover(cover_url: str) -> bytes:
    """下载并处理封面图片"""
    try:
        cover_response = requests.get(cover_url, timeout=5)
        cover_response.raise_for_status()
        image = Image.open(io.BytesIO(cover_response.content))
        image = image.convert('RGB')  # 将图像转换为 RGB 模式，避免 RGBA 问题
        image = image.resize((300, 300))
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format='JPEG')
        return img_byte_arr.getvalue()
    except Exception as e:
        logging.warning(f"处理封面图片失败：{str(e)}")
        return None
