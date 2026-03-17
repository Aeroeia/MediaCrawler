# -*- coding: utf-8 -*-
# Copyright (c) 2025 relakkes@gmail.com
#
# This file is part of MediaCrawler project.
# Repository: https://github.com/NanmiCoder/MediaCrawler/blob/main/tests/test_task_schema_manual_only.py
# GitHub: https://github.com/NanmiCoder
# Licensed under NON-COMMERCIAL LEARNING LICENSE 1.1
#

from api.schemas.task import TaskUpsertRequest


def test_task_upsert_accepts_manual_only_without_cron():
    payload = TaskUpsertRequest(
        name="wx-task",
        platform="wx",
        crawler_type="search",
        login_type="qrcode",
        save_option="jsonl",
        manual_only=True,
        cron_expr="",
    )
    assert payload.manual_only is True
    assert payload.cron_expr == ""
