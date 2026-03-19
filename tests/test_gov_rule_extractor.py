# -*- coding: utf-8 -*-
# Copyright (c) 2025 relakkes@gmail.com
#
# This file is part of MediaCrawler project.
# Repository: https://github.com/NanmiCoder/MediaCrawler/blob/main/tests/test_gov_rule_extractor.py
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

from pathlib import Path

from media_platform.gov.core import GovCrawler
from media_platform.gov.extractor import GovExtractor
from media_platform.gov.rule_loader import GovRuleLoader


def _read_fixture(file_name: str) -> str:
    path = Path(__file__).parent / "fixtures" / file_name
    return path.read_text(encoding="utf-8")


def test_gov_rule_loader_loads_szfb_rule():
    loader = GovRuleLoader()
    rule = loader.load_site_rule(site="szfb")
    assert rule["site"]["code"] == "szfb"
    assert "tzgg" in rule["channels"]
    assert rule["extract"]["list"]["item_xpath"]


def test_gov_extract_list_items_with_20_records():
    loader = GovRuleLoader()
    rule = loader.load_site_rule(site="szfb")
    html = _read_fixture("gov_szfb_tzgg_list.html")

    extractor = GovExtractor()
    list_items = extractor.extract_list_items(
        html=html,
        page_url="https://szfb.sz.gov.cn/xwzx/tzgg/index.html",
        list_rule=rule["extract"]["list"],
    )

    assert len(list_items) == 20
    assert list_items[0]["title"] == "标题01"
    assert list_items[0]["publish_time"] == "2026-03-01"
    assert list_items[-1]["url"].endswith("post_10000020.html")


def test_gov_extract_detail_fields_and_attachments():
    loader = GovRuleLoader()
    rule = loader.load_site_rule(site="szfb")
    html = _read_fixture("gov_szfb_tzgg_detail.html")

    extractor = GovExtractor()
    detail = extractor.extract_detail(
        html=html,
        page_url="https://szfb.sz.gov.cn/xwzx/tzgg/content/post_10000001.html",
        detail_rule=rule["extract"]["detail"],
    )

    assert detail["title"] == "2026年3月17日深圳市政府债券发行结果公告"
    assert detail["source"] == "深圳市财政局"
    assert detail["publish_time"] == "2026-03-17 17:21:27"
    assert "这是正文第一段" in detail["content_text"]
    assert detail["attachments"] == [
        "https://szfb.sz.gov.cn/files/test1.pdf",
        "https://szfb.sz.gov.cn/files/test2.docx",
    ]


def test_gov_pagination_url_pattern_generates_second_page():
    loader = GovRuleLoader()
    rule = loader.load_site_rule(site="szfb")
    channel_rule = loader.get_channel_rule(rule, "tzgg")
    urls = GovCrawler._build_list_page_urls(rule=rule, channel_rule=channel_rule, max_pages=2)

    assert len(urls) == 2
    assert urls[1] == "https://szfb.sz.gov.cn/xwzx/tzgg/index_2.html"


def test_gov_extract_list_items_fallback_when_rule_misses():
    html = """
    <html>
      <body>
        <div class="ListconC">
          <span>2026-03-18</span>
          <a href="/xxgk/xxgk/tzgg/content/post_12688325.html" title="测试公告A">测试公告A</a>
        </div>
      </body>
    </html>
    """
    extractor = GovExtractor()
    # Intentionally mismatched xpath to trigger fallback scan.
    list_rule = {
        "item_xpath": ["//ul/li[@class='not-exists']"],
        "title_xpath": [".//a/@title"],
        "link_xpath": [".//a/@href"],
        "date_xpath": [".//span/text()"],
    }
    rows = extractor.extract_list_items(
        html=html,
        page_url="https://www.dpxq.gov.cn/xxgk/xxgk/tzgg/index.html",
        list_rule=list_rule,
    )
    assert len(rows) == 1
    assert rows[0]["title"] == "测试公告A"
    assert rows[0]["url"] == "https://www.dpxq.gov.cn/xxgk/xxgk/tzgg/content/post_12688325.html"
    assert rows[0]["publish_time"] == "2026-03-18"
