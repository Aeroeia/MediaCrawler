# -*- coding: utf-8 -*-
# Copyright (c) 2025 relakkes@gmail.com
#
# This file is part of MediaCrawler project.
# Repository: https://github.com/NanmiCoder/MediaCrawler/blob/main/tests/test_gov_fetcher.py
# GitHub: https://github.com/NanmiCoder
# Licensed under NON-COMMERCIAL LEARNING LICENSE 1.1
#

import pytest

from media_platform.gov.fetcher import GovBrowserFetcher


class _FakeLocator:
    def __init__(self, page, key: str, count: int = 1):
        self._page = page
        self._key = key
        self._count = count

    async def count(self) -> int:
        return self._count

    @property
    def first(self):
        return self

    async def click(self, timeout: int = 0):
        self._page.clicked.append((self._key, timeout))


class _FakePage:
    def __init__(self):
        self.clicked: list[tuple[str, int]] = []
        self._selector_count = {"#history": 1}

    def get_by_text(self, text: str, exact: bool = False):  # noqa: ARG002
        return _FakeLocator(self, f"text:{text}", 1)

    def locator(self, selector: str):
        return _FakeLocator(self, f"selector:{selector}", self._selector_count.get(selector, 0))


@pytest.mark.asyncio
async def test_gov_browser_fetcher_runs_actions_in_order():
    fetcher = GovBrowserFetcher(
        timeout_seconds=10,
        retry_times=1,
        min_interval_seconds=0,
        page_cfg={"actions": [{"click_text": "历史公告"}, {"click_selector": "#history"}, {"wait_ms": 10}]},
    )
    fake_page = _FakePage()
    fetcher._page = fake_page
    await fetcher._run_actions(actions=fetcher._actions(), timeout_ms=1234)

    assert fake_page.clicked == [
        ("text:历史公告", 1234),
        ("selector:#history", 1234),
    ]
