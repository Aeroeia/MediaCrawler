# -*- coding: utf-8 -*-
# Copyright (c) 2025 relakkes@gmail.com
#
# This file is part of MediaCrawler project.
# Repository: https://github.com/NanmiCoder/MediaCrawler/blob/main/media_platform/gov/fetcher.py
# GitHub: https://github.com/NanmiCoder
# Licensed under NON-COMMERCIAL LEARNING LICENSE 1.1
#

from __future__ import annotations

import asyncio
import time
from pathlib import Path
from typing import Any

from playwright.async_api import Browser, BrowserContext, Page, Playwright, async_playwright

from tools import utils

from .client import GovClient


class GovHttpFetcher:
    def __init__(
        self,
        timeout_seconds: float = 20.0,
        retry_times: int = 3,
        min_interval_seconds: float = 1.0,
    ) -> None:
        self.client = GovClient(
            timeout_seconds=timeout_seconds,
            retry_times=retry_times,
            min_interval_seconds=min_interval_seconds,
        )

    async def start(self) -> None:
        return

    async def close(self) -> None:
        return

    async def get_text(self, url: str, page_cfg: dict[str, Any] | None = None) -> str:
        return await self.client.get_text(url)


class GovBrowserFetcher:
    _WAIT_UNTIL_ALLOW = {"load", "domcontentloaded", "networkidle", "commit"}

    def __init__(
        self,
        timeout_seconds: float = 30.0,
        retry_times: int = 2,
        min_interval_seconds: float = 1.0,
        page_cfg: dict[str, Any] | None = None,
        headless: bool = True,
    ) -> None:
        self.timeout_seconds = max(1.0, float(timeout_seconds))
        self.retry_times = max(1, int(retry_times))
        self.min_interval_seconds = max(0.0, float(min_interval_seconds))
        self.page_cfg = dict(page_cfg or {})
        self.headless = bool(headless)

        self._playwright: Playwright | None = None
        self._browser: Browser | None = None
        self._context: BrowserContext | None = None
        self._page: Page | None = None
        self._nav_lock = asyncio.Lock()
        self._throttle_lock = asyncio.Lock()
        self._last_request_ts = 0.0

    async def start(self) -> None:
        if self._browser:
            return
        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(headless=self.headless)
        self._context = await self._browser.new_context(user_agent=utils.get_user_agent())
        stealth_path = Path("libs/stealth.min.js")
        if stealth_path.exists():
            await self._context.add_init_script(path=str(stealth_path))
        self._page = await self._context.new_page()

    async def close(self) -> None:
        if self._page:
            await self._page.close()
            self._page = None
        if self._context:
            await self._context.close()
            self._context = None
        if self._browser:
            await self._browser.close()
            self._browser = None
        if self._playwright:
            await self._playwright.stop()
            self._playwright = None

    async def _throttle(self) -> None:
        if self.min_interval_seconds <= 0:
            return
        async with self._throttle_lock:
            now = time.monotonic()
            elapsed = now - self._last_request_ts
            if elapsed < self.min_interval_seconds:
                await asyncio.sleep(self.min_interval_seconds - elapsed)
            self._last_request_ts = time.monotonic()

    def _wait_until(self, override_cfg: dict[str, Any] | None = None) -> str:
        raw = str((override_cfg or {}).get("wait_until") or self.page_cfg.get("wait_until") or "domcontentloaded")
        value = raw.strip().lower()
        if value not in self._WAIT_UNTIL_ALLOW:
            return "domcontentloaded"
        return value

    def _wait_selector(self, override_cfg: dict[str, Any] | None = None) -> str:
        return str((override_cfg or {}).get("wait_selector") or self.page_cfg.get("wait_selector") or "").strip()

    def _timeout_ms(self, override_cfg: dict[str, Any] | None = None) -> int:
        raw = (override_cfg or {}).get("timeout_ms")
        if raw is None:
            raw = self.page_cfg.get("timeout_ms")
        if raw is None:
            raw = int(self.timeout_seconds * 1000)
        return max(3000, int(raw))

    def _scroll_times(self, override_cfg: dict[str, Any] | None = None) -> int:
        raw = (override_cfg or {}).get("scroll_times")
        if raw is None:
            raw = self.page_cfg.get("scroll_times")
        if raw is None:
            return 0
        return max(0, int(raw))

    def _actions(self, override_cfg: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        if override_cfg is not None:
            if "actions" not in override_cfg:
                return []
            raw = override_cfg.get("actions")
        else:
            raw = self.page_cfg.get("actions")
        if not isinstance(raw, list):
            return []
        return [dict(item) for item in raw if isinstance(item, dict)]

    async def _run_actions(self, actions: list[dict[str, Any]], timeout_ms: int) -> None:
        if not actions or not self._page:
            return
        for index, action in enumerate(actions):
            click_text = str(action.get("click_text") or "").strip()
            click_selector = str(action.get("click_selector") or "").strip()
            wait_ms = action.get("wait_ms")
            try:
                if click_text:
                    locator = self._page.get_by_text(click_text, exact=False)
                    if await locator.count() > 0:
                        await locator.first.click(timeout=timeout_ms)
                    else:
                        utils.logger.warning(
                            "[GovBrowserFetcher] action[%s] click_text not found: %s",
                            index,
                            click_text,
                        )
                elif click_selector:
                    locator = self._page.locator(click_selector)
                    if await locator.count() > 0:
                        await locator.first.click(timeout=timeout_ms)
                    else:
                        utils.logger.warning(
                            "[GovBrowserFetcher] action[%s] click_selector not found: %s",
                            index,
                            click_selector,
                        )

                if wait_ms is not None:
                    await asyncio.sleep(min(max(0, int(wait_ms)), 30000) / 1000.0)
            except Exception as exc:
                utils.logger.warning(
                    "[GovBrowserFetcher] action[%s] failed: %s",
                    index,
                    exc,
                )

    async def get_text(self, url: str, page_cfg: dict[str, Any] | None = None) -> str:
        if not self._page:
            await self.start()
        if not self._page:
            raise RuntimeError("[GovBrowserFetcher] browser page is not initialized")

        last_error: Exception | None = None
        for attempt in range(1, self.retry_times + 1):
            try:
                await self._throttle()
                async with self._nav_lock:
                    wait_until = self._wait_until(page_cfg)
                    timeout_ms = self._timeout_ms(page_cfg)
                    wait_selector = self._wait_selector(page_cfg)
                    scroll_times = self._scroll_times(page_cfg)
                    actions = self._actions(page_cfg)
                    await self._page.goto(url, wait_until=wait_until, timeout=timeout_ms)
                    if wait_selector:
                        await self._page.wait_for_selector(wait_selector, timeout=timeout_ms)
                    if actions:
                        await self._run_actions(actions=actions, timeout_ms=timeout_ms)
                    for _ in range(scroll_times):
                        await self._page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                        await asyncio.sleep(0.4)
                    return await self._page.content()
            except Exception as exc:
                last_error = exc
                if attempt >= self.retry_times:
                    break
                utils.logger.warning(
                    "[GovBrowserFetcher] request failed, attempt=%s url=%s err=%s",
                    attempt,
                    url,
                    exc,
                )
                await asyncio.sleep(float(attempt))
        raise RuntimeError(f"[GovBrowserFetcher] request failed after retries, url={url}, err={last_error}")
