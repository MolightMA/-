# -*- coding: utf-8 -*-
"""主窗口：顶栏、录入卡片、双栏内容区、状态栏。"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any, List

from PyQt6.QtCore import QObject, Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QAction, QIcon, QPalette, QPixmap
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
    QComboBox,
    QVBoxLayout,
    QWidget,
)

from config import CACHE_DIR, VOICE_EN, VOICE_ZH, load_settings, save_settings
from core.audio_utils import word_needs_audio
from core.cloud_sync import sync_pull, sync_push
from core.database import get_db
from core.translation import fill_missing_translation
from core.tts_engine import generate_word_audio
from core.voice_presets import EDGE_VOICES_EN, EDGE_VOICES_ZH
from ui.player import PlayerPanel
from ui.stats_chart import StatsPanel
from ui.theme import APP_STYLESHEET
from ui.word_list import WordListPanel

_ICON_PATH = Path(__file__).resolve().parent.parent / "icon.png"


class _AudioSignals(QObject):
    """跨线程通知主界面刷新（QueuedConnection）。"""

    ready = pyqtSignal()
    failed = pyqtSignal(str)


class _BatchSignals(QObject):
    """批量生成进度（后台线程 → 主线程）。"""

    progress = pyqtSignal(int, int, str)  # 当前序号, 总数, 当前英文
    batch_done = pyqtSignal()
    batch_failed = pyqtSignal(str)


class _TransSignals(QObject):
    """在线翻译补全结果。"""

    filled = pyqtSignal(str, str)
    failed = pyqtSignal(str)


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("英语学习")
        self.setMinimumSize(1000, 680)
        self.resize(1100, 760)
        # 设置窗口图标
        if _ICON_PATH.is_file():
            self.setWindowIcon(QIcon(str(_ICON_PATH)))
        self._db = get_db()
        # 单线程池：批量生成与单条生成串行，避免 Edge TTS / asyncio 并发冲突
        self._executor = ThreadPoolExecutor(max_workers=1)
        self._audio_sig = _AudioSignals()
        self._audio_sig.ready.connect(self._on_audio_ready)
        self._audio_sig.failed.connect(self._on_audio_failed)

        self._batch_sig = _BatchSignals()
        self._batch_sig.progress.connect(self._on_batch_progress)
        self._batch_sig.batch_done.connect(self._on_batch_done)
        self._batch_sig.batch_failed.connect(self._on_batch_failed_msg)

        self._trans_sig = _TransSignals()
        self._trans_sig.filled.connect(self._on_translation_filled)
        self._trans_sig.failed.connect(self._on_translation_failed)

        self._word_list = WordListPanel()
        self._player = PlayerPanel()
        self._stats = StatsPanel()

        self._en_edit = QLineEdit()
        self._en_edit.setPlaceholderText("输入英文单词…")
        self._zh_edit = QLineEdit()
        self._zh_edit.setPlaceholderText("中文释义…（可只填一侧后点翻译补全）")

        self._combo_voice_en = QComboBox()
        self._combo_voice_zh = QComboBox()
        self._combo_voice_en.setMinimumWidth(200)
        self._combo_voice_zh.setMinimumWidth(200)

        self._btn_translate = QPushButton("自动翻译补全")
        self._btn_translate.setObjectName("ghostBtn")
        self._btn_translate.setToolTip(
            "仅填英文则自动补中文，仅填中文则自动补英文\n"
            "使用免费在线翻译（效果接近常见网页翻译），仅供参考"
        )

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
        self._btn_translate.clicked.connect(self._on_translate_clicked)

        self._combo_voice_en.currentIndexChanged.connect(self._on_voice_en_changed)
        self._combo_voice_zh.currentIndexChanged.connect(self._on_voice_zh_changed)

        self._en_edit.returnPressed.connect(self._on_translate_or_add_hint)
        self._zh_edit.returnPressed.connect(self._on_translate_or_add_hint)

        self._word_list.word_selected.connect(self._on_word_selected)
        self._player.current_word_changed.connect(self._word_list.highlight_word)

        # ---- 顶栏 ----
        header = QFrame()
        header.setObjectName("headerBar")
        header.setFixedHeight(72)
        hl = QHBoxLayout(header)
        hl.setContentsMargins(24, 12, 24, 12)

        # 应用图标
        if _ICON_PATH.is_file():
            icon_label = QLabel()
            pix = QPixmap(str(_ICON_PATH)).scaled(
                44, 44,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            icon_label.setPixmap(pix)
            icon_label.setFixedSize(44, 44)
            hl.addWidget(icon_label)
            hl.addSpacing(12)

        title_col = QVBoxLayout()
        title_col.setSpacing(2)
        app_title = QLabel("英语学习")
        app_title.setObjectName("appTitle")
        sub = QLabel("Edge 多音色朗读 · 在线翻译补全中英 · 启动后自动补全缺失音频")
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

        row_voice = QHBoxLayout()
        row_voice.setSpacing(12)
        lv_en = QLabel("英语发音")
        lv_en.setObjectName("labelHint")
        lv_zh = QLabel("中文发音")
        lv_zh.setObjectName("labelHint")
        row_voice.addWidget(lv_en)
        row_voice.addWidget(self._combo_voice_en, 2)
        row_voice.addWidget(lv_zh)
        row_voice.addWidget(self._combo_voice_zh, 2)
        row_voice.addStretch()
        ic.addLayout(row_voice)

        row1 = QHBoxLayout()
        row1.setSpacing(12)
        row1.addWidget(self._en_edit, 2)
        row1.addWidget(self._zh_edit, 2)
        row1.addWidget(self._btn_translate)
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

        # ---- 左侧：词库列表 + 统计图表（垂直分割）----
        left_splitter = QSplitter(Qt.Orientation.Vertical)
        left_splitter.addWidget(self._word_list)
        left_splitter.addWidget(self._stats)
        left_splitter.setStretchFactor(0, 3)
        left_splitter.setStretchFactor(1, 2)
        left_splitter.setHandleWidth(2)

        split = QSplitter(Qt.Orientation.Horizontal)
        split.addWidget(left_splitter)
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

        self._populate_voice_combos()

        # 注入 db 并刷新统计
        self._stats.set_db(self._db)
        self.reload_words()
        # 启动后短暂延迟再扫描，避免与界面首帧争抢
        QTimer.singleShot(400, self._kick_auto_audio_fill)

    def _build_menu(self) -> None:
        bar = QMenuBar(self)
        m = bar.addMenu("帮助")
        act = QAction("关于", self)
        act.triggered.connect(self._about)
        m.addAction(act)
        self.setMenuBar(bar)

    def _populate_voice_combos(self) -> None:
        """填充 Edge TTS 音色下拉框并恢复上次选择。"""
        self._combo_voice_en.blockSignals(True)
        self._combo_voice_zh.blockSignals(True)
        self._combo_voice_en.clear()
        self._combo_voice_zh.clear()
        for label, vid in EDGE_VOICES_EN:
            self._combo_voice_en.addItem(label, vid)
        for label, vid in EDGE_VOICES_ZH:
            self._combo_voice_zh.addItem(label, vid)
        s = load_settings()
        ie = self._combo_voice_en.findData(s.get("voice_en", VOICE_EN))
        if ie >= 0:
            self._combo_voice_en.setCurrentIndex(ie)
        iz = self._combo_voice_zh.findData(s.get("voice_zh", VOICE_ZH))
        if iz >= 0:
            self._combo_voice_zh.setCurrentIndex(iz)
        self._combo_voice_en.blockSignals(False)
        self._combo_voice_zh.blockSignals(False)

    def _on_voice_en_changed(self, _: int) -> None:
        vid = self._combo_voice_en.currentData()
        if vid:
            save_settings({"voice_en": str(vid)})
            self._status.showMessage("已保存英语发音，新录制的朗读将使用此声音")

    def _on_voice_zh_changed(self, _: int) -> None:
        vid = self._combo_voice_zh.currentData()
        if vid:
            save_settings({"voice_zh": str(vid)})
            self._status.showMessage("已保存中文发音，新录制的朗读将使用此声音")

    def _on_translate_clicked(self) -> None:
        en = self._en_edit.text().strip()
        zh = self._zh_edit.text().strip()
        if en and zh:
            QMessageBox.information(
                self,
                "提示",
                "两侧都已填写时不会自动覆盖。\n如需重新翻译，请先清空其中一侧。",
            )
            return
        if not en and not zh:
            QMessageBox.information(self, "提示", "请先输入英文或中文其中一侧。")
            return
        self._status.showMessage("正在在线翻译…")
        self._executor.submit(self._translate_job, en, zh)

    def _translate_job(self, en: str, zh: str) -> None:
        try:
            ne, nz = fill_missing_translation(en, zh)
            self._trans_sig.filled.emit(ne, nz)
        except Exception as e:
            self._trans_sig.failed.emit(str(e))

    def _on_translation_filled(self, en: str, zh: str) -> None:
        self._en_edit.setText(en)
        self._zh_edit.setText(zh)
        self._status.showMessage("已补全翻译（机器翻译仅供参考）")

    def _on_translation_failed(self, msg: str) -> None:
        QMessageBox.warning(self, "翻译失败", msg)
        self._status.showMessage(msg)

    def _on_translate_or_add_hint(self) -> None:
        """回车：仅一侧有时先翻译；两侧都有时直接添加单词。"""
        en = self._en_edit.text().strip()
        zh = self._zh_edit.text().strip()
        if en and zh:
            self._on_add()
            return
        if (en and not zh) or (zh and not en):
            self._on_translate_clicked()

    def reload_words(self) -> None:
        words = self._db.list_words()
        self._word_list.set_words(words)
        self._player.set_words(words)
        self._stats.refresh()

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

    def _on_batch_progress(self, cur: int, total: int, en: str) -> None:
        self.statusBar().showMessage(f"后台生成音频 {cur}/{total} · {en}")

    def _on_batch_done(self) -> None:
        self.reload_words()
        self.statusBar().showMessage("缺失音频已生成完毕（若个别失败请查看状态栏提示）")

    def _on_batch_failed_msg(self, msg: str) -> None:
        self.statusBar().showMessage(f"生成出错：{msg}")

    def _kick_auto_audio_fill(self) -> None:
        """进入程序后为尚无文件的词条顺序生成音频。"""
        words = self._db.list_words()
        missing = [w for w in words if word_needs_audio(w)]
        if not missing:
            self.statusBar().showMessage("词条音频已齐全 · 数据保存在程序目录 data 文件夹")
            return
        self.statusBar().showMessage(f"检测到 {len(missing)} 个词条缺音频，正在后台生成…")
        self._executor.submit(self._batch_generate_worker, missing)

    def _batch_generate_worker(self, missing: List[dict[str, Any]]) -> None:
        total = len(missing)
        for i, w in enumerate(missing):
            try:
                primary, segments = generate_word_audio(w["english"], w["chinese"], w["id"])
                if segments and len(segments) > 1:
                    self._db.update_audio(w["id"], segments[0], segments)
                elif primary:
                    self._db.update_audio(w["id"], primary, None)
                else:
                    self._batch_sig.batch_failed.emit(f"{w['english']} 未写出文件")
                    continue
                self._batch_sig.progress.emit(i + 1, total, w["english"])
            except Exception as e:
                self._batch_sig.batch_failed.emit(f"{w['english']} — {e}")
        self._batch_sig.batch_done.emit()

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
        self._status.showMessage(f"已导入 {n} 条，将为缺音频词条自动生成朗读…")
        QTimer.singleShot(300, self._kick_auto_audio_fill)

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
            "朗读：微软 Edge 免费神经语音（多音色可选），非豆包/有道官方接口。\n"
            "翻译补全：免费在线机器翻译（仅供参考），效果接近常见网页翻译。\n\n"
            "合并长音频建议安装 FFmpeg；否则将分段顺序播放。\n"
            "打包版数据与 settings.json 保存在 exe 同目录下的 data 文件夹。",
        )
