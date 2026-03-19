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

import hashlib
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


_DATE_PATTERN = re.compile(
    r"(20\d{2}[-/.年]\d{1,2}[-/.月]\d{1,2}(?:[日]?(?:\s+\d{1,2}:\d{2}(?::\d{2})?)?)?)"
)


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
        if value.startswith("javascript:") or value.startswith("#") or value.startswith("mailto:"):
            return False
        if "toarticledetails" in value:
            return True
        if "/portal/notice?id=" in value:
            return True
        if "/notice?id=" in value:
            return True
        if not value.endswith(".html"):
            return "/article/" in value or "/info/" in value or "/detail" in value
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
            lowered = href.lower()
            keep_without_date = any(
                token in lowered
                for token in (
                    "content/post_",
                    "toarticledetails",
                    "/portal/notice?id=",
                    "/notice?id=",
                )
            )
            if not keep_without_date and not publish_time:
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
            normalized = {
                "title": _clean_text(row.get("title", "")),
                "url": url,
                "publish_time": _clean_text(row.get("publish_time", "")),
            }
            for key in ("source", "content_text", "content_html", "inline_mode"):
                value = row.get(key)
                if value is None:
                    continue
                normalized[key] = _clean_text(value) if key != "content_html" else str(value)
            deduped.append(normalized)

        if len(deduped) > 30:
            with_date = [row for row in deduped if row["publish_time"]]
            if len(with_date) >= 5:
                return with_date
        with_date = [row for row in deduped if row["publish_time"]]
        if len(with_date) >= 3 and len(with_date) >= int(len(deduped) * 0.6):
            return with_date
        return deduped

    def extract_inline_list_items(
        self,
        html: str,
        page_url: str,
        inline_rule: dict[str, Any],
    ) -> list[dict[str, str]]:
        root = Selector(text=html or "")
        item_xpath_list = _to_xpath_list(inline_rule.get("item_xpath"))
        if not item_xpath_list:
            return []

        nodes = []
        for item_xpath in item_xpath_list:
            nodes = root.xpath(item_xpath)
            if nodes:
                break

        title_xpath = inline_rule.get("title_xpath")
        date_xpath = inline_rule.get("date_xpath")
        source_xpath = inline_rule.get("source_xpath")
        summary_xpath = inline_rule.get("summary_xpath")
        link_xpath = inline_rule.get("link_xpath")

        rows: list[dict[str, str]] = []
        for node in nodes:
            title = self._extract_first_text(node, title_xpath)
            if not title:
                for token in [_clean_text(item) for item in node.xpath(".//text()").getall()]:
                    if not token:
                        continue
                    if self._extract_date_from_text(token):
                        continue
                    title = token
                    break
            if not title:
                continue
            publish_time = self._extract_first_text(node, date_xpath)
            source = self._extract_first_text(node, source_xpath)
            summary = self._extract_first_text(node, summary_xpath)
            node_text = _clean_text(" ".join(node.xpath(".//text()").getall()))
            if not publish_time:
                publish_time = self._extract_date_from_text(node_text)
            link = self._extract_first_text(node, link_xpath)
            item_url = urljoin(page_url, link) if link else ""
            if not item_url:
                fingerprint = hashlib.sha1(
                    f"{page_url}|{title}|{publish_time}|{source}|{summary}".encode("utf-8")
                ).hexdigest()
                item_url = f"{page_url}#inline-{fingerprint}"
            rows.append(
                {
                    "title": _clean_text(title),
                    "url": _clean_text(item_url),
                    "publish_time": _clean_text(publish_time),
                    "source": _clean_text(source),
                    "content_text": _clean_text(summary or node_text),
                    "content_html": node.get() or "",
                    "inline_mode": "1",
                }
            )

        return self._post_process_items(rows)

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
        if not publish_time:
            publish_time = self._extract_date_from_text(" ".join(root.xpath("//body//text()").getall()))
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
