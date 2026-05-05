# -*- coding: utf-8 -*-
"""学习进度统计图表面板：词库概览柱状图 + 环形进度。

数据从 Database 实时读取，支持手动刷新。
"""
from __future__ import annotations

import math
from datetime import datetime, timezone, timedelta
from typing import List, Optional

from PyQt6.QtCore import QPointF, QRectF, Qt, QTimer
from PyQt6.QtGui import (
    QBrush,
    QColor,
    QFont,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPen,
)
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

# ---------- 设计令牌（与 theme.py 保持一致）---------- #
C_BG_DEEP = QColor("#0f1419")
C_BG_PANEL = QColor("#161b22")
C_BG_ELEVATED = QColor("#1c232d")
C_BORDER = QColor("#30363d")
C_ACCENT = QColor("#2dd4bf")
C_ACCENT_DIM = QColor("#14b8a6")
C_TEXT_PRIMARY = QColor("#e6edf3")
C_TEXT_SECONDARY = QColor("#8b949e")
C_TEXT_MUTED = QColor("#6e7681")
C_RED = QColor("#ff7b72")
C_PURPLE = QColor("#d2a8ff")
C_YELLOW = QColor("#e3b341")


# ================================================================ #
#  迷你环形图（圆心显示数字）                                        #
# ================================================================ #
class _DonutWidget(QWidget):
    """单个环形指标。"""

    def __init__(
        self,
        label: str,
        color: QColor,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self._label = label
        self._color = color
        self._ratio = 0.0   # 0.0 ~ 1.0
        self._value = 0
        self._total = 0
        self.setMinimumSize(120, 120)
        self.setMaximumSize(140, 140)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

    def set_data(self, value: int, total: int) -> None:
        self._value = value
        self._total = total
        self._ratio = (value / total) if total > 0 else 0.0
        self.update()

    def paintEvent(self, _) -> None:  # type: ignore[override]
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        w, h = self.width(), self.height()
        side = min(w, h) - 8
        rect = QRectF((w - side) / 2, (h - side) / 2, side, side)
        thickness = side * 0.14

        # 背景轨道
        pen_bg = QPen(C_BG_ELEVATED, thickness)
        pen_bg.setCapStyle(Qt.PenCapStyle.RoundCap)
        p.setPen(pen_bg)
        p.drawArc(rect.adjusted(thickness / 2, thickness / 2, -thickness / 2, -thickness / 2),
                  0, 360 * 16)

        # 前景弧度
        if self._ratio > 0:
            pen_fg = QPen(self._color, thickness)
            pen_fg.setCapStyle(Qt.PenCapStyle.RoundCap)
            p.setPen(pen_fg)
            inner = rect.adjusted(thickness / 2, thickness / 2, -thickness / 2, -thickness / 2)
            span = int(self._ratio * 360 * 16)
            p.drawArc(inner, 90 * 16, -span)

        # 圆心数字
        p.setPen(QPen(C_TEXT_PRIMARY))
        f = QFont("Segoe UI", int(side * 0.18), QFont.Weight.Bold)
        p.setFont(f)
        p.drawText(rect, Qt.AlignmentFlag.AlignCenter, str(self._value))

        # 底部标签
        p.setPen(QPen(C_TEXT_SECONDARY))
        f2 = QFont("Microsoft YaHei UI", int(side * 0.10))
        p.setFont(f2)
        label_rect = QRectF(0, h - 18, w, 18)
        p.drawText(label_rect, Qt.AlignmentFlag.AlignCenter, self._label)
        p.end()


# ================================================================ #
#  柱状图（按周/按天新增词数）                                        #
# ================================================================ #
class _BarChartWidget(QWidget):
    """近 7 天每日新增词数柱状图。"""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._bars: List[tuple[str, int]] = []  # (label, count)
        self.setMinimumHeight(140)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

    def set_data(self, bars: List[tuple[str, int]]) -> None:
        self._bars = bars
        self.update()

    def paintEvent(self, _) -> None:  # type: ignore[override]
        if not self._bars:
            return
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        w, h = self.width(), self.height()
        pad_l, pad_r, pad_top, pad_bot = 36, 12, 16, 32
        chart_w = w - pad_l - pad_r
        chart_h = h - pad_top - pad_bot

        max_val = max(v for _, v in self._bars) or 1
        n = len(self._bars)
        bar_w = max(8, chart_w // n - 8)
        gap = (chart_w - bar_w * n) // (n + 1)

        # 网格线
        pen_grid = QPen(C_BORDER)
        pen_grid.setStyle(Qt.PenStyle.DotLine)
        p.setPen(pen_grid)
        for i in range(1, 4):
            y = pad_top + chart_h * i // 4
            p.drawLine(pad_l, y, w - pad_r, y)

        # Y 轴标签
        p.setPen(QPen(C_TEXT_MUTED))
        f_small = QFont("Segoe UI", 9)
        p.setFont(f_small)
        for i in range(0, 4):
            y = pad_top + chart_h * i // 4
            val = int(max_val * (4 - i) / 4)
            p.drawText(0, y - 6, pad_l - 4, 14, Qt.AlignmentFlag.AlignRight, str(val))

        # 柱子
        for i, (label, val) in enumerate(self._bars):
            x = pad_l + gap + i * (bar_w + gap)
            bar_h = int(chart_h * val / max_val) if max_val else 0

            # 渐变填充
            grad = QLinearGradient(x, pad_top + chart_h - bar_h, x, pad_top + chart_h)
            grad.setColorAt(0, C_ACCENT)
            grad.setColorAt(1, C_ACCENT_DIM)
            grad.setColorAt(1, QColor(45, 212, 191, 60))

            path = QPainterPath()
            rx = min(4, bar_w // 2)
            path.addRoundedRect(
                QRectF(x, pad_top + chart_h - bar_h, bar_w, bar_h), rx, rx
            )
            p.fillPath(path, QBrush(grad))

            # 数值标签（非零时显示）
            if val > 0:
                p.setPen(QPen(C_ACCENT))
                f_val = QFont("Segoe UI", 9, QFont.Weight.Bold)
                p.setFont(f_val)
                p.drawText(
                    int(x), pad_top + chart_h - bar_h - 16,
                    bar_w, 14,
                    Qt.AlignmentFlag.AlignCenter,
                    str(val),
                )

            # X 轴日期标签
            p.setPen(QPen(C_TEXT_MUTED))
            p.setFont(f_small)
            p.drawText(
                int(x) - 2, pad_top + chart_h + 6,
                bar_w + 4, 20,
                Qt.AlignmentFlag.AlignCenter,
                label,
            )

        p.end()


# ================================================================ #
#  完整统计面板                                                       #
# ================================================================ #
class StatsPanel(QFrame):
    """嵌入主界面的学习统计面板。"""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setObjectName("statsPanel")
        self._db = None  # 延迟注入

        # ---- 三个环形指标 ----
        self._donut_total = _DonutWidget("总词数", C_ACCENT)
        self._donut_audio = _DonutWidget("有音频", C_PURPLE)
        self._donut_synced = _DonutWidget("已同步", C_YELLOW)

        donut_row = QHBoxLayout()
        donut_row.setSpacing(16)
        donut_row.addStretch()
        for d in (self._donut_total, self._donut_audio, self._donut_synced):
            donut_row.addWidget(d)
        donut_row.addStretch()

        # ---- 柱状图 ----
        self._bar_title = QLabel("近 7 天新增")
        self._bar_title.setObjectName("listTitle")
        self._bar_chart = _BarChartWidget()

        # ---- 刷新按钮 ----
        self._btn_refresh = QPushButton("↻ 刷新统计")
        self._btn_refresh.setObjectName("ghostBtn")
        self._btn_refresh.setFixedWidth(100)
        self._btn_refresh.clicked.connect(self.refresh)

        # ---- 布局 ----
        vl = QVBoxLayout(self)
        vl.setContentsMargins(20, 16, 20, 16)
        vl.setSpacing(12)

        title_row = QHBoxLayout()
        title_lbl = QLabel("学习统计")
        title_lbl.setObjectName("listTitle")
        title_row.addWidget(title_lbl)
        title_row.addStretch()
        title_row.addWidget(self._btn_refresh)
        vl.addLayout(title_row)

        vl.addLayout(donut_row)
        vl.addWidget(self._bar_title)
        vl.addWidget(self._bar_chart, 1)

        # 应用样式
        self.setStyleSheet(f"""
            #statsPanel {{
                background-color: #161b22;
                border: 1px solid #30363d;
                border-radius: 14px;
            }}
        """)

    def set_db(self, db) -> None:
        self._db = db
        self.refresh()

    def refresh(self) -> None:
        if self._db is None:
            return
        words: List[dict] = self._db.list_words()
        total = len(words)
        has_audio = sum(1 for w in words if w.get("audio_path"))
        synced = sum(1 for w in words if w.get("synced"))

        self._donut_total.set_data(total, max(total, 1))
        self._donut_audio.set_data(has_audio, max(total, 1))
        self._donut_synced.set_data(synced, max(total, 1))

        # 近 7 天柱状图
        today = datetime.now(timezone.utc).date()
        day_counts: dict[str, int] = {}
        for i in range(6, -1, -1):
            d = today - timedelta(days=i)
            key = d.strftime("%m/%d")
            day_counts[key] = 0

        for w in words:
            raw = w.get("created_at", "")
            try:
                dt = datetime.fromisoformat(raw).date()
            except (ValueError, TypeError):
                continue
            key = dt.strftime("%m/%d")
            if key in day_counts:
                day_counts[key] += 1

        self._bar_chart.set_data(list(day_counts.items()))
