# -*- coding: utf-8 -*-
"""
免费在线翻译（机器翻译，仅供参考；非有道/豆包官方 SDK）。
策略：先 MyMemory 公共接口，失败或额度用尽时用公共网页翻译接口作为后备。
"""
from __future__ import annotations

import re
from typing import Tuple

import requests


def _looks_mostly_chinese(text: str) -> bool:
    """粗略判断是否主要为中文。"""
    cn = sum(1 for c in text if "\u4e00" <= c <= "\u9fff")
    latin = sum(1 for c in text if ("a" <= c.lower() <= "z"))
    return cn >= latin and cn > 0


def translate_en_to_zh(text: str) -> str:
    """英译中。"""
    text = text.strip()
    if not text:
        return ""
    t = _try_mymemory(text, "en", "zh-CN")
    if t:
        return t
    return _try_gtx(text, "en", "zh-CN")


def translate_zh_to_en(text: str) -> str:
    """中译英。"""
    text = text.strip()
    if not text:
        return ""
    t = _try_mymemory(text, "zh-CN", "en")
    if t:
        return t
    return _try_gtx(text, "zh-CN", "en")


def _try_mymemory(q: str, src: str, tgt: str) -> str:
    try:
        pair = f"{src}|{tgt}"
        r = requests.get(
            "https://api.mymemory.translated.net/get",
            params={"q": q, "langpair": pair},
            timeout=12,
        )
        r.raise_for_status()
        data = r.json()
        msg = data.get("responseData", {}).get("translatedText", "") or ""
        if not msg or "MYMEMORY WARNING" in msg.upper():
            return ""
        return msg.strip()
    except Exception:
        return ""


def _try_gtx(q: str, sl: str, tl: str) -> str:
    """公共网页翻译接口（后备，无密钥）。"""
    try:
        url = "https://translate.googleapis.com/translate_a/single"
        params = {
            "client": "gtx",
            "sl": sl,
            "tl": tl,
            "dt": "t",
            "q": q,
        }
        r = requests.get(url, params=params, timeout=12)
        r.raise_for_status()
        data = r.json()
        if isinstance(data, list) and data and isinstance(data[0], list):
            part = data[0][0]
            if isinstance(part, list) and part:
                return str(part[0]).strip()
        return ""
    except Exception:
        return ""


def fill_missing_translation(en: str, zh: str) -> Tuple[str, str]:
    """
    仅补全缺失的一侧：仅有英文则填中文，仅有中文则填英文。
    两侧皆空则抛出 ValueError。
    """
    en = en.strip()
    zh = zh.strip()
    if not en and not zh:
        raise ValueError("请先输入英文或中文其中一侧")
    if en and not zh:
        zh = translate_en_to_zh(en)
        if not zh:
            raise RuntimeError("翻译失败，请检查网络或稍后重试")
        return en, zh
    if zh and not en:
        # 若用户误把英文打在中文框，尽量纠正
        if not _looks_mostly_chinese(zh) and re.search(r"[a-zA-Z]", zh):
            en = zh.strip()
            zh = translate_en_to_zh(en)
            if not zh:
                raise RuntimeError("翻译失败，请检查网络或稍后重试")
            return en, zh
        en = translate_zh_to_en(zh)
        if not en:
            raise RuntimeError("翻译失败，请检查网络或稍后重试")
        return en, zh
    return en, zh
