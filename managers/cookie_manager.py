"""
Cookie 管理器
"""
import logging
import requests
from typing import Dict, Tuple


class CookieManager:
    """Cookie 管理"""
    
    def __init__(self, cookie_file='cookie.txt'):
        self.cookie_file = cookie_file
        self.cookie_text = None

    def set_cookie(self, cookie_text: str):
        """设置Cookie文本"""
        self.cookie_text = cookie_text.strip()

    def read_cookie(self) -> str:
        """读取Cookie，优先使用内存中的Cookie"""
        if self.cookie_text:
            return self.cookie_text
        try:
            with open(self.cookie_file, 'r', encoding='utf-8') as f:
                return f.read().strip()
        except FileNotFoundError:
            raise Exception("未找到 cookie.txt，请运行 qr_login.py 获取 Cookie")

    def parse_cookie(self) -> Dict[str, str]:
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

    def validate_cookie(self) -> Tuple[bool, str]:
        """验证Cookie有效性"""
        try:
            cookies = self.parse_cookie()
            # 使用用户信息API验证Cookie
            return self._test_cookie_validity(cookies)
        except Exception as e:
            logging.error(f"Cookie验证失败：{str(e)}")
            return False, str(e)

    def _test_cookie_validity(self, cookies: Dict[str, str]) -> Tuple[bool, str]:
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
