# -*- coding: utf-8 -*-
"""应用配置：路径、TTS 音色、云端同步（可选）。"""
import sys
from pathlib import Path


def _resolve_root() -> Path:
    """开发模式为源码目录；PyInstaller 打包后为 exe 所在目录（数据持久化）。"""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


# 项目根目录
ROOT_DIR = _resolve_root()
DATA_DIR = ROOT_DIR / "data"
DB_PATH = DATA_DIR / "words.db"
CACHE_DIR = DATA_DIR / "cache"

# Edge TTS 音色（中等语速由 rate 控制）
VOICE_EN = "en-US-JennyNeural"
VOICE_ZH = "zh-CN-XiaoxiaoNeural"
# 相对默认语速的百分比，略慢利于学习
TTS_RATE = "-5%"

# 合并音频时片段间隔（毫秒）
AUDIO_GAP_MS = 300

# 腾讯云开发 / 自定义同步端点（未配置时仅使用本地库）
CLOUDBASE_ENABLED = False
# 若启用：填写云函数或自建 HTTPS 接口，用于上传/拉取单词 JSON
CLOUDBASE_SYNC_URL = ""
CLOUDBASE_API_KEY = ""
