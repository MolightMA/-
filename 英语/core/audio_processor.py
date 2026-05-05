# -*- coding: utf-8 -*-
"""使用 pydub 合并音频片段；若系统无 FFmpeg 则返回 None 由上层改用分段播放。"""
from __future__ import annotations

import shutil
from pathlib import Path
from typing import List, Optional

from pydub import AudioSegment

try:
    from pydub.utils import which as pydub_which
except Exception:  # pragma: no cover
    pydub_which = None


def ffmpeg_available() -> bool:
    return bool(shutil.which("ffmpeg")) or bool(pydub_which and pydub_which("ffmpeg"))


def merge_mp3_files(paths: List[Path], output_path: Path, gap_ms: int) -> bool:
    """
    将多个 MP3 合并为一个文件，片段之间插入静音。
    需要 FFmpeg；失败时返回 False。
    """
    if not paths:
        return False
    if not ffmpeg_available():
        return False
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        combined: Optional[AudioSegment] = None
        gap = AudioSegment.silent(duration=gap_ms)
        for i, p in enumerate(paths):
            seg = AudioSegment.from_file(str(p), format="mp3")
            if combined is None:
                combined = seg
            else:
                combined += gap + seg
        if combined is None:
            return False
        combined.export(str(output_path), format="mp3")
        return output_path.is_file()
    except Exception:
        return False
