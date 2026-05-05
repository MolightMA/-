"""
数据库模块 - SQLite 单例模式
"""
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict
from config import DB_PATH


class Database:
    """单词数据库"""
    
    _instance = None
    _connection = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._connection is None:
            self._connect()
            self._init_tables()
    
    def _connect(self):
        """建立数据库连接"""
        self._connection = sqlite3.connect(str(DB_PATH), check_same_thread=False)
        self._connection.row_factory = sqlite3.Row
    
    def _init_tables(self):
        """初始化表结构"""
        self._connection.execute("""
            CREATE TABLE IF NOT EXISTS words (
                id TEXT PRIMARY KEY,
                english TEXT NOT NULL,
                chinese TEXT NOT NULL,
                audio_path TEXT,
                voice_type TEXT DEFAULT '微软小娜(女声)',
                created_at TEXT NOT NULL,
                synced INTEGER DEFAULT 0
            )
        """)
        try:
            self._connection.execute("ALTER TABLE words ADD COLUMN voice_type TEXT DEFAULT '微软小娜(女声)'")
            self._connection.commit()
        except:
            pass
    
    def add_word(self, english: str, chinese: str, voice_type: str = "微软小娜(女声)") -> Dict:
        """添加单词"""
        word_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        
        self._connection.execute(
            "INSERT INTO words (id, english, chinese, voice_type, created_at, synced) VALUES (?, ?, ?, ?, ?, 0)",
            (word_id, english, chinese, voice_type, now)
        )
        self._connection.commit()
        
        return {
            "id": word_id,
            "english": english,
            "chinese": chinese,
            "audio_path": None,
            "voice_type": voice_type,
            "created_at": now,
            "synced": False
        }
    
    def delete_word(self, word_id: str) -> bool:
        """删除单词"""
        cursor = self._connection.execute("DELETE FROM words WHERE id = ?", (word_id,))
        self._connection.commit()
        return cursor.rowcount > 0
    
    def update_word(self, word_id: str, english: str = None, chinese: str = None, voice_type: str = None) -> bool:
        """更新单词"""
        updates = []
        params = []
        if english is not None:
            updates.append("english = ?")
            params.append(english)
        if chinese is not None:
            updates.append("chinese = ?")
            params.append(chinese)
        if voice_type is not None:
            updates.append("voice_type = ?")
            params.append(voice_type)
        
        if not updates:
            return False
        
        params.append(word_id)
        cursor = self._connection.execute(
            f"UPDATE words SET {', '.join(updates)} WHERE id = ?",
            params
        )
        self._connection.commit()
        return cursor.rowcount > 0
    
    def get_all_words(self) -> List[Dict]:
        """获取所有单词"""
        cursor = self._connection.execute("SELECT * FROM words ORDER BY created_at DESC")
        return [dict(row) for row in cursor.fetchall()]
    
    def get_word_by_id(self, word_id: str) -> Optional[Dict]:
        """根据ID获取单词"""
        cursor = self._connection.execute("SELECT * FROM words WHERE id = ?", (word_id,))
        row = cursor.fetchone()
        return dict(row) if row else None
    
    def update_audio_path(self, word_id: str, audio_path: str):
        """更新音频路径"""
        self._connection.execute(
            "UPDATE words SET audio_path = ? WHERE id = ?",
            (audio_path, word_id)
        )
        self._connection.commit()
    
    def mark_synced(self, word_id: str):
        """标记为已同步"""
        self._connection.execute("UPDATE words SET synced = 1 WHERE id = ?", (word_id,))
        self._connection.commit()
    
    def get_unsynced_words(self) -> List[Dict]:
        """获取未同步的单词"""
        cursor = self._connection.execute("SELECT * FROM words WHERE synced = 0")
        return [dict(row) for row in cursor.fetchall()]
    
    def get_word_count(self) -> int:
        """获取单词总数"""
        cursor = self._connection.execute("SELECT COUNT(*) FROM words")
        return cursor.fetchone()[0]
    
    def batch_import(self, words: List[Dict]) -> int:
        """批量导入单词"""
        count = 0
        for word in words:
            try:
                self.add_word(word.get("english", ""), word.get("chinese", ""))
                count += 1
            except Exception:
                continue
        return count
    
    def clear_all(self) -> bool:
        """清空所有单词"""
        self._connection.execute("DELETE FROM words")
        self._connection.commit()
        return True
    
    def close(self):
        """关闭连接"""
        if self._connection:
            self._connection.close()
            self._connection = None


# 全局数据库实例
db = Database()
