# -*- coding: utf-8 -*-
# Copyright (c) 2025 relakkes@gmail.com
#
# This file is part of MediaCrawler project.
# Repository: https://github.com/NanmiCoder/MediaCrawler/blob/main/tests/test_gov_registry_scaffold.py
# GitHub: https://github.com/NanmiCoder
# Licensed under NON-COMMERCIAL LEARNING LICENSE 1.1
#

from media_platform.gov.rule_scaffold import discover_channel_url, infer_pagination_pattern
from media_platform.gov.site_registry import GovSiteRegistry


def test_gov_site_registry_has_ready_and_pending_sites():
    zfcg = GovSiteRegistry.get_site("zfcg")
    assert zfcg["status"] == "ready"
    assert zfcg["default_channel"] == "main"

    gdzwfw = GovSiteRegistry.get_site("gdzwfw")
    assert gdzwfw["status"] == "pending_dynamic"


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
