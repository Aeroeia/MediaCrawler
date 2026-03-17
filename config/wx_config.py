# -*- coding: utf-8 -*-
# Copyright (c) 2025 relakkes@gmail.com
#
# This file is part of MediaCrawler project.
# Repository: https://github.com/NanmiCoder/MediaCrawler/blob/main/config/wx_config.py
# GitHub: https://github.com/NanmiCoder
# Licensed under NON-COMMERCIAL LEARNING LICENSE 1.1
#

# WeChat Official Account platform configuration

# detail mode input: article urls or sns
WX_SPECIFIED_ID_LIST = []

# creator mode input: __biz list
WX_CREATOR_ID_LIST = []

# mitmproxy listen host/port
WX_SERVICE_HOST = "0.0.0.0"
WX_SERVICE_PORT = 8088

# scheduling and pacing
WX_MONITOR_INTERVAL_SEC = 60 * 30
WX_NO_TASK_SLEEP_SEC = 30
WX_TASK_SLEEP_MIN_SEC = 2
WX_TASK_SLEEP_MAX_SEC = 5

# article crawl time range in local date time, format:
# "YYYY-mm-dd HH:MM:SS~YYYY-mm-dd HH:MM:SS", empty means no limit.
WX_CRAWL_TIME_RANGE = "~"

# if latest article older than this number of days, mark account as zombie
WX_ZOMBIE_ACCOUNT_DAYS = 90

# enable auto html injection for next-page redirect
WX_ENABLE_AUTO_NAV = True
