# -*- coding: utf-8 -*-
# Copyright (c) 2025 relakkes@gmail.com
#
# This file is part of MediaCrawler project.
# Repository: https://github.com/NanmiCoder/MediaCrawler/blob/main/tests/test_gov_registry_scaffold.py
# GitHub: https://github.com/NanmiCoder
# Licensed under NON-COMMERCIAL LEARNING LICENSE 1.1
#

from media_platform.gov.rule_scaffold import (
    discover_channel_url,
    discover_standard_channels,
    enrich_rule_with_standard_channels,
    infer_pagination_pattern,
)
from media_platform.gov.site_registry import GovSiteRegistry


def test_gov_site_registry_has_site_status_and_verify_fields():
    zfcg = GovSiteRegistry.get_site("zfcg")
    assert zfcg["status"] == "ready"
    assert zfcg["default_channel"] == "main"
    assert "verify_error" in zfcg
    assert "verified_mode" in zfcg

    gdzwfw = GovSiteRegistry.get_site("gdzwfw")
    assert gdzwfw["status"] in {"ready", "blocked", "pending_dynamic"}


def test_discover_channel_url_prefers_notice_like_link():
    home = "https://example.gov.cn/"
    html = """
    <html><body>
      <a href="/xxgk/index.html">信息公开</a>
      <a href="/xxgk/qt/tzgg/index.html">通知公告</a>
      <a href="https://other.example.com/a.html">外链</a>
    </body></html>
    """
    discovered = discover_channel_url(home, html)
    assert discovered == "https://example.gov.cn/xxgk/qt/tzgg/index.html"


def test_infer_pagination_pattern_from_index_url():
    assert (
        infer_pagination_pattern("https://example.gov.cn/xxgk/tzgg/index.html")
        == "https://example.gov.cn/xxgk/tzgg/index_{page}.html"
    )


def test_discover_standard_channels_returns_three_keys():
    html = """
    <html><body>
      <a href="/xxgk/tzgg/index.html">通知公告</a>
      <a href="/xxgk/zcfg/index.html">政策法规</a>
      <a href="/xxgk/gzdt/index.html">工作动态</a>
    </body></html>
    """
    channels = discover_standard_channels("https://example.gov.cn/", html)
    assert set(channels.keys()) == {"tzgg", "policy", "dynamic"}
    assert channels["tzgg"]["url"] == "https://example.gov.cn/xxgk/tzgg/index.html"
    assert channels["policy"]["url"] == "https://example.gov.cn/xxgk/zcfg/index.html"
    assert channels["dynamic"]["url"] == "https://example.gov.cn/xxgk/gzdt/index.html"


def test_enrich_rule_with_standard_channels_keeps_main_compat_alias():
    rule = {
        "site": {"code": "demo", "name": "Demo", "base_url": "https://example.gov.cn/"},
        "channels": {
            "main": {
                "start_urls": ["https://example.gov.cn/old/main/index.html"],
                "pagination": {"pattern": "https://example.gov.cn/old/main/index_{page}.html", "start_page": 2},
            }
        },
        "extract": {"list": {"item_xpath": "//ul/li"}, "detail": {"title_xpath": "//h1"}},
    }
    discovered = {
        "tzgg": {"url": "https://example.gov.cn/xxgk/tzgg/index.html"},
        "policy": {"url": "https://example.gov.cn/xxgk/zcfg/index.html"},
        "dynamic": {"url": "https://example.gov.cn/xxgk/gzdt/index.html"},
    }
    merged, report = enrich_rule_with_standard_channels(rule=rule, discovered_channels=discovered)
    assert report["default_standard_channel"] == "tzgg"
    assert set(report["available_standard_channels"]) == {"tzgg", "policy", "dynamic"}
    assert merged["channels"]["main"]["compat_alias"] is True
    assert merged["channels"]["main"]["start_urls"][0] == "https://example.gov.cn/xxgk/tzgg/index.html"
