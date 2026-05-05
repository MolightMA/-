# -*- coding: utf-8 -*-
"""Edge TTS：英文 → 中文 → 英文，生成缓存文件。"""
from __future__ import annotations

import asyncio
from pathlib import Path
from typing import List, Optional, Tuple

import edge_tts

from config import AUDIO_GAP_MS, CACHE_DIR, TTS_RATE, VOICE_EN, VOICE_ZH


async def _save_tts(text: str, voice: str, out_path: Path) -> None:
    communicate = edge_tts.Communicate(text, voice=voice, rate=TTS_RATE)
    await communicate.save(str(out_path))


def generate_word_audio(english: str, chinese: str, word_id: str) -> Tuple[Optional[str], Optional[List[str]]]:
    """
    生成 [英文] - [中文] - [英文] 结构音频。
    若已安装 FFmpeg，合并为单个 MP3；否则返回三段路径供播放器顺序播放。
    返回 (合并文件路径或首段路径, 分段路径列表或 None)。
    """
    from core.audio_processor import merge_mp3_files

    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    base = CACHE_DIR / word_id
    p_en1 = Path(str(base) + "_en1.mp3")
    p_zh = Path(str(base) + "_zh.mp3")
    p_en2 = Path(str(base) + "_en2.mp3")

    async def _run() -> None:
        await _save_tts(english, VOICE_EN, p_en1)
        await _save_tts(chinese, VOICE_ZH, p_zh)
        await _save_tts(english, VOICE_EN, p_en2)

    asyncio.run(_run())
    parts = [p_en1, p_zh, p_en2]
    merged = CACHE_DIR / f"{word_id}_merged.mp3"
    if merge_mp3_files(parts, merged, AUDIO_GAP_MS):
        # 合并成功后可删除分段以节省空间（保留逻辑简单则暂不删，便于无 FFmpeg 环境调试）
        return str(merged), None
    part_strs = [str(p) for p in parts]
    return part_strs[0], part_strs
