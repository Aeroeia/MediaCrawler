# -*- coding: utf-8 -*-
# Copyright (c) 2025 relakkes@gmail.com
#
# This file is part of MediaCrawler project.
# Repository: https://github.com/NanmiCoder/MediaCrawler/blob/main/api/services/task_scheduler_service.py
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

import asyncio
from collections import deque
import logging
import os
import re
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from zoneinfo import ZoneInfo

from croniter import croniter
from sqlalchemy import delete, select, update
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from api.schemas import PlatformEnum, TaskUpsertRequest
from config.db_config import mysql_db_config
from database.models import Base, CrawlerTask, CrawlerTaskRun


logger = logging.getLogger(__name__)


class TaskSchedulerError(RuntimeError):
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.status_code = status_code


class TaskSchedulerService:
    _TZ = ZoneInfo("Asia/Shanghai")
    _LOG_BUFFER_MAX = 600
    _DATA_HIT_RE = re.compile(r"\[store\.[^\]]+\.(update_|save_)", re.IGNORECASE)

    def __init__(self) -> None:
        mysql_url = (
            f"mysql+asyncmy://{mysql_db_config['user']}:{mysql_db_config['password']}"
            f"@{mysql_db_config['host']}:{mysql_db_config['port']}/{mysql_db_config['db_name']}"
        )
        self.engine: AsyncEngine = create_async_engine(
            mysql_url,
            echo=False,
            pool_pre_ping=True,
            poolclass=NullPool,
        )
        self.session_factory = async_sessionmaker(self.engine, expire_on_commit=False)
        self.project_root = Path(__file__).parent.parent.parent
        self._started = False
        self._scheduler_task: Optional[asyncio.Task] = None
        self._lock = asyncio.Lock()
        self._running_processes: Dict[int, subprocess.Popen] = {}
        self._running_run_ids: Dict[int, int] = {}
        self._platform_running_tasks: Dict[str, int] = {}
        self._monitor_tasks: Dict[int, asyncio.Task] = {}
        self._log_reader_tasks: Dict[int, asyncio.Task] = {}
        self._task_log_buffers: Dict[int, deque[str]] = {}
        self._last_task_log_buffers: Dict[int, deque[str]] = {}
        self._task_data_hits: Dict[int, int] = {}
        self._last_task_data_hits: Dict[int, int] = {}
        self._stop_requested_tasks: set[int] = set()

    @staticmethod
    def _now_ts() -> int:
        return int(time.time())

    @classmethod
    def _format_ts(cls, ts: int) -> str:
        if ts <= 0:
            return "-"
        return datetime.fromtimestamp(ts, tz=cls._TZ).strftime("%Y-%m-%d %H:%M:%S")

    @classmethod
    def _next_run_ts(cls, cron_expr: str, base_ts: Optional[int] = None) -> int:
        base_dt = datetime.fromtimestamp(base_ts or cls._now_ts(), tz=cls._TZ)
        return int(croniter(cron_expr, base_dt).get_next(datetime).timestamp())

    def _validate_cron_expr(self, cron_expr: str) -> None:
        try:
            self._next_run_ts(cron_expr, self._now_ts())
        except Exception as exc:
            raise TaskSchedulerError(f"Invalid cron_expr: {cron_expr}", status_code=400) from exc

    def _build_command(self, task: CrawlerTask) -> List[str]:
        cmd = ["uv", "run", "python", "main.py"]
        cmd.extend(["--platform", str(task.platform)])
        cmd.extend(["--lt", str(task.login_type or "qrcode")])
        cmd.extend(["--type", str(task.crawler_type or "search")])
        cmd.extend(["--save_data_option", str(task.save_option or "jsonl")])

        crawler_type = str(task.crawler_type or "")
        if crawler_type == "search" and task.keywords:
            cmd.extend(["--keywords", str(task.keywords)])
        elif crawler_type == "detail" and task.specified_ids:
            cmd.extend(["--specified_id", str(task.specified_ids)])
        elif crawler_type == "creator" and task.creator_ids:
            cmd.extend(["--creator_id", str(task.creator_ids)])

        if int(task.start_page or 1) != 1:
            cmd.extend(["--start", str(task.start_page)])

        cmd.extend(["--get_comment", "true" if bool(task.enable_comments) else "false"])
        cmd.extend(["--get_sub_comment", "true" if bool(task.enable_sub_comments) else "false"])
        if task.cookies:
            cmd.extend(["--cookies", str(task.cookies)])
        cmd.extend(["--headless", "true" if bool(task.headless) else "false"])
        return cmd

    @classmethod
    def _is_data_hit_line(cls, line: str) -> bool:
        return bool(cls._DATA_HIT_RE.search(line))

    def _append_task_log(self, task_id: int, line: str) -> None:
        if not line:
            return
        buf = self._task_log_buffers.setdefault(task_id, deque(maxlen=self._LOG_BUFFER_MAX))
        buf.append(line)

    def _task_to_dict(self, task: CrawlerTask) -> Dict[str, Any]:
        return {
            "id": task.id,
            "name": task.name,
            "description": task.description or "",
            "platform": task.platform,
            "priority": task.priority or "medium",
            "timeout_seconds": int(task.timeout_seconds or 30),
            "cron_expr": task.cron_expr,
            "is_enabled": bool(task.is_enabled),
            "status": task.status or "idle",
            "next_run_at": int(task.next_run_at or 0),
            "next_run_at_text": self._format_ts(int(task.next_run_at or 0)),
            "last_run_at": int(task.last_run_at or 0),
            "last_run_at_text": self._format_ts(int(task.last_run_at or 0)),
            "success_count": int(task.success_count or 0),
            "fail_count": int(task.fail_count or 0),
            "last_error": task.last_error or "",
            "running_pid": int(task.running_pid or 0),
            "data_hit_count": int(self._task_data_hits.get(task.id, self._last_task_data_hits.get(task.id, 0))),
            "crawler_params": {
                "crawler_type": task.crawler_type or "search",
                "login_type": task.login_type or "qrcode",
                "save_option": task.save_option or "jsonl",
                "keywords": task.keywords or "",
                "specified_ids": task.specified_ids or "",
                "creator_ids": task.creator_ids or "",
                "cookies": task.cookies or "",
                "start_page": int(task.start_page or 1),
                "enable_comments": bool(task.enable_comments),
                "enable_sub_comments": bool(task.enable_sub_comments),
                "headless": bool(task.headless),
            },
        }

    async def ensure_tables(self) -> None:
        async with self.engine.begin() as conn:
            await conn.run_sync(
                lambda sync_conn: Base.metadata.create_all(
                    sync_conn,
                    tables=[CrawlerTask.__table__, CrawlerTaskRun.__table__],
                )
            )

    async def _reset_stale_running_tasks(self) -> None:
        now_ts = self._now_ts()
        async with self.session_factory() as session:
            await session.execute(
                update(CrawlerTask)
                .where(CrawlerTask.status == "running")
                .values(status="idle", running_pid=0, last_modify_ts=now_ts)
            )
            await session.execute(
                update(CrawlerTaskRun)
                .where(CrawlerTaskRun.status == "running")
                .values(status="failed", finished_at=now_ts, error_message="service_restarted")
            )
            await session.commit()

    async def start(self) -> None:
        if self._started:
            return
        try:
            await self.ensure_tables()
            await self._reset_stale_running_tasks()
            self._started = True
            self._scheduler_task = asyncio.create_task(self._scheduler_loop(), name="task-scheduler-loop")
            logger.info("[task_scheduler] started")
        except Exception:
            logger.exception("[task_scheduler] failed to start")
            self._started = False
            raise

    async def stop(self) -> None:
        self._started = False
        if self._scheduler_task:
            self._scheduler_task.cancel()
            try:
                await self._scheduler_task
            except asyncio.CancelledError:
                pass
            self._scheduler_task = None

        for task_id in list(self._running_processes.keys()):
            try:
                await self.stop_task(task_id)
            except Exception:
                logger.exception("[task_scheduler] stop task %s failed on shutdown", task_id)

        for monitor in list(self._monitor_tasks.values()):
            monitor.cancel()
        for reader in list(self._log_reader_tasks.values()):
            reader.cancel()
        self._log_reader_tasks.clear()
        self._monitor_tasks.clear()
        self._running_processes.clear()
        self._running_run_ids.clear()
        self._platform_running_tasks.clear()
        self._task_log_buffers.clear()
        self._last_task_log_buffers.clear()
        self._task_data_hits.clear()
        self._last_task_data_hits.clear()
        self._stop_requested_tasks.clear()
        await self.engine.dispose()
        logger.info("[task_scheduler] stopped")

    async def _scheduler_loop(self) -> None:
        while self._started:
            try:
                await self._schedule_due_tasks()
            except Exception:
                logger.exception("[task_scheduler] scheduler loop error")
            await asyncio.sleep(1)

    async def _schedule_due_tasks(self) -> None:
        now_ts = self._now_ts()
        async with self.session_factory() as session:
            result = await session.execute(
                select(CrawlerTask.id)
                .where(CrawlerTask.is_enabled.is_(True))
                .where(CrawlerTask.next_run_at > 0)
                .where(CrawlerTask.next_run_at <= now_ts)
                .order_by(CrawlerTask.next_run_at.asc())
            )
            due_task_ids = [row[0] for row in result.fetchall()]

        for task_id in due_task_ids:
            try:
                await self._start_task(task_id, trigger_type="cron", allow_busy_skip=True)
            except TaskSchedulerError:
                # expected business errors are already reflected in task status/run records
                continue
            except Exception:
                logger.exception("[task_scheduler] start due task %s failed", task_id)

    async def _insert_run(
        self,
        session: AsyncSession,
        task: CrawlerTask,
        trigger_type: str,
        status: str,
        started_at: int,
        pid: int = 0,
        finished_at: int = 0,
        exit_code: int = 0,
        error_message: str = "",
    ) -> int:
        run = CrawlerTaskRun(
            task_id=task.id,
            platform=task.platform,
            trigger_type=trigger_type,
            status=status,
            started_at=started_at,
            finished_at=finished_at,
            exit_code=exit_code,
            pid=pid,
            error_message=error_message,
        )
        session.add(run)
        await session.flush()
        return int(run.id)

    async def _read_task_output(self, task_id: int, process: subprocess.Popen) -> None:
        if not process.stdout:
            return
        loop = asyncio.get_running_loop()
        try:
            while True:
                line = await loop.run_in_executor(None, process.stdout.readline)
                if not line:
                    if process.poll() is not None:
                        break
                    await asyncio.sleep(0.05)
                    continue
                msg = line.rstrip("\r\n")
                if not msg:
                    continue
                self._append_task_log(task_id, msg)
                if self._is_data_hit_line(msg):
                    self._task_data_hits[task_id] = int(self._task_data_hits.get(task_id, 0)) + 1

            remaining = await loop.run_in_executor(None, process.stdout.read)
            if remaining:
                for row in remaining.splitlines():
                    msg = row.strip()
                    if not msg:
                        continue
                    self._append_task_log(task_id, msg)
                    if self._is_data_hit_line(msg):
                        self._task_data_hits[task_id] = int(self._task_data_hits.get(task_id, 0)) + 1
        except asyncio.CancelledError:
            pass
        except Exception as exc:
            self._append_task_log(task_id, f"[task_scheduler.log_reader] {exc}")
        finally:
            try:
                process.stdout.close()
            except Exception:
                pass

    async def _start_task(self, task_id: int, trigger_type: str, allow_busy_skip: bool = False) -> Dict[str, Any]:
        now_ts = self._now_ts()
        async with self._lock:
            if task_id in self._running_processes:
                raise TaskSchedulerError("Task is already running", status_code=409)

            async with self.session_factory() as session:
                task = await session.get(CrawlerTask, task_id)
                if not task:
                    raise TaskSchedulerError("Task not found", status_code=404)

                if task.platform in self._platform_running_tasks:
                    if allow_busy_skip and trigger_type == "cron":
                        await self._insert_run(
                            session=session,
                            task=task,
                            trigger_type=trigger_type,
                            status="skipped",
                            started_at=now_ts,
                            finished_at=now_ts,
                            error_message="platform_busy",
                        )
                        task.status = "idle"
                        task.next_run_at = self._next_run_ts(task.cron_expr, now_ts)
                        task.last_modify_ts = now_ts
                        await session.commit()
                        raise TaskSchedulerError("Platform is busy", status_code=409)
                    raise TaskSchedulerError("Platform is busy", status_code=409)

                command = self._build_command(task)
                try:
                    process = subprocess.Popen(
                        command,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT,
                        text=True,
                        encoding="utf-8",
                        errors="ignore",
                        bufsize=1,
                        cwd=str(self.project_root),
                        env={**os.environ, "PYTHONUNBUFFERED": "1"},
                    )
                except Exception as exc:
                    raise TaskSchedulerError(f"Failed to start task process: {exc}", status_code=500) from exc

                run_id = await self._insert_run(
                    session=session,
                    task=task,
                    trigger_type=trigger_type,
                    status="running",
                    started_at=now_ts,
                    pid=int(process.pid or 0),
                )

                task.status = "running"
                task.running_pid = int(process.pid or 0)
                task.last_run_at = now_ts
                task.last_modify_ts = now_ts
                if task.is_enabled:
                    task.next_run_at = self._next_run_ts(task.cron_expr, now_ts)
                await session.commit()

                self._running_processes[task_id] = process
                self._running_run_ids[task_id] = run_id
                self._platform_running_tasks[task.platform] = task_id
                self._task_log_buffers[task_id] = deque(maxlen=self._LOG_BUFFER_MAX)
                self._task_data_hits[task_id] = 0
                log_reader = asyncio.create_task(
                    self._read_task_output(task_id=task_id, process=process),
                    name=f"task-log-reader-{task_id}",
                )
                self._log_reader_tasks[task_id] = log_reader
                monitor = asyncio.create_task(
                    self._wait_task_process(task_id=task_id, platform=task.platform, process=process, run_id=run_id)
                )
                self._monitor_tasks[task_id] = monitor
                return {"task_id": task_id, "run_id": run_id, "pid": int(process.pid or 0)}

    async def _wait_task_process(self, task_id: int, platform: str, process: subprocess.Popen, run_id: int) -> None:
        exit_code = await asyncio.to_thread(process.wait)
        reader_task = self._log_reader_tasks.pop(task_id, None)
        if reader_task:
            try:
                await reader_task
            except asyncio.CancelledError:
                pass
            except Exception:
                logger.exception("[task_scheduler] task %s log reader failed", task_id)
        now_ts = self._now_ts()
        was_stopped = task_id in self._stop_requested_tasks
        data_hits = int(self._task_data_hits.pop(task_id, 0))
        self._last_task_data_hits[task_id] = data_hits
        logs = self._task_log_buffers.pop(task_id, deque(maxlen=self._LOG_BUFFER_MAX))
        self._last_task_log_buffers[task_id] = deque(logs, maxlen=self._LOG_BUFFER_MAX)
        async with self._lock:
            if was_stopped:
                self._stop_requested_tasks.discard(task_id)

            self._running_processes.pop(task_id, None)
            self._running_run_ids.pop(task_id, None)
            if self._platform_running_tasks.get(platform) == task_id:
                self._platform_running_tasks.pop(platform, None)
            self._monitor_tasks.pop(task_id, None)

            async with self.session_factory() as session:
                task = await session.get(CrawlerTask, task_id)
                run = await session.get(CrawlerTaskRun, run_id)
                if run:
                    if was_stopped:
                        run.status = "killed"
                        run.error_message = "stopped_by_user"
                    elif data_hits > 0:
                        run.status = "success"
                        run.error_message = ""
                    else:
                        run.status = "failed"
                        run.error_message = f"no_data_crawled (exit_code={int(exit_code or 0)})"
                    run.finished_at = now_ts
                    run.exit_code = int(exit_code or 0)

                if task:
                    task.running_pid = 0
                    task.last_modify_ts = now_ts
                    if was_stopped:
                        task.status = "paused" if not bool(task.is_enabled) else "idle"
                    elif data_hits > 0:
                        task.status = "idle"
                        task.success_count = int(task.success_count or 0) + 1
                        task.last_error = ""
                    else:
                        task.status = "error"
                        task.fail_count = int(task.fail_count or 0) + 1
                        task.last_error = f"no_data_crawled (exit_code={int(exit_code or 0)})"

                await session.commit()

    async def list_tasks(self) -> Dict[str, Any]:
        try:
            async with self.session_factory() as session:
                result = await session.execute(select(CrawlerTask).order_by(CrawlerTask.id.desc()))
                tasks = [self._task_to_dict(item) for item in result.scalars().all()]

            status_map = await self.get_platform_status()
            status_by_platform = {item["platform"]: item for item in status_map["rows"]}
            for task in tasks:
                platform_status = status_by_platform.get(task["platform"], {"busy": False, "running_task_id": 0})
                task["platform_busy"] = bool(platform_status.get("busy", False))
                task["platform_running_task_id"] = int(platform_status.get("running_task_id", 0))
            return {"rows": tasks}
        except SQLAlchemyError as exc:
            raise TaskSchedulerError(f"MySQL query failed: {exc}", status_code=503) from exc

    async def create_task(self, payload: TaskUpsertRequest) -> Dict[str, Any]:
        self._validate_cron_expr(payload.cron_expr)
        now_ts = self._now_ts()
        next_run_at = self._next_run_ts(payload.cron_expr, now_ts) if payload.is_enabled else 0
        task = CrawlerTask(
            name=payload.name.strip(),
            description=payload.description.strip(),
            platform=payload.platform.value,
            crawler_type=payload.crawler_type.value,
            login_type=payload.login_type.value,
            save_option=payload.save_option.value,
            keywords=payload.keywords.strip(),
            specified_ids=payload.specified_ids.strip(),
            creator_ids=payload.creator_ids.strip(),
            cookies=payload.cookies.strip(),
            start_page=int(payload.start_page),
            enable_comments=bool(payload.enable_comments),
            enable_sub_comments=bool(payload.enable_sub_comments),
            headless=bool(payload.headless),
            priority=payload.priority,
            timeout_seconds=int(payload.timeout_seconds),
            cron_expr=payload.cron_expr.strip(),
            is_enabled=bool(payload.is_enabled),
            status="idle" if payload.is_enabled else "paused",
            next_run_at=next_run_at,
            last_run_at=0,
            success_count=0,
            fail_count=0,
            last_error="",
            running_pid=0,
            add_ts=now_ts,
            last_modify_ts=now_ts,
        )
        try:
            async with self.session_factory() as session:
                session.add(task)
                await session.commit()
                await session.refresh(task)
            return self._task_to_dict(task)
        except SQLAlchemyError as exc:
            raise TaskSchedulerError(f"MySQL query failed: {exc}", status_code=503) from exc

    async def update_task(self, task_id: int, payload: TaskUpsertRequest) -> Dict[str, Any]:
        self._validate_cron_expr(payload.cron_expr)
        now_ts = self._now_ts()
        try:
            async with self._lock:
                if task_id in self._running_processes:
                    raise TaskSchedulerError("Task is running, stop it before edit", status_code=409)
                async with self.session_factory() as session:
                    task = await session.get(CrawlerTask, task_id)
                    if not task:
                        raise TaskSchedulerError("Task not found", status_code=404)

                    task.name = payload.name.strip()
                    task.description = payload.description.strip()
                    task.platform = payload.platform.value
                    task.crawler_type = payload.crawler_type.value
                    task.login_type = payload.login_type.value
                    task.save_option = payload.save_option.value
                    task.keywords = payload.keywords.strip()
                    task.specified_ids = payload.specified_ids.strip()
                    task.creator_ids = payload.creator_ids.strip()
                    task.cookies = payload.cookies.strip()
                    task.start_page = int(payload.start_page)
                    task.enable_comments = bool(payload.enable_comments)
                    task.enable_sub_comments = bool(payload.enable_sub_comments)
                    task.headless = bool(payload.headless)
                    task.priority = payload.priority
                    task.timeout_seconds = int(payload.timeout_seconds)
                    task.cron_expr = payload.cron_expr.strip()
                    task.is_enabled = bool(payload.is_enabled)
                    task.status = "idle" if payload.is_enabled else "paused"
                    task.next_run_at = self._next_run_ts(task.cron_expr, now_ts) if payload.is_enabled else 0
                    task.last_modify_ts = now_ts
                    await session.commit()
                    await session.refresh(task)
                    return self._task_to_dict(task)
        except SQLAlchemyError as exc:
            raise TaskSchedulerError(f"MySQL query failed: {exc}", status_code=503) from exc

    async def delete_task(self, task_id: int) -> None:
        try:
            async with self._lock:
                if task_id in self._running_processes:
                    raise TaskSchedulerError("Task is running, stop it before delete", status_code=409)
                async with self.session_factory() as session:
                    task = await session.get(CrawlerTask, task_id)
                    if not task:
                        raise TaskSchedulerError("Task not found", status_code=404)
                    await session.execute(delete(CrawlerTaskRun).where(CrawlerTaskRun.task_id == task_id))
                    await session.delete(task)
                    await session.commit()
        except SQLAlchemyError as exc:
            raise TaskSchedulerError(f"MySQL query failed: {exc}", status_code=503) from exc

    async def run_now(self, task_id: int) -> Dict[str, Any]:
        return await self._start_task(task_id, trigger_type="manual", allow_busy_skip=False)

    async def pause_task(self, task_id: int) -> Dict[str, Any]:
        now_ts = self._now_ts()
        try:
            async with self.session_factory() as session:
                task = await session.get(CrawlerTask, task_id)
                if not task:
                    raise TaskSchedulerError("Task not found", status_code=404)
                task.is_enabled = False
                if task_id not in self._running_processes:
                    task.status = "paused"
                task.next_run_at = 0
                task.last_modify_ts = now_ts
                await session.commit()
                await session.refresh(task)
                return self._task_to_dict(task)
        except SQLAlchemyError as exc:
            raise TaskSchedulerError(f"MySQL query failed: {exc}", status_code=503) from exc

    async def resume_task(self, task_id: int) -> Dict[str, Any]:
        now_ts = self._now_ts()
        try:
            async with self.session_factory() as session:
                task = await session.get(CrawlerTask, task_id)
                if not task:
                    raise TaskSchedulerError("Task not found", status_code=404)
                self._validate_cron_expr(task.cron_expr)
                task.is_enabled = True
                task.next_run_at = self._next_run_ts(task.cron_expr, now_ts)
                if task_id not in self._running_processes:
                    task.status = "idle"
                task.last_modify_ts = now_ts
                await session.commit()
                await session.refresh(task)
                return self._task_to_dict(task)
        except SQLAlchemyError as exc:
            raise TaskSchedulerError(f"MySQL query failed: {exc}", status_code=503) from exc

    async def stop_task(self, task_id: int) -> Dict[str, Any]:
        async with self._lock:
            process = self._running_processes.get(task_id)
            if not process or process.poll() is not None:
                raise TaskSchedulerError("Task is not running", status_code=400)
            self._stop_requested_tasks.add(task_id)
            process.terminate()

        try:
            await asyncio.to_thread(process.wait, 15)
        except subprocess.TimeoutExpired:
            process.kill()
            await asyncio.to_thread(process.wait)
        return {"task_id": task_id, "message": "stopped"}

    async def get_task_runs(self, task_id: int, limit: int) -> Dict[str, Any]:
        limit = max(1, min(limit, 200))
        try:
            async with self.session_factory() as session:
                task = await session.get(CrawlerTask, task_id)
                if not task:
                    raise TaskSchedulerError("Task not found", status_code=404)

                result = await session.execute(
                    select(CrawlerTaskRun)
                    .where(CrawlerTaskRun.task_id == task_id)
                    .order_by(CrawlerTaskRun.id.desc())
                    .limit(limit)
                )
                rows = []
                for row in result.scalars().all():
                    rows.append(
                        {
                            "id": int(row.id),
                            "task_id": int(row.task_id),
                            "platform": row.platform,
                            "trigger_type": row.trigger_type,
                            "status": row.status,
                            "started_at": int(row.started_at or 0),
                            "started_at_text": self._format_ts(int(row.started_at or 0)),
                            "finished_at": int(row.finished_at or 0),
                            "finished_at_text": self._format_ts(int(row.finished_at or 0)),
                            "exit_code": int(row.exit_code or 0),
                            "pid": int(row.pid or 0),
                            "error_message": row.error_message or "",
                        }
                    )
                return {"rows": rows}
        except SQLAlchemyError as exc:
            raise TaskSchedulerError(f"MySQL query failed: {exc}", status_code=503) from exc

    async def get_task_logs(self, task_id: int, limit: int) -> Dict[str, Any]:
        limit = max(1, min(limit, 1000))
        try:
            async with self.session_factory() as session:
                task = await session.get(CrawlerTask, task_id)
                if not task:
                    raise TaskSchedulerError("Task not found", status_code=404)

            async with self._lock:
                running = task_id in self._running_processes
                buf = self._task_log_buffers.get(task_id) if running else self._last_task_log_buffers.get(task_id)
                logs = list(buf or [])
                data_hit_count = int(
                    self._task_data_hits.get(task_id, self._last_task_data_hits.get(task_id, 0))
                )
            return {
                "task_id": task_id,
                "running": running,
                "data_hit_count": data_hit_count,
                "rows": logs[-limit:],
            }
        except SQLAlchemyError as exc:
            raise TaskSchedulerError(f"MySQL query failed: {exc}", status_code=503) from exc

    async def get_platform_status(self) -> Dict[str, Any]:
        async with self._lock:
            busy_map = dict(self._platform_running_tasks)

        rows = []
        for platform in PlatformEnum:
            running_task_id = int(busy_map.get(platform.value, 0) or 0)
            rows.append(
                {
                    "platform": platform.value,
                    "busy": running_task_id > 0,
                    "running_task_id": running_task_id,
                }
            )
        return {"rows": rows}


task_scheduler_service = TaskSchedulerService()
