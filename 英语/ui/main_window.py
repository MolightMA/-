# -*- coding: utf-8 -*-
"""主窗口：顶栏、录入卡片、双栏内容区、状态栏。"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from PyQt6.QtCore import QObject, Qt, pyqtSignal
from PyQt6.QtGui import QAction, QPalette
from PyQt6.QtWidgets import (
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMenuBar,
    QMessageBox,
    QPushButton,
    QSplitter,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

from config import CACHE_DIR
from core.cloud_sync import sync_pull, sync_push
from core.database import get_db
from core.tts_engine import generate_word_audio
from ui.player import PlayerPanel
from ui.theme import APP_STYLESHEET
from ui.word_list import WordListPanel


class _AudioSignals(QObject):
    """跨线程通知主界面刷新（QueuedConnection）。"""

    ready = pyqtSignal()
    failed = pyqtSignal(str)


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("英语学习")
        self.setMinimumSize(1000, 680)
        self.resize(1100, 720)
        self._db = get_db()
        self._executor = ThreadPoolExecutor(max_workers=2)
        self._audio_sig = _AudioSignals()
        self._audio_sig.ready.connect(self._on_audio_ready)
        self._audio_sig.failed.connect(self._on_audio_failed)

        self._word_list = WordListPanel()
        self._player = PlayerPanel()

        self._en_edit = QLineEdit()
        self._en_edit.setPlaceholderText("输入英文单词…")
        self._zh_edit = QLineEdit()
        self._zh_edit.setPlaceholderText("中文释义…")

        self._btn_add = QPushButton("添加单词")
        self._btn_add.setObjectName("primaryBtn")
        self._btn_del = QPushButton("删除所选")
        self._btn_del.setObjectName("dangerBtn")
        self._btn_import = QPushButton("批量导入")
        self._btn_shuffle = QPushButton("打乱播放顺序")
        self._btn_sync_up = QPushButton("上传同步")
        self._btn_sync_down = QPushButton("拉取同步")
        self._btn_gen = QPushButton("重新生成音频")
        for b in (
            self._btn_import,
            self._btn_shuffle,
            self._btn_sync_up,
            self._btn_sync_down,
            self._btn_gen,
        ):
            b.setObjectName("ghostBtn")

        self._btn_add.clicked.connect(self._on_add)
        self._btn_del.clicked.connect(self._on_delete)
        self._btn_import.clicked.connect(self._on_import)
        self._btn_shuffle.clicked.connect(self._on_shuffle)
        self._btn_sync_up.clicked.connect(self._on_sync_up)
        self._btn_sync_down.clicked.connect(self._on_sync_down)
        self._btn_gen.clicked.connect(self._on_regenerate_audio)

        self._word_list.word_selected.connect(self._on_word_selected)
        self._player.current_word_changed.connect(self._word_list.highlight_word)

        # ---- 顶栏 ----
        header = QFrame()
        header.setObjectName("headerBar")
        header.setFixedHeight(72)
        hl = QHBoxLayout(header)
        hl.setContentsMargins(24, 12, 24, 12)
        title_col = QVBoxLayout()
        title_col.setSpacing(2)
        app_title = QLabel("英语学习")
        app_title.setObjectName("appTitle")
        sub = QLabel("本地词库 · Edge TTS 朗读 · 离线优先")
        sub.setObjectName("appSubtitle")
        title_col.addWidget(app_title)
        title_col.addWidget(sub)
        hl.addLayout(title_col)
        hl.addStretch()

        # ---- 录入与快捷操作 ----
        input_card = QFrame()
        input_card.setObjectName("inputCard")
        ic = QVBoxLayout(input_card)
        ic.setContentsMargins(20, 16, 20, 16)
        ic.setSpacing(12)
        row1 = QHBoxLayout()
        row1.setSpacing(12)
        row1.addWidget(self._en_edit, 2)
        row1.addWidget(self._zh_edit, 2)
        row1.addWidget(self._btn_add)
        ic.addLayout(row1)
        row2 = QHBoxLayout()
        row2.setSpacing(8)
        for b in (
            self._btn_del,
            self._btn_import,
            self._btn_shuffle,
            self._btn_gen,
            self._btn_sync_up,
            self._btn_sync_down,
        ):
            row2.addWidget(b)
        row2.addStretch()
        ic.addLayout(row2)

        split = QSplitter(Qt.Orientation.Horizontal)
        split.addWidget(self._word_list)
        split.addWidget(self._player)
        split.setStretchFactor(0, 4)
        split.setStretchFactor(1, 5)
        split.setHandleWidth(2)

        root = QWidget()
        lay = QVBoxLayout(root)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)
        lay.addWidget(header)
        lay.addWidget(input_card)
        lay.addWidget(split, 1)
        self.setCentralWidget(root)

        self._build_menu()

        self._status = QStatusBar()
        self.setStatusBar(self._status)
        self._status.showMessage("就绪 · 数据保存在程序目录下 data 文件夹")

        self.setStyleSheet(APP_STYLESHEET)
        pal = self.palette()
        pal.setColor(QPalette.ColorRole.Window, pal.color(QPalette.ColorRole.Base))
        self.setPalette(pal)

        self.reload_words()

    def _build_menu(self) -> None:
        bar = QMenuBar(self)
        m = bar.addMenu("帮助")
        act = QAction("关于", self)
        act.triggered.connect(self._about)
        m.addAction(act)
        self.setMenuBar(bar)

    def reload_words(self) -> None:
        words = self._db.list_words()
        self._word_list.set_words(words)
        self._player.set_words(words)

    def _current_list_word_id(self) -> str | None:
        lw = self._word_list._list
        it = lw.currentItem()
        if not it:
            return None
        return str(it.data(Qt.ItemDataRole.UserRole))

    def _on_word_selected(self, word_id: str) -> None:
        self._player.select_word(word_id)

    def _on_add(self) -> None:
        en = self._en_edit.text().strip()
        zh = self._zh_edit.text().strip()
        if not en or not zh:
            QMessageBox.warning(self, "提示", "请填写英文与中文。")
            return
        wid = self._db.add_word(en, zh)
        self._en_edit.clear()
        self._zh_edit.clear()
        self.reload_words()
        self._status.showMessage("正在生成音频…")
        self._executor.submit(self._generate_audio_job, wid, en, zh)

    def _on_audio_ready(self) -> None:
        self.reload_words()
        self.statusBar().showMessage("音频已就绪")

    def _on_audio_failed(self, msg: str) -> None:
        self.statusBar().showMessage(msg)

    def _generate_audio_job(self, word_id: str, en: str, zh: str) -> None:
        try:
            primary, segments = generate_word_audio(en, zh, word_id)
            if segments and len(segments) > 1:
                self._db.update_audio(word_id, segments[0], segments)
            elif primary:
                self._db.update_audio(word_id, primary, None)
            else:
                self._audio_sig.failed.emit("未生成有效音频文件")
                return
        except Exception as e:
            self._audio_sig.failed.emit(f"音频生成失败: {e}")
            return
        self._audio_sig.ready.emit()

    def _on_delete(self) -> None:
        wid = self._current_list_word_id()
        if not wid:
            QMessageBox.information(self, "提示", "请先选择要删除的单词。")
            return
        if QMessageBox.question(self, "确认", "确定删除该单词？") != QMessageBox.StandardButton.Yes:
            return
        row = next((w for w in self._db.list_words() if w["id"] == wid), None)
        self._db.delete_word(wid)
        if row and row.get("audio_path"):
            p = Path(row["audio_path"])
            if p.is_file():
                try:
                    p.unlink()
                except OSError:
                    pass
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        for f in CACHE_DIR.glob(f"{wid}*"):
            if f.suffix.lower() == ".mp3":
                try:
                    f.unlink()
                except OSError:
                    pass
        self.reload_words()
        self._status.showMessage("已删除")

    def _on_import(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "选择文本文件", "", "文本 (*.txt);;所有 (*.*)")
        if not path:
            return
        try:
            raw = Path(path).read_text(encoding="utf-8")
        except UnicodeDecodeError:
            raw = Path(path).read_text(encoding="gbk", errors="replace")
        lines = raw.splitlines()
        n = self._db.bulk_import_lines(lines)
        self.reload_words()
        self._status.showMessage(f"已导入 {n} 条（仅词条，可逐个重新生成音频）")

    def _on_shuffle(self) -> None:
        self._player.shuffle_playlist()
        self._status.showMessage("已打乱播放顺序")

    def _on_sync_up(self) -> None:
        _, msg = sync_push()
        self.reload_words()
        self._status.showMessage(msg)

    def _on_sync_down(self) -> None:
        _, msg = sync_pull()
        self.reload_words()
        self._status.showMessage(msg)

    def _on_regenerate_audio(self) -> None:
        wid = self._current_list_word_id()
        if not wid:
            QMessageBox.information(self, "提示", "请先选择单词。")
            return
        row = next((w for w in self._db.list_words() if w["id"] == wid), None)
        if not row:
            return
        self._status.showMessage("正在重新生成音频…")
        self._executor.submit(
            self._generate_audio_job,
            wid,
            row["english"],
            row["chinese"],
        )

    def _about(self) -> None:
        QMessageBox.about(
            self,
            "关于",
            "英语学习\n\n"
            "PyQt6 + SQLite + Edge TTS\n"
            "合并长音频建议安装 FFmpeg；否则将分段顺序播放。\n\n"
            "打包版数据保存在 exe 同目录下的 data 文件夹。",
        )
