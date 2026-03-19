# -*- coding: utf-8 -*-
# Copyright (c) 2025 relakkes@gmail.com
#
# This file is part of MediaCrawler project.
# Repository: https://github.com/NanmiCoder/MediaCrawler/blob/main/store/gov/_store_impl.py
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

from __future__ import annotations

import json
from typing import Dict

from sqlalchemy import select

from base.base_crawler import AbstractStore
from database.db_session import get_session
from database.models import GovArticle
from tools.async_file_writer import AsyncFileWriter
from tools.time_util import get_current_timestamp
from var import crawler_type_var


class _GovFileStoreBase(AbstractStore):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.writer = AsyncFileWriter(platform="gov", crawler_type=crawler_type_var.get())

    async def store_comment(self, comment_item: Dict):
        return

    async def store_creator(self, creator: Dict):
        return


class GovCsvStoreImplement(_GovFileStoreBase):
    async def store_content(self, content_item: Dict):
        await self.writer.write_to_csv(item_type="contents", item=content_item)


class GovJsonStoreImplement(_GovFileStoreBase):
    async def store_content(self, content_item: Dict):
        await self.writer.write_single_item_to_json(item_type="contents", item=content_item)


class GovJsonlStoreImplement(_GovFileStoreBase):
    async def store_content(self, content_item: Dict):
        await self.writer.write_to_jsonl(item_type="contents", item=content_item)


class GovDbStoreImplement(AbstractStore):
    async def store_content(self, content_item: Dict):
        payload = dict(content_item)
        fingerprint = str(payload.get("fingerprint") or "").strip()
        if not fingerprint:
            return

        now_ts = int(get_current_timestamp())
        attachments = payload.get("attachments") or []
        if not isinstance(attachments, list):
            attachments = []
        attachments_json = json.dumps(attachments, ensure_ascii=False)

        async with get_session() as session:
            stmt = select(GovArticle).where(GovArticle.fingerprint == fingerprint)
            res = await session.execute(stmt)
            db_item = res.scalar_one_or_none()
            if db_item:
                db_item.site_code = str(payload.get("site_code") or "")
                db_item.site_name = str(payload.get("site_name") or "")
                db_item.channel = str(payload.get("channel") or "")
                db_item.title = str(payload.get("title") or "")
                db_item.url = str(payload.get("url") or "")
                db_item.publish_time = str(payload.get("publish_time") or "")
                db_item.source = str(payload.get("source") or "")
                db_item.content_html = str(payload.get("content_html") or "")
                db_item.content_text = str(payload.get("content_text") or "")
                db_item.attachments_json = attachments_json
                db_item.crawl_time = str(payload.get("crawl_time") or "")
                db_item.last_modify_ts = now_ts
            else:
                session.add(
                    GovArticle(
                        site_code=str(payload.get("site_code") or ""),
                        site_name=str(payload.get("site_name") or ""),
                        channel=str(payload.get("channel") or ""),
                        title=str(payload.get("title") or ""),
                        url=str(payload.get("url") or ""),
                        publish_time=str(payload.get("publish_time") or ""),
                        source=str(payload.get("source") or ""),
                        content_html=str(payload.get("content_html") or ""),
                        content_text=str(payload.get("content_text") or ""),
                        attachments_json=attachments_json,
                        crawl_time=str(payload.get("crawl_time") or ""),
                        fingerprint=fingerprint,
                        add_ts=now_ts,
                        last_modify_ts=now_ts,
                    )
                )

    async def store_comment(self, comment_item: Dict):
        return

    async def store_creator(self, creator: Dict):
        return


class GovExcelStoreImplement:
    def __new__(cls, *args, **kwargs):
        from store.excel_store_base import ExcelStoreBase

        return ExcelStoreBase.get_instance(
            platform="gov",
            crawler_type=crawler_type_var.get(),
        )
