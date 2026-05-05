# -*- coding: utf-8 -*-
"""SQLite 数据访问，单例连接，避免多线程重复打开冲突。"""
from __future__ import annotations

import json
import sqlite3
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, List, Optional

from config import DB_PATH, DATA_DIR


def _ensure_dirs() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)


class Database:
    """数据库单例：同进程内共享一个连接（写锁由 SQLite 处理）。"""

    _instance: Optional["Database"] = None
    _lock = threading.Lock()

    def __new__(cls, db_path: Optional[Path] = None) -> "Database":
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self, db_path: Optional[Path] = None) -> None:
        if getattr(self, "_initialized", False):
            return
        _ensure_dirs()
        self._path = Path(db_path or DB_PATH)
        self._conn = sqlite3.connect(
            str(self._path),
            check_same_thread=False,
        )
        self._conn.row_factory = sqlite3.Row
        self._create_tables()
        self._initialized = True

    def _create_tables(self) -> None:
        cur = self._conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS words (
                id TEXT PRIMARY KEY,
                english TEXT NOT NULL,
                chinese TEXT NOT NULL,
                audio_path TEXT,
                audio_segments TEXT,
                created_at TEXT NOT NULL,
                synced INTEGER NOT NULL DEFAULT 0
            );
            """
        )
        self._conn.commit()

    def connection(self) -> sqlite3.Connection:
        return self._conn

    def add_word(
        self,
        english: str,
        chinese: str,
        audio_path: Optional[str] = None,
        audio_segments: Optional[List[str]] = None,
        word_id: Optional[str] = None,
    ) -> str:
        wid = word_id or str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        seg_json = json.dumps(audio_segments, ensure_ascii=False) if audio_segments else None
        cur = self._conn.cursor()
        cur.execute(
            """
            INSERT INTO words (id, english, chinese, audio_path, audio_segments, created_at, synced)
            VALUES (?, ?, ?, ?, ?, ?, 0)
            """,
            (wid, english.strip(), chinese.strip(), audio_path, seg_json, now),
        )
        self._conn.commit()
        return wid

    def delete_word(self, word_id: str) -> None:
        cur = self._conn.cursor()
        cur.execute("DELETE FROM words WHERE id = ?", (word_id,))
        self._conn.commit()

    def update_audio(
        self,
        word_id: str,
        audio_path: Optional[str],
        audio_segments: Optional[List[str]] = None,
    ) -> None:
        seg_json = json.dumps(audio_segments, ensure_ascii=False) if audio_segments else None
        cur = self._conn.cursor()
        cur.execute(
            """
            UPDATE words SET audio_path = ?, audio_segments = ?, synced = 0
            WHERE id = ?
            """,
            (audio_path, seg_json, word_id),
        )
        self._conn.commit()

    def set_synced(self, word_id: str, synced: bool = True) -> None:
        cur = self._conn.cursor()
        cur.execute(
            "UPDATE words SET synced = ? WHERE id = ?",
            (1 if synced else 0, word_id),
        )
        self._conn.commit()

    def list_words(self) -> List[dict[str, Any]]:
        cur = self._conn.cursor()
        cur.execute(
            "SELECT id, english, chinese, audio_path, audio_segments, created_at, synced FROM words ORDER BY created_at DESC"
        )
        rows = cur.fetchall()
        out: List[dict[str, Any]] = []
        for r in rows:
            segs = None
            if r["audio_segments"]:
                try:
                    segs = json.loads(r["audio_segments"])
                except json.JSONDecodeError:
                    segs = None
            out.append(
                {
                    "id": r["id"],
                    "english": r["english"],
                    "chinese": r["chinese"],
                    "audio_path": r["audio_path"],
                    "audio_segments": segs,
                    "created_at": r["created_at"],
                    "synced": bool(r["synced"]),
                }
            )
        return out

    def list_unsynced(self) -> List[dict[str, Any]]:
        return [w for w in self.list_words() if not w["synced"]]

    def upsert_word_from_cloud(self, row: dict[str, Any]) -> None:
        """云端拉取后写入或更新本地。"""
        cur = self._conn.cursor()
        cur.execute(
            """
            INSERT INTO words (id, english, chinese, audio_path, audio_segments, created_at, synced)
            VALUES (?, ?, ?, ?, ?, ?, 1)
            ON CONFLICT(id) DO UPDATE SET
                english = excluded.english,
                chinese = excluded.chinese,
                audio_path = excluded.audio_path,
                audio_segments = excluded.audio_segments,
                created_at = excluded.created_at,
                synced = 1
            """,
            (
                row["id"],
                row["english"],
                row["chinese"],
                row.get("audio_path"),
                json.dumps(row.get("audio_segments"), ensure_ascii=False)
                if row.get("audio_segments")
                else None,
                row.get("created_at") or datetime.now(timezone.utc).isoformat(),
            ),
        )
        self._conn.commit()

    def bulk_import_lines(self, lines: Iterable[str]) -> int:
        """每行格式：英文,中文 或 英文\t中文"""
        n = 0
        for line in lines:
            s = line.strip()
            if not s:
                continue
            if "\t" in s:
                parts = s.split("\t", 1)
            elif "," in s:
                parts = s.split(",", 1)
            else:
                continue
            en, zh = parts[0].strip(), parts[1].strip()
            if en and zh:
                self.add_word(en, zh)
                n += 1
        return n


def get_db() -> Database:
    return Database()
