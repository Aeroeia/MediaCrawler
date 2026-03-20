# -*- coding: utf-8 -*-
# Copyright (c) 2025 relakkes@gmail.com
#
# This file is part of MediaCrawler project.
# Repository: https://github.com/NanmiCoder/MediaCrawler/blob/main/tests/test_gov_api_channels.py
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

import pytest

from api.main import get_gov_channels
from media_platform.gov.rule_loader import GovRuleLoader
from media_platform.gov.site_registry import GovSiteRegistry


@pytest.mark.asyncio
async def test_get_gov_channels_hides_main_compat_alias_by_default(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(
        GovSiteRegistry,
        "get_site",
        staticmethod(
            lambda site_code: {
                "site_code": site_code,
                "default_channel": "main",
                "status": "ready",
            }
        ),
    )
    monkeypatch.setattr(
        GovRuleLoader,
        "load_site_rule",
        lambda self, site: {
            "channels": {
                "tzgg": {"label": "通知公告", "start_urls": ["https://example.gov.cn/tzgg/index.html"]},
                "main": {"label": "兼容入口(main)", "compat_alias": True, "start_urls": ["https://example.gov.cn/tzgg/index.html"]},
            }
        },
    )
    payload = await get_gov_channels(site="demo", include_compat=False)
    values = [row["value"] for row in payload["channels"]]
    assert "main" not in values
    assert values == ["tzgg"]
    assert payload["raw_default_channel"] == "main"
    assert payload["default_channel"] == "tzgg"


@pytest.mark.asyncio
async def test_get_gov_channels_can_include_main_compat_alias(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(
        GovSiteRegistry,
        "get_site",
        staticmethod(
            lambda site_code: {
                "site_code": site_code,
                "default_channel": "main",
                "status": "ready",
            }
        ),
    )
    monkeypatch.setattr(
        GovRuleLoader,
        "load_site_rule",
        lambda self, site: {
            "channels": {
                "tzgg": {"label": "通知公告", "start_urls": ["https://example.gov.cn/tzgg/index.html"]},
                "main": {"label": "兼容入口(main)", "compat_alias": True, "start_urls": ["https://example.gov.cn/tzgg/index.html"]},
            }
        },
    )
    payload = await get_gov_channels(site="demo", include_compat=True)
    values = [row["value"] for row in payload["channels"]]
    assert "main" in values
