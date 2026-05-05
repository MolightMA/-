# -*- coding: utf-8 -*-
"""Edge TTS 免费神经语音列表（与微软 Edge 朗读引擎一致，非豆包/有道官方接口）。"""
from __future__ import annotations

from typing import List, Tuple

# (界面显示名称, Edge 语音 ID)
EDGE_VOICES_EN: List[Tuple[str, str]] = [
    ("美式 · Jenny 女声", "en-US-JennyNeural"),
    ("美式 · Guy 男声", "en-US-GuyNeural"),
    ("美式 · Aria 女声", "en-US-AriaNeural"),
    ("美式 · Davis 男声", "en-US-DavisNeural"),
    ("英式 · Sonia 女声", "en-GB-SoniaNeural"),
    ("英式 · Ryan 男声", "en-GB-RyanNeural"),
    ("澳式 · Natasha 女声", "en-AU-NatashaNeural"),
    ("澳式 · William 男声", "en-AU-WilliamNeural"),
]

EDGE_VOICES_ZH: List[Tuple[str, str]] = [
    ("中文 · 晓晓 女声（默认）", "zh-CN-XiaoxiaoNeural"),
    ("中文 · 云希 男声", "zh-CN-YunxiNeural"),
    ("中文 · 云健 男声", "zh-CN-YunjianNeural"),
    ("中文 · 晓伊 女声", "zh-CN-XiaoyiNeural"),
    ("台湾 · 晓臻 女声", "zh-TW-HsiaoChenNeural"),
    ("香港 · 晓曼 女声", "zh-HK-HiuMaanNeural"),
]
