# -*- coding: utf-8 -*-
# Copyright (c) 2025 relakkes@gmail.com
#
# This file is part of MediaCrawler project.
# Repository: https://github.com/NanmiCoder/MediaCrawler/blob/main/store/gov/__init__.py
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

import config
from base.base_crawler import AbstractStore

from ._store_impl import (
    GovCsvStoreImplement,
    GovDbStoreImplement,
    GovExcelStoreImplement,
    GovJsonStoreImplement,
    GovJsonlStoreImplement,
)


class GovStoreFactory:
    STORES = {
        "csv": GovCsvStoreImplement,
        "db": GovDbStoreImplement,
        "json": GovJsonStoreImplement,
        "jsonl": GovJsonlStoreImplement,
        "excel": GovExcelStoreImplement,
    }

    @staticmethod
    def create_store() -> AbstractStore:
        store_class = GovStoreFactory.STORES.get(config.SAVE_DATA_OPTION)
        if not store_class:
            supported = ", ".join(sorted(GovStoreFactory.STORES))
            raise ValueError(
                f"[GovStoreFactory.create_store] save option '{config.SAVE_DATA_OPTION}' is not supported in gov v2. "
                f"Supported: {supported}"
            )
        return store_class()


async def update_gov_content(content_item: dict) -> None:
    await GovStoreFactory.create_store().store_content(dict(content_item))
