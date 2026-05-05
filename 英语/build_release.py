# -*- coding: utf-8 -*-
"""在本目录执行 PyInstaller，避免命令行中文路径编码问题。"""
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)
subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", "pyinstaller>=6.0"])
subprocess.check_call(
    [sys.executable, "-m", "PyInstaller", "--noconfirm", "--clean", "english_learning.spec"]
)
print("构建完成，输出: ", os.path.join(ROOT, "dist"))
