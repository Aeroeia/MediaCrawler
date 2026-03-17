# -*- coding: utf-8 -*-
# Copyright (c) 2025 relakkes@gmail.com
#
# This file is part of MediaCrawler project.
# Repository: https://github.com/NanmiCoder/MediaCrawler/blob/main/tests/test_wechat_cmd_arg.py
# GitHub: https://github.com/NanmiCoder
# Licensed under NON-COMMERCIAL LEARNING LICENSE 1.1
#

import pytest

import config
from cmd_arg import parse_cmd


@pytest.mark.asyncio
async def test_parse_cmd_wx_detail_sets_specified_list():
    await parse_cmd(
        argv=[
            "--platform",
            "wx",
            "--type",
            "detail",
            "--specified_id",
            "https://mp.weixin.qq.com/s?__biz=MzA&sn=abc",
        ]
    )
    assert config.PLATFORM == "wx"
    assert config.CRAWLER_TYPE == "detail"
    assert config.WX_SPECIFIED_ID_LIST == ["https://mp.weixin.qq.com/s?__biz=MzA&sn=abc"]


@pytest.mark.asyncio
async def test_parse_cmd_wx_creator_sets_creator_list():
    await parse_cmd(
        argv=[
            "--platform",
            "wx",
            "--type",
            "creator",
            "--creator_id",
            "MzAAA==,MzBBB==",
        ]
    )
    assert config.PLATFORM == "wx"
    assert config.CRAWLER_TYPE == "creator"
    assert config.WX_CREATOR_ID_LIST == ["MzAAA==", "MzBBB=="]
