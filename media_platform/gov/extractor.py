# -*- coding: utf-8 -*-
# Copyright (c) 2025 relakkes@gmail.com
#
# This file is part of MediaCrawler project.
# Repository: https://github.com/NanmiCoder/MediaCrawler/blob/main/media_platform/gov/extractor.py
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

import re
from typing import Any, Iterable
from urllib.parse import urljoin

from parsel import Selector

from tools import utils


def _to_xpath_list(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, Iterable):
        return [str(item).strip() for item in value if str(item).strip()]
    return []


def _clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


_DATE_PATTERN = re.compile(r"(20\d{2}[-/.年]\d{1,2}[-/.月]\d{1,2}(?:\s+\d{1,2}:\d{2}(?::\d{2})?)?)")


class GovExtractor:
    """Generic extractor based on XPath rules."""

    @staticmethod
    def _extract_first_text(selector: Selector, xpath_rule: Any) -> str:
        for xpath_expr in _to_xpath_list(xpath_rule):
            values = selector.xpath(xpath_expr).getall()
            cleaned = [_clean_text(item) for item in values if _clean_text(item)]
            if cleaned:
                return cleaned[0]
        return ""

    @staticmethod
    def _extract_first_html(selector: Selector, xpath_rule: Any) -> str:
        for xpath_expr in _to_xpath_list(xpath_rule):
            value = selector.xpath(xpath_expr).get(default="").strip()
            if value:
                return value
        return ""

    @staticmethod
    def _extract_many_text(selector: Selector, xpath_rule: Any) -> list[str]:
        for xpath_expr in _to_xpath_list(xpath_rule):
            values = selector.xpath(xpath_expr).getall()
            cleaned = [_clean_text(item) for item in values if _clean_text(item)]
            if cleaned:
                return cleaned
        return []

    def extract_list_items(
        self,
        html: str,
        page_url: str,
        list_rule: dict[str, Any],
    ) -> list[dict[str, str]]:
        root = Selector(text=html or "")
        item_xpath_list = _to_xpath_list(list_rule.get("item_xpath"))
        if not item_xpath_list:
            raise ValueError("[GovExtractor.extract_list_items] extract.list.item_xpath is required.")
        nodes = []
        for item_xpath in item_xpath_list:
            nodes = root.xpath(item_xpath)
            if nodes:
                break

        title_xpath = list_rule.get("title_xpath")
        link_xpath = list_rule.get("link_xpath")
        date_xpath = list_rule.get("date_xpath")

        items: list[dict[str, str]] = []
        for node in nodes:
            title = self._extract_first_text(node, title_xpath)
            link = self._extract_first_text(node, link_xpath)
            publish_time = self._extract_first_text(node, date_xpath)
            if not link:
                continue
            item_url = urljoin(page_url, link)
            items.append(
                {
                    "title": title,
                    "url": item_url,
                    "publish_time": publish_time,
                }
            )
        if not items:
            items = self._fallback_extract_list_items(root=root, page_url=page_url)
        return self._post_process_items(items)

    @staticmethod
    def _is_article_href(href: str) -> bool:
        value = str(href or "").strip().lower()
        if not value:
            return False
        if value.startswith("javascript:") or value.startswith("#"):
            return False
        if not value.endswith(".html"):
            return False
        if "content/post_" in value or "/content/" in value:
            return True
        if "/index" in value or value.endswith("/index.html"):
            return False
        return "/article/" in value or "/info/" in value

    @staticmethod
    def _extract_date_from_text(text: str) -> str:
        match = _DATE_PATTERN.search(str(text or ""))
        if not match:
            return ""
        return _clean_text(match.group(1))

    @classmethod
    def _fallback_extract_list_items(cls, root: Selector, page_url: str) -> list[dict[str, str]]:
        items: list[dict[str, str]] = []
        seen_urls: set[str] = set()
        for node in root.xpath("//a[@href]"):
            href = _clean_text(node.xpath("./@href").get(default=""))
            if not cls._is_article_href(href):
                continue

            title = _clean_text(node.xpath("./@title").get(default=""))
            if not title:
                title = _clean_text(" ".join(node.xpath(".//text()").getall()))
            if not title:
                continue

            item_url = urljoin(page_url, href)
            if item_url in seen_urls:
                continue
            seen_urls.add(item_url)

            nearby = _clean_text(
                " ".join(
                    node.xpath(
                        "preceding-sibling::text()"
                        " | following-sibling::text()"
                        " | preceding-sibling::*[1]//text()"
                        " | following-sibling::*[1]//text()"
                        " | ancestor::*[1]//text()"
                    ).getall()
                )
            )
            publish_time = cls._extract_date_from_text(nearby)
            if "content/post_" not in href.lower() and not publish_time:
                continue
            items.append(
                {
                    "title": title,
                    "url": item_url,
                    "publish_time": publish_time,
                }
            )
        return items

    @staticmethod
    def _post_process_items(items: list[dict[str, str]]) -> list[dict[str, str]]:
        deduped: list[dict[str, str]] = []
        seen_urls: set[str] = set()
        for row in items:
            url = _clean_text(row.get("url", ""))
            if not url or url in seen_urls:
                continue
            seen_urls.add(url)
            deduped.append(
                {
                    "title": _clean_text(row.get("title", "")),
                    "url": url,
                    "publish_time": _clean_text(row.get("publish_time", "")),
                }
            )

        if len(deduped) > 30:
            with_date = [row for row in deduped if row["publish_time"]]
            if len(with_date) >= 5:
                return with_date
        return deduped

    def extract_detail(
        self,
        html: str,
        page_url: str,
        detail_rule: dict[str, Any],
    ) -> dict[str, Any]:
        root = Selector(text=html or "")
        title = self._extract_first_text(root, detail_rule.get("title_xpath"))
        source = self._extract_first_text(root, detail_rule.get("source_xpath"))
        publish_time = self._extract_first_text(root, detail_rule.get("pub_time_xpath"))
        content_html = self._extract_first_html(root, detail_rule.get("content_xpath"))
        content_text = utils.extract_text_from_html(content_html)

        attachment_raw_list = self._extract_many_text(root, detail_rule.get("attachments_xpath"))
        attachments: list[str] = []
        seen: set[str] = set()
        for raw_url in attachment_raw_list:
            full_url = urljoin(page_url, raw_url)
            if full_url in seen:
                continue
            seen.add(full_url)
            attachments.append(full_url)

        return {
            "title": title,
            "source": source,
            "publish_time": publish_time,
            "content_html": content_html,
            "content_text": content_text,
            "attachments": attachments,
        }
