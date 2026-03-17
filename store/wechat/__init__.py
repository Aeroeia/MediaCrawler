# -*- coding: utf-8 -*-
# Copyright (c) 2025 relakkes@gmail.com
#
# This file is part of MediaCrawler project.
# Repository: https://github.com/NanmiCoder/MediaCrawler/blob/main/store/wechat/__init__.py
# GitHub: https://github.com/NanmiCoder
# Licensed under NON-COMMERCIAL LEARNING LICENSE 1.1
#

from __future__ import annotations

import hashlib
from typing import Iterable, Optional

from sqlalchemy import select

import config
from base.base_crawler import AbstractStore
from database.db_session import get_session
from database.models import WxAccountTask, WxArticleTask
from tools import utils
from var import source_keyword_var

from ._store_impl import (
    WxCsvStoreImplement,
    WxDbStoreImplement,
    WxExcelStoreImplement,
    WxJsonStoreImplement,
    WxJsonlStoreImplement,
    WxMongoStoreImplement,
    WxSqliteStoreImplement,
)


class WxStoreFactory:
    STORES = {
        "csv": WxCsvStoreImplement,
        "db": WxDbStoreImplement,
        "postgres": WxDbStoreImplement,
        "json": WxJsonStoreImplement,
        "jsonl": WxJsonlStoreImplement,
        "sqlite": WxSqliteStoreImplement,
        "mongodb": WxMongoStoreImplement,
        "excel": WxExcelStoreImplement,
    }

    @staticmethod
    def create_store() -> AbstractStore:
        store_class = WxStoreFactory.STORES.get(config.SAVE_DATA_OPTION)
        if not store_class:
            raise ValueError("[WxStoreFactory.create_store] Invalid save option.")
        return store_class()


async def update_wx_account(account_item: dict) -> None:
    local_item = dict(account_item)
    now_ts = utils.get_current_timestamp()
    local_item.setdefault("add_ts", now_ts)
    local_item["last_modify_ts"] = now_ts
    utils.logger.info(
        "[store.wechat.update_wx_account] biz:%s account:%s",
        str(local_item.get("biz") or ""),
        str(local_item.get("account") or ""),
    )
    await WxStoreFactory.create_store().store_creator(local_item)


async def update_wx_article(article_item: dict) -> None:
    local_item = dict(article_item)
    now_ts = utils.get_current_timestamp()
    local_item.setdefault("add_ts", now_ts)
    local_item["last_modify_ts"] = now_ts
    local_item["source_keyword"] = str(local_item.get("source_keyword") or source_keyword_var.get() or "")
    utils.logger.info(
        "[store.wechat.update_wx_article] article_id:%s sn:%s biz:%s url:%s",
        str(local_item.get("article_id") or ""),
        str(local_item.get("sn") or ""),
        str(local_item.get("biz") or ""),
        str(local_item.get("url") or ""),
    )
    await WxStoreFactory.create_store().store_content(local_item)


async def update_wx_article_dynamic(dynamic_item: dict) -> None:
    local_item = dict(dynamic_item)
    now_ts = utils.get_current_timestamp()
    local_item.setdefault("add_ts", now_ts)
    local_item["last_modify_ts"] = now_ts
    utils.logger.info(
        "[store.wechat.update_wx_article_dynamic] sn:%s biz:%s read_num:%s like_num:%s comment_count:%s",
        str(local_item.get("sn") or ""),
        str(local_item.get("biz") or ""),
        str(local_item.get("read_num") or ""),
        str(local_item.get("like_num") or ""),
        str(local_item.get("comment_count") or ""),
    )
    store = WxStoreFactory.create_store()
    if hasattr(store, "store_dynamic"):
        await store.store_dynamic(local_item)  # type: ignore[attr-defined]


async def update_wx_article_comment(comment_item: dict) -> None:
    local_item = dict(comment_item)
    now_ts = utils.get_current_timestamp()
    local_item.setdefault("add_ts", now_ts)
    local_item["last_modify_ts"] = now_ts
    utils.logger.info(
        "[store.wechat.update_wx_article_comment] content_id:%s sn:%s article_id:%s",
        str(local_item.get("content_id") or ""),
        str(local_item.get("sn") or ""),
        str(local_item.get("article_id") or ""),
    )
    await WxStoreFactory.create_store().store_comment(local_item)


def _normalize_biz(raw: str) -> str:
    text = str(raw or "").strip()
    return text


async def upsert_wx_account_tasks(biz_list: Iterable[str]) -> int:
    biz_values = [_normalize_biz(biz) for biz in biz_list if _normalize_biz(biz)]
    if not biz_values:
        return 0
    inserted = 0
    now_ts = utils.get_current_timestamp()
    async with get_session() as session:
        if session is None:
            return 0
        for biz in biz_values:
            stmt = select(WxAccountTask).where(WxAccountTask.biz == biz)
            res = await session.execute(stmt)
            row = res.scalar_one_or_none()
            if row:
                row.last_modify_ts = now_ts
                continue
            session.add(
                WxAccountTask(
                    biz=biz,
                    last_publish_time="",
                    last_spider_time="",
                    is_zombie=False,
                    add_ts=now_ts,
                    last_modify_ts=now_ts,
                )
            )
            inserted += 1
        await session.commit()
    return inserted


async def upsert_wx_article_task(article_url: str, sn: str = "", biz: str = "") -> None:
    article_url = str(article_url or "").strip()
    sn = str(sn or "").strip()
    biz = _normalize_biz(biz)
    if not article_url and not sn:
        return
    now_ts = utils.get_current_timestamp()
    async with get_session() as session:
        if session is None:
            return
        if sn:
            stmt = select(WxArticleTask).where(WxArticleTask.sn == sn)
        else:
            stmt = select(WxArticleTask).where(WxArticleTask.article_url == article_url)
        res = await session.execute(stmt)
        row = res.scalar_one_or_none()
        if row:
            row.article_url = article_url or row.article_url
            row.biz = biz or row.biz
            row.last_modify_ts = now_ts
            await session.commit()
            return
        session.add(
            WxArticleTask(
                sn=sn or hashlib.md5(article_url.encode("utf-8")).hexdigest(),
                article_url=article_url,
                biz=biz,
                state=0,
                add_ts=now_ts,
                last_modify_ts=now_ts,
            )
        )
        await session.commit()


async def mark_wx_article_task_state(sn: str, state: int) -> None:
    sn = str(sn or "").strip()
    if not sn:
        return
    now_ts = utils.get_current_timestamp()
    async with get_session() as session:
        if session is None:
            return
        stmt = select(WxArticleTask).where(WxArticleTask.sn == sn)
        res = await session.execute(stmt)
        row = res.scalar_one_or_none()
        if not row:
            return
        row.state = int(state)
        row.last_modify_ts = now_ts
        await session.commit()


async def query_biz_by_keyword(keyword: str, limit: int = 200) -> list[str]:
    keyword = str(keyword or "").strip()
    if not keyword:
        return []
    async with get_session() as session:
        if session is None:
            return []
        sql = (
            "SELECT biz FROM wx_account "
            "WHERE (account LIKE :kw OR summary LIKE :kw OR biz LIKE :kw) "
            "LIMIT :limit"
        )
        rows = await session.execute(select(WxAccountTask.biz).where(WxAccountTask.biz.like(f"%{keyword}%")).limit(limit))
        from_task = [str(row[0] or "").strip() for row in rows.fetchall() if str(row[0] or "").strip()]
        if from_task:
            return list(dict.fromkeys(from_task))

        from sqlalchemy import text

        query_res = await session.execute(text(sql), {"kw": f"%{keyword}%", "limit": int(limit)})
        values = [str(row[0] or "").strip() for row in query_res.fetchall() if str(row[0] or "").strip()]
        return list(dict.fromkeys(values))


async def query_article_url_by_sn(sn: str) -> Optional[str]:
    sn = str(sn or "").strip()
    if not sn:
        return None
    async with get_session() as session:
        if session is None:
            return None
        from database.models import WxArticle

        stmt = select(WxArticle.url).where(WxArticle.sn == sn).limit(1)
        res = await session.execute(stmt)
        row = res.first()
        if not row:
            return None
        return str(row[0] or "").strip() or None


async def list_wx_account_tasks(limit: int = 500) -> list[str]:
    async with get_session() as session:
        if session is None:
            return []
        stmt = select(WxAccountTask.biz).where(WxAccountTask.is_zombie.is_(False)).limit(limit)
        rows = await session.execute(stmt)
        return [str(row[0] or "").strip() for row in rows.fetchall() if str(row[0] or "").strip()]


async def list_wx_pending_article_tasks(limit: int = 500) -> list[str]:
    async with get_session() as session:
        if session is None:
            return []
        stmt = (
            select(WxArticleTask.article_url)
            .where(WxArticleTask.state.in_([0, 2]))
            .limit(limit)
        )
        rows = await session.execute(stmt)
        return [str(row[0] or "").strip() for row in rows.fetchall() if str(row[0] or "").strip()]
