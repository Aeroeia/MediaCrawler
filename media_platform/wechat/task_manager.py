# -*- coding: utf-8 -*-
# Copyright (c) 2025 relakkes@gmail.com
#
# This file is part of MediaCrawler project.
# Repository: https://github.com/NanmiCoder/MediaCrawler/blob/main/media_platform/wechat/task_manager.py
# GitHub: https://github.com/NanmiCoder
# Licensed under NON-COMMERCIAL LEARNING LICENSE 1.1
#

from __future__ import annotations

import random
import time
from collections import deque

import config


class WxTaskManager:
    def __init__(self) -> None:
        self._account_tasks: deque[str] = deque()
        self._article_tasks: deque[str] = deque()
        self._account_seen: set[str] = set()
        self._article_seen: set[str] = set()

    def add_account_tasks(self, biz_list: list[str]) -> None:
        for biz in biz_list:
            value = str(biz or "").strip()
            if not value or value in self._account_seen:
                continue
            self._account_seen.add(value)
            self._account_tasks.append(value)

    def add_article_tasks(self, article_urls: list[str]) -> None:
        for url in article_urls:
            value = str(url or "").strip()
            if not value or value in self._article_seen:
                continue
            self._article_seen.add(value)
            self._article_tasks.append(value)

    def pop_next_task_url(self) -> str:
        if self._account_tasks:
            biz = self._account_tasks.popleft()
            return f"https://mp.weixin.qq.com/mp/profile_ext?action=home&__biz={biz}&scene=124#wechat_redirect"
        if self._article_tasks:
            return self._article_tasks.popleft()
        return ""

    def _sleep_seconds(self, has_next: bool) -> int:
        if has_next:
            low = max(1, int(config.WX_TASK_SLEEP_MIN_SEC))
            high = max(low, int(config.WX_TASK_SLEEP_MAX_SEC))
            return random.randint(low, high)
        return max(1, int(config.WX_NO_TASK_SLEEP_SEC))

    def build_navigation_html(self, next_url: str, tip: str = "") -> str:
        has_next = bool(str(next_url or "").strip())
        sleep_seconds = self._sleep_seconds(has_next=has_next)
        refresh_ts = int(time.time()) + sleep_seconds
        refresh_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(refresh_ts))
        action = (
            f"window.location.href='{next_url}';"
            if has_next
            else "window.location.reload();"
        )
        return (
            f"{tip} 休眠 {sleep_seconds}s 下次刷新时间 {refresh_time} "
            f"<script>setTimeout(function(){{{action}}},{sleep_seconds * 1000});</script>"
        )
