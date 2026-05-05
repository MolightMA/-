# -*- coding: utf-8 -*-
"""
云端增量同步：仅上传 synced=0 的记录。
未配置 CLOUDBASE_SYNC_URL 时跳过网络请求，仅标记为「未启用云端」。
实际接入腾讯云开发时，可将 SYNC_URL 指向云函数，请求体为单词 JSON 数组。
"""
from __future__ import annotations

import json
from typing import Any, Dict, List, Tuple

import requests

from config import CLOUDBASE_API_KEY, CLOUDBASE_ENABLED, CLOUDBASE_SYNC_URL
from core.database import get_db


def sync_push() -> Tuple[bool, str]:
    """将未同步记录 POST 到服务端。"""
    if not CLOUDBASE_ENABLED or not CLOUDBASE_SYNC_URL.strip():
        return True, "本地模式：未配置云端，跳过上传"

    db = get_db()
    pending = db.list_unsynced()
    if not pending:
        return True, "无待同步记录"

    headers = {"Content-Type": "application/json"}
    if CLOUDBASE_API_KEY:
        headers["Authorization"] = f"Bearer {CLOUDBASE_API_KEY}"

    payload = {"words": pending}
    try:
        r = requests.post(
            CLOUDBASE_SYNC_URL,
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers=headers,
            timeout=30,
        )
        r.raise_for_status()
        for w in pending:
            db.set_synced(w["id"], True)
        return True, f"已上传 {len(pending)} 条"
    except Exception as e:
        return False, f"上传失败: {e}"


def sync_pull() -> Tuple[bool, str]:
    """从服务端拉取并合并（需服务端提供 GET 返回 words 列表）。"""
    if not CLOUDBASE_ENABLED or not CLOUDBASE_SYNC_URL.strip():
        return True, "本地模式：未配置云端，跳过拉取"

    url = CLOUDBASE_SYNC_URL.rstrip("/")
    get_url = url if url.endswith("/pull") else url + "/pull"
    headers = {}
    if CLOUDBASE_API_KEY:
        headers["Authorization"] = f"Bearer {CLOUDBASE_API_KEY}"

    try:
        r = requests.get(get_url, headers=headers, timeout=30)
        r.raise_for_status()
        data = r.json()
        words: List[Dict[str, Any]] = data.get("words") or data.get("data") or []
        db = get_db()
        for row in words:
            if "id" in row and "english" in row and "chinese" in row:
                db.upsert_word_from_cloud(row)
        return True, f"已合并 {len(words)} 条"
    except Exception as e:
        return False, f"拉取失败: {e}"
