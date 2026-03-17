# -*- coding: utf-8 -*-
# Copyright (c) 2025 relakkes@gmail.com
#
# This file is part of MediaCrawler project.
# Repository: https://github.com/NanmiCoder/MediaCrawler/blob/main/api/schemas/task.py
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

from pydantic import BaseModel, Field

from .crawler import CrawlerTypeEnum, LoginTypeEnum, PlatformEnum, SaveDataOptionEnum


class TaskUpsertRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str = ""
    platform: PlatformEnum
    crawler_type: CrawlerTypeEnum = CrawlerTypeEnum.SEARCH
    login_type: LoginTypeEnum = LoginTypeEnum.QRCODE
    save_option: SaveDataOptionEnum = SaveDataOptionEnum.JSONL
    keywords: str = ""
    specified_ids: str = ""
    creator_ids: str = ""
    cookies: str = ""
    start_page: int = Field(default=1, ge=1)
    enable_comments: bool = True
    enable_sub_comments: bool = False
    headless: bool = False
    priority: str = Field(default="medium", pattern="^(low|medium|high)$")
    timeout_seconds: int = Field(default=30, ge=5, le=3600)
    cron_expr: str = Field(default="", max_length=128)
    manual_only: bool = False
    is_enabled: bool = True
