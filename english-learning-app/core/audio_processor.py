"""
音频处理模块 - pydub 合并音频
"""
from pydub import AudioSegment
import threading
from pathlib import Path
from typing import List, Optional
from config import PLAYER_CONFIG


class AudioProcessor:
    """音频处理器"""
    
    def __init__(self):
        self.gap_seconds = PLAYER_CONFIG["gap_seconds"]
        self.speed = PLAYER_CONFIG["speed"]
        self.is_playing = False
        self.current_audio = None
        self.play_thread = None
    
    def combine_word_audio(
        self, 
        en1_path: str, 
        cn_path: str, 
        en2_path: str, 
        output_path: str,
        speed: float = 1.0
    ) -> bool:
        """合并单词音频片段"""
        try:
            from pydub import AudioSegment
            
            gap = AudioSegment.silent(duration=int(self.gap_seconds * 1000))
            
            en1 = AudioSegment.from_mp3(en1_path)
            cn = AudioSegment.from_mp3(cn_path)
            en2 = AudioSegment.from_mp3(en2_path)
            
            if speed != 1.0:
                en1 = en1.speedup(playback_speed=speed)
                cn = cn.speedup(playback_speed=speed)
                en2 = en2.speedup(playback_speed=speed)
            
            combined = en1 + gap + cn + gap + en2
            combined.export(output_path, format="mp3")
            return True
        except Exception as e:
            print(f"音频合并失败: {e}")
            return False
    
    def play_audio(self, audio_path: str, on_finished=None):
        """播放音频"""
        def _play():
            try:
                from pydub import AudioSegment
                from pydub.playback import play
                
                self.is_playing = True
                audio = AudioSegment.from_mp3(audio_path)
                play(audio)
                self.is_playing = False
                if on_finished:
                    on_finished()
            except Exception as e:
                print(f"播放失败: {e}")
                self.is_playing = False
        
        if self.play_thread and self.play_thread.is_alive():
            self.stop()
        
        self.play_thread = threading.Thread(target=_play, daemon=True)
        self.play_thread.start()
    
    def stop(self):
        """停止播放"""
        self.is_playing = False
    
    def set_speed(self, speed: float):
        """设置播放速度"""
        self.speed = speed


# 全局音频处理器
audio_processor = AudioProcessor()
