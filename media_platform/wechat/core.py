# -*- coding: utf-8 -*-
# Copyright (c) 2025 relakkes@gmail.com
#
# This file is part of MediaCrawler project.
# Repository: https://github.com/NanmiCoder/MediaCrawler/blob/main/media_platform/wechat/core.py
# GitHub: https://github.com/NanmiCoder
# Licensed under NON-COMMERCIAL LEARNING LICENSE 1.1
#

from __future__ import annotations

import asyncio
import inspect
from typing import Dict, Optional

from playwright.async_api import BrowserContext, BrowserType

import config
from base.base_crawler import AbstractCrawler
from store import wechat as wx_store
from tools import utils
from var import crawler_type_var

from .addon import WechatMitmAddon
from .help import get_param, looks_like_biz, looks_like_sn
from .parser import WechatParser
from .task_manager import WxTaskManager


class WechatCrawler(AbstractCrawler):
    browser_context: Optional[BrowserContext]

    def __init__(self) -> None:
        self.browser_context = None
        self.master = None
        self._queue: asyncio.Queue[tuple[str, Dict]] = asyncio.Queue()
        self._consumer_task: Optional[asyncio.Task] = None
        self._task_manager = WxTaskManager()
        self._parser = WechatParser()

    async def launch_browser(
        self,
        chromium: BrowserType,
        playwright_proxy: Optional[Dict],
        user_agent: Optional[str],
        headless: bool = True,
    ) -> BrowserContext:
        raise RuntimeError("WechatCrawler does not use Playwright browser launch flow.")

    async def search(self):
        # WeChat mode is task-driven; search keywords are resolved to __biz seeds in _seed_tasks().
        return

    async def _enqueue_event(self, kind: str, payload: Dict) -> None:
        await self._queue.put((kind, payload))

    async def _consume_events(self) -> None:
        while True:
            kind, payload = await self._queue.get()
            if kind == "_stop":
                return
            try:
                if kind == "account":
                    await wx_store.update_wx_account(payload)
                    continue

                if kind == "article_seed":
                    await wx_store.update_wx_article(payload)
                    await wx_store.upsert_wx_article_task(
                        article_url=str(payload.get("url") or ""),
                        sn=str(payload.get("sn") or ""),
                        biz=str(payload.get("biz") or ""),
                    )
                    continue

                if kind == "article":
                    await wx_store.update_wx_article(payload)
                    await wx_store.mark_wx_article_task_state(str(payload.get("sn") or ""), state=1)
                    continue

                if kind == "dynamic":
                    await wx_store.update_wx_article_dynamic(payload)
                    continue

                if kind == "comment":
                    await wx_store.update_wx_article_comment(payload)
                    continue
            except Exception as exc:
                utils.logger.error("[WechatCrawler._consume_events] kind=%s err=%s", kind, exc)

    async def _resolve_search_biz(self) -> list[str]:
        raw_tokens = [str(item).strip() for item in str(config.KEYWORDS or "").split(",") if str(item).strip()]
        values: list[str] = []
        for token in raw_tokens:
            if looks_like_biz(token):
                values.append(token)
                continue
            matches = await wx_store.query_biz_by_keyword(token)
            values.extend(matches)
        uniq = list(dict.fromkeys([item for item in values if item]))
        return uniq

    async def _resolve_detail_urls(self) -> list[str]:
        urls: list[str] = []
        for token in config.WX_SPECIFIED_ID_LIST:
            value = str(token or "").strip()
            if not value:
                continue
            if value.startswith("http://") or value.startswith("https://"):
                urls.append(value)
                continue
            if looks_like_sn(value):
                query_url = await wx_store.query_article_url_by_sn(value)
                if query_url:
                    urls.append(query_url)
        return list(dict.fromkeys(urls))

    async def _seed_tasks(self) -> None:
        crawler_type_var.set(config.CRAWLER_TYPE)
        if config.CRAWLER_TYPE == "search":
            biz_list = await self._resolve_search_biz()
            if not biz_list:
                biz_list = await wx_store.list_wx_account_tasks()
            if not biz_list:
                utils.logger.warning("[WechatCrawler] No __biz found for search mode.")
            self._task_manager.add_account_tasks(biz_list)
            await wx_store.upsert_wx_account_tasks(biz_list)
            return

        if config.CRAWLER_TYPE == "creator":
            biz_list = [str(item).strip() for item in config.WX_CREATOR_ID_LIST if str(item).strip()]
            if not biz_list:
                biz_list = await wx_store.list_wx_account_tasks()
            self._task_manager.add_account_tasks(biz_list)
            await wx_store.upsert_wx_account_tasks(biz_list)
            return

        if config.CRAWLER_TYPE == "detail":
            urls = await self._resolve_detail_urls()
            if not urls:
                urls = await wx_store.list_wx_pending_article_tasks()
            self._task_manager.add_article_tasks(urls)
            for url in urls:
                await wx_store.upsert_wx_article_task(
                    article_url=url,
                    sn=get_param(url, "sn"),
                    biz=get_param(url, "__biz"),
                )
            return

    def _create_master(self, addon: WechatMitmAddon):
        from mitmproxy import options
        from mitmproxy.tools.dump import DumpMaster

        opts = options.Options(
            listen_host=str(config.WX_SERVICE_HOST),
            listen_port=int(config.WX_SERVICE_PORT),
            ssl_insecure=True,
        )
        try:
            master = DumpMaster(opts, with_termlog=False, with_dumper=False)
            master.addons.add(addon)
            return master
        except TypeError:
            # compatibility fallback for old mitmproxy APIs
            from mitmproxy import proxy

            master = DumpMaster(opts)
            pconf = proxy.config.ProxyConfig(opts)
            master.server = proxy.server.ProxyServer(pconf)
            master.addons.add(addon)
            return master

    async def _shutdown_master(self) -> None:
        if not self.master:
            return
        try:
            ret = self.master.shutdown()
            if inspect.isawaitable(ret):
                await ret
        except Exception:
            pass
        finally:
            self.master = None

    async def start(self) -> None:
        try:
            import mitmproxy  # noqa: F401
        except Exception as exc:
            raise RuntimeError(
                "wx platform requires mitmproxy. Please run `uv sync` to install dependencies."
            ) from exc

        await self._seed_tasks()

        self._consumer_task = asyncio.create_task(self._consume_events(), name="wx-event-consumer")
        loop = asyncio.get_running_loop()
        addon = WechatMitmAddon(
            parser=self._parser,
            task_manager=self._task_manager,
            loop=loop,
            enqueue_handler=self._enqueue_event,
        )
        self.master = self._create_master(addon=addon)
        utils.logger.info(
            "[WechatCrawler.start] starting mitm proxy host=%s port=%s",
            config.WX_SERVICE_HOST,
            config.WX_SERVICE_PORT,
        )

        try:
            run_ret = self.master.run()
            if inspect.isawaitable(run_ret):
                await run_ret
            else:
                await asyncio.to_thread(self.master.run)
        except asyncio.CancelledError:
            await self._shutdown_master()
            raise
        finally:
            await self._shutdown_master()
            if self._consumer_task:
                await self._queue.put(("_stop", {}))
                try:
                    await self._consumer_task
                except Exception:
                    pass
                self._consumer_task = None
