# -*- coding: utf-8 -*-
"""Edge TTS：英文 → 中文 → 英文，生成缓存文件。"""
from __future__ import annotations

import asyncio
import threading
from pathlib import Path
from typing import List, Optional, Tuple

import edge_tts

from config import AUDIO_GAP_MS, CACHE_DIR, TTS_RATE, VOICE_EN, VOICE_ZH, load_settings

# 全局串行：避免多线程同时 asyncio.run 与 Edge 请求冲突
_tts_lock = threading.Lock()


async def _save_tts(text: str, voice: str, out_path: Path) -> None:
    communicate = edge_tts.Communicate(text, voice=voice, rate=TTS_RATE)
    await communicate.save(str(out_path))


def generate_word_audio(
    english: str,
    chinese: str,
    word_id: str,
    voice_en: Optional[str] = None,
    voice_zh: Optional[str] = None,
) -> Tuple[Optional[str], Optional[List[str]]]:
    """
    生成 [英文] - [中文] - [英文] 结构音频。
    若已安装 FFmpeg，合并为单个 MP3；否则返回三段路径供播放器顺序播放。
    返回 (合并文件路径或首段路径, 分段路径列表或 None)。
    在工作线程中调用时使用独立事件循环，避免与主线程 asyncio 冲突。
    """
    st = load_settings()
    ve = voice_en or st.get("voice_en") or VOICE_EN
    vz = voice_zh or st.get("voice_zh") or VOICE_ZH

    with _tts_lock:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        base = CACHE_DIR / word_id
        p_en1 = Path(str(base) + "_en1.mp3")
        p_zh = Path(str(base) + "_zh.mp3")
        p_en2 = Path(str(base) + "_en2.mp3")

        async def _run() -> None:
            await _save_tts(english, ve, p_en1)
            await _save_tts(chinese, vz, p_zh)
            await _save_tts(english, ve, p_en2)

        # 非主线程内不能使用 asyncio.run() 与已有策略混用；显式新建循环更稳
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(_run())
        finally:
            loop.close()

        parts = [p_en1, p_zh, p_en2]
        merged = CACHE_DIR / f"{word_id}_merged.mp3"
        # 合并逻辑放在生成三段音频之后，避免 pydub/audioop 导入失败导致整段不生成
        from core.audio_processor import merge_mp3_files

        if merge_mp3_files(parts, merged, AUDIO_GAP_MS):
            return str(merged), None
        part_strs = [str(p) for p in parts]
        return part_strs[0], part_strs
