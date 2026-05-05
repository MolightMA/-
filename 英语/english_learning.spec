# -*- mode: python ; coding: utf-8 -*-
# PyInstaller 配置：生成 Windows 下可双击运行的目录版程序（含 Qt 插件）。
from pathlib import Path

from PyInstaller.utils.hooks import collect_all

# 收集 PyQt6 的二进制与插件（多媒体播放必需）
datas, binaries, hiddenimports = collect_all("PyQt6")

block_cipher = None

ROOT = Path(SPECPATH).resolve()

a = Analysis(
    [str(ROOT / "main.py")],
    pathex=[str(ROOT)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports
    + [
        "PyQt6.QtMultimedia",
        "edge_tts",
        "pydub",
        "sqlite3",
        "uuid",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["matplotlib", "numpy"],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="英语学习",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="英语学习",
)
