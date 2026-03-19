# -*- coding: utf-8 -*-
# Copyright (c) 2025 relakkes@gmail.com
#
# This file is part of MediaCrawler project.
# Repository: https://github.com/NanmiCoder/MediaCrawler/blob/main/media_platform/wechat/addon.py
# GitHub: https://github.com/NanmiCoder
# Licensed under NON-COMMERCIAL LEARNING LICENSE 1.1
#

from __future__ import annotations

import asyncio
from typing import Any, Awaitable, Callable

import config
from tools import utils

from .parser import WechatParser
from .task_manager import WxTaskManager


class WechatMitmAddon:
    def __init__(
        self,
        parser: WechatParser,
        task_manager: WxTaskManager,
        loop: asyncio.AbstractEventLoop,
        enqueue_handler: Callable[[str, Any], Awaitable[None]],
    ) -> None:
        self.parser = parser
        self.task_manager = task_manager
        self.loop = loop
        self.enqueue_handler = enqueue_handler

    def _enqueue(self, kind: str, payload: Any) -> None:
        asyncio.run_coroutine_threadsafe(self.enqueue_handler(kind, payload), self.loop)

    @staticmethod
    def _verbose_enabled() -> bool:
        return bool(getattr(config, "WX_VERBOSE_LOG", False))

    @staticmethod
    def _request_text(flow: Any) -> str:
        request = getattr(flow, "request", None)
        if request is None:
            return ""
        try:
            return request.get_text(strict=False) or ""
        except Exception:
            try:
                body = getattr(request, "raw_content", b"")
                return body.decode("utf-8", errors="ignore")
            except Exception:
                return ""

    @staticmethod
    def _response_text(flow: Any) -> str:
        response = getattr(flow, "response", None)
        if response is None:
            return ""
        try:
            return response.get_text(strict=False) or ""
        except Exception:
            return ""

    @staticmethod
    def _set_html_response(flow: Any, html_prefix: str, body: str) -> None:
        response = getattr(flow, "response", None)
        if response is None:
            return
        for key in ("Content-Security-Policy", "content-security-policy-report-only", "Strict-Transport-Security"):
            try:
                response.headers.pop(key, None)
            except Exception:
                pass
        try:
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
            response.headers["content-type"] = "text/html; charset=UTF-8"
            response.set_text(f"{html_prefix}{body}")
        except Exception:
            pass

    def response(self, flow: Any) -> None:
        url = str(getattr(flow.request, "url", "") or "")
        if "mp.weixin.qq.com" not in url:
            return

        text = self._response_text(flow)
        request_text = self._request_text(flow)
        content_type = str(getattr(flow.response.headers, "get", lambda *_: "")("content-type", "") or "").lower()
        if self._verbose_enabled():
            utils.logger.info(
                "[WechatMitmAddon.response] hit url=%s content_type=%s body_len=%s",
                url,
                content_type or "-",
                len(text or ""),
            )
        next_url = ""
        tip = ""
        try:
            if "mp/profile_ext?action=home" in url or "mp/profile_ext?action=getmsg" in url:
                parsed = self.parser.parse_article_list(req_url=url, text=text)
                account = parsed.get("account")
                if account and account.get("biz"):
                    self._enqueue("account", account)
                articles = parsed.get("articles", [])
                article_urls = parsed.get("article_urls", [])
                if articles:
                    for item in articles:
                        self._enqueue("article_seed", item)
                if article_urls:
                    self.task_manager.add_article_tasks(article_urls)
                next_url = str(parsed.get("next_url") or "")
                if not next_url:
                    next_url = self.task_manager.pop_next_task_url()
                if self._verbose_enabled():
                    utils.logger.info(
                        "[WechatMitmAddon.list] account_biz=%s article_count=%s article_url_count=%s has_next=%s",
                        (account or {}).get("biz", ""),
                        len(articles),
                        len(article_urls),
                        bool(next_url),
                    )
                tip = "正在抓取列表"
                if config.WX_ENABLE_AUTO_NAV:
                    self._set_html_response(
                        flow,
                        self.task_manager.build_navigation_html(next_url=next_url, tip=tip),
                        self.parser.sanitize_response_html(text),
                    )
                return

            if (
                "/s?__biz=" in url
                or "mp.weixin.qq.com/s?" in url
                or "mp.weixin.qq.com/s/" in url
                or "/mp/appmsg/show?__biz=" in url
                or "/mp/rumor" in url
            ):
                article = self.parser.parse_article_detail(req_url=url, text=text)
                if article.get("article_id"):
                    self._enqueue("article", article)
                    if self._verbose_enabled():
                        utils.logger.info(
                            "[WechatMitmAddon.article] parsed article_id=%s sn=%s biz=%s title=%s",
                            str(article.get("article_id") or ""),
                            str(article.get("sn") or ""),
                            str(article.get("biz") or ""),
                            str(article.get("title") or "").strip()[:80],
                        )
                elif self._verbose_enabled():
                    utils.logger.warning(
                        "[WechatMitmAddon.article] parse empty url=%s text_sample=%s",
                        url,
                        str(text or "")[:120].replace("\n", " "),
                    )
                next_url = self.task_manager.pop_next_task_url()
                tip = "正在抓取详情"
                if config.WX_ENABLE_AUTO_NAV:
                    self._set_html_response(
                        flow,
                        self.task_manager.build_navigation_html(next_url=next_url, tip=tip),
                        self.parser.sanitize_response_html(text),
                    )
                return

            if "mp/getappmsgext" in url:
                dynamic = self.parser.parse_article_dynamic(request_body=request_text, text=text)
                if dynamic.get("sn"):
                    self._enqueue("dynamic", dynamic)
                    if self._verbose_enabled():
                        utils.logger.info(
                            "[WechatMitmAddon.dynamic] sn=%s biz=%s read_num=%s like_num=%s comment_count=%s",
                            str(dynamic.get("sn") or ""),
                            str(dynamic.get("biz") or ""),
                            int(dynamic.get("read_num") or 0),
                            int(dynamic.get("like_num") or 0),
                            int(dynamic.get("comment_count") or 0),
                        )
                elif self._verbose_enabled():
                    utils.logger.warning(
                        "[WechatMitmAddon.dynamic] parse empty url=%s req_body_sample=%s",
                        url,
                        str(request_text or "")[:120].replace("\n", " "),
                    )
                return

            if "/mp/appmsg_comment" in url:
                comments = self.parser.parse_comment(req_url=url, text=text)
                for comment in comments:
                    self._enqueue("comment", comment)
                if self._verbose_enabled():
                    utils.logger.info(
                        "[WechatMitmAddon.comment] parsed comment_count=%s url=%s",
                        len(comments),
                        url,
                    )
                return

            # fallback for updated body URLs
            if "text/html" in content_type and ("rich_media_content" in text or 'id="js_content"' in text):
                article = self.parser.parse_article_detail(req_url=url, text=text)
                if article.get("article_id"):
                    self._enqueue("article", article)
                    if self._verbose_enabled():
                        utils.logger.info(
                            "[WechatMitmAddon.fallback_article] parsed article_id=%s sn=%s biz=%s",
                            str(article.get("article_id") or ""),
                            str(article.get("sn") or ""),
                            str(article.get("biz") or ""),
                        )
                    if config.WX_ENABLE_AUTO_NAV:
                        next_url = self.task_manager.pop_next_task_url()
                        self._set_html_response(
                            flow,
                            self.task_manager.build_navigation_html(next_url=next_url, tip="命中兜底文章解析"),
                            self.parser.sanitize_response_html(text),
                        )
                elif self._verbose_enabled():
                    utils.logger.warning("[WechatMitmAddon.fallback_article] parse empty url=%s", url)
        except Exception as exc:
            utils.logger.error("[WechatMitmAddon.response] parse failed url=%s err=%s", url, exc)
