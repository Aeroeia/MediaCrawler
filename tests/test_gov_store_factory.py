# -*- coding: utf-8 -*-
# Copyright (c) 2025 relakkes@gmail.com
#
# This file is part of MediaCrawler project.
# Repository: https://github.com/NanmiCoder/MediaCrawler/blob/main/tests/test_gov_store_factory.py
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

import pytest
from unittest.mock import patch

from store.gov import GovStoreFactory
from store.gov._store_impl import (
    GovCsvStoreImplement,
    GovDbStoreImplement,
    GovJsonStoreImplement,
    GovJsonlStoreImplement,
)


@patch("config.SAVE_DATA_OPTION", "csv")
def test_gov_store_factory_csv():
    store = GovStoreFactory.create_store()
    assert isinstance(store, GovCsvStoreImplement)


@patch("config.SAVE_DATA_OPTION", "json")
def test_gov_store_factory_json():
    store = GovStoreFactory.create_store()
    assert isinstance(store, GovJsonStoreImplement)


@patch("config.SAVE_DATA_OPTION", "jsonl")
def test_gov_store_factory_jsonl():
    store = GovStoreFactory.create_store()
    assert isinstance(store, GovJsonlStoreImplement)


@patch("config.SAVE_DATA_OPTION", "db")
def test_gov_store_factory_db():
    store = GovStoreFactory.create_store()
    assert isinstance(store, GovDbStoreImplement)


@patch("config.SAVE_DATA_OPTION", "sqlite")
def test_gov_store_factory_rejects_sqlite():
    with pytest.raises(ValueError) as exc_info:
        GovStoreFactory.create_store()
    assert "not supported in gov v2" in str(exc_info.value)
