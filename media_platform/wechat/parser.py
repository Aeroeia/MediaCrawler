# -*- coding: utf-8 -*-
# Copyright (c) 2025 relakkes@gmail.com
#
# This file is part of MediaCrawler project.
# Repository: https://github.com/NanmiCoder/MediaCrawler/blob/main/media_platform/wechat/parser.py
# GitHub: https://github.com/NanmiCoder
# Licensed under NON-COMMERCIAL LEARNING LICENSE 1.1
#

from __future__ import annotations

import re
import time
from typing import Any, Dict

from parsel import Selector

from .help import (
    build_article_id,
    extract_biz_from_url,
    get_param,
    parse_request_body,
    safe_json_loads,
    strip_images,
    timestamp_to_str,
)


class WechatParser:
    def __init__(self) -> None:
        self._comment_id_to_sn: dict[str, str] = {}

    def _parse_account_info(self, text: str, req_url: str) -> dict:
        biz = extract_biz_from_url(req_url)
        account = re.findall(r'id="nickname">(.*?)</strong>', text, flags=re.S)
        head_url = re.findall(r'profile_avatar">.*?<img src="(.*?)"', text, flags=re.S)
        summary = re.findall(r'class="profile_desc">(.*?)</p>', text, flags=re.S)
        verify = re.findall(r'<i class="icon_verify success">.*?</i>(.*?)</span>', text, flags=re.S)
        qr_code = re.findall(r'var username = "" \|\| "(.*?)";', text, flags=re.S)
        qr_link = f"http://open.weixin.qq.com/qr/code?username={qr_code[0]}" if qr_code else ""
        return {
            "biz": biz,
            "account": (account[0] if account else "").strip(),
            "head_url": (head_url[0] if head_url else "").strip(),
            "summary": (summary[0] if summary else "").strip(),
            "verify": (verify[0] if verify else "").strip(),
            "qr_code": qr_link,
            "spider_time": timestamp_to_str(int(time.time())),
        }

    @staticmethod
    def _parse_article_entry(item: Dict[str, Any], comm_msg: Dict[str, Any], biz: str) -> dict:
        url = str(item.get("content_url") or "").replace("\\", "").replace("amp;", "")
        source_url = str(item.get("source_url") or "").replace("\\", "")
        sn = get_param(url, "sn")
        publish_time = timestamp_to_str(comm_msg.get("datetime"))
        article_id = build_article_id(sn=sn, biz=biz, url=url)
        return {
            "article_id": article_id,
            "sn": sn,
            "biz": biz,
            "title": str(item.get("title") or ""),
            "digest": str(item.get("digest") or ""),
            "url": url,
            "source_url": source_url,
            "cover": str(item.get("cover") or "").replace("\\", ""),
            "author": str(item.get("author") or ""),
            "publish_time": publish_time,
            "spider_time": timestamp_to_str(int(__import__("time").time())),
            "comment_id": "",
            "pics_url": "",
            "content_html": "",
            "read_num": 0,
            "like_num": 0,
            "comment_count": 0,
        }

    def parse_article_list(self, req_url: str, text: str) -> dict:
        biz = extract_biz_from_url(req_url)
        result = {
            "account": None,
            "articles": [],
            "article_urls": [],
            "next_url": "",
        }

        article_list_raw = ""
        can_more = False
        if "action=home" in req_url:
            result["account"] = self._parse_account_info(text=text, req_url=req_url)
            matched = re.findall(r"msgList = '(.*?})';", text, flags=re.S)
            article_list_raw = matched[0].replace("&quot;", '"') if matched else ""
            can_more_match = re.findall(r"can_msg_continue = '(\d)'", text, flags=re.S)
            can_more = (can_more_match[0] == "1") if can_more_match else False
            appmsg_token = re.findall(r'appmsg_token = "(.*?)";', text, flags=re.S)
            pass_ticket = get_param(req_url, "pass_ticket")
            if can_more and appmsg_token:
                result["next_url"] = (
                    "https://mp.weixin.qq.com/mp/profile_ext?"
                    f"action=getmsg&__biz={biz}&f=json&offset=10&count=10&is_ok=1&scene=124"
                    f"&uin=777&key=777&pass_ticket={pass_ticket}&wxtoken=&appmsg_token={appmsg_token[0]}&x5=0&f=json"
                )
        else:
            payload = safe_json_loads(text)
            article_list_raw = payload.get("general_msg_list") or ""
            can_more = bool(payload.get("can_msg_continue"))
            if can_more:
                next_offset = int(payload.get("next_offset") or 0)
                pass_ticket = get_param(req_url, "pass_ticket")
                appmsg_token = get_param(req_url, "appmsg_token")
                result["next_url"] = (
                    "https://mp.weixin.qq.com/mp/profile_ext?"
                    f"action=getmsg&__biz={biz}&f=json&offset={next_offset}&count=10&is_ok=1&scene=124"
                    f"&uin=777&key=777&pass_ticket={pass_ticket}&wxtoken=&appmsg_token={appmsg_token}&x5=0&f=json"
                )

        if isinstance(article_list_raw, dict):
            article_list_json = article_list_raw
        else:
            article_list_json = safe_json_loads(article_list_raw)
        articles = []
        for article in article_list_json.get("list", []):
            comm_msg = article.get("comm_msg_info", {}) or {}
            article_type = int(comm_msg.get("type") or 0)
            if article_type != 49:
                continue
            app_msg_ext = article.get("app_msg_ext_info", {}) or {}
            if app_msg_ext:
                parsed = self._parse_article_entry(app_msg_ext, comm_msg, biz=biz)
                if parsed.get("url"):
                    articles.append(parsed)
            for sub in app_msg_ext.get("multi_app_msg_item_list") or []:
                parsed = self._parse_article_entry(sub, comm_msg, biz=biz)
                if parsed.get("url"):
                    articles.append(parsed)

        result["articles"] = articles
        result["article_urls"] = [row.get("url", "") for row in articles if row.get("url")]
        return result

    def parse_article_detail(self, req_url: str, text: str) -> dict:
        selector = Selector(text)
        content = selector.xpath(
            '//div[@class="rich_media_content "]|//div[@class="rich_media_content"]|//div[@class="share_media"]'
        )
        canonical_url = (
            selector.xpath('//meta[@property="og:url"]/@content').get(default="").strip().replace("&amp;", "&")
        )
        final_url = canonical_url or req_url
        sn = get_param(req_url, "sn") or get_param(canonical_url, "sn")
        biz = get_param(req_url, "__biz") or get_param(canonical_url, "__biz")
        if not biz:
            biz = selector.re_first(r'var biz = "(.*?)"') or selector.re_first(r'window.__biz = "(.*?)"') or ""
        publish_ts = selector.re_first(r'n="(\d{10})"')
        publish_time = timestamp_to_str(publish_ts)
        comment_id = selector.re_first(r'var comment_id = "([A-Za-z0-9_]+)"') or ""
        if comment_id and sn:
            self._comment_id_to_sn[comment_id] = sn
        article_id = build_article_id(sn=sn, biz=biz, url=final_url)
        pics = content.xpath(".//img/@src|.//img/@data-src").extract()

        return {
            "article_id": article_id,
            "sn": sn,
            "biz": biz,
            "account": selector.xpath('//a[@id="js_name"]/text()').get(default="").strip(),
            "title": selector.xpath('//h2[@class="rich_media_title"]/text()').get(default="").strip(),
            "url": final_url,
            "author": selector.xpath('//span[@class="rich_media_meta rich_media_meta_text"]//text()').get(default="").strip(),
            "publish_time": publish_time,
            "digest": selector.re_first(r'var msg_desc = "(.*?)"') or "",
            "cover": selector.re_first(r'var cover = "(.*?)";') or selector.re_first(r'msg_cdn_url = "(.*?)"') or "",
            "pics_url": ",".join([str(item) for item in pics if item]),
            "content_html": content.get(default=""),
            "source_url": selector.re_first(r"var msg_source_url = '(.*?)';") or "",
            "comment_id": comment_id,
            "spider_time": timestamp_to_str(int(__import__("time").time())),
        }

    def parse_article_dynamic(self, request_body: str, text: str) -> dict:
        payload = parse_request_body(request_body)
        data = safe_json_loads(text)
        biz = str(payload.get("__biz") or "").replace("%3D", "=")
        return {
            "sn": str(payload.get("sn") or ""),
            "biz": biz,
            "read_num": int(data.get("appmsgstat", {}).get("read_num") or 0),
            "like_num": int(data.get("appmsgstat", {}).get("like_num") or 0),
            "comment_count": int(data.get("comment_count") or 0),
            "spider_time": timestamp_to_str(int(__import__("time").time())),
        }

    def parse_comment(self, req_url: str, text: str) -> list[dict]:
        data = safe_json_loads(text)
        biz = extract_biz_from_url(req_url)
        comment_id = get_param(req_url, "comment_id")
        sn = self._comment_id_to_sn.get(comment_id, "")
        rows = []
        for comment in data.get("elected_comment", []) or []:
            rows.append(
                {
                    "content_id": str(comment.get("content_id") or ""),
                    "comment_id": comment_id,
                    "sn": sn,
                    "biz": biz,
                    "nick_name": str(comment.get("nick_name") or ""),
                    "logo_url": str(comment.get("logo_url") or ""),
                    "content": str(comment.get("content") or ""),
                    "create_time": timestamp_to_str(comment.get("create_time")),
                    "like_num": int(comment.get("like_num") or 0),
                    "is_top": int(comment.get("is_top") or 0),
                    "spider_time": timestamp_to_str(int(time.time())),
                }
            )
        return rows

    @staticmethod
    def sanitize_response_html(text: str) -> str:
        return strip_images(text)
