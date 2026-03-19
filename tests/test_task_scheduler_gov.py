# -*- coding: utf-8 -*-
# Copyright (c) 2025 relakkes@gmail.com
#
# This file is part of MediaCrawler project.
# Repository: https://github.com/NanmiCoder/MediaCrawler/blob/main/tests/test_task_scheduler_gov.py
# GitHub: https://github.com/NanmiCoder
# Licensed under NON-COMMERCIAL LEARNING LICENSE 1.1
#

import pytest

from media_platform.gov.site_registry import GovSiteRegistry
from api.schemas.task import TaskUpsertRequest
from api.services.task_scheduler_service import TaskSchedulerError, TaskSchedulerService
from database.models import CrawlerTask


def test_normalize_task_upsert_payload_for_gov_sets_defaults():
    service = TaskSchedulerService()
    payload = TaskUpsertRequest(
        name="gov-task",
        platform="gov",
        crawler_type="search",
        login_type="cookie",
        save_option="db",
        keywords="will-be-cleared",
        gov_site="dpxq",
        gov_channel="",
        gov_max_pages=1,
        gov_rule_path="  /tmp/custom-rules  ",
        cookies="to-clear",
        cron_expr="*/10 * * * *",
        manual_only=False,
        is_enabled=True,
    )

    normalized = service._normalize_task_upsert_payload(payload)
    assert normalized["platform"] == "gov"
    assert normalized["crawler_type"] == "search"
    assert normalized["gov_site"] == "dpxq"
    assert normalized["gov_channel"] == "main"
    assert normalized["gov_max_pages"] == 1
    assert normalized["gov_rule_path"] == "/tmp/custom-rules"
    assert normalized["keywords"] == ""
    assert normalized["creator_ids"] == ""
    assert normalized["cookies"] == ""


def test_normalize_task_upsert_payload_for_gov_creator_rejected():
    service = TaskSchedulerService()
    payload = TaskUpsertRequest(
        name="gov-creator",
        platform="gov",
        crawler_type="creator",
        login_type="qrcode",
        save_option="jsonl",
        gov_site="dpxq",
        manual_only=True,
    )

    with pytest.raises(TaskSchedulerError) as exc_info:
        service._normalize_task_upsert_payload(payload)
    assert "does not support creator mode" in str(exc_info.value)


def test_build_command_for_gov_contains_gov_args():
    service = TaskSchedulerService()
    task = CrawlerTask(
        id=1,
        platform="gov",
        crawler_type="search",
        login_type="qrcode",
        save_option="db",
        keywords="",
        gov_site="dpxq",
        gov_channel="main",
        gov_max_pages=2,
        gov_rule_path="/tmp/rules",
        enable_comments=False,
        enable_sub_comments=False,
        headless=True,
        start_page=1,
    )

    command, runtime_params = service._build_command(task)
    command_text = " ".join(command)
    assert "--platform gov" in command_text
    assert "--gov_site dpxq" in command_text
    assert "--gov_channel main" in command_text
    assert "--gov_max_pages 2" in command_text
    assert "--gov_rule_path /tmp/rules" in command_text
    assert runtime_params["gov_site"] == "dpxq"
    assert runtime_params["gov_max_pages"] == 2


def test_normalize_task_upsert_payload_for_non_ready_gov_rejected(monkeypatch: pytest.MonkeyPatch):
    service = TaskSchedulerService()
    monkeypatch.setattr(
        GovSiteRegistry,
        "get_site",
        staticmethod(
            lambda site_code: {
                "site_code": site_code,
                "default_channel": "main",
                "status": "pending_dynamic",
                "verify_error": "captcha required",
            }
        ),
    )
    payload = TaskUpsertRequest(
        name="gov-pending",
        platform="gov",
        crawler_type="search",
        login_type="qrcode",
        save_option="jsonl",
        gov_site="dummy-site",
        manual_only=True,
    )
    with pytest.raises(TaskSchedulerError) as exc_info:
        service._normalize_task_upsert_payload(payload)
    assert "not ready" in str(exc_info.value)
