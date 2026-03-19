# -*- coding: utf-8 -*-
# Copyright (c) 2025 relakkes@gmail.com
#
# This file is part of MediaCrawler project.
# Repository: https://github.com/NanmiCoder/MediaCrawler/blob/main/media_platform/gov/client.py
# GitHub: https://github.com/NanmiCoder
# Licensed under NON-COMMERCIAL LEARNING LICENSE 1.1
#

# 声明：本代码仅供学习和研究目的使用。使用者应遵守以下原则：
# 1. 不得用于任何商业用途。
# 2. 使用时应遵守目标平台的使用条款和robots.txt规则。
# 3. 不得进行大规模爬取或对平台造成运营干扰。
# 4. 应合理控制请求频率，避免给目标平台带来不必要的负担。
# 5. 不得用于任何非法或不当的用途。
#
# 详细许可条款请参阅项目根目录下的LICENSE文件。
# 使用本代码即表示您同意遵守上述原则和LICENSE中的所有条款。

from __future__ import annotations

import asyncio
import time
from urllib.parse import urlparse

import httpx

from tools import utils


class GovClient:
    """HTTP client for government site crawling."""

    def __init__(
        self,
        timeout_seconds: float = 20.0,
        retry_times: int = 3,
        min_interval_seconds: float = 1.0,
    ) -> None:
        self.timeout_seconds = max(1.0, float(timeout_seconds))
        self.retry_times = max(1, int(retry_times))
        self.min_interval_seconds = max(0.0, float(min_interval_seconds))
        self._throttle_lock = asyncio.Lock()
        self._last_request_ts = 0.0
        self._prefer_http_hosts: set[str] = set()
        self._headers = {
            "User-Agent": utils.get_user_agent(),
        }

    async def _throttle(self) -> None:
        if self.min_interval_seconds <= 0:
            return
        async with self._throttle_lock:
            now = time.monotonic()
            elapsed = now - self._last_request_ts
            if elapsed < self.min_interval_seconds:
                await asyncio.sleep(self.min_interval_seconds - elapsed)
            self._last_request_ts = time.monotonic()

    async def get_text(self, url: str) -> str:
        """Fetch text content from URL with retry and throttling."""
        url = str(url or "").strip()
        if not url:
            raise ValueError("[GovClient.get_text] URL cannot be empty.")
        url = self._maybe_downgrade_https(url)

        last_error: Exception | None = None
        for attempt in range(1, self.retry_times + 1):
            try:
                await self._throttle()
                async with httpx.AsyncClient(
                    follow_redirects=True,
                    timeout=self.timeout_seconds,
                    headers=self._headers,
                ) as client:
                    response = await client.get(url)
                    response.raise_for_status()
                    return response.text
            except Exception as exc:
                if url.startswith("https://") and self._is_ssl_error(exc):
                    fallback_url = "http://" + url[len("https://"):]
                    self._mark_host_http_preferred(url)
                    utils.logger.warning(
                        "[GovClient.get_text] SSL handshake issue detected, fallback to http url=%s",
                        fallback_url,
                    )
                    try:
                        await self._throttle()
                        async with httpx.AsyncClient(
                            follow_redirects=True,
                            timeout=self.timeout_seconds,
                            headers=self._headers,
                        ) as client:
                            response = await client.get(fallback_url)
                            response.raise_for_status()
                            return response.text
                    except Exception as fallback_exc:
                        last_error = fallback_exc
                else:
                    last_error = exc
                if attempt >= self.retry_times:
                    break
                backoff = float(attempt)
                utils.logger.warning(
                    "[GovClient.get_text] request failed, attempt=%s url=%s err=%s, retrying in %.1fs",
                    attempt,
                    url,
                    exc,
                    backoff,
                )
                await asyncio.sleep(backoff)

        raise RuntimeError(f"[GovClient.get_text] request failed after retries, url={url}, err={last_error}")

    def _maybe_downgrade_https(self, url: str) -> str:
        if not url.startswith("https://"):
            return url
        host = (urlparse(url).hostname or "").lower()
        if host and host in self._prefer_http_hosts:
            return "http://" + url[len("https://"):]
        return url

    def _mark_host_http_preferred(self, url: str) -> None:
        host = (urlparse(url).hostname or "").lower()
        if host:
            self._prefer_http_hosts.add(host)

    @staticmethod
    def _is_ssl_error(exc: Exception | None) -> bool:
        if not exc:
            return False
        text = str(exc).lower()
        return "ssl" in text or "bad ecpoint" in text or "certificate" in text
