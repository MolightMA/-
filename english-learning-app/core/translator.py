"""
自动翻译模块
"""
import requests
import re
from typing import Optional


class Translator:
    """翻译引擎"""
    
    def __init__(self):
        self.timeout = 10
    
    def is_english(self, text: str) -> bool:
        """判断是否为英文"""
        return bool(re.match(r'^[a-zA-Z\s\-\'\.,!?]+$', text.strip()))
    
    def translate(self, text: str, target_lang: str = "zh") -> Optional[str]:
        """翻译文本"""
        if not text.strip():
            return None
        
        if target_lang == "zh":
            return self._translate_en_to_zh(text)
        else:
            return self._translate_zh_to_en(text)
    
    def _translate_en_to_zh(self, text: str) -> Optional[str]:
        """英译中"""
        result = self._google_translate(text, "en", "zh-CN")
        if result:
            return result
        
        result = self._youdao_translate(text, "EN2ZH_CN")
        if result:
            return result
        
        return None
    
    def _translate_zh_to_en(self, text: str) -> Optional[str]:
        """中译英"""
        result = self._google_translate(text, "zh-CN", "en")
        if result:
            return result
        
        result = self._youdao_translate(text, "ZH_CN2EN")
        if result:
            return result
        
        return None
    
    def _google_translate(self, text: str, source_lang: str, target_lang: str) -> Optional[str]:
        """Google翻译"""
        try:
            url = "https://translate.googleapis.com/translate_a/single"
            params = {
                "client": "gtx",
                "sl": source_lang,
                "tl": target_lang,
                "dt": "t",
                "q": text
            }
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            response = requests.get(url, params=params, headers=headers, timeout=self.timeout)
            if response.status_code == 200:
                data = response.json()
                if data and data[0]:
                    return ''.join([item[0] for item in data[0] if item[0]])
            return None
        except Exception as e:
            print(f"Google翻译失败: {e}")
            return None
    
    def _youdao_translate(self, text: str, lang: str) -> Optional[str]:
        """有道翻译"""
        try:
            import hashlib
            import time
            
            appid = "20250605002235453"
            secret = "abc123def456"
            
            salt = str(int(time.time() * 1000))
            sign_str = appid + text + salt + secret
            sign = hashlib.md5(sign_str.encode()).hexdigest()
            
            url = "https://fanyi-api.baidu.com/api/trans/vip/translate"
            data = {
                "q": text,
                "appid": appid,
                "salt": salt,
                "from": "auto",
                "to": "zh" if lang == "EN2ZH_CN" else "en",
                "sign": sign
            }
            
            response = requests.post(url, data=data, timeout=self.timeout)
            if response.status_code == 200:
                result = response.json()
                if "trans_result" in result and result["trans_result"]:
                    return result["trans_result"][0]["dst"]
            return None
        except Exception as e:
            print(f"有道翻译失败: {e}")
            return None


# 全局翻译器
translator = Translator()
