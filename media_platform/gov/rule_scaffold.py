# -*- coding: utf-8 -*-
# Copyright (c) 2025 relakkes@gmail.com
#
# This file is part of MediaCrawler project.
# Repository: https://github.com/NanmiCoder/MediaCrawler/blob/main/media_platform/gov/rule_scaffold.py
# GitHub: https://github.com/NanmiCoder
# Licensed under NON-COMMERCIAL LEARNING LICENSE 1.1
#

from __future__ import annotations

import argparse
import asyncio
import json
import re
from pathlib import Path
from typing import Iterable
from urllib.parse import urljoin, urlparse

from parsel import Selector

from .client import GovClient
from .site_registry import GovSiteRegistry


PRIORITY_PATTERNS = [
    re.compile(r"/tzgg|/gsgg|/wjtz|通知|公告", re.IGNORECASE),
    re.compile(r"/gzdt|/zwdt|动态", re.IGNORECASE),
    re.compile(r"/xxgk|/zwgk", re.IGNORECASE),
]

DEFAULT_EXTRACT_RULE = {
    "list": {
        "item_xpath": [
            "//ul[contains(@class,'tzgg_content')]/li[.//a[contains(@href,'content/post_')]]",
            "//div[contains(@class,'ListconC')][.//a[contains(@href,'content/post_')]]",
            "//ul[contains(@class,'list')]/li[.//a[contains(@href,'content/post_')]]",
            "//div[contains(@class,'list')]//li[.//a[contains(@href,'content/post_')]]",
            "//ul/li[.//a[contains(@href,'content/post_')]]",
            "//div[.//a[contains(@href,'content/post_')] and .//span[contains(.,'-')]]",
            "//table//tr[.//a[contains(@href,'content/post_')]]",
        ],
        "title_xpath": [
            ".//a[contains(@href,'content/post_')][1]/@title",
            ".//a[contains(@href,'content/post_')][1]/text()",
            ".//a[1]/@title",
            ".//a[1]/text()",
        ],
        "link_xpath": [
            ".//a[contains(@href,'content/post_')][1]/@href",
            ".//a[1]/@href",
        ],
        "date_xpath": [
            ".//span[contains(@class,'time')]/text()",
            ".//span[contains(@class,'date')]/text()",
            ".//span[contains(@class,'f-fr')]/text()",
            ".//span[last()]/text()",
            ".//em/text()",
        ],
    },
    "detail": {
        "title_xpath": [
            "//meta[@name='ArticleTitle']/@content",
            "//h1/text()",
            "//h2/text()",
        ],
        "source_xpath": [
            "//meta[@name='ContentSource']/@content",
            "//span[contains(text(),'信息来源')]/text()",
            "//span[contains(text(),'来源')]/text()",
            "//*[contains(text(),'信息来源')]/text()",
        ],
        "pub_time_xpath": [
            "//meta[@name='PubDate']/@content",
            "//span[contains(text(),'发布时间')]/text()",
            "//*[contains(text(),'发布时间')]/text()",
        ],
        "content_xpath": [
            "//div[@id='content']",
            "//div[@id='ContentRegion']",
            "//div[contains(@class,'articleBox')]",
            "//div[contains(@class,'acontent')]",
            "//div[contains(@class,'detailBox')]",
            "//div[contains(@class,'text-content')]",
            "//div[contains(@class,'content')]",
        ],
        "attachments_xpath": [
            "//a[contains(@class,'doc')]/@href",
            "//*[contains(text(),'附件')]/ancestor::*[1]//a/@href",
            "//a[contains(@href,'.pdf') or contains(@href,'.doc') or contains(@href,'.docx') or contains(@href,'.xls') or contains(@href,'.xlsx') or contains(@href,'.zip')]/@href",
        ],
    },
}


def _is_same_domain(home: str, url: str) -> bool:
    home_host = (urlparse(home).hostname or "").lower()
    target_host = (urlparse(url).hostname or "").lower()
    if not home_host or not target_host:
        return False
    if target_host == home_host:
        return True
    return target_host.endswith("." + home_host)


def _iter_links(home_url: str, html: str) -> Iterable[tuple[str, str]]:
    root = Selector(text=html or "")
    for node in root.xpath("//a[@href]"):
        href = str(node.xpath("./@href").get(default="")).strip()
        text = " ".join([part.strip() for part in node.xpath(".//text()").getall() if part.strip()])
        if not href:
            continue
        full = urljoin(home_url, href)
        if full.startswith("javascript:"):
            continue
        yield full, text


def discover_channel_url(home_url: str, html: str) -> str:
    links = []
    for full_url, text in _iter_links(home_url, html):
        if not _is_same_domain(home_url, full_url):
            continue
        links.append((full_url, text))

    for pattern in PRIORITY_PATTERNS:
        for full_url, text in links:
            hit_text = text or ""
            if pattern.search(full_url) or pattern.search(hit_text):
                return full_url

    for full_url, _ in links:
        if "/index" in full_url or full_url.endswith("/"):
            return full_url
    return home_url


def infer_pagination_pattern(start_url: str) -> str:
    clean = str(start_url or "").strip()
    if not clean:
        return ""
    if clean.endswith("/"):
        return clean + "index_{page}.html"
    if "index.html" in clean:
        return clean.replace("index.html", "index_{page}.html")
    if clean.endswith(".html"):
        return clean.replace(".html", "_index_{page}.html")
    return clean.rstrip("/") + "/index_{page}.html"


def build_rule(site: dict, start_url: str, channel_name: str = "main") -> dict:
    return {
        "site": {
            "code": site["site_code"],
            "name": site["site_name"],
            "base_url": site["base_url"],
            "fetch_mode": "http",
        },
        "channels": {
            channel_name: {
                "start_urls": [start_url],
                "pagination": {
                    "pattern": infer_pagination_pattern(start_url),
                    "start_page": 2,
                },
            }
        },
        "extract": DEFAULT_EXTRACT_RULE,
    }


async def scaffold_one(site_code: str, output_dir: Path, channel_name: str, start_url: str = "") -> Path:
    site = GovSiteRegistry.get_site(site_code=site_code)
    homepage = site["base_url"]
    resolved_start_url = str(start_url or "").strip()

    if not resolved_start_url:
        client = GovClient(timeout_seconds=20.0, retry_times=2, min_interval_seconds=0.0)
        html = await client.get_text(homepage)
        resolved_start_url = discover_channel_url(homepage, html)

    rule = build_rule(site=site, start_url=resolved_start_url, channel_name=channel_name)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{site_code}.yaml"
    output_path.write_text(json.dumps(rule, ensure_ascii=False, indent=2), encoding="utf-8")
    return output_path


async def scaffold_ready_sites(output_dir: Path, channel_name: str) -> list[Path]:
    paths: list[Path] = []
    for site in GovSiteRegistry.list_sites():
        if str(site.get("status") or "").strip().lower() != "ready":
            continue
        paths.append(await scaffold_one(site_code=site["site_code"], output_dir=output_dir, channel_name=channel_name))
    return paths


def main() -> None:
    parser = argparse.ArgumentParser(description="Scaffold gov crawler rule from homepage links")
    parser.add_argument("--site", default="", help="site code in gov sites manifest")
    parser.add_argument("--batch_ready", action="store_true", help="generate rules for all sites marked ready")
    parser.add_argument("--channel", default="main", help="channel key in generated rule")
    parser.add_argument("--start_url", default="", help="override discovered start url")
    parser.add_argument("--output_dir", default="media_platform/gov/rules", help="rule output directory")
    args = parser.parse_args()

    output_dir = Path(args.output_dir).expanduser()
    if not output_dir.is_absolute():
        output_dir = Path.cwd() / output_dir

    if not args.site and not args.batch_ready:
        raise SystemExit("Provide --site <code> or --batch_ready")

    async def _run() -> None:
        if args.batch_ready:
            rows = await scaffold_ready_sites(output_dir=output_dir, channel_name=args.channel)
            for path in rows:
                print(path)
            return
        path = await scaffold_one(
            site_code=args.site,
            output_dir=output_dir,
            channel_name=args.channel,
            start_url=args.start_url,
        )
        print(path)

    asyncio.run(_run())


if __name__ == "__main__":
    main()
