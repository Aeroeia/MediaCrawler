# -*- coding: utf-8 -*-
# Copyright (c) 2025 relakkes@gmail.com
#
# This file is part of MediaCrawler project.
# Repository: https://github.com/NanmiCoder/MediaCrawler/blob/main/tests/test_task_scheduler_resume.py
# GitHub: https://github.com/NanmiCoder
# Licensed under NON-COMMERCIAL LEARNING LICENSE 1.1
#

from collections import deque

import pytest

from api.services.task_scheduler_service import TaskSchedulerService
from database.models import CrawlerTask, CrawlerTaskRun


class _FakeProcess:
    def __init__(self, exit_code: int):
        self._exit_code = int(exit_code)

    def wait(self) -> int:
        return self._exit_code


class _FakeSession:
    def __init__(self, task: CrawlerTask, run: CrawlerTaskRun):
        self._task = task
        self._run = run
        self.committed = False

    async def get(self, model_cls, key):
        if model_cls is CrawlerTask and int(key) == int(self._task.id):
            return self._task
        if model_cls is CrawlerTaskRun and int(key) == int(self._run.id):
            return self._run
        return None

    async def commit(self) -> None:
        self.committed = True


class _FakeSessionCtx:
    def __init__(self, session: _FakeSession):
        self._session = session

    async def __aenter__(self):
        return self._session

    async def __aexit__(self, exc_type, exc, tb):
        return False


def _bind_fake_session(service: TaskSchedulerService, task: CrawlerTask, run: CrawlerTaskRun) -> _FakeSession:
    session = _FakeSession(task=task, run=run)
    service.session_factory = lambda: _FakeSessionCtx(session)  # type: ignore[assignment]
    return session


def test_resume_search_checkpoint_and_override():
    service = TaskSchedulerService()
    service._task_progress_states[1] = {
        "crawler_type": "search",
        "keywords": ["k1", "k2", "k3"],
        "current_keyword": "k2",
        "current_page": 4,
    }
    payload = service._build_checkpoint_payload(1)
    assert payload == {
        "current_keyword": "k2",
        "current_page": 4,
        "remaining_keywords": ["k3"],
    }
    overrides, can_resume = service._build_resume_override("search", payload)
    assert can_resume is True
    assert overrides == {
        "keywords": "k2,k3",
        "start_page": 4,
        "resume_mode": True,
    }


def test_resume_track_progress_with_wechat_sn_and_biz():
    service = TaskSchedulerService()

    service._init_task_progress(
        task_id=2,
        runtime_params={
            "crawler_type": "detail",
            "specified_ids": "sn_A,sn_B",
        },
    )
    service._track_task_progress(
        task_id=2,
        line="[store.wechat.update_wx_article] article_id:wx_1 sn:sn_A biz:MzA== url:https://mp.weixin.qq.com/s?...",
    )
    payload = service._build_checkpoint_payload(2)
    assert payload == {
        "processed_ids": ["sn_A"],
        "remaining_ids": ["sn_B"],
    }

    service._init_task_progress(
        task_id=3,
        runtime_params={
            "crawler_type": "creator",
            "creator_ids": "MzA==,MzB==",
        },
    )
    service._track_task_progress(
        task_id=3,
        line="[store.wechat.update_wx_account] biz:MzB== account:demo",
    )
    creator_payload = service._build_checkpoint_payload(3)
    assert creator_payload == {
        "processed_ids": ["MzB=="],
        "remaining_ids": ["MzA=="],
    }


def test_data_hit_line_with_wechat_store_log():
    service = TaskSchedulerService()
    assert service._is_data_hit_line("[store.wechat.update_wx_article] article_id:wx_1")
    assert service._is_data_hit_line("[store.wechat.update_wx_account] biz:MzA==")
    assert not service._is_data_hit_line("[WechatCrawler.start] starting mitm proxy")


@pytest.mark.asyncio
async def test_wait_task_process_success_deletes_checkpoint():
    service = TaskSchedulerService()
    task = CrawlerTask(
        id=11,
        platform="wx",
        is_enabled=True,
        status="running",
        success_count=0,
        fail_count=0,
    )
    run = CrawlerTaskRun(id=111, task_id=11, platform="wx", status="running")
    session = _bind_fake_session(service, task, run)

    stats = {"save": 0, "delete": 0}

    async def fake_save(*args, **kwargs):
        stats["save"] += 1

    async def fake_delete(*args, **kwargs):
        stats["delete"] += 1

    service._save_checkpoint = fake_save  # type: ignore[assignment]
    service._delete_checkpoint = fake_delete  # type: ignore[assignment]
    service._running_processes[11] = object()  # type: ignore[assignment]
    service._running_run_ids[11] = 111
    service._platform_running_tasks["wx"] = 11
    service._task_data_hits[11] = 3
    service._task_log_buffers[11] = deque(["log"], maxlen=service._LOG_BUFFER_MAX)
    service._task_progress_states[11] = {
        "crawler_type": "detail",
        "target_ids": ["sn_1"],
        "processed_ids": ["sn_1"],
    }

    await service._wait_task_process(
        task_id=11,
        platform="wx",
        process=_FakeProcess(exit_code=0),
        run_id=111,
    )

    assert session.committed is True
    assert run.status == "success"
    assert task.status == "idle"
    assert int(task.success_count or 0) == 1
    assert stats["delete"] == 1
    assert stats["save"] == 0


@pytest.mark.asyncio
async def test_wait_task_process_stopped_for_wx_does_not_save_checkpoint():
    service = TaskSchedulerService()
    task = CrawlerTask(
        id=12,
        platform="wx",
        is_enabled=False,
        status="running",
        success_count=0,
        fail_count=0,
    )
    run = CrawlerTaskRun(id=112, task_id=12, platform="wx", status="running")
    session = _bind_fake_session(service, task, run)

    stats = {"save": 0, "delete": 0}

    async def fake_save(*args, **kwargs):
        stats["save"] += 1

    async def fake_delete(*args, **kwargs):
        stats["delete"] += 1

    service._save_checkpoint = fake_save  # type: ignore[assignment]
    service._delete_checkpoint = fake_delete  # type: ignore[assignment]
    service._running_processes[12] = object()  # type: ignore[assignment]
    service._running_run_ids[12] = 112
    service._platform_running_tasks["wx"] = 12
    service._stop_requested_tasks.add(12)
    service._task_data_hits[12] = 0
    service._task_log_buffers[12] = deque(["log"], maxlen=service._LOG_BUFFER_MAX)
    service._task_progress_states[12] = {
        "crawler_type": "search",
        "keywords": ["k1", "k2"],
        "current_keyword": "k1",
        "current_page": 2,
    }

    await service._wait_task_process(
        task_id=12,
        platform="wx",
        process=_FakeProcess(exit_code=0),
        run_id=112,
    )

    assert session.committed is True
    assert run.status == "killed"
    assert run.error_message == "stopped_by_user"
    assert task.status == "paused"
    assert stats["save"] == 0
    assert stats["delete"] == 1


@pytest.mark.asyncio
async def test_wait_task_process_failed_for_wx_does_not_save_checkpoint():
    service = TaskSchedulerService()
    task = CrawlerTask(
        id=13,
        platform="wx",
        is_enabled=True,
        status="running",
        success_count=0,
        fail_count=0,
    )
    run = CrawlerTaskRun(id=113, task_id=13, platform="wx", status="running")
    session = _bind_fake_session(service, task, run)

    stats = {"save": 0, "delete": 0}

    async def fake_save(*args, **kwargs):
        stats["save"] += 1

    async def fake_delete(*args, **kwargs):
        stats["delete"] += 1

    service._save_checkpoint = fake_save  # type: ignore[assignment]
    service._delete_checkpoint = fake_delete  # type: ignore[assignment]
    service._running_processes[13] = object()  # type: ignore[assignment]
    service._running_run_ids[13] = 113
    service._platform_running_tasks["wx"] = 13
    service._task_data_hits[13] = 0
    service._task_log_buffers[13] = deque(["log"], maxlen=service._LOG_BUFFER_MAX)
    service._task_progress_states[13] = {
        "crawler_type": "creator",
        "target_ids": ["MzA==", "MzB=="],
        "processed_ids": ["MzA=="],
    }

    await service._wait_task_process(
        task_id=13,
        platform="wx",
        process=_FakeProcess(exit_code=2),
        run_id=113,
    )

    assert session.committed is True
    assert run.status == "failed"
    assert run.error_message == "no_data_crawled (exit_code=2)"
    assert task.status == "error"
    assert int(task.fail_count or 0) == 1
    assert task.last_error == "no_data_crawled (exit_code=2)"
    assert stats["save"] == 0
    assert stats["delete"] == 1


@pytest.mark.asyncio
async def test_wait_task_process_stopped_for_non_wx_saves_checkpoint():
    service = TaskSchedulerService()
    task = CrawlerTask(
        id=14,
        platform="xhs",
        is_enabled=False,
        status="running",
        success_count=0,
        fail_count=0,
    )
    run = CrawlerTaskRun(id=114, task_id=14, platform="xhs", status="running")
    session = _bind_fake_session(service, task, run)

    saved_payloads = []
    stats = {"delete": 0}

    async def fake_save(_session, _task, payload, _now_ts):
        saved_payloads.append(payload)

    async def fake_delete(*args, **kwargs):
        stats["delete"] += 1

    service._save_checkpoint = fake_save  # type: ignore[assignment]
    service._delete_checkpoint = fake_delete  # type: ignore[assignment]
    service._running_processes[14] = object()  # type: ignore[assignment]
    service._running_run_ids[14] = 114
    service._platform_running_tasks["xhs"] = 14
    service._stop_requested_tasks.add(14)
    service._task_data_hits[14] = 0
    service._task_log_buffers[14] = deque(["log"], maxlen=service._LOG_BUFFER_MAX)
    service._task_progress_states[14] = {
        "crawler_type": "search",
        "keywords": ["k1", "k2"],
        "current_keyword": "k1",
        "current_page": 2,
    }

    await service._wait_task_process(
        task_id=14,
        platform="xhs",
        process=_FakeProcess(exit_code=0),
        run_id=114,
    )

    assert session.committed is True
    assert run.status == "killed"
    assert task.status == "paused"
    assert len(saved_payloads) == 1
    assert saved_payloads[0] == {
        "current_keyword": "k1",
        "current_page": 2,
        "remaining_keywords": ["k2"],
    }
    assert stats["delete"] == 0
