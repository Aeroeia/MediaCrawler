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

import json
from pathlib import Path

from media_platform.gov.core import GovCrawler
from media_platform.gov.extractor import GovExtractor
from media_platform.gov.fetcher import GovBrowserFetcher, GovHttpFetcher
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


def test_gov_rule_loader_accepts_browser_fetch_mode(tmp_path):
    rule = {
        "site": {
            "code": "tmpgov",
            "base_url": "https://example.gov.cn",
            "fetch_mode": "browser",
            "allow_inline_detail": True,
            "browser": {
                "wait_until": "domcontentloaded",
                "timeout_ms": 20000,
                "scroll_times": 1,
                "actions": [{"click_text": "历史公告"}, {"wait_ms": 1200}],
            },
        },
        "channels": {"main": {"start_urls": ["https://example.gov.cn/list/index.html"], "pagination": {"pattern": "", "start_page": 2}}},
        "extract": {
            "list": {
                "item_xpath": ["//ul/li"],
                "title_xpath": [".//a/text()"],
                "link_xpath": [".//a/@href"],
                "date_xpath": [".//span/text()"],
            },
            "detail": {
                "title_xpath": ["//h1/text()"],
                "source_xpath": ["//span/text()"],
                "pub_time_xpath": ["//time/text()"],
                "content_xpath": ["//article"],
                "attachments_xpath": ["//a/@href"],
            },
            "inline_list": {
                "item_xpath": ["//div[@class='item']"],
                "title_xpath": [".//h3/text()"],
            },
        },
    }
    (tmp_path / "tmpgov.yaml").write_text(json.dumps(rule, ensure_ascii=False), encoding="utf-8")
    loaded = GovRuleLoader().load_site_rule(site="tmpgov", custom_rule_path=str(tmp_path))
    assert loaded["site"]["fetch_mode"] == "browser"


def test_gov_create_fetcher_by_fetch_mode():
    rule_http = {"site": {"fetch_mode": "http"}}
    assert isinstance(GovCrawler._create_fetcher(rule_http, "http"), GovHttpFetcher)

    rule_browser = {"site": {"fetch_mode": "browser", "browser": {"timeout_ms": 15000}}}
    assert isinstance(GovCrawler._create_fetcher(rule_browser, "browser"), GovBrowserFetcher)


def test_gov_extract_list_items_support_query_style_detail_url():
    html = """
    <html>
      <body>
        <ul>
          <li><a href="/portal/notice?id=13700000955">系统维护公告</a></li>
          <li><a href="/portal/notice?id=13700000939">广东省公安厅政务服务等业务系统维护公告</a></li>
        </ul>
      </body>
    </html>
    """
    extractor = GovExtractor()
    list_rule = {
        "item_xpath": ["//ul/li[.//a]"],
        "title_xpath": [".//a/text()"],
        "link_xpath": [".//a/@href"],
        "date_xpath": [".//span/text()"],
    }
    rows = extractor.extract_list_items(
        html=html,
        page_url="https://www.gdzwfw.gov.cn/portal/v2/notices?region=440300",
        list_rule=list_rule,
    )
    assert len(rows) == 2
    assert rows[0]["url"] == "https://www.gdzwfw.gov.cn/portal/notice?id=13700000955"


def test_gov_extract_detail_publish_time_fallback_from_body_text():
    html = """
    <html>
      <body>
        <h1>深圳市前海管理局关于机场南货站园区项目建设工程规划许可的批前公示</h1>
        <div class="meta">发布时间：2026-03-18 10:18:21</div>
        <div id="content">正文内容示例。</div>
      </body>
    </html>
    """
    extractor = GovExtractor()
    detail = extractor.extract_detail(
        html=html,
        page_url="https://qh.sz.gov.cn/sygnan/qhzx/tzgg/content/post_12689393.html",
        detail_rule={
            "title_xpath": ["//h1/text()"],
            "source_xpath": ["//span[@class='no-source']/text()"],
            "pub_time_xpath": ["//span[@class='no-date']/text()"],
            "content_xpath": ["//div[@id='content']"],
            "attachments_xpath": ["//a/@href"],
        },
    )
    assert detail["publish_time"] == "2026-03-18 10:18:21"


def test_gov_extract_inline_list_items_generate_inline_url():
    html = """
    <html>
      <body>
        <div class="list-item-wrap">
          <div class="img-right">
            <h1 class="title"><p>深圳市：植绿添新彩 诚信润人心</p></h1>
            <p class="content">为深入推进社会信用体系建设，开展诚信植树宣传。</p>
            <div class="info">
              <span class="author">宝安区</span>
              <span class="date">2026-03-17 16:23:43</span>
            </div>
          </div>
        </div>
      </body>
    </html>
    """
    extractor = GovExtractor()
    rows = extractor.extract_inline_list_items(
        html=html,
        page_url="https://www.szcredit.org.cn/#/index",
        inline_rule={
            "item_xpath": ["//div[contains(@class,'list-item-wrap')]"],
            "title_xpath": [".//*[contains(@class,'title')]//p/text()", ".//*[contains(@class,'title')]//text()"],
            "date_xpath": [".//*[contains(@class,'date')]/text()"],
            "source_xpath": [".//*[contains(@class,'author')]/text()"],
            "summary_xpath": [".//*[contains(@class,'content')]/text()"],
        },
    )
    assert len(rows) == 1
    assert rows[0]["inline_mode"] == "1"
    assert rows[0]["source"] == "宝安区"
    assert rows[0]["publish_time"] == "2026-03-17 16:23:43"
    assert rows[0]["url"].startswith("https://www.szcredit.org.cn/#/index#inline-")
