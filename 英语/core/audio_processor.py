# -*- coding: utf-8 -*-
"""
合并多段 MP3：优先 lazy 加载 pydub；失败时用 FFmpeg 直接拼接（不依赖 audioop）。
Python 3.13+ 已移除标准库 audioop，pydub 需配合 audioop-lts，否则在 import 阶段即失败。
"""
from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import List, Optional


def ffmpeg_available() -> bool:
    """是否能在 PATH 中找到 ffmpeg（不导入 pydub，避免 Python 3.13+ audioop 问题）。"""
    return bool(shutil.which("ffmpeg"))


def _merge_ffmpeg_concat(paths: List[Path], output_path: Path) -> bool:
    """用 FFmpeg concat 协议合并（无间隙；不依赖 pydub）。"""
    if not paths:
        return False
    if not shutil.which("ffmpeg"):
        return False
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if len(paths) == 1:
        try:
            shutil.copy2(paths[0], output_path)
            return output_path.is_file()
        except OSError:
            return False

    # concat 列表：路径中的单引号需转义
    lines: List[str] = []
    for p in paths:
        # FFmpeg concat：使用正斜杠路径，避免 Windows 反斜杠转义问题
        ap = p.resolve().as_posix()
        s = ap.replace("'", r"'\''")
        lines.append(f"file '{s}'")
    list_text = "\n".join(lines) + "\n"

    list_path: Optional[str] = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            suffix=".ffconcat.txt",
            delete=False,
            encoding="utf-8",
            newline="\n",
        ) as f:
            f.write(list_text)
            list_path = f.name

        win = os.name == "nt"
        cmd = [
            "ffmpeg",
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            list_path,
            "-c",
            "copy",
            str(output_path),
        ]
        r = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120,
            creationflags=subprocess.CREATE_NO_WINDOW if win else 0,
        )
        if r.returncode == 0 and output_path.is_file():
            return True
        # 不同参数 MP3 直拷失败时回退为重编码
        cmd2 = [
            "ffmpeg",
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            list_path,
            "-c:a",
            "libmp3lame",
            "-q:a",
            "2",
            str(output_path),
        ]
        r2 = subprocess.run(
            cmd2,
            capture_output=True,
            text=True,
            timeout=120,
            creationflags=subprocess.CREATE_NO_WINDOW if win else 0,
        )
        return r2.returncode == 0 and output_path.is_file()
    except Exception:
        return False
    finally:
        if list_path:
            try:
                os.unlink(list_path)
            except OSError:
                pass


def merge_mp3_files(paths: List[Path], output_path: Path, gap_ms: int) -> bool:
    """
    将多个 MP3 合并；片段间可插静音（pydub 路径）。
    无 pydub 或 audioop 时，若存在 FFmpeg 则用纯命令行合并（无间隙，仍为一整段可播文件）。
    """
    if not paths:
        return False
    if not ffmpeg_available():
        return False

    # 1) 尝试 lazy 加载 pydub（需安装 audioop-lts 于 Python 3.13+）
    try:
        from pydub import AudioSegment  # noqa: WPS433 延迟导入

        output_path.parent.mkdir(parents=True, exist_ok=True)
        combined: Optional[AudioSegment] = None
        gap = AudioSegment.silent(duration=gap_ms)
        for p in paths:
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
        pass

    # 2) 回退：FFmpeg 直连（避免 pydub/audioop）
    return _merge_ffmpeg_concat(paths, output_path)

