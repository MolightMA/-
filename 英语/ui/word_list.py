# -*- coding: utf-8 -*-
"""左侧词库：搜索过滤、列表高亮当前播放项。"""
from __future__ import annotations

from typing import List, Optional

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QVBoxLayout,
    QWidget,
)


class WordListPanel(QFrame):
    """单词列表面板（带搜索）。"""

    word_selected = pyqtSignal(str)  # word_id

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setObjectName("listCard")
        self._all_words: List[dict] = []

        self._search = QLineEdit()
        self._search.setPlaceholderText("搜索英文或中文…")
        self._search.setClearButtonEnabled(True)
        self._search.textChanged.connect(self._on_search)

        self._list = QListWidget()
        self._list.itemClicked.connect(self._on_item_clicked)

        title = QLabel("词库")
        title.setObjectName("listTitle")

        self._count = QLabel("0 词")
        self._count.setObjectName("statBadge")

        head = QFrame()
        hl = QVBoxLayout(head)
        hl.setContentsMargins(0, 0, 0, 0)
        row = QFrame()
        r = QHBoxLayout(row)
        r.setContentsMargins(0, 0, 0, 0)
        r.addWidget(title)
        r.addStretch()
        r.addWidget(self._count)
        hl.addWidget(row)
        hl.addWidget(self._search)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        layout.addWidget(head)
        layout.addWidget(self._list, 1)

    def _on_item_clicked(self, item: QListWidgetItem) -> None:
        wid = item.data(Qt.ItemDataRole.UserRole)
        if wid:
            self.word_selected.emit(str(wid))

    def _on_search(self, _: str) -> None:
        self._refill_list()

    def _refill_list(self) -> None:
        q = self._search.text().strip().lower()
        self._list.clear()
        n = 0
        for w in self._all_words:
            en = w.get("english", "").lower()
            zh = w.get("chinese", "").lower()
            if q and q not in en and q not in zh:
                continue
            text = f'{w["english"]}  —  {w["chinese"]}'
            it = QListWidgetItem(text)
            it.setData(Qt.ItemDataRole.UserRole, w["id"])
            self._list.addItem(it)
            n += 1
        total = len(self._all_words)
        if q:
            self._count.setText(f"显示 {n} / {total} 词")
        else:
            self._count.setText(f"{total} 词")

    def set_words(self, words: List[dict]) -> None:
        self._all_words = list(words)
        self._refill_list()

    def highlight_word(self, word_id: str) -> None:
        for i in range(self._list.count()):
            it = self._list.item(i)
            if it and it.data(Qt.ItemDataRole.UserRole) == word_id:
                self._list.setCurrentItem(it)
                self._list.scrollToItem(it)
                break
