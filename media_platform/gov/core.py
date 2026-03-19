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

import hashlib
from datetime import datetime
from typing import Any, Dict, Optional
from urllib.parse import urljoin

from playwright.async_api import BrowserContext, BrowserType

import config
from base.base_crawler import AbstractCrawler
from store import gov as gov_store
from tools import utils
from var import crawler_type_var

from .client import GovClient
from .extractor import GovExtractor
from .rule_loader import GovRuleLoader
from .site_registry import GovSiteRegistry


class GovCrawler(AbstractCrawler):
    """Government websites crawler, rule-driven for multi-site reuse."""

    def __init__(self) -> None:
        self.client = GovClient(
            timeout_seconds=20.0,
            retry_times=3,
            min_interval_seconds=float(config.CRAWLER_MAX_SLEEP_SEC),
        )
        self.extractor = GovExtractor()
        self.rule_loader = GovRuleLoader()

    async def launch_browser(
        self,
        chromium: BrowserType,
        playwright_proxy: Optional[Dict],
        user_agent: Optional[str],
        headless: bool = True,
    ) -> BrowserContext:
        raise RuntimeError("GovCrawler does not use browser mode in V2 static-first mode.")

    async def search(self) -> None:
        site_code = str(config.GOV_SITE or "").strip()
        self._ensure_site_ready(site_code)
        rule = self.rule_loader.load_site_rule(site=site_code, custom_rule_path=str(config.GOV_RULE_PATH or "").strip())
        channel = str(config.GOV_CHANNEL or "").strip() or self.rule_loader.get_default_channel(site=site_code)
        await self._crawl_by_channel(rule=rule, channel=channel)

    async def _crawl_by_channel(self, rule: dict[str, Any], channel: str) -> None:
        channel_rule = self.rule_loader.get_channel_rule(rule=rule, channel=channel)
        extract_rule = rule["extract"]
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
            page_html = await self.client.get_text(page_url)
            items = self.extractor.extract_list_items(
                html=page_html,
                page_url=page_url,
                list_rule=extract_rule["list"],
            )
            list_item_count += len(items)
            utils.logger.info(
                "[GovCrawler] fetched list page=%s item_count=%s",
                page_url,
                len(items),
            )

            for list_item in items:
                detail_url = str(list_item.get("url") or "").strip()
                if not detail_url or detail_url in seen_urls:
                    continue
                seen_urls.add(detail_url)

                try:
                    detail_html = await self.client.get_text(detail_url)
                    detail_item = self.extractor.extract_detail(
                        html=detail_html,
                        page_url=detail_url,
                        detail_rule=extract_rule["detail"],
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
                detail_html = await self.client.get_text(detail_url)
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
        if fetch_mode != "http":
            raise ValueError(
                f"[GovCrawler] site={site_code} fetch_mode={fetch_mode} is not supported in V2 static-first mode."
            )
        channel = str(config.GOV_CHANNEL or "").strip() or self.rule_loader.get_default_channel(site=site_code)

        if config.CRAWLER_TYPE == "search":
            await self._crawl_by_channel(rule=rule, channel=channel)
            return

        if config.CRAWLER_TYPE == "detail":
            await self._crawl_detail_urls(rule=rule, channel=channel)
            return

        if config.CRAWLER_TYPE == "creator":
            raise ValueError("[GovCrawler] creator mode is not supported for gov platform.")

        raise ValueError(f"[GovCrawler] unsupported crawler type: {config.CRAWLER_TYPE}")

    @staticmethod
    def _ensure_site_ready(site_code: str) -> None:
        try:
            site_info = GovSiteRegistry.get_site(site_code=site_code)
        except Exception:
            utils.logger.warning("[GovCrawler] site=%s not found in manifest, continue with custom rule.", site_code)
            return
        status = str(site_info.get("status") or "").strip().lower()
        if status != "ready":
            raise ValueError(
                f"[GovCrawler] site={site_code} status={status or 'unknown'} is not ready for HTTP crawling."
            )

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
