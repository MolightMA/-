# -*- coding: utf-8 -*-
"""应用入口。"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QApplication

from ui.main_window import MainWindow

_ICON_PATH = ROOT / "icon.png"
_ICO_PATH = ROOT / "icon.ico"


def main() -> None:
    # 确保数据目录存在
    from config import CACHE_DIR, DATA_DIR

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    CACHE_DIR.mkdir(parents=True, exist_ok=True)

    app = QApplication(sys.argv)

    # 设置应用级图标（任务栏 / Alt+Tab）
    icon_file = _ICO_PATH if _ICO_PATH.is_file() else _ICON_PATH
    if icon_file.is_file():
        app.setWindowIcon(QIcon(str(icon_file)))

    win = MainWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

