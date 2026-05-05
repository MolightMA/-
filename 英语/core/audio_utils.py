# -*- coding: utf-8 -*-
"""判断词条是否已有可用本地音频文件。"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict


def word_needs_audio(word: Dict[str, Any]) -> bool:
    """缺少路径、文件不存在或分段不完整时返回 True。"""
    segs = word.get("audio_segments")
    if segs and isinstance(segs, list) and len(segs) > 0:
        if all(Path(s).is_file() for s in segs if s):
            return False
    ap = word.get("audio_path")
    if ap and str(ap).strip() and Path(ap).is_file():
        return False
    return True
