# -*- coding: utf-8 -*-
# Copyright (c) 2025 relakkes@gmail.com
#
# This file is part of MediaCrawler project.
# Repository: https://github.com/NanmiCoder/MediaCrawler/blob/main/tests/test_wechat_store_factory.py
# GitHub: https://github.com/NanmiCoder
# Licensed under NON-COMMERCIAL LEARNING LICENSE 1.1
#

from unittest.mock import patch

import pytest

from store.wechat import WxStoreFactory
from store.wechat._store_impl import (
    WxCsvStoreImplement,
    WxDbStoreImplement,
    WxJsonStoreImplement,
    WxJsonlStoreImplement,
    WxMongoStoreImplement,
    WxSqliteStoreImplement,
)


@patch("config.SAVE_DATA_OPTION", "csv")
def test_create_wx_csv_store():
    assert isinstance(WxStoreFactory.create_store(), WxCsvStoreImplement)


@patch("config.SAVE_DATA_OPTION", "json")
def test_create_wx_json_store():
    assert isinstance(WxStoreFactory.create_store(), WxJsonStoreImplement)


@patch("config.SAVE_DATA_OPTION", "jsonl")
def test_create_wx_jsonl_store():
    assert isinstance(WxStoreFactory.create_store(), WxJsonlStoreImplement)


@patch("config.SAVE_DATA_OPTION", "db")
def test_create_wx_db_store():
    assert isinstance(WxStoreFactory.create_store(), WxDbStoreImplement)


@patch("config.SAVE_DATA_OPTION", "sqlite")
def test_create_wx_sqlite_store():
    assert isinstance(WxStoreFactory.create_store(), WxSqliteStoreImplement)


@patch("config.SAVE_DATA_OPTION", "mongodb")
def test_create_wx_mongo_store():
    assert isinstance(WxStoreFactory.create_store(), WxMongoStoreImplement)


@patch("config.SAVE_DATA_OPTION", "invalid")
def test_create_wx_invalid_store():
    with pytest.raises(ValueError):
        WxStoreFactory.create_store()
