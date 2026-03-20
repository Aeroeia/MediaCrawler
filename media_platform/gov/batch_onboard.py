# -*- coding: utf-8 -*-
# Copyright (c) 2025 relakkes@gmail.com
#
# This file is part of MediaCrawler project.
# Repository: https://github.com/NanmiCoder/MediaCrawler/blob/main/media_platform/gov/batch_onboard.py
# GitHub: https://github.com/NanmiCoder
# Licensed under NON-COMMERCIAL LEARNING LICENSE 1.1
#

from __future__ import annotations

import argparse
import asyncio
import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from tools import utils

from .core import GovCrawler
from .extractor import GovExtractor
from .fetcher import GovBrowserFetcher, GovHttpFetcher
from .rule_loader import GovRuleLoader
from .rule_scaffold import build_rule, scaffold_one
from .site_registry import GovSiteRegistry


@dataclass
class VerifyResult:
    site_code: str
    status: str
    verified_mode: str
    list_count: int
    detail_attempt: int
    detail_success: int
    verify_success_rate: float
    verify_error_code: str
    verify_error: str
    report_row: dict[str, Any]


def classify_error(text: str) -> str:
    msg = str(text or "").lower()
    if "timed out" in msg or "timeout" in msg:
        return "timeout"
    if "403" in msg or "forbidden" in msg:
        return "http_403"
    if "404" in msg:
        return "http_404"
    if "429" in msg:
        return "http_429"
    if "captcha" in msg or "验证码" in msg:
        return "captcha"
    if "ssl" in msg or "certificate" in msg:
        return "ssl_error"
    if "connection" in msg or "connect" in msg:
        return "connection_error"
    return "unknown_error"


def _rule_path(site_code: str, rules_dir: Path) -> Path:
    return rules_dir / f"{site_code}.yaml"


async def _ensure_rule(site_code: str, rules_dir: Path, channel_name: str) -> Path:
    path = _rule_path(site_code, rules_dir)
    if path.exists():
        return path
    try:
        await scaffold_one(site_code=site_code, output_dir=rules_dir, channel_name=channel_name)
    except Exception as exc:
        site = GovSiteRegistry.get_site(site_code=site_code)
        fallback_rule = build_rule(
            site={
                "site_code": site["site_code"],
                "site_name": site["site_name"],
                "base_url": site["base_url"],
            },
            start_url=site["base_url"],
            channel_name=channel_name,
        )
        path.write_text(json.dumps(fallback_rule, ensure_ascii=False, indent=2), encoding="utf-8")
        utils.logger.warning(
            "[gov-batch] scaffold failed, fallback rule generated for site=%s err=%s",
            site_code,
            exc,
        )
    return path


def _set_rule_fetch_mode(rule_path: Path, mode: str) -> None:
    payload = json.loads(rule_path.read_text(encoding="utf-8"))
    site = payload.setdefault("site", {})
    site["fetch_mode"] = mode
    if mode == "browser":
        browser_cfg = site.setdefault("browser", {})
        browser_cfg.setdefault("wait_until", "domcontentloaded")
        browser_cfg.setdefault("timeout_ms", 30000)
        browser_cfg.setdefault("scroll_times", 1)
    rule_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _validate_detail(min_record: dict[str, Any]) -> bool:
    title = str(min_record.get("title") or "").strip()
    url = str(min_record.get("url") or "").strip()
    publish_time = str(min_record.get("publish_time") or "").strip()
    return bool(title and url and publish_time)


def _extract_rows_for_page(
    extractor: GovExtractor,
    rule: dict[str, Any],
    html: str,
    page_url: str,
) -> list[dict[str, Any]]:
    extract_rule = rule.get("extract") or {}
    list_rows = extractor.extract_list_items(html=html, page_url=page_url, list_rule=extract_rule.get("list") or {})
    if list_rows:
        return list_rows
    site_cfg = rule.get("site") or {}
    if not bool(site_cfg.get("allow_inline_detail")):
        return []
    inline_rule = extract_rule.get("inline_list") or {}
    if not isinstance(inline_rule, dict):
        return []
    return extractor.extract_inline_list_items(html=html, page_url=page_url, inline_rule=inline_rule)


async def _verify_once(
    rule: dict[str, Any],
    channel_name: str,
    mode: str,
    max_pages: int,
    detail_sample: int,
    min_interval_seconds: float,
) -> tuple[int, int, int, str]:
    site = rule.get("site") or {}
    channel_rule = GovRuleLoader.get_channel_rule(rule, channel_name)
    page_urls = GovCrawler._build_list_page_urls(rule=rule, channel_rule=channel_rule, max_pages=max_pages)
    extractor = GovExtractor()
    browser_cfg = dict(site.get("browser") or {})
    if mode == "browser":
        fetcher = GovBrowserFetcher(
            timeout_seconds=max(10.0, float(browser_cfg.get("timeout_ms") or 30000) / 1000.0),
            retry_times=2,
            min_interval_seconds=min_interval_seconds,
            page_cfg=browser_cfg,
            headless=True,
        )
    else:
        fetcher = GovHttpFetcher(
            timeout_seconds=20.0,
            retry_times=2,
            min_interval_seconds=min_interval_seconds,
        )

    list_count = 0
    detail_success = 0
    verify_error = ""
    seen: set[str] = set()
    details: list[dict[str, str]] = []
    await fetcher.start()
    try:
        for page_url in page_urls:
            html = await fetcher.get_text(page_url, page_cfg=browser_cfg)
            rows = _extract_rows_for_page(extractor=extractor, rule=rule, html=html, page_url=page_url)
            list_count += len(rows)
            for row in rows:
                url = str(row.get("url") or "").strip()
                if not url or url in seen:
                    continue
                seen.add(url)
                details.append(row)
    except Exception as exc:
        verify_error = classify_error(str(exc)) + ": " + str(exc)

    detail_attempt = min(max(0, int(detail_sample)), len(details))
    if not verify_error and detail_attempt > 0:
        try:
            for row in details[:detail_attempt]:
                detail_url = str(row.get("url") or "").strip()
                inline_mode = str(row.get("inline_mode") or "").strip().lower() in {"1", "true", "yes"}
                if inline_mode:
                    detail = {
                        "title": str(row.get("title") or "").strip(),
                        "source": str(row.get("source") or "").strip(),
                        "publish_time": str(row.get("publish_time") or "").strip(),
                        "content_html": str(row.get("content_html") or "").strip(),
                        "content_text": str(row.get("content_text") or "").strip(),
                        "attachments": [],
                    }
                else:
                    html = await fetcher.get_text(detail_url, page_cfg=browser_cfg)
                    detail = extractor.extract_detail(
                        html=html,
                        page_url=detail_url,
                        detail_rule=rule["extract"]["detail"],
                    )
                record = GovCrawler._normalize_record(
                    rule=rule,
                    channel=channel_name,
                    list_item=row,
                    detail_item=detail,
                    url=detail_url,
                )
                if _validate_detail(record):
                    detail_success += 1
        except Exception as exc:
            verify_error = classify_error(str(exc)) + ": " + str(exc)

    await fetcher.close()
    return list_count, detail_attempt, detail_success, verify_error


def _iter_verify_channels(rule: dict[str, Any]) -> list[str]:
    channels = rule.get("channels") or {}
    if not isinstance(channels, dict):
        return []
    rows: list[str] = []
    for channel_name in sorted(channels.keys()):
        cfg = channels.get(channel_name) or {}
        if not isinstance(cfg, dict):
            cfg = {}
        if bool(cfg.get("compat_alias")):
            continue
        if not cfg.get("start_urls"):
            continue
        rows.append(str(channel_name))
    if rows:
        return rows
    if "main" in channels:
        return ["main"]
    return []


async def _verify_site_by_mode(
    rule: dict[str, Any],
    channel_names: list[str],
    mode: str,
    max_pages: int,
    detail_sample: int,
    min_interval_seconds: float,
) -> tuple[list[dict[str, Any]], int, int, int, str]:
    results: list[dict[str, Any]] = []
    total_list_count = 0
    total_detail_attempt = 0
    total_detail_success = 0
    first_error = ""

    for channel_name in channel_names:
        list_count, detail_attempt, detail_success, verify_error = await _verify_once(
            rule=rule,
            channel_name=channel_name,
            mode=mode,
            max_pages=max_pages,
            detail_sample=detail_sample,
            min_interval_seconds=min_interval_seconds,
        )
        total_list_count += int(list_count)
        total_detail_attempt += int(detail_attempt)
        total_detail_success += int(detail_success)
        if verify_error and not first_error:
            first_error = verify_error
        results.append(
            {
                "channel": channel_name,
                "list_count": int(list_count),
                "detail_attempt": int(detail_attempt),
                "detail_success": int(detail_success),
                "verify_success_rate": round((float(detail_success) / float(detail_attempt)) if detail_attempt > 0 else 0.0, 4),
                "verify_error": verify_error,
                "verify_error_code": verify_error.split(":", 1)[0].strip() if verify_error else "",
            }
        )

    return results, total_list_count, total_detail_attempt, total_detail_success, first_error


async def verify_site(
    site: dict[str, Any],
    loader: GovRuleLoader,
    rules_dir: Path,
    max_pages: int,
    detail_sample: int,
    min_interval_seconds: float,
) -> VerifyResult:
    site_code = str(site.get("site_code") or "")
    rule_path = await _ensure_rule(site_code=site_code, rules_dir=rules_dir, channel_name="main")
    rule = loader.load_site_rule(site=site_code, custom_rule_path=str(rules_dir))
    channel_names = _iter_verify_channels(rule)
    if not channel_names:
        raise ValueError(f"[gov-batch] site={site_code} has no valid channels to verify")
    mode = str((rule.get("site") or {}).get("fetch_mode") or "http").strip().lower()

    channel_results, list_count, detail_attempt, detail_success, verify_error = await _verify_site_by_mode(
        rule=rule,
        channel_names=channel_names,
        mode=mode,
        max_pages=max_pages,
        detail_sample=detail_sample,
        min_interval_seconds=min_interval_seconds,
    )
    success = detail_success > 0 and list_count > 0

    if (verify_error or not success) and mode != "browser":
        channel_results2, list_count2, detail_attempt2, detail_success2, verify_error2 = await _verify_site_by_mode(
            rule=rule,
            channel_names=channel_names,
            mode="browser",
            max_pages=max_pages,
            detail_sample=detail_sample,
            min_interval_seconds=min_interval_seconds,
        )
        if detail_success2 > detail_success:
            mode = "browser"
            channel_results = channel_results2
            list_count, detail_attempt, detail_success, verify_error = (list_count2, detail_attempt2, detail_success2, verify_error2)
            _set_rule_fetch_mode(rule_path, "browser")
            success = detail_success > 0 and list_count > 0

    success = detail_success > 0 and list_count > 0
    if success:
        status = "ready"
        verify_error = ""
    else:
        status = "blocked"
        if not verify_error:
            if list_count <= 0:
                verify_error = "no_list_items: list extraction returned 0 items"
            elif detail_attempt <= 0:
                verify_error = "no_detail_candidates: list extracted items but no valid detail urls"
            elif detail_success <= 0:
                verify_error = "detail_extract_failed: detail extraction failed for sampled urls"
            else:
                verify_error = "verify_failed: unknown verification failure"
    verify_success_rate = (float(detail_success) / float(detail_attempt)) if detail_attempt > 0 else 0.0
    verify_error_code = verify_error.split(":", 1)[0].strip() if verify_error else ""

    return VerifyResult(
        site_code=site_code,
        status=status,
        verified_mode=mode,
        list_count=list_count,
        detail_attempt=detail_attempt,
        detail_success=detail_success,
        verify_success_rate=round(verify_success_rate, 4),
        verify_error_code=verify_error_code,
        verify_error=verify_error,
        report_row={
            "site_code": site_code,
            "site_name": str(site.get("site_name") or ""),
            "base_url": str(site.get("base_url") or ""),
            "status": status,
            "verified_mode": mode,
            "channel_count": len(channel_names),
            "channels_verified": channel_names,
            "channel_results": channel_results,
            "list_count": list_count,
            "detail_attempt": detail_attempt,
            "detail_success": detail_success,
            "verify_success_rate": round(verify_success_rate, 4),
            "verify_error_code": verify_error_code,
            "verify_error": verify_error,
            "last_verified_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        },
    )


async def run_batch(args: argparse.Namespace) -> dict[str, Any]:
    manifest_path = Path(args.manifest).expanduser()
    if not manifest_path.is_absolute():
        manifest_path = Path.cwd() / manifest_path
    rules_dir = Path(args.rules_dir).expanduser()
    if not rules_dir.is_absolute():
        rules_dir = Path.cwd() / rules_dir
    rules_dir.mkdir(parents=True, exist_ok=True)

    sites = GovSiteRegistry.list_sites(str(manifest_path))
    selected_sites = [str(code).strip() for code in str(getattr(args, "sites", "") or "").split(",") if str(code).strip()]
    if selected_sites:
        selected_set = set(selected_sites)
        sites = [site for site in sites if str(site.get("site_code") or "") in selected_set]
    if bool(getattr(args, "exclude_ready", False)):
        sites = [site for site in sites if str(site.get("status") or "").strip().lower() != "ready"]
    loader = GovRuleLoader()
    report_rows: list[dict[str, Any]] = []
    updates: dict[str, dict[str, Any]] = {}

    for site in sites:
        code = str(site.get("site_code") or "")
        utils.logger.info("[gov-batch] verifying site=%s", code)
        try:
            result = await verify_site(
                site=site,
                loader=loader,
                rules_dir=rules_dir,
                max_pages=max(1, int(args.max_pages)),
                detail_sample=max(1, int(args.detail_sample)),
                min_interval_seconds=float(args.sleep_sec),
            )
            report_rows.append(result.report_row)
            updates[code] = {
                "status": result.status,
                "verified_mode": result.verified_mode,
                "verify_error": result.verify_error,
                "last_verified_at": result.report_row["last_verified_at"],
                "verify_success_rate": result.verify_success_rate,
            }
        except Exception as exc:
            err = classify_error(str(exc)) + ": " + str(exc)
            err_code = err.split(":", 1)[0].strip() if err else ""
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            status = "blocked"
            report_rows.append(
                {
                    "site_code": code,
                    "site_name": str(site.get("site_name") or ""),
                    "base_url": str(site.get("base_url") or ""),
                    "status": status,
                    "verified_mode": "",
                    "list_count": 0,
                    "detail_attempt": 0,
                    "detail_success": 0,
                    "verify_success_rate": 0.0,
                    "verify_error_code": err_code,
                    "verify_error": err,
                    "last_verified_at": now,
                }
            )
            updates[code] = {
                "status": status,
                "verified_mode": "",
                "verify_error": err,
                "last_verified_at": now,
                "verify_success_rate": 0.0,
            }

    GovSiteRegistry.update_sites(updates=updates, manifest_path=str(manifest_path))

    summary = {
        "total": len(report_rows),
        "ready": len([row for row in report_rows if row.get("status") == "ready"]),
        "blocked": len([row for row in report_rows if row.get("status") == "blocked"]),
    }
    report = {
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "summary": summary,
        "rows": report_rows,
    }
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Gov batch onboard + smoke verify")
    parser.add_argument("--manifest", default="media_platform/gov/sites_manifest.json")
    parser.add_argument("--rules_dir", default="media_platform/gov/rules")
    parser.add_argument("--max_pages", default=1, type=int)
    parser.add_argument("--detail_sample", default=3, type=int)
    parser.add_argument("--sleep_sec", default=1.0, type=float)
    parser.add_argument("--sites", default="", help="comma-separated site codes for partial run")
    parser.add_argument("--exclude_ready", action="store_true", help="skip sites already marked ready")
    parser.add_argument(
        "--report",
        default=f"data/gov/onboard_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
    )
    args = parser.parse_args()

    report = asyncio.run(run_batch(args))
    output_path = Path(args.report).expanduser()
    if not output_path.is_absolute():
        output_path = Path.cwd() / output_path
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(output_path)


if __name__ == "__main__":
    main()
