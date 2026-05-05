# -*- coding: utf-8 -*-
"""全局界面主题：深色基底 + 薄荷强调色，统一圆角与间距。"""

# 设计令牌（便于后续微调）
ACCENT = "#2dd4bf"  # 薄荷青
ACCENT_DIM = "#14b8a6"
BG_DEEP = "#0f1419"
BG_PANEL = "#161b22"
BG_ELEVATED = "#1c232d"
BORDER = "#30363d"
TEXT_PRIMARY = "#e6edf3"
TEXT_SECONDARY = "#8b949e"
TEXT_MUTED = "#6e7681"

APP_STYLESHEET = f"""
/* 全局 */
QMainWindow, QWidget {{
    background-color: {BG_DEEP};
    color: {TEXT_PRIMARY};
    font-family: "Segoe UI", "Microsoft YaHei UI", sans-serif;
    font-size: 13px;
}}

/* 顶部标题区 */
#headerBar {{
    background-color: {BG_PANEL};
    border-bottom: 1px solid {BORDER};
    border-radius: 0px;
}}
#appTitle {{
    color: {TEXT_PRIMARY};
    font-size: 22px;
    font-weight: 700;
    letter-spacing: 0.5px;
}}
#appSubtitle {{
    color: {TEXT_MUTED};
    font-size: 12px;
}}

/* 输入卡片 */
#inputCard {{
    background-color: {BG_PANEL};
    border: 1px solid {BORDER};
    border-radius: 12px;
}}
QLineEdit {{
    background-color: {BG_ELEVATED};
    border: 1px solid {BORDER};
    border-radius: 8px;
    padding: 10px 14px;
    selection-background-color: {ACCENT_DIM};
}}
QLineEdit:focus {{
    border: 1px solid {ACCENT};
}}

/* 主按钮 */
QPushButton#primaryBtn {{
    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #2dd4bf, stop:1 #14b8a6);
    color: #0f1419;
    font-weight: 600;
    border: none;
    border-radius: 8px;
    padding: 10px 18px;
    min-height: 20px;
}}
QPushButton#primaryBtn:hover {{
    background-color: #5eead4;
}}
QPushButton#primaryBtn:pressed {{
    background-color: {ACCENT_DIM};
}}

/* 次要按钮 */
QPushButton#ghostBtn {{
    background-color: transparent;
    border: 1px solid {BORDER};
    border-radius: 8px;
    padding: 8px 14px;
    color: {TEXT_SECONDARY};
}}
QPushButton#ghostBtn:hover {{
    background-color: {BG_ELEVATED};
    color: {TEXT_PRIMARY};
    border-color: #484f58;
}}

/* 危险操作 */
QPushButton#dangerBtn {{
    background-color: rgba(248, 81, 73, 0.12);
    border: 1px solid rgba(248, 81, 73, 0.4);
    color: #ff7b72;
    border-radius: 8px;
    padding: 8px 14px;
}}
QPushButton#dangerBtn:hover {{
    background-color: rgba(248, 81, 73, 0.22);
}}

/* 列表卡片 */
#listCard {{
    background-color: {BG_PANEL};
    border: 1px solid {BORDER};
    border-radius: 14px;
}}
#listTitle {{
    color: {TEXT_SECONDARY};
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 1.2px;
    text-transform: uppercase;
}}
QListWidget {{
    background-color: {BG_ELEVATED};
    border: none;
    border-radius: 10px;
    padding: 6px;
    outline: none;
}}
QListWidget::item {{
    border-radius: 8px;
    padding: 12px 14px;
    margin: 2px 0px;
    color: {TEXT_PRIMARY};
}}
QListWidget::item:hover {{
    background-color: rgba(45, 212, 191, 0.08);
}}
QListWidget::item:selected {{
    background-color: rgba(45, 212, 191, 0.18);
    border-left: 3px solid {ACCENT};
}}

/* 播放区卡片 */
#playerCard {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #161b22, stop:1 #121820);
    border: 1px solid {BORDER};
    border-radius: 16px;
}}
#playerGlow {{
    background-color: rgba(45, 212, 191, 0.06);
    border: 1px solid rgba(45, 212, 191, 0.15);
    border-radius: 14px;
}}
#labelEnglish {{
    color: {TEXT_PRIMARY};
    font-size: 28px;
    font-weight: 700;
    letter-spacing: 0.3px;
}}
#labelChinese {{
    color: {ACCENT};
    font-size: 17px;
    font-weight: 500;
    margin-top: 4px;
}}
#labelHint {{
    color: {TEXT_MUTED};
    font-size: 12px;
}}

/* 播放控制大按钮 */
QPushButton#ctrlBtn {{
    background-color: {BG_ELEVATED};
    border: 1px solid {BORDER};
    border-radius: 10px;
    min-width: 48px;
    min-height: 48px;
    font-size: 15px;
}}
QPushButton#ctrlBtn:hover {{
    border-color: {ACCENT};
    background-color: rgba(45, 212, 191, 0.1);
}}
QPushButton#playMainBtn {{
    background-color: rgba(45, 212, 191, 0.2);
    border: 2px solid {ACCENT};
    border-radius: 14px;
    min-width: 56px;
    min-height: 56px;
    font-size: 18px;
}}
QPushButton#playMainBtn:hover {{
    background-color: rgba(45, 212, 191, 0.35);
}}

QComboBox {{
    background-color: {BG_ELEVATED};
    border: 1px solid {BORDER};
    border-radius: 8px;
    padding: 8px 12px;
    min-width: 120px;
}}
QComboBox:hover {{
    border-color: #484f58;
}}
QComboBox::drop-down {{
    border: none;
    width: 24px;
}}

QSplitter::handle {{
    background-color: {BORDER};
    width: 1px;
}}

QMenuBar {{
    background-color: {BG_PANEL};
    border-bottom: 1px solid {BORDER};
    padding: 4px 12px;
}}
QMenuBar::item:selected {{
    background-color: {BG_ELEVATED};
}}

QStatusBar {{
    background-color: {BG_PANEL};
    border-top: 1px solid {BORDER};
    color: {TEXT_SECONDARY};
    padding: 4px 12px;
}}

QLabel#statBadge {{
    color: {ACCENT};
    font-size: 11px;
    font-weight: 600;
}}
"""
