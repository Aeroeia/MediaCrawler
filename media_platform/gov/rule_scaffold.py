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
from datetime import datetime
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import urljoin, urlparse

from parsel import Selector

from .client import GovClient
from .rule_loader import GovRuleLoader
from .site_registry import GovSiteRegistry


PRIORITY_PATTERNS = [
    re.compile(r"/tzgg|/gsgg|/wjtz|通知|公告", re.IGNORECASE),
    re.compile(r"/gzdt|/zwdt|动态", re.IGNORECASE),
    re.compile(r"/xxgk|/zwgk", re.IGNORECASE),
]

STANDARD_CHANNEL_ORDER = ["tzgg", "policy", "dynamic"]
STANDARD_CHANNEL_LABELS = {
    "tzgg": "通知公告",
    "policy": "政策文件",
    "dynamic": "工作动态",
}
STANDARD_CHANNEL_PATTERNS = {
    "tzgg": [
        re.compile(r"通知公告|公告公示|公示公告|信息公告|通知通告", re.IGNORECASE),
        re.compile(r"/tzgg|/gsgg|/gggs|/wjtz|/notice", re.IGNORECASE),
    ],
    "policy": [
        re.compile(r"政策文件|政策法规|规范性文件|政策解读", re.IGNORECASE),
        re.compile(r"/zcwj|/zcfg|/fgwj|/zcjd|/gfxwj", re.IGNORECASE),
    ],
    "dynamic": [
        re.compile(r"工作动态|政务动态|部门动态|新闻动态|最新动态", re.IGNORECASE),
        re.compile(r"/gzdt|/zwdt|/xwdt|/news", re.IGNORECASE),
    ],
}
_LIST_HINT_RE = re.compile(r"/index(?:_\d+)?\.html|/list|/xxgk|/zwgk|/gkml", re.IGNORECASE)
_DETAIL_HINT_RE = re.compile(
    r"/content/post_|/art/\d+|/article/|/detail|[?&](?:id|articleid|contentid)=",
    re.IGNORECASE,
)
_BINARY_HINT_RE = re.compile(r"\.(?:pdf|doc|docx|xls|xlsx|zip|rar)(?:\?|$)", re.IGNORECASE)


@dataclass
class ChannelCandidate:
    channel: str
    url: str
    text: str
    score: float


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


def _is_list_like_url(url: str) -> bool:
    value = str(url or "").strip().lower()
    if not value:
        return False
    if _DETAIL_HINT_RE.search(value):
        return False
    if _BINARY_HINT_RE.search(value):
        return False
    if _LIST_HINT_RE.search(value):
        return True
    return value.endswith("/") or value.endswith(".html")


def _score_candidate(channel: str, url: str, text: str) -> float:
    score = 0.0
    text_norm = str(text or "").strip()
    url_norm = str(url or "").strip()
    for pattern in STANDARD_CHANNEL_PATTERNS.get(channel, []):
        if pattern.search(text_norm):
            score += 65.0
        if pattern.search(url_norm):
            score += 50.0

    if _BINARY_HINT_RE.search(url_norm):
        score -= 120.0
    if _DETAIL_HINT_RE.search(url_norm):
        score -= 55.0
    if _is_list_like_url(url_norm):
        score += 18.0
    if "index" in url_norm:
        score += 6.0
    if text_norm and len(text_norm) <= 18:
        score += 4.0
    if not text_norm:
        score -= 6.0
    return score


def discover_standard_channels(home_url: str, html: str) -> dict[str, dict[str, Any]]:
    best: dict[str, ChannelCandidate] = {}
    links = list(_iter_links(home_url, html))
    for full_url, text in links:
        if not _is_same_domain(home_url, full_url):
            continue
        for channel in STANDARD_CHANNEL_ORDER:
            score = _score_candidate(channel=channel, url=full_url, text=text)
            if score < 55.0:
                continue
            current = best.get(channel)
            candidate = ChannelCandidate(channel=channel, url=full_url, text=text, score=score)
            if not current:
                best[channel] = candidate
                continue
            # Prefer higher score and "list-like" urls.
            current_is_list = _is_list_like_url(current.url)
            cand_is_list = _is_list_like_url(candidate.url)
            if candidate.score > current.score + 0.01:
                best[channel] = candidate
            elif abs(candidate.score - current.score) <= 0.01 and cand_is_list and not current_is_list:
                best[channel] = candidate

    # Backward-compatible fallback for notice-like channel.
    if "tzgg" not in best:
        fallback_url = discover_channel_url(home_url, html)
        if fallback_url and fallback_url != home_url and _is_list_like_url(fallback_url):
            best["tzgg"] = ChannelCandidate(
                channel="tzgg",
                url=fallback_url,
                text="",
                score=56.0,
            )

    return {
        key: {
            "url": row.url,
            "label": STANDARD_CHANNEL_LABELS.get(key, key),
            "text": row.text,
            "score": round(row.score, 2),
        }
        for key, row in best.items()
    }


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


def _derive_start_url_from_pagination(pattern: str) -> str:
    text = str(pattern or "").strip()
    if not text:
        return ""
    candidate = text.replace("_{page}", "").replace("{page}", "1")
    candidate = candidate.replace("index_1.html", "index.html")
    candidate = candidate.replace("list_1.", "list.")
    return candidate if _is_list_like_url(candidate) else ""


def _recover_list_url_from_detail(url: str) -> str:
    value = str(url or "").strip()
    if not value:
        return ""
    if "/content/post_" in value:
        return value.split("/content/post_", 1)[0].rstrip("/") + "/index.html"
    if "/article/article/toArticleDetails/" in value:
        return value.split("/article/article/toArticleDetails/", 1)[0].rstrip("/") + "/index.html"
    if "/content/" in value:
        return value.split("/content/", 1)[0].rstrip("/") + "/index.html"
    return ""


def _build_channel_rule(
    channel_key: str,
    start_url: str,
    existing: dict[str, Any] | None = None,
    *,
    label: str = "",
    compat_alias: bool = False,
) -> dict[str, Any]:
    existing = existing or {}
    pagination = existing.get("pagination") if isinstance(existing, dict) else {}
    pagination = pagination if isinstance(pagination, dict) else {}
    pattern = str(pagination.get("pattern") or "").strip() or infer_pagination_pattern(start_url)
    if "{page}" not in pattern or not _derive_start_url_from_pagination(pattern):
        pattern = infer_pagination_pattern(start_url)
    if not _is_list_like_url(start_url):
        recovered = _derive_start_url_from_pagination(pattern)
        if recovered:
            start_url = recovered
    if not _is_list_like_url(start_url):
        recovered = _recover_list_url_from_detail(start_url)
        if recovered:
            start_url = recovered
    start_page = max(2, int(pagination.get("start_page") or 2))
    output = {
        "label": label or STANDARD_CHANNEL_LABELS.get(channel_key, channel_key),
        "start_urls": [start_url],
        "pagination": {
            "pattern": pattern,
            "start_page": start_page,
        },
    }
    if compat_alias:
        output["compat_alias"] = True
    return output


def build_rule(site: dict, start_url: str, channel_name: str = "main", channels: dict[str, Any] | None = None) -> dict:
    channel_rows = channels if isinstance(channels, dict) and channels else {
        channel_name: _build_channel_rule(channel_name, start_url)
    }
    return {
        "site": {
            "code": site["site_code"],
            "name": site["site_name"],
            "base_url": site["base_url"],
            "fetch_mode": "http",
        },
        "channels": channel_rows,
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


def _first_start_url(channel_rule: Any) -> str:
    if not isinstance(channel_rule, dict):
        return ""
    start_urls = channel_rule.get("start_urls") or []
    if not isinstance(start_urls, list):
        return ""
    for row in start_urls:
        url = str(row or "").strip()
        if url:
            return url
    return ""


def enrich_rule_with_standard_channels(
    rule: dict[str, Any],
    discovered_channels: dict[str, dict[str, Any]],
) -> tuple[dict[str, Any], dict[str, Any]]:
    site = rule.setdefault("site", {})
    existing_channels = rule.get("channels") or {}
    if not isinstance(existing_channels, dict):
        existing_channels = {}

    custom_channels: dict[str, Any] = {
        str(key): value
        for key, value in existing_channels.items()
        if str(key) not in set(STANDARD_CHANNEL_ORDER + ["main"])
    }
    standard_channels: dict[str, Any] = {}
    available_standard: list[str] = []
    missing_standard: list[str] = []
    existing_main = existing_channels.get("main") if isinstance(existing_channels.get("main"), dict) else {}
    existing_main_url = _first_start_url(existing_main)
    if existing_main_url and not _is_list_like_url(existing_main_url):
        existing_main_url = _derive_start_url_from_pagination(
            str((existing_main.get("pagination") or {}).get("pattern") or "")
        ) or existing_main_url

    for key in STANDARD_CHANNEL_ORDER:
        existing_rule = existing_channels.get(key)
        discovered_url = str((discovered_channels.get(key) or {}).get("url") or "").strip()
        if discovered_url and not _is_list_like_url(discovered_url):
            discovered_url = ""
        existing_url = _first_start_url(existing_rule)
        selected_url = discovered_url or existing_url
        if not selected_url and key == "tzgg" and existing_main_url:
            selected_url = existing_main_url
        if selected_url and not _is_list_like_url(selected_url):
            existing_pattern = str(((existing_rule or {}).get("pagination") or {}).get("pattern") or "")
            selected_url = _derive_start_url_from_pagination(existing_pattern) or selected_url
        if selected_url and not _is_list_like_url(selected_url):
            selected_url = _recover_list_url_from_detail(selected_url) or selected_url
        if selected_url and not _is_list_like_url(selected_url):
            if key == "tzgg" and existing_main_url and _is_list_like_url(existing_main_url):
                selected_url = existing_main_url
            else:
                selected_url = ""
        if not selected_url:
            missing_standard.append(key)
            continue
        standard_channels[key] = _build_channel_rule(
            channel_key=key,
            start_url=selected_url,
            existing=existing_rule if isinstance(existing_rule, dict) else None,
            label=STANDARD_CHANNEL_LABELS.get(key, key),
            compat_alias=False,
        )
        available_standard.append(key)

    default_standard = available_standard[0] if available_standard else ""
    if not default_standard:
        for key in STANDARD_CHANNEL_ORDER:
            if key in custom_channels:
                default_standard = key
                break
    if not default_standard:
        default_standard = "main"

    main_url = ""
    if default_standard in standard_channels:
        main_url = _first_start_url(standard_channels.get(default_standard))
    if not main_url:
        main_url = _first_start_url(existing_main)
        if main_url and not _is_list_like_url(main_url):
            recovered_main = _derive_start_url_from_pagination(
                str((existing_main.get("pagination") or {}).get("pattern") or "")
            )
            if recovered_main:
                main_url = recovered_main
    if not main_url:
        for value in standard_channels.values():
            main_url = _first_start_url(value)
            if main_url:
                break
    if not main_url:
        main_url = str(site.get("base_url") or "").strip()

    main_channel = _build_channel_rule(
        channel_key="main",
        start_url=main_url,
        existing=existing_main,
        label="兼容入口(main)",
        compat_alias=True,
    )

    final_channels: dict[str, Any] = {}
    for key in STANDARD_CHANNEL_ORDER:
        if key in standard_channels:
            final_channels[key] = standard_channels[key]
    for key, value in custom_channels.items():
        if key in final_channels or key == "main":
            continue
        final_channels[key] = value
    final_channels["main"] = main_channel
    rule["channels"] = final_channels
    site["default_channel"] = default_standard

    report_row = {
        "available_standard_channels": available_standard,
        "missing_standard_channels": missing_standard,
        "default_standard_channel": default_standard,
        "compat_main_url": main_url,
    }
    return rule, report_row


async def extend_site_rule_multichannel(
    site_code: str,
    rules_dir: Path,
    manifest_path: str = "",
) -> dict[str, Any]:
    site = GovSiteRegistry.get_site(site_code=site_code, manifest_path=manifest_path)
    loader = GovRuleLoader()

    try:
        rule_path = loader._resolve_rule_path(site=site_code, custom_rule_path=str(rules_dir))
    except Exception:
        rule_path = await scaffold_one(site_code=site_code, output_dir=rules_dir, channel_name="main")

    rule = loader.load_site_rule(site=site_code, custom_rule_path=str(rules_dir))
    discovered: dict[str, dict[str, Any]] = {}
    error = ""
    try:
        client = GovClient(timeout_seconds=20.0, retry_times=2, min_interval_seconds=0.0)
        html = await client.get_text(str(site.get("base_url") or ""))
        discovered = discover_standard_channels(home_url=str(site.get("base_url") or ""), html=html)
    except Exception as exc:
        error = str(exc)

    merged_rule, channel_report = enrich_rule_with_standard_channels(rule=rule, discovered_channels=discovered)
    rule_path.write_text(json.dumps(merged_rule, ensure_ascii=False, indent=2), encoding="utf-8")

    return {
        "site_code": site_code,
        "site_name": str(site.get("site_name") or ""),
        "base_url": str(site.get("base_url") or ""),
        "rule_path": str(rule_path),
        "discovered_channels": discovered,
        **channel_report,
        "error": error,
    }


async def extend_manifest_rules_multichannel(
    manifest_path: str,
    rules_dir: Path,
    report_out: Path | None = None,
) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    sites = GovSiteRegistry.list_sites(manifest_path=manifest_path)
    for site in sites:
        code = str(site.get("site_code") or "").strip()
        if not code:
            continue
        rows.append(await extend_site_rule_multichannel(site_code=code, rules_dir=rules_dir, manifest_path=manifest_path))

    summary = {
        "total_sites": len(rows),
        "sites_with_3_standard_channels": len([r for r in rows if len(r.get("available_standard_channels") or []) == 3]),
        "sites_with_2_standard_channels": len([r for r in rows if len(r.get("available_standard_channels") or []) == 2]),
        "sites_with_1_standard_channels": len([r for r in rows if len(r.get("available_standard_channels") or []) == 1]),
        "sites_with_0_standard_channels": len([r for r in rows if len(r.get("available_standard_channels") or []) == 0]),
        "sites_with_discovery_error": len([r for r in rows if str(r.get("error") or "").strip()]),
    }
    report = {
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "summary": summary,
        "rows": rows,
    }
    if report_out:
        report_out.parent.mkdir(parents=True, exist_ok=True)
        report_out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Scaffold gov crawler rule from homepage links")
    parser.add_argument("--site", default="", help="site code in gov sites manifest")
    parser.add_argument("--batch_ready", action="store_true", help="generate rules for all sites marked ready")
    parser.add_argument(
        "--batch_extend_multichannel",
        action="store_true",
        help="backfill existing rules with standard channels (tzgg/policy/dynamic) + main compatibility alias",
    )
    parser.add_argument("--channel", default="main", help="channel key in generated rule")
    parser.add_argument("--start_url", default="", help="override discovered start url")
    parser.add_argument("--output_dir", default="media_platform/gov/rules", help="rule output directory")
    parser.add_argument("--manifest", default="media_platform/gov/sites_manifest.json", help="gov manifest path")
    parser.add_argument(
        "--report_out",
        default=f"data/gov/multichannel_backfill_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
        help="output report path for --batch_extend_multichannel",
    )
    args = parser.parse_args()

    output_dir = Path(args.output_dir).expanduser()
    if not output_dir.is_absolute():
        output_dir = Path.cwd() / output_dir
    manifest_path = Path(args.manifest).expanduser()
    if not manifest_path.is_absolute():
        manifest_path = Path.cwd() / manifest_path
    report_out = Path(args.report_out).expanduser()
    if not report_out.is_absolute():
        report_out = Path.cwd() / report_out

    if not args.site and not args.batch_ready and not args.batch_extend_multichannel:
        raise SystemExit("Provide --site <code> or --batch_ready or --batch_extend_multichannel")

    async def _run() -> None:
        if args.batch_extend_multichannel:
            report = await extend_manifest_rules_multichannel(
                manifest_path=str(manifest_path),
                rules_dir=output_dir,
                report_out=report_out,
            )
            print(report_out)
            print(json.dumps(report.get("summary") or {}, ensure_ascii=False))
            return
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
