# -*- coding: utf-8 -*-
# Copyright (c) 2025 relakkes@gmail.com
#
# This file is part of MediaCrawler project.
# Repository: https://github.com/NanmiCoder/MediaCrawler/blob/main/media_platform/wechat/field.py
# GitHub: https://github.com/NanmiCoder
# Licensed under NON-COMMERCIAL LEARNING LICENSE 1.1
#

import re

BIZ_RE = re.compile(r"^[A-Za-z0-9+/=]{8,}$")
SN_RE = re.compile(r"^[0-9a-fA-F]{32,64}$")

WX_URL_LIST = ("mp.weixin.qq.com",)
