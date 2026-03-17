# -*- coding: utf-8 -*-
# Copyright (c) 2025 relakkes@gmail.com
#
# This file is part of MediaCrawler project.
# Repository: https://github.com/NanmiCoder/MediaCrawler/blob/main/tests/test_wechat_parser.py
# GitHub: https://github.com/NanmiCoder
# Licensed under NON-COMMERCIAL LEARNING LICENSE 1.1
#

from media_platform.wechat.parser import WechatParser


def test_parse_article_detail_basic_fields():
    parser = WechatParser()
    html = """
    <html>
      <head><meta property="og:url" content="https://mp.weixin.qq.com/s?__biz=MzABC%3D%3D&sn=abcdef1234567890abcdef1234567890" /></head>
      <body>
        <a id="js_name">测试号</a>
        <h2 class="rich_media_title">测试标题</h2>
        <span class="rich_media_meta rich_media_meta_text">作者A</span>
        <div class="rich_media_content">正文内容<img src="https://a/b.jpg"></div>
        <script>
          var comment_id = "998877";
          var msg_desc = "摘要";
          var cover = "https://a/c.jpg";
          var msg_source_url = 'https://source';
        </script>
      </body>
    </html>
    """
    row = parser.parse_article_detail("https://mp.weixin.qq.com/s?__biz=MzABC%3D%3D&sn=abcdef1234567890abcdef1234567890", html)
    assert row["biz"] == "MzABC=="
    assert row["sn"] == "abcdef1234567890abcdef1234567890"
    assert row["comment_id"] == "998877"
    assert row["title"] == "测试标题"
    assert row["account"] == "测试号"
    assert row["pics_url"] == "https://a/b.jpg"


def test_parse_article_list_home_generates_next_url():
    parser = WechatParser()
    html = """
    <strong id="nickname">公众号A</strong>
    <div class="profile_avatar"><img src="https://a/logo.jpg"></div>
    <p class="profile_desc">简介A</p>
    <script>
      var username = "" || "gh_test";
      appmsg_token = "token_x";
      can_msg_continue = '1';
      msgList = '{"list":[{"comm_msg_info":{"type":49,"datetime":1700000000},"app_msg_ext_info":{"title":"标题1","digest":"摘要1","content_url":"https:\\/\\/mp.weixin.qq.com\\/s?__biz=MzAAA==&sn=sn123","source_url":"","cover":"","author":"作者1","multi_app_msg_item_list":[]}}]}';
    </script>
    """
    data = parser.parse_article_list(
        "https://mp.weixin.qq.com/mp/profile_ext?action=home&__biz=MzAAA%3D%3D&pass_ticket=pt",
        html,
    )
    assert data["account"]["biz"] == "MzAAA=="
    assert len(data["articles"]) == 1
    assert data["articles"][0]["sn"] == "sn123"
    assert "action=getmsg" in data["next_url"]


def test_parse_comment_uses_comment_id_to_sn_map():
    parser = WechatParser()
    parser.parse_article_detail(
        "https://mp.weixin.qq.com/s?__biz=MzAAA%3D%3D&sn=sn999",
        '<div class="rich_media_content">x</div><script>var comment_id = "cid_1";</script>',
    )
    comments = parser.parse_comment(
        "https://mp.weixin.qq.com/mp/appmsg_comment?__biz=MzAAA%3D%3D&comment_id=cid_1",
        '{"elected_comment":[{"content_id":"xx1","nick_name":"n1","logo_url":"l1","content":"c1","create_time":1700000000,"like_num":3,"is_top":0}]}',
    )
    assert len(comments) == 1
    assert comments[0]["sn"] == "sn999"
    assert comments[0]["biz"] == "MzAAA=="
