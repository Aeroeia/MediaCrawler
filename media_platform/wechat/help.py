# -*- coding: utf-8 -*-
# Copyright (c) 2025 relakkes@gmail.com
#
# This file is part of MediaCrawler project.
# Repository: https://github.com/NanmiCoder/MediaCrawler/blob/main/media_platform/wechat/help.py
# GitHub: https://github.com/NanmiCoder
# Licensed under NON-COMMERCIAL LEARNING LICENSE 1.1
#

from __future__ import annotations

import datetime
import hashlib
import json
import re
from urllib.parse import parse_qs, urlparse

from .field import BIZ_RE, SN_RE


def safe_json_loads(text: str) -> dict:
    try:
        return json.loads(text or "{}")
    except Exception:
        return {}


def get_param(url: str, key: str) -> str:
    query = parse_qs(urlparse(url).query)
    values = query.get(key, [])
    return str(values[0]) if values else ""


def timestamp_to_str(ts: int | str | None) -> str:
    try:
        value = int(ts or 0)
    except Exception:
        return ""
    if value <= 0:
        return ""
    return datetime.datetime.fromtimestamp(value).strftime("%Y-%m-%d %H:%M:%S")


def parse_request_body(body: str) -> dict:
    query = parse_qs(str(body or ""), keep_blank_values=True)
    return {k: (v[0] if v else "") for k, v in query.items()}


def build_article_id(sn: str, biz: str, url: str) -> str:
    raw = f"{sn}|{biz}|{url}"
    return hashlib.md5(raw.encode("utf-8")).hexdigest()


def looks_like_biz(token: str) -> bool:
    return bool(BIZ_RE.match(str(token or "").strip()))


def looks_like_sn(token: str) -> bool:
    return bool(SN_RE.match(str(token or "").strip()))


def strip_images(html: str) -> str:
    return re.sub(r"<img.*?>", "", str(html or ""), flags=re.S)


def extract_biz_from_url(url: str) -> str:
    biz = get_param(url, "__biz")
    if biz:
        return biz
    match = re.search(r"__biz=([^&\"']+)", str(url or ""))
    return match.group(1) if match else ""


def normalize_text(text: str) -> str:
    return str(text or "").strip()
