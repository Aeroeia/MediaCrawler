# -*- coding: utf-8 -*-
# Copyright (c) 2025 relakkes@gmail.com
#
# This file is part of MediaCrawler project.
# Repository: https://github.com/NanmiCoder/MediaCrawler/blob/main/media_platform/gov/core.py
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
import hashlib
from datetime import datetime
from typing import Any, Dict, Optional
from urllib.parse import urljoin

from playwright.async_api import BrowserContext, BrowserType
from sqlalchemy import text

import config
from base.base_crawler import AbstractCrawler
from store import gov as gov_store
from tools import utils
from var import crawler_type_var
from database.db_session import create_tables, get_async_engine

from .extractor import GovExtractor
from .fetcher import GovBrowserFetcher, GovHttpFetcher
from .rule_loader import GovRuleLoader
from .site_registry import GovSiteRegistry


class GovCrawler(AbstractCrawler):
    """Government websites crawler, rule-driven for multi-site reuse."""
    _db_schema_ready = False
    _db_schema_lock = asyncio.Lock()

    def __init__(self) -> None:
        self.extractor = GovExtractor()
        self.rule_loader = GovRuleLoader()
        self.fetcher: GovHttpFetcher | GovBrowserFetcher | None = None

    async def launch_browser(
        self,
        chromium: BrowserType,
        playwright_proxy: Optional[Dict],
        user_agent: Optional[str],
        headless: bool = True,
    ) -> BrowserContext:
        raise RuntimeError("GovCrawler does not use platform login/browser context lifecycle.")

    async def search(self) -> None:
        site_code = str(config.GOV_SITE or "").strip()
        self._ensure_site_ready(site_code)
        rule = self.rule_loader.load_site_rule(site=site_code, custom_rule_path=str(config.GOV_RULE_PATH or "").strip())
        channel = str(config.GOV_CHANNEL or "").strip() or self.rule_loader.get_default_channel(site=site_code)
        fetch_mode = str((rule.get("site") or {}).get("fetch_mode") or "http").strip().lower()
        self.fetcher = self._create_fetcher(rule=rule, fetch_mode=fetch_mode)
        await self.fetcher.start()
        try:
            await self._crawl_by_channel(rule=rule, channel=channel)
        finally:
            if self.fetcher:
                await self.fetcher.close()
                self.fetcher = None

    async def _crawl_by_channel(self, rule: dict[str, Any], channel: str) -> None:
        channel_rule = self.rule_loader.get_channel_rule(rule=rule, channel=channel)
        page_urls = self._build_list_page_urls(rule=rule, channel_rule=channel_rule, max_pages=config.GOV_MAX_PAGES)
        utils.logger.info(
            "[GovCrawler] site=%s channel=%s list_pages=%s",
            rule["site"].get("code"),
            channel,
            len(page_urls),
        )

        seen_urls: set[str] = set()
        list_item_count = 0
        success_count = 0
        fail_count = 0

        for page_url in page_urls:
            if not self.fetcher:
                raise RuntimeError("[GovCrawler] fetcher is not initialized")
            list_page_cfg = self._get_list_page_cfg(rule=rule)
            detail_page_cfg = self._get_detail_page_cfg(rule=rule)
            page_html = await self.fetcher.get_text(page_url, page_cfg=list_page_cfg)
            items = self._extract_page_items(rule=rule, page_url=page_url, page_html=page_html)
            list_item_count += len(items)
            utils.logger.info(
                "[GovCrawler] fetched list page=%s item_count=%s",
                page_url,
                len(items),
            )

            for list_item in items:
                detail_url = str(list_item.get("url") or "").strip()
                inline_mode = str(list_item.get("inline_mode") or "").strip().lower() in {"1", "true", "yes"}
                if not detail_url or detail_url in seen_urls:
                    continue
                seen_urls.add(detail_url)

                try:
                    if inline_mode:
                        detail_item = {
                            "title": str(list_item.get("title") or "").strip(),
                            "source": str(list_item.get("source") or "").strip(),
                            "publish_time": str(list_item.get("publish_time") or "").strip(),
                            "content_html": str(list_item.get("content_html") or "").strip(),
                            "content_text": str(list_item.get("content_text") or "").strip(),
                            "attachments": [],
                        }
                    else:
                        if not self.fetcher:
                            raise RuntimeError("[GovCrawler] fetcher is not initialized")
                        detail_html = await self.fetcher.get_text(detail_url, page_cfg=detail_page_cfg)
                        detail_item = self.extractor.extract_detail(
                            html=detail_html,
                            page_url=detail_url,
                            detail_rule=rule["extract"]["detail"],
                        )
                    normalized = self._normalize_record(
                        rule=rule,
                        channel=channel,
                        list_item=list_item,
                        detail_item=detail_item,
                        url=detail_url,
                    )
                    await gov_store.update_gov_content(normalized)
                    success_count += 1
                except Exception as exc:
                    fail_count += 1
                    utils.logger.error(
                        "[GovCrawler] detail fetch failed, url=%s err=%s",
                        detail_url,
                        exc,
                    )

        utils.logger.info(
            "[GovCrawler] completed. list_items=%s success=%s failed=%s",
            list_item_count,
            success_count,
            fail_count,
        )

    def _extract_page_items(self, rule: dict[str, Any], page_url: str, page_html: str) -> list[dict[str, Any]]:
        extract_rule = rule.get("extract") or {}
        list_items = self.extractor.extract_list_items(
            html=page_html,
            page_url=page_url,
            list_rule=extract_rule.get("list") or {},
        )
        if list_items:
            return list_items
        site_cfg = rule.get("site") or {}
        if not bool(site_cfg.get("allow_inline_detail")):
            return []
        inline_rule = extract_rule.get("inline_list") or {}
        if not isinstance(inline_rule, dict):
            return []
        inline_items = self.extractor.extract_inline_list_items(
            html=page_html,
            page_url=page_url,
            inline_rule=inline_rule,
        )
        if inline_items:
            utils.logger.info("[GovCrawler] inline list extracted page=%s count=%s", page_url, len(inline_items))
        return inline_items

    async def _crawl_detail_urls(self, rule: dict[str, Any], channel: str) -> None:
        urls = [str(url).strip() for url in config.GOV_SPECIFIED_URL_LIST if str(url).strip()]
        if not urls:
            utils.logger.warning("[GovCrawler] detail mode has no URLs. Use --specified_id with comma-separated URLs.")
            return

        extract_detail_rule = rule["extract"]["detail"]
        success_count = 0
        fail_count = 0

        for detail_url in urls:
            try:
                if not self.fetcher:
                    raise RuntimeError("[GovCrawler] fetcher is not initialized")
                detail_html = await self.fetcher.get_text(
                    detail_url,
                    page_cfg=self._get_detail_page_cfg(rule=rule),
                )
                detail_item = self.extractor.extract_detail(
                    html=detail_html,
                    page_url=detail_url,
                    detail_rule=extract_detail_rule,
                )
                normalized = self._normalize_record(
                    rule=rule,
                    channel=channel,
                    list_item={},
                    detail_item=detail_item,
                    url=detail_url,
                )
                await gov_store.update_gov_content(normalized)
                success_count += 1
            except Exception as exc:
                fail_count += 1
                utils.logger.error(
                    "[GovCrawler] detail mode failed, url=%s err=%s",
                    detail_url,
                    exc,
                )

        utils.logger.info("[GovCrawler] detail mode completed. success=%s failed=%s", success_count, fail_count)

    async def start(self) -> None:
        await self._ensure_db_schema_if_needed()
        # validate save option early
        gov_store.GovStoreFactory.create_store()

        crawler_type_var.set(config.CRAWLER_TYPE)
        site_code = str(config.GOV_SITE or "").strip()
        self._ensure_site_ready(site_code)
        rule = self.rule_loader.load_site_rule(
            site=site_code,
            custom_rule_path=str(config.GOV_RULE_PATH or "").strip(),
        )
        fetch_mode = str((rule.get("site") or {}).get("fetch_mode") or "http").strip().lower()
        self.fetcher = self._create_fetcher(rule=rule, fetch_mode=fetch_mode)
        await self.fetcher.start()
        channel = str(config.GOV_CHANNEL or "").strip() or self.rule_loader.get_default_channel(site=site_code)

        try:
            if config.CRAWLER_TYPE == "search":
                await self._crawl_by_channel(rule=rule, channel=channel)
                return

            if config.CRAWLER_TYPE == "detail":
                await self._crawl_detail_urls(rule=rule, channel=channel)
                return

            if config.CRAWLER_TYPE == "creator":
                raise ValueError("[GovCrawler] creator mode is not supported for gov platform.")

            raise ValueError(f"[GovCrawler] unsupported crawler type: {config.CRAWLER_TYPE}")
        finally:
            if self.fetcher:
                await self.fetcher.close()
                self.fetcher = None

    @staticmethod
    def _ensure_site_ready(site_code: str) -> None:
        try:
            site_info = GovSiteRegistry.get_site(site_code=site_code)
        except Exception:
            utils.logger.warning("[GovCrawler] site=%s not found in manifest, continue with custom rule.", site_code)
            return
        status = str(site_info.get("status") or "").strip().lower()
        if status != "ready":
            verify_error = str(site_info.get("verify_error") or "").strip()
            raise ValueError(
                f"[GovCrawler] site={site_code} status={status or 'unknown'} is not ready for crawling."
                + (f" reason={verify_error}" if verify_error else "")
            )

    @staticmethod
    def _create_fetcher(rule: dict[str, Any], fetch_mode: str) -> GovHttpFetcher | GovBrowserFetcher:
        mode = str(fetch_mode or "http").strip().lower()
        if mode == "http":
            return GovHttpFetcher(
                timeout_seconds=20.0,
                retry_times=3,
                min_interval_seconds=float(config.CRAWLER_MAX_SLEEP_SEC),
            )
        if mode == "browser":
            browser_cfg = dict((rule.get("site") or {}).get("browser") or {})
            timeout_ms = int(browser_cfg.get("timeout_ms") or 30000)
            return GovBrowserFetcher(
                timeout_seconds=max(5.0, timeout_ms / 1000.0),
                retry_times=2,
                min_interval_seconds=float(config.CRAWLER_MAX_SLEEP_SEC),
                page_cfg=browser_cfg,
                headless=bool(config.HEADLESS),
            )
        raise ValueError(f"[GovCrawler] unsupported fetch_mode: {mode}")

    @staticmethod
    def _get_list_page_cfg(rule: dict[str, Any]) -> dict[str, Any]:
        cfg = (rule.get("site") or {}).get("browser") or {}
        return dict(cfg) if isinstance(cfg, dict) else {}

    @classmethod
    def _get_detail_page_cfg(cls, rule: dict[str, Any]) -> dict[str, Any]:
        cfg = cls._get_list_page_cfg(rule=rule)
        cfg.pop("actions", None)
        return cfg

    @classmethod
    async def _ensure_db_schema_if_needed(cls) -> None:
        if config.SAVE_DATA_OPTION != "db":
            return
        if cls._db_schema_ready:
            return
        async with cls._db_schema_lock:
            if cls._db_schema_ready:
                return
            engine = get_async_engine("db")
            table_exists = False
            if engine:
                async with engine.connect() as conn:
                    res = await conn.execute(
                        text(
                            """
                            SELECT COUNT(1)
                            FROM information_schema.tables
                            WHERE table_schema = DATABASE() AND table_name = 'gov_article'
                            """
                        )
                    )
                    table_exists = int(res.scalar() or 0) > 0
            if not table_exists:
                await create_tables("db")
            cls._db_schema_ready = True

    @staticmethod
    def _build_list_page_urls(rule: dict[str, Any], channel_rule: dict[str, Any], max_pages: int) -> list[str]:
        site_base_url = str(rule["site"].get("base_url") or "").strip()
        start_urls = channel_rule.get("start_urls") or []
        if not isinstance(start_urls, list):
            raise ValueError("[GovCrawler] channels.<name>.start_urls must be a list.")

        urls: list[str] = []
        for raw_url in start_urls:
            clean_url = str(raw_url or "").strip()
            if not clean_url:
                continue
            urls.append(urljoin(site_base_url, clean_url))

        max_pages = max(1, int(max_pages))
        if len(urls) >= max_pages:
            return urls[:max_pages]

        pagination = channel_rule.get("pagination") or {}
        pattern = str(pagination.get("pattern") or "").strip()
        start_page = int(pagination.get("start_page") or 2)

        if not pattern:
            return urls[:max_pages]

        page = start_page
        while len(urls) < max_pages:
            page_url = urljoin(site_base_url, pattern.format(page=page))
            urls.append(page_url)
            page += 1

        return urls

    @staticmethod
    def _normalize_record(
        rule: dict[str, Any],
        channel: str,
        list_item: dict[str, Any],
        detail_item: dict[str, Any],
        url: str,
    ) -> dict[str, Any]:
        site = rule.get("site") or {}
        title = str(detail_item.get("title") or list_item.get("title") or "").strip()
        publish_time = str(detail_item.get("publish_time") or list_item.get("publish_time") or "").strip()
        source = str(detail_item.get("source") or "").strip()
        content_html = str(detail_item.get("content_html") or "").strip()
        content_text = str(detail_item.get("content_text") or "").strip()
        attachments = detail_item.get("attachments") or []
        if not isinstance(attachments, list):
            attachments = []

        digest = hashlib.sha1(f"{url}|{title}|{publish_time}".encode("utf-8")).hexdigest()
        return {
            "site_code": str(site.get("code") or "").strip(),
            "site_name": str(site.get("name") or "").strip(),
            "channel": str(channel or "").strip(),
            "title": title,
            "url": str(url or "").strip(),
            "publish_time": publish_time,
            "source": source,
            "content_html": content_html,
            "content_text": content_text,
            "attachments": attachments,
            "crawl_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "fingerprint": digest,
        }
