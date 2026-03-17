# -*- coding: utf-8 -*-
# Copyright (c) 2025 relakkes@gmail.com
#
# This file is part of MediaCrawler project.
# Repository: https://github.com/NanmiCoder/MediaCrawler/blob/main/store/wechat/_store_impl.py
# GitHub: https://github.com/NanmiCoder
# Licensed under NON-COMMERCIAL LEARNING LICENSE 1.1
#

from typing import Dict, Optional

from sqlalchemy import select

from base.base_crawler import AbstractStore
from database.db_session import get_session
from database.models import WxAccount, WxArticle, WxArticleComment, WxArticleDynamic
from database.mongodb_store_base import MongoDBStoreBase
from tools import utils
from tools.async_file_writer import AsyncFileWriter
from var import crawler_type_var


class _WxFileStoreBase(AbstractStore):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.writer = AsyncFileWriter(platform="wx", crawler_type=crawler_type_var.get())

    async def store_dynamic(self, dynamic_item: Dict):
        raise NotImplementedError


class WxCsvStoreImplement(_WxFileStoreBase):
    async def store_content(self, content_item: Dict):
        await self.writer.write_to_csv(item_type="contents", item=content_item)

    async def store_comment(self, comment_item: Dict):
        await self.writer.write_to_csv(item_type="comments", item=comment_item)

    async def store_creator(self, creator: Dict):
        await self.writer.write_to_csv(item_type="accounts", item=creator)

    async def store_dynamic(self, dynamic_item: Dict):
        await self.writer.write_to_csv(item_type="dynamics", item=dynamic_item)


class WxJsonStoreImplement(_WxFileStoreBase):
    async def store_content(self, content_item: Dict):
        await self.writer.write_single_item_to_json(item_type="contents", item=content_item)

    async def store_comment(self, comment_item: Dict):
        await self.writer.write_single_item_to_json(item_type="comments", item=comment_item)

    async def store_creator(self, creator: Dict):
        await self.writer.write_single_item_to_json(item_type="accounts", item=creator)

    async def store_dynamic(self, dynamic_item: Dict):
        await self.writer.write_single_item_to_json(item_type="dynamics", item=dynamic_item)


class WxJsonlStoreImplement(_WxFileStoreBase):
    async def store_content(self, content_item: Dict):
        await self.writer.write_to_jsonl(item_type="contents", item=content_item)

    async def store_comment(self, comment_item: Dict):
        await self.writer.write_to_jsonl(item_type="comments", item=comment_item)

    async def store_creator(self, creator: Dict):
        await self.writer.write_to_jsonl(item_type="accounts", item=creator)

    async def store_dynamic(self, dynamic_item: Dict):
        await self.writer.write_to_jsonl(item_type="dynamics", item=dynamic_item)


class WxDbStoreImplement(AbstractStore):
    @staticmethod
    async def _upsert(
        model_cls,
        unique_key: str,
        unique_value: str,
        payload: Dict,
    ) -> None:
        async with get_session() as session:
            stmt = select(model_cls).where(getattr(model_cls, unique_key) == unique_value)
            res = await session.execute(stmt)
            db_item = res.scalar_one_or_none()
            if db_item:
                for key, value in payload.items():
                    setattr(db_item, key, value)
            else:
                db_item = model_cls(**payload)
                session.add(db_item)
            await session.commit()

    async def store_content(self, content_item: Dict):
        content_item = dict(content_item)
        article_id = str(content_item.get("article_id") or "").strip()
        sn = str(content_item.get("sn") or "").strip()
        unique_value = article_id or sn
        if not unique_value:
            return
        now_ts = utils.get_current_timestamp()
        content_item.setdefault("add_ts", now_ts)
        content_item["last_modify_ts"] = now_ts
        if not article_id:
            content_item["article_id"] = unique_value
        await self._upsert(WxArticle, "article_id", content_item["article_id"], content_item)

    async def store_comment(self, comment_item: Dict):
        comment_item = dict(comment_item)
        content_id = str(comment_item.get("content_id") or "").strip()
        if not content_id:
            return
        now_ts = utils.get_current_timestamp()
        comment_item.setdefault("add_ts", now_ts)
        comment_item["last_modify_ts"] = now_ts
        await self._upsert(WxArticleComment, "content_id", content_id, comment_item)

    async def store_creator(self, creator: Dict):
        creator = dict(creator)
        biz = str(creator.get("biz") or "").strip()
        if not biz:
            return
        now_ts = utils.get_current_timestamp()
        creator.setdefault("add_ts", now_ts)
        creator["last_modify_ts"] = now_ts
        await self._upsert(WxAccount, "biz", biz, creator)

    async def store_dynamic(self, dynamic_item: Dict):
        dynamic_item = dict(dynamic_item)
        sn = str(dynamic_item.get("sn") or "").strip()
        if not sn:
            return
        now_ts = utils.get_current_timestamp()
        dynamic_item.setdefault("add_ts", now_ts)
        dynamic_item["last_modify_ts"] = now_ts
        await self._upsert(WxArticleDynamic, "sn", sn, dynamic_item)

        # keep article summary counters aligned for dashboard queries
        async with get_session() as session:
            stmt = select(WxArticle).where(WxArticle.sn == sn)
            res = await session.execute(stmt)
            article = res.scalar_one_or_none()
            if article:
                article.read_num = int(dynamic_item.get("read_num") or 0)
                article.like_num = int(dynamic_item.get("like_num") or 0)
                article.comment_count = int(dynamic_item.get("comment_count") or 0)
                article.last_modify_ts = now_ts
                await session.commit()


class WxSqliteStoreImplement(WxDbStoreImplement):
    pass


class WxMongoStoreImplement(AbstractStore):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.mongo_store = MongoDBStoreBase(collection_prefix="wx")

    async def store_content(self, content_item: Dict):
        article_id = str(content_item.get("article_id") or content_item.get("sn") or "").strip()
        if not article_id:
            return
        await self.mongo_store.save_or_update(
            collection_suffix="contents",
            query={"article_id": article_id},
            data=content_item,
        )

    async def store_comment(self, comment_item: Dict):
        content_id = str(comment_item.get("content_id") or "").strip()
        if not content_id:
            return
        await self.mongo_store.save_or_update(
            collection_suffix="comments",
            query={"content_id": content_id},
            data=comment_item,
        )

    async def store_creator(self, creator: Dict):
        biz = str(creator.get("biz") or "").strip()
        if not biz:
            return
        await self.mongo_store.save_or_update(
            collection_suffix="accounts",
            query={"biz": biz},
            data=creator,
        )

    async def store_dynamic(self, dynamic_item: Dict):
        sn = str(dynamic_item.get("sn") or "").strip()
        if not sn:
            return
        await self.mongo_store.save_or_update(
            collection_suffix="dynamics",
            query={"sn": sn},
            data=dynamic_item,
        )


class WxExcelStoreImplement:
    def __new__(cls, *args, **kwargs):
        from store.excel_store_base import ExcelStoreBase

        return ExcelStoreBase.get_instance(
            platform="wx",
            crawler_type=crawler_type_var.get(),
        )
