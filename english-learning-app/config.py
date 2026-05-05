"""
配置模块
"""
import os
from pathlib import Path

# 项目根目录
BASE_DIR = Path(__file__).resolve().parent

# 数据目录
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

# 数据库路径
DB_PATH = DATA_DIR / "words.db"

# 音频缓存目录
CACHE_DIR = DATA_DIR / "cache"
CACHE_DIR.mkdir(exist_ok=True)

# 日志目录
LOG_DIR = DATA_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)

# 腾讯云配置
TENCENT_CLOUD_CONFIG = {
    "env_id": "your-env-id",
    "secret_id": "your-secret-id",
    "secret_key": "your-secret-key",
}

# TTS 配置 - 多种声音
TTS_VOICES = {
    "微软小娜(女声)": {"zh": "zh-CN-XiaoxiaoNeural", "en": "en-US-JennyNeural"},
    "微软云希(男声)": {"zh": "zh-CN-YunxiNeural", "en": "en-US-GuyNeural"},
    "微软晓睿(女声)": {"zh": "zh-CN-XiaoruiNeural", "en": "en-US-SaraNeural"},
    "英式英语(女声)": {"zh": "zh-CN-XiaoxiaoNeural", "en": "en-GB-SoniaNeural"},
    "美式英语(男声)": {"zh": "zh-CN-XiaoxiaoNeural", "en": "en-US-GuyNeural"},
}

TTS_CONFIG = {
    "rate": "+0%",
    "volume": "+0%",
    "pitch": "+0Hz",
    "default_voice": "微软小娜(女声)",
}

# 播放配置
PLAYER_CONFIG = {
    "mode": "random",
    "gap_seconds": 0.5,
    "speed": 1.0,
}

# 翻译API配置
TRANSLATOR_CONFIG = {
    "primary": "google",
    "timeout": 10,
}
