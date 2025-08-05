"""
网易云音乐 API 函数
"""
import json
import logging
import requests
import urllib.parse
from hashlib import md5
from random import randrange
from typing import Dict, Any
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes


def post(url: str, params: str, cookies: Dict[str, str]) -> str:
    """发送POST请求"""
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


def hash_hex_digest(text: str) -> str:
    """计算MD5哈希值"""
    return ''.join(hex(d)[2:].zfill(2) for d in md5(text.encode('utf-8')).digest())


def url_v1(id: str, level: str, cookies: Dict[str, str]) -> Dict[str, Any]:
    """获取歌曲下载链接"""
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


def name_v1(id: str) -> Dict[str, Any]:
    """获取歌曲详细信息"""
    url = "https://interface3.music.163.com/api/v3/song/detail"
    data = {'c': json.dumps([{"id": id, "v": 0}])}
    try:
        response = requests.post(url, data=data, timeout=5)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        logging.error(f"获取歌曲信息失败：{id}，错误：{str(e)}")
        raise


def lyric_v1(id: str, cookies: Dict[str, str]) -> Dict[str, Any]:
    """获取歌词"""
    url = "https://interface3.music.163.com/api/song/lyric"
    data = {'id': id, 'cp': 'false', 'tv': '0', 'lv': '0', 'rv': '0', 'kv': '0', 'yv': '0', 'ytv': '0', 'yrv': '0'}
    try:
        response = requests.post(url, data=data, cookies=cookies, timeout=5)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        logging.error(f"获取歌词失败：{id}，错误：{str(e)}")
        raise


def playlist_detail(playlist_id: str, cookies: Dict[str, str]) -> Dict[str, Any]:
    """获取歌单详情"""
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
