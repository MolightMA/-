# -*- coding: utf-8 -*-
"""播放控制：四种模式、一词结束后自动连播下一词（重复模式仅重复当前词）。"""
from __future__ import annotations

import random
from enum import IntEnum
from pathlib import Path
from typing import List, Optional

from PyQt6.QtCore import QUrl, Qt, pyqtSignal
from PyQt6.QtGui import QFont
from PyQt6.QtMultimedia import QAudioOutput, QMediaPlayer
from PyQt6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class PlayMode(IntEnum):
    SEQUENTIAL = 0  # 顺序，末尾接回第一项
    REVERSE = 1  # 倒序，索引递减循环
    RANDOM = 2  # 随机下一词
    REPEAT_ONE = 3  # 仅重复当前词，不自动切词


class PlayerPanel(QFrame):
    """右侧播放区。"""

    current_word_changed = pyqtSignal(str)  # word_id

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setObjectName("playerCard")
        self._words: List[dict] = []
        self._order: List[str] = []
        self._index = 0
        self._mode = PlayMode.SEQUENTIAL
        self._segment_queue: List[str] = []
        self._segment_idx = 0

        self._player = QMediaPlayer(self)
        self._audio_out = QAudioOutput(self)
        self._player.setAudioOutput(self._audio_out)
        self._player.mediaStatusChanged.connect(self._on_media_status)

        glow = QFrame()
        glow.setObjectName("playerGlow")
        glow_l = QVBoxLayout(glow)
        glow_l.setContentsMargins(24, 28, 24, 28)

        self._en_label = QLabel("English")
        self._en_label.setObjectName("labelEnglish")
        self._en_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._en_label.setFont(QFont(self._en_label.font().family(), 22, QFont.Weight.Bold))

        self._zh_label = QLabel("选择左侧单词开始学习")
        self._zh_label.setObjectName("labelChinese")
        self._zh_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._zh_label.setWordWrap(True)

        self._hint = QLabel("词条朗读结束后将按模式自动播放下一词（重复模式除外）")
        self._hint.setObjectName("labelHint")
        self._hint.setAlignment(Qt.AlignmentFlag.AlignCenter)

        glow_l.addWidget(self._en_label)
        glow_l.addWidget(self._zh_label)
        glow_l.addWidget(self._hint)

        self._btn_prev = QPushButton("◀  上一首")
        self._btn_play = QPushButton("▶  播放")
        self._btn_pause = QPushButton("⏸  暂停")
        self._btn_next = QPushButton("下一首  ▶")
        for b in (self._btn_prev, self._btn_pause, self._btn_next):
            b.setObjectName("ctrlBtn")
        self._btn_play.setObjectName("playMainBtn")

        self._btn_play.clicked.connect(self.play)
        self._btn_pause.clicked.connect(self.pause)
        self._btn_prev.clicked.connect(self.prev_track)
        self._btn_next.clicked.connect(self.next_track)

        mode_row = QFrame()
        mr = QHBoxLayout(mode_row)
        mr.setContentsMargins(0, 0, 0, 0)
        ml = QLabel("播放模式")
        ml.setObjectName("labelHint")
        self._mode_combo = QComboBox()
        self._mode_combo.addItems(
            [
                "顺序播放（连播）",
                "倒序播放（连播）",
                "随机播放（连播）",
                "重复播放（单曲循环）",
            ]
        )
        self._mode_combo.currentIndexChanged.connect(self._on_mode_changed)

        mr.addWidget(ml)
        mr.addWidget(self._mode_combo, 1)

        ctrl = QHBoxLayout()
        ctrl.addStretch()
        for b in (self._btn_prev, self._btn_play, self._btn_pause, self._btn_next):
            ctrl.addWidget(b)
        ctrl.addStretch()

        outer = QVBoxLayout(self)
        outer.setContentsMargins(20, 20, 20, 20)
        outer.setSpacing(20)
        outer.addWidget(glow, 1)
        outer.addLayout(ctrl)
        outer.addWidget(mode_row)

    def _on_mode_changed(self, idx: int) -> None:
        cur_id = self._order[self._index] if self._order and self._index < len(self._order) else None
        old_mode = self._mode
        self._mode = PlayMode(idx)

        if self._mode == PlayMode.RANDOM:
            random.shuffle(self._order)
            if cur_id and cur_id in self._order:
                self._index = self._order.index(cur_id)
            return

        # 从随机切回其他模式：恢复与词库列表一致的顺序
        if old_mode == PlayMode.RANDOM:
            self._order = [w["id"] for w in self._words]
            if cur_id and cur_id in self._order:
                self._index = self._order.index(cur_id)
            else:
                self._index = min(self._index, len(self._order) - 1) if self._order else 0

    def set_words(self, words: List[dict]) -> None:
        self._words = words
        ids = [w["id"] for w in words]
        cur_id = self._order[self._index] if self._order and self._index < len(self._order) else None

        if self._mode == PlayMode.RANDOM:
            self._order = ids.copy()
            random.shuffle(self._order)
        else:
            self._order = ids.copy()

        if cur_id and cur_id in self._order:
            self._index = self._order.index(cur_id)
        else:
            self._index = 0

    def shuffle_playlist(self) -> None:
        """打乱当前播放顺序（随机模式下重新洗牌）。"""
        if not self._order:
            return
        cur_id = self._order[self._index] if self._index < len(self._order) else None
        random.shuffle(self._order)
        if cur_id and cur_id in self._order:
            self._index = self._order.index(cur_id)
        else:
            self._index = 0

    def select_word(self, word_id: str) -> None:
        """列表选中时切换到对应条目。"""
        if word_id in self._order:
            self._index = self._order.index(word_id)
        elif self._words:
            self._order = [w["id"] for w in self._words]
            if self._mode == PlayMode.RANDOM:
                random.shuffle(self._order)
            self._index = self._order.index(word_id) if word_id in self._order else 0
        self._update_title()
        self.current_word_changed.emit(word_id)

    def _current_word(self) -> Optional[dict]:
        if not self._order or self._index >= len(self._order):
            return None
        wid = self._order[self._index]
        for w in self._words:
            if w["id"] == wid:
                return w
        return None

    def _update_title(self) -> None:
        w = self._current_word()
        if not w:
            self._en_label.setText("—")
            self._zh_label.setText("词库为空，请在上方添加单词")
            self._hint.setText("")
            return
        self._en_label.setText(w["english"])
        self._zh_label.setText(w["chinese"])
        self._hint.setText(self._mode_hint_text())

    def _mode_hint_text(self) -> str:
        if self._mode == PlayMode.REPEAT_ONE:
            return "重复模式：仅重复朗读当前词"
        if self._mode == PlayMode.REVERSE:
            return "倒序连播：播放完自动移至列表中上一个词"
        if self._mode == PlayMode.RANDOM:
            return "随机连播：播放完自动随机下一词"
        return "顺序连播：播放完自动移至下一个词"

    def play(self) -> None:
        w = self._current_word()
        if not w:
            return
        self._start_word_audio(w)

    def pause(self) -> None:
        self._player.pause()

    def _start_word_audio(self, w: dict) -> None:
        segs = w.get("audio_segments")
        path_one = w.get("audio_path")
        if segs and isinstance(segs, list) and len(segs) > 1:
            self._segment_queue = [s for s in segs if s]
            self._segment_idx = 0
            self._play_path(self._segment_queue[0])
            self._hint.setText("正在朗读…（分段）")
        elif path_one and Path(path_one).is_file():
            self._segment_queue = []
            self._play_path(path_one)
            self._hint.setText("正在播放…")
        else:
            self._zh_label.setText(w["chinese"])
            self._hint.setText("暂无音频：请等待后台生成或点击「重新生成音频」")

    def _play_path(self, path: str) -> None:
        self._player.setSource(QUrl.fromLocalFile(str(Path(path).resolve())))
        self._player.play()

    def _on_media_status(self, status: QMediaPlayer.MediaStatus) -> None:
        if status != QMediaPlayer.MediaStatus.EndOfMedia:
            return
        w = self._current_word()
        if not w:
            return
        # 同一词内多段音频
        if self._segment_queue and self._segment_idx < len(self._segment_queue) - 1:
            self._segment_idx += 1
            self._play_path(self._segment_queue[self._segment_idx])
            return
        # 一词结束
        if self._mode == PlayMode.REPEAT_ONE:
            self._segment_idx = 0
            self._start_word_audio(w)
            return
        self._auto_advance_next_word()

    def _auto_advance_next_word(self) -> None:
        """一词完整结束后自动播放下一词（重复模式不经过此处）。"""
        n = len(self._order)
        if n == 0:
            return
        if n == 1:
            self._segment_idx = 0
            w = self._current_word()
            if w:
                self._start_word_audio(w)
            return

        if self._mode == PlayMode.SEQUENTIAL:
            self._index = (self._index + 1) % n
        elif self._mode == PlayMode.REVERSE:
            self._index = (self._index - 1 + n) % n
        elif self._mode == PlayMode.RANDOM:
            choices = [i for i in range(n) if i != self._index]
            self._index = random.choice(choices)

        self._segment_idx = 0
        self._update_title()
        nw = self._current_word()
        if nw:
            self.current_word_changed.emit(nw["id"])
            self._start_word_audio(nw)

    def _manual_step_next(self) -> None:
        """上一首 / 下一首 手动切换时的索引规则。"""
        n = len(self._order)
        if n == 0:
            return
        if self._mode == PlayMode.REVERSE:
            self._index = (self._index - 1 + n) % n
        elif self._mode == PlayMode.RANDOM and n > 1:
            choices = [i for i in range(n) if i != self._index]
            self._index = random.choice(choices)
        else:
            self._index = (self._index + 1) % n

    def _manual_step_prev(self) -> None:
        n = len(self._order)
        if n == 0:
            return
        if self._mode == PlayMode.REVERSE:
            self._index = (self._index + 1) % n
        elif self._mode == PlayMode.RANDOM and n > 1:
            choices = [i for i in range(n) if i != self._index]
            self._index = random.choice(choices)
        else:
            self._index = (self._index - 1 + n) % n

    def prev_track(self) -> None:
        if not self._order:
            return
        self._manual_step_prev()
        self._segment_idx = 0
        self._update_title()
        w = self._current_word()
        if w:
            self.current_word_changed.emit(w["id"])
            self._start_word_audio(w)

    def next_track(self) -> None:
        if not self._order:
            return
        self._manual_step_next()
        self._segment_idx = 0
        self._update_title()
        w = self._current_word()
        if w:
            self.current_word_changed.emit(w["id"])
            self._start_word_audio(w)
