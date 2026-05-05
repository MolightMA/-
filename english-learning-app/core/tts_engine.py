"""
TTS 引擎 - Edge TTS 微软配音
"""
import asyncio
import edge_tts
from pathlib import Path
from typing import Optional, Dict
from config import TTS_VOICES, TTS_CONFIG, CACHE_DIR


class TTSEngine:
    """Edge TTS 引擎"""
    
    def __init__(self):
        self.voices = TTS_VOICES
        self.rate = TTS_CONFIG["rate"]
        self.volume = TTS_CONFIG["volume"]
        self.pitch = TTS_CONFIG["pitch"]
        self.default_voice = TTS_CONFIG["default_voice"]
    
    def get_available_voices(self) -> list:
        """获取可用声音列表"""
        return list(self.voices.keys())
    
    def get_voice_config(self, voice_name: str) -> Dict:
        """获取声音配置"""
        return self.voices.get(voice_name, self.voices[self.default_voice])
    
    async def _generate_audio(self, text: str, voice: str, output_path: Path, rate: str = None) -> bool:
        """生成单个音频文件"""
        try:
            communicate = edge_tts.Communicate(
                text,
                voice,
                rate=rate or self.rate,
                volume=self.volume,
                pitch=self.pitch
            )
            await communicate.save(str(output_path))
            return True
        except Exception as e:
            print(f"TTS生成失败 ({voice}): {e}")
            return False
    
    async def generate_word_audio(
        self, 
        english: str, 
        chinese: str, 
        word_id: str, 
        voice_name: str = None
    ) -> Optional[Dict]:
        """为单词生成音频：[英文] - [中文] - [英文]"""
        voice_name = voice_name or self.default_voice
        voice_config = self.get_voice_config(voice_name)
        
        audio_dir = CACHE_DIR / word_id
        audio_dir.mkdir(exist_ok=True)
        
        en1_path = audio_dir / "en1.mp3"
        cn_path = audio_dir / "cn.mp3"
        en2_path = audio_dir / "en2.mp3"
        
        tasks = [
            self._generate_audio(english, voice_config["en"], en1_path),
            self._generate_audio(chinese, voice_config["zh"], cn_path),
            self._generate_audio(english, voice_config["en"], en2_path),
        ]
        results = await asyncio.gather(*tasks)
        
        if all(results):
            return {
                "en1": str(en1_path),
                "cn": str(cn_path),
                "en2": str(en2_path),
                "combined": str(audio_dir / "combined.mp3")
            }
        return None
    
    def generate_word_audio_sync(
        self, 
        english: str, 
        chinese: str, 
        word_id: str, 
        voice_name: str = None
    ) -> Optional[Dict]:
        """同步版本"""
        try:
            return asyncio.run(self.generate_word_audio(english, chinese, word_id, voice_name))
        except Exception as e:
            print(f"生成音频失败: {e}")
            return None
    
    def delete_audio_cache(self, word_id: str) -> bool:
        """删除音频缓存"""
        audio_dir = CACHE_DIR / word_id
        if audio_dir.exists():
            import shutil
            shutil.rmtree(audio_dir)
            return True
        return False
    
    def clear_all_cache(self) -> bool:
        """清空所有音频缓存"""
        if CACHE_DIR.exists():
            import shutil
            shutil.rmtree(CACHE_DIR)
            CACHE_DIR.mkdir(exist_ok=True)
            return True
        return False


# 全局TTS引擎实例
tts_engine = TTSEngine()
