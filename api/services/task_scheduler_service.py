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
import json
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
from sqlalchemy import delete, select, text, update
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from api.schemas import PlatformEnum, TaskUpsertRequest
from config.db_config import mysql_db_config
from database.models import Base, CrawlerTask, CrawlerTaskCheckpoint, CrawlerTaskRun, GovArticle
from media_platform.gov.rule_loader import GovRuleLoader
from media_platform.gov.site_registry import GovSiteRegistry


logger = logging.getLogger(__name__)


class TaskSchedulerError(RuntimeError):
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.status_code = status_code


class TaskSchedulerService:
    _TZ = ZoneInfo("Asia/Shanghai")
    _LOG_BUFFER_MAX = 600
    _DATA_HIT_RE = re.compile(r"\[store\.[^\]]+\.(update_|save_)", re.IGNORECASE)
    _CURRENT_KEYWORD_RE = re.compile(r"Current(?: search)? keyword:\s*(.+)$", re.IGNORECASE)
    _SEARCH_PAGE_RE = re.compile(r"search .* keyword:\s*(.+?),\s*(?:date:.*?,\s*)?page:\s*(\d+)", re.IGNORECASE)
    _SKIP_PAGE_RE = re.compile(r"Skip page[:\s]+(\d+)|Skip[:\s]+(\d+)", re.IGNORECASE)
    _ID_CANDIDATE_PATTERNS = (
        re.compile(
            r"\b(?:note_id|aweme_id|video_id|content_id|creator_id|user_id|sec_user_id|bvid|aid|article_id|answer_id|biz|__biz|sn)\s*[:=]\s*['\"]?([A-Za-z0-9_\-=+/]+)",
            re.IGNORECASE,
        ),
        re.compile(r"['\"](?:note_id|aweme_id|video_id|content_id|user_id|id|biz|__biz|sn)['\"]\s*:\s*['\"]([^'\"]+)['\"]", re.IGNORECASE),
    )

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
        self._task_progress_states: Dict[int, Dict[str, Any]] = {}
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

    @staticmethod
    def _split_csv_values(value: str) -> List[str]:
        if not value:
            return []
        rows = re.split(r"[,\n，]+", value)
        return [item.strip() for item in rows if item and item.strip()]

    @staticmethod
    def _join_csv_values(rows: List[str]) -> str:
        return ",".join([item for item in rows if item])

    @staticmethod
    def _safe_json_loads(raw: str) -> Dict[str, Any]:
        if not raw:
            return {}
        try:
            payload = json.loads(raw)
            return payload if isinstance(payload, dict) else {}
        except Exception:
            return {}

    @staticmethod
    def _is_resume_supported(platform: str) -> bool:
        return str(platform or "").lower() != "wx"

    def _normalize_task_upsert_payload(self, payload: TaskUpsertRequest) -> Dict[str, Any]:
        platform = payload.platform.value
        is_wx = platform == "wx"
        is_gov = platform == "gov"
        normalized = {
            "name": payload.name.strip(),
            "description": payload.description.strip(),
            "platform": platform,
            "crawler_type": payload.crawler_type.value,
            "login_type": payload.login_type.value,
            "save_option": payload.save_option.value,
            "keywords": payload.keywords.strip(),
            "specified_ids": payload.specified_ids.strip(),
            "creator_ids": payload.creator_ids.strip(),
            "gov_site": payload.gov_site.strip(),
            "gov_channel": payload.gov_channel.strip(),
            "gov_max_pages": max(1, int(payload.gov_max_pages or 1)),
            "gov_rule_path": payload.gov_rule_path.strip(),
            "cookies": payload.cookies.strip(),
            "start_page": int(payload.start_page),
            "enable_comments": bool(payload.enable_comments),
            "enable_sub_comments": bool(payload.enable_sub_comments),
            "headless": bool(payload.headless),
            "priority": payload.priority,
            "timeout_seconds": int(payload.timeout_seconds),
            "is_enabled": bool(payload.is_enabled),
            "manual_only": bool(payload.manual_only) or is_wx,
            "cron_expr": payload.cron_expr.strip(),
        }

        if is_wx:
            normalized.update(
                {
                    "description": "",
                    "crawler_type": "detail",
                    "keywords": "",
                    "creator_ids": "",
                    "gov_site": "",
                    "gov_channel": "",
                    "gov_max_pages": 1,
                    "gov_rule_path": "",
                    "login_type": "qrcode",
                    "cookies": "",
                    "start_page": 1,
                    "enable_comments": True,
                    "enable_sub_comments": False,
                    "headless": False,
                    "priority": "medium",
                    "timeout_seconds": 30,
                    "manual_only": True,
                    "cron_expr": "",
                }
            )
        elif is_gov:
            if normalized["crawler_type"] == "creator":
                raise TaskSchedulerError("gov platform does not support creator mode", status_code=400)
            if normalized["crawler_type"] not in ("search", "detail"):
                raise TaskSchedulerError(
                    f"Unsupported gov crawler_type: {normalized['crawler_type']}",
                    status_code=400,
                )
            if not normalized["gov_site"]:
                raise TaskSchedulerError("gov_site is required for gov platform tasks", status_code=400)

            try:
                site_info = GovSiteRegistry.get_site(site_code=normalized["gov_site"])
            except Exception:
                if normalized["gov_rule_path"]:
                    site_info = {"default_channel": "main", "status": "ready"}
                else:
                    raise TaskSchedulerError(
                        f"gov_site '{normalized['gov_site']}' is not in gov manifest",
                        status_code=400,
                    )
            raw_channel = normalized["gov_channel"]
            channels = self._split_csv_values(raw_channel)
            if not channels:
                channels = [str(site_info.get("default_channel") or "main").strip() or "main"]

            status = str(site_info.get("status") or "").strip().lower()
            if status == "ready" and not normalized["gov_rule_path"]:
                try:
                    rule = GovRuleLoader().load_site_rule(site=normalized["gov_site"])
                    for ch in channels:
                        GovRuleLoader.get_channel_rule(rule=rule, channel=ch)
                except Exception as exc:
                    raise TaskSchedulerError(
                        f"gov_channel '{','.join(channels)}' is not valid for site '{normalized['gov_site']}'",
                        status_code=400,
                    ) from exc

            normalized["gov_channel"] = ",".join(channels)
            if status != "ready":
                verify_error = str(site_info.get("verify_error") or "").strip()
                raise TaskSchedulerError(
                    f"gov_site '{normalized['gov_site']}' is not ready (status={status or 'unknown'})"
                    + (f", reason={verify_error}" if verify_error else ""),
                    status_code=400,
                )

            normalized.update(
                {
                    "keywords": "",
                    "creator_ids": "",
                    "login_type": "qrcode",
                    "cookies": "",
                    "start_page": 1,
                    "enable_comments": False,
                    "enable_sub_comments": False,
                    "headless": True,
                }
            )
        else:
            normalized.update(
                {
                    "gov_site": "",
                    "gov_channel": "",
                    "gov_max_pages": 1,
                    "gov_rule_path": "",
                }
            )

        if normalized["manual_only"]:
            normalized["cron_expr"] = ""
        else:
            self._validate_cron_expr(str(normalized["cron_expr"]))
        return normalized

    @classmethod
    def _id_token_match(cls, target: str, candidate: str) -> bool:
        a = str(target or "").strip().lower()
        b = str(candidate or "").strip().lower()
        if not a or not b:
            return False
        if a == b:
            return True
        if a in b or b in a:
            return True
        return False

    @classmethod
    def _extract_id_candidates(cls, line: str) -> List[str]:
        candidates: List[str] = []
        text = str(line or "")
        for pattern in cls._ID_CANDIDATE_PATTERNS:
            for match in pattern.findall(text):
                value = str(match or "").strip().strip("'\"")
                if value:
                    candidates.append(value)
        return candidates

    def _extract_processed_target(self, target_ids: List[str], line: str) -> str:
        if not target_ids:
            return ""
        text = str(line or "")
        for target in target_ids:
            if target and target in text:
                return target
        for candidate in self._extract_id_candidates(text):
            for target in target_ids:
                if self._id_token_match(target, candidate):
                    return target
        return ""

    def _build_search_checkpoint_summary(self, payload: Dict[str, Any]) -> tuple[bool, str]:
        current_keyword = str(payload.get("current_keyword") or "").strip()
        current_page = int(payload.get("current_page") or 1)
        remaining = payload.get("remaining_keywords") or []
        remaining_count = len([item for item in remaining if str(item or "").strip()])
        available = bool(current_keyword or remaining_count > 0)
        if not available:
            return False, ""
        return (
            True,
            f"关键词: {current_keyword or '-'} | 页码: {max(1, current_page)} | 后续关键词: {remaining_count}",
        )

    def _build_id_checkpoint_summary(self, payload: Dict[str, Any]) -> tuple[bool, str]:
        processed_ids = [str(item).strip() for item in (payload.get("processed_ids") or []) if str(item).strip()]
        remaining_ids = [str(item).strip() for item in (payload.get("remaining_ids") or []) if str(item).strip()]
        available = len(remaining_ids) > 0
        if not processed_ids and not remaining_ids:
            return False, ""
        return available, f"剩余ID: {len(remaining_ids)} | 已处理: {len(processed_ids)}"

    def _checkpoint_fields(self, crawler_type: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        checkpoint_type = str(crawler_type or "")
        if checkpoint_type == "search":
            available, summary = self._build_search_checkpoint_summary(payload)
        else:
            available, summary = self._build_id_checkpoint_summary(payload)
        return {
            "resume_available": bool(available),
            "resume_type": checkpoint_type if summary else "",
            "resume_summary": summary or "",
        }

    def _build_resume_override(
        self,
        crawler_type: str,
        payload: Dict[str, Any],
    ) -> tuple[Dict[str, Any], bool]:
        checkpoint_type = str(crawler_type or "")
        if checkpoint_type == "search":
            current_keyword = str(payload.get("current_keyword") or "").strip()
            current_page = max(1, int(payload.get("current_page") or 1))
            remaining = [str(item).strip() for item in (payload.get("remaining_keywords") or []) if str(item).strip()]
            keyword_rows: List[str] = []
            if current_keyword:
                keyword_rows.append(current_keyword)
            keyword_rows.extend(remaining)
            if not keyword_rows:
                return {}, False
            return {
                "keywords": self._join_csv_values(keyword_rows),
                "start_page": current_page,
                "resume_mode": True,
            }, True
        if checkpoint_type == "detail":
            remaining_ids = [str(item).strip() for item in (payload.get("remaining_ids") or []) if str(item).strip()]
            if not remaining_ids:
                return {}, False
            return {"specified_ids": self._join_csv_values(remaining_ids), "resume_mode": True}, True
        if checkpoint_type == "creator":
            remaining_ids = [str(item).strip() for item in (payload.get("remaining_ids") or []) if str(item).strip()]
            if not remaining_ids:
                return {}, False
            return {"creator_ids": self._join_csv_values(remaining_ids), "resume_mode": True}, True
        return {}, False

    def _build_command(self, task: CrawlerTask, override_params: Optional[Dict[str, Any]] = None) -> tuple[List[str], Dict[str, Any]]:
        override_params = override_params or {}
        cmd = ["uv", "run", "python", "main.py"]
        platform = str(task.platform or "")
        cmd.extend(["--platform", platform])
        cmd.extend(["--lt", str(task.login_type or "qrcode")])
        cmd.extend(["--type", str(task.crawler_type or "search")])
        cmd.extend(["--save_data_option", str(task.save_option or "jsonl")])

        crawler_type = str(task.crawler_type or "")
        keywords = str(override_params.get("keywords", task.keywords or ""))
        specified_ids = str(override_params.get("specified_ids", task.specified_ids or ""))
        creator_ids = str(override_params.get("creator_ids", task.creator_ids or ""))
        start_page = int(override_params.get("start_page", task.start_page or 1))

        if crawler_type == "search" and keywords:
            cmd.extend(["--keywords", keywords])
        elif crawler_type == "detail" and specified_ids:
            cmd.extend(["--specified_id", specified_ids])
        elif crawler_type == "creator" and creator_ids:
            cmd.extend(["--creator_id", creator_ids])

        if start_page != 1:
            cmd.extend(["--start", str(start_page)])

        gov_site = str(getattr(task, "gov_site", "") or "")
        gov_channel = str(getattr(task, "gov_channel", "") or "")
        gov_max_pages = max(1, int(getattr(task, "gov_max_pages", 1) or 1))
        gov_rule_path = str(getattr(task, "gov_rule_path", "") or "")
        if platform == "gov":
            if gov_site:
                cmd.extend(["--gov_site", gov_site])
            if gov_channel:
                cmd.extend(["--gov_channel", gov_channel])
            cmd.extend(["--gov_max_pages", str(gov_max_pages)])
            if gov_rule_path:
                cmd.extend(["--gov_rule_path", gov_rule_path])

        cmd.extend(["--get_comment", "true" if bool(task.enable_comments) else "false"])
        cmd.extend(["--get_sub_comment", "true" if bool(task.enable_sub_comments) else "false"])
        if task.cookies:
            cmd.extend(["--cookies", str(task.cookies)])
        cmd.extend(["--headless", "true" if bool(task.headless) else "false"])
        if bool(override_params.get("resume_mode", False)):
            cmd.extend(["--resume_mode", "true"])

        return cmd, {
            "crawler_type": crawler_type,
            "keywords": keywords,
            "specified_ids": specified_ids,
            "creator_ids": creator_ids,
            "start_page": start_page,
            "gov_site": gov_site,
            "gov_channel": gov_channel,
            "gov_max_pages": gov_max_pages,
            "gov_rule_path": gov_rule_path,
            "resume_mode": bool(override_params.get("resume_mode", False)),
        }

    def _init_task_progress(self, task_id: int, runtime_params: Dict[str, Any]) -> None:
        crawler_type = str(runtime_params.get("crawler_type") or "").strip()
        if crawler_type == "search":
            keywords = self._split_csv_values(str(runtime_params.get("keywords", "")))
            self._task_progress_states[task_id] = {
                "crawler_type": "search",
                "keywords": keywords,
                "current_keyword": keywords[0] if keywords else "",
                "current_page": max(1, int(runtime_params.get("start_page") or 1)),
            }
            return

        if crawler_type == "detail":
            target_ids = self._split_csv_values(str(runtime_params.get("specified_ids", "")))
            self._task_progress_states[task_id] = {
                "crawler_type": "detail",
                "target_ids": target_ids,
                "processed_ids": [],
            }
            return

        if crawler_type == "creator":
            target_ids = self._split_csv_values(str(runtime_params.get("creator_ids", "")))
            self._task_progress_states[task_id] = {
                "crawler_type": "creator",
                "target_ids": target_ids,
                "processed_ids": [],
            }
            return

        self._task_progress_states[task_id] = {
            "crawler_type": crawler_type,
        }

    def _track_task_progress(self, task_id: int, line: str) -> None:
        state = self._task_progress_states.get(task_id)
        if not state:
            return

        crawler_type = str(state.get("crawler_type") or "")
        text = str(line or "")
        if crawler_type == "search":
            keyword_match = self._CURRENT_KEYWORD_RE.search(text)
            if keyword_match:
                keyword = str(keyword_match.group(1) or "").strip()
                if keyword:
                    state["current_keyword"] = keyword
                    if not state.get("keywords"):
                        state["keywords"] = [keyword]
                return

            page_match = self._SEARCH_PAGE_RE.search(text)
            if page_match:
                keyword = str(page_match.group(1) or "").strip()
                if keyword:
                    state["current_keyword"] = keyword
                page = int(page_match.group(2) or 1)
                state["current_page"] = max(1, page)
                return

            skip_match = self._SKIP_PAGE_RE.search(text)
            if skip_match:
                skip_page = int(skip_match.group(1) or skip_match.group(2) or 1)
                state["current_page"] = max(1, skip_page)
            return

        if crawler_type in ("detail", "creator"):
            target_ids = [str(item) for item in (state.get("target_ids") or []) if str(item).strip()]
            if not target_ids:
                return
            matched = self._extract_processed_target(target_ids, text)
            if not matched:
                return
            processed = state.setdefault("processed_ids", [])
            if matched not in processed:
                processed.append(matched)

    def _build_checkpoint_payload(self, task_id: int) -> Dict[str, Any]:
        state = self._task_progress_states.get(task_id) or {}
        crawler_type = str(state.get("crawler_type") or "")

        if crawler_type == "search":
            keywords = [str(item).strip() for item in (state.get("keywords") or []) if str(item).strip()]
            current_keyword = str(state.get("current_keyword") or "").strip()
            current_page = max(1, int(state.get("current_page") or 1))
            if not keywords and not current_keyword:
                return {}

            if current_keyword and current_keyword in keywords:
                index = keywords.index(current_keyword)
                remaining = keywords[index + 1 :]
            else:
                remaining = [item for item in keywords if item != current_keyword]
                if not current_keyword and keywords:
                    current_keyword = keywords[0]
                    remaining = keywords[1:]

            return {
                "current_keyword": current_keyword,
                "current_page": current_page,
                "remaining_keywords": remaining,
            }

        if crawler_type in ("detail", "creator"):
            target_ids = [str(item).strip() for item in (state.get("target_ids") or []) if str(item).strip()]
            processed_ids = [str(item).strip() for item in (state.get("processed_ids") or []) if str(item).strip()]
            if not target_ids and not processed_ids:
                return {}
            processed_set = {item for item in processed_ids}
            remaining_ids = [item for item in target_ids if item not in processed_set]
            return {
                "processed_ids": processed_ids,
                "remaining_ids": remaining_ids,
            }

        return {}

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
            "manual_only": bool(task.manual_only),
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
                "gov_site": task.gov_site or "",
                "gov_channel": task.gov_channel or "",
                "gov_max_pages": int(task.gov_max_pages or 1),
                "gov_rule_path": task.gov_rule_path or "",
                "cookies": task.cookies or "",
                "start_page": int(task.start_page or 1),
                "enable_comments": bool(task.enable_comments),
                "enable_sub_comments": bool(task.enable_sub_comments),
                "headless": bool(task.headless),
                "manual_only": bool(task.manual_only),
            },
            "resume_available": False,
            "resume_type": "",
            "resume_summary": "",
        }

    async def ensure_tables(self) -> None:
        async def _has_column(conn: AsyncConnection, table: str, column: str) -> bool:
            result = await conn.execute(
                text(
                    """
                    SELECT COUNT(1)
                    FROM information_schema.COLUMNS
                    WHERE TABLE_SCHEMA = DATABASE()
                      AND TABLE_NAME = :table_name
                      AND COLUMN_NAME = :column_name
                    """
                ),
                {"table_name": table, "column_name": column},
            )
            return int(result.scalar() or 0) > 0

        async with self.engine.begin() as conn:
            await conn.run_sync(
                lambda sync_conn: Base.metadata.create_all(
                    sync_conn,
                    tables=[
                        CrawlerTask.__table__,
                        CrawlerTaskRun.__table__,
                        CrawlerTaskCheckpoint.__table__,
                        GovArticle.__table__,
                    ],
                )
            )
            # schema compatibility for existing deployments without migration tool
            if not await _has_column(conn, "crawler_task", "manual_only"):
                await conn.execute(
                    text(
                        "ALTER TABLE crawler_task "
                        "ADD COLUMN manual_only TINYINT(1) NOT NULL DEFAULT 0 COMMENT '仅手动执行'"
                    )
                )
                logger.info("[task_scheduler] added missing column crawler_task.manual_only")

            if not await _has_column(conn, "crawler_task", "gov_site"):
                await conn.execute(
                    text(
                        "ALTER TABLE crawler_task "
                        "ADD COLUMN gov_site VARCHAR(64) NOT NULL DEFAULT '' COMMENT 'gov站点代号'"
                    )
                )
                logger.info("[task_scheduler] added missing column crawler_task.gov_site")

            if not await _has_column(conn, "crawler_task", "gov_channel"):
                await conn.execute(
                    text(
                        "ALTER TABLE crawler_task "
                        "ADD COLUMN gov_channel VARCHAR(64) NOT NULL DEFAULT '' COMMENT 'gov栏目代号'"
                    )
                )
                logger.info("[task_scheduler] added missing column crawler_task.gov_channel")

            if not await _has_column(conn, "crawler_task", "gov_max_pages"):
                await conn.execute(
                    text(
                        "ALTER TABLE crawler_task "
                        "ADD COLUMN gov_max_pages INT NOT NULL DEFAULT 1 COMMENT 'gov列表最大页数'"
                    )
                )
                logger.info("[task_scheduler] added missing column crawler_task.gov_max_pages")

            if not await _has_column(conn, "crawler_task", "gov_rule_path"):
                await conn.execute(
                    text(
                        "ALTER TABLE crawler_task "
                        "ADD COLUMN gov_rule_path TEXT NULL COMMENT 'gov规则目录或文件路径'"
                    )
                )
                logger.info("[task_scheduler] added missing column crawler_task.gov_rule_path")

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
        self._task_progress_states.clear()
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
                .where(CrawlerTask.manual_only.is_(False))
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

    async def _get_checkpoint(self, session: AsyncSession, task_id: int) -> Optional[CrawlerTaskCheckpoint]:
        return await session.get(CrawlerTaskCheckpoint, task_id)

    async def _delete_checkpoint(self, session: AsyncSession, task_id: int) -> None:
        await session.execute(delete(CrawlerTaskCheckpoint).where(CrawlerTaskCheckpoint.task_id == task_id))

    async def _save_checkpoint(self, session: AsyncSession, task: CrawlerTask, payload: Dict[str, Any], now_ts: int) -> None:
        if not payload:
            return
        checkpoint = await self._get_checkpoint(session, task.id)
        payload_text = json.dumps(payload, ensure_ascii=False)
        if checkpoint:
            checkpoint.crawler_type = task.crawler_type
            checkpoint.resume_payload = payload_text
            checkpoint.updated_at = now_ts
            return
        session.add(
            CrawlerTaskCheckpoint(
                task_id=task.id,
                crawler_type=task.crawler_type,
                resume_payload=payload_text,
                updated_at=now_ts,
            )
        )

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
                self._track_task_progress(task_id, msg)
                if self._is_data_hit_line(msg):
                    self._task_data_hits[task_id] = int(self._task_data_hits.get(task_id, 0)) + 1

            remaining = await loop.run_in_executor(None, process.stdout.read)
            if remaining:
                for row in remaining.splitlines():
                    msg = row.strip()
                    if not msg:
                        continue
                    self._append_task_log(task_id, msg)
                    self._track_task_progress(task_id, msg)
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

    async def _start_task(
        self,
        task_id: int,
        trigger_type: str,
        allow_busy_skip: bool = False,
        use_resume_checkpoint: bool = False,
    ) -> Dict[str, Any]:
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
                        if not bool(task.manual_only) and task.cron_expr:
                            task.next_run_at = self._next_run_ts(task.cron_expr, now_ts)
                        task.last_modify_ts = now_ts
                        await session.commit()
                        raise TaskSchedulerError("Platform is busy", status_code=409)
                    raise TaskSchedulerError("Platform is busy", status_code=409)

                if trigger_type == "cron" and bool(task.manual_only):
                    raise TaskSchedulerError("Manual-only task cannot be triggered by cron", status_code=400)

                command_overrides: Dict[str, Any] = {}
                if use_resume_checkpoint and trigger_type == "manual" and self._is_resume_supported(task.platform):
                    checkpoint = await self._get_checkpoint(session, task.id)
                    checkpoint_payload = self._safe_json_loads(checkpoint.resume_payload if checkpoint else "")
                    if checkpoint and checkpoint_payload:
                        overrides, can_resume = self._build_resume_override(task.crawler_type, checkpoint_payload)
                        if can_resume:
                            command_overrides = overrides

                command, runtime_params = self._build_command(task, command_overrides)
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
                if task.is_enabled and (not bool(task.manual_only)) and task.cron_expr:
                    task.next_run_at = self._next_run_ts(task.cron_expr, now_ts)
                await session.commit()

                self._running_processes[task_id] = process
                self._running_run_ids[task_id] = run_id
                self._platform_running_tasks[task.platform] = task_id
                self._task_log_buffers[task_id] = deque(maxlen=self._LOG_BUFFER_MAX)
                self._task_data_hits[task_id] = 0
                self._init_task_progress(task_id, runtime_params)
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
        checkpoint_payload = self._build_checkpoint_payload(task_id)
        self._task_progress_states.pop(task_id, None)
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
                    resume_supported = self._is_resume_supported(task.platform)
                    if was_stopped:
                        task.status = "paused" if not bool(task.is_enabled) else "idle"
                        if resume_supported:
                            await self._save_checkpoint(session, task, checkpoint_payload, now_ts)
                        else:
                            await self._delete_checkpoint(session, task.id)
                    elif data_hits > 0:
                        task.status = "idle"
                        task.success_count = int(task.success_count or 0) + 1
                        task.last_error = ""
                        await self._delete_checkpoint(session, task.id)
                    else:
                        task.status = "error"
                        task.fail_count = int(task.fail_count or 0) + 1
                        task.last_error = f"no_data_crawled (exit_code={int(exit_code or 0)})"
                        if resume_supported:
                            await self._save_checkpoint(session, task, checkpoint_payload, now_ts)
                        else:
                            await self._delete_checkpoint(session, task.id)

                await session.commit()

    async def list_tasks(self) -> Dict[str, Any]:
        try:
            async with self.session_factory() as session:
                result = await session.execute(select(CrawlerTask).order_by(CrawlerTask.id.desc()))
                tasks = [self._task_to_dict(item) for item in result.scalars().all()]
                checkpoint_result = await session.execute(select(CrawlerTaskCheckpoint))
                checkpoint_rows = {
                    int(item.task_id): item for item in checkpoint_result.scalars().all()
                }

            status_map = await self.get_platform_status()
            status_by_platform = {item["platform"]: item for item in status_map["rows"]}
            gov_site_map = {row["site_code"]: row for row in GovSiteRegistry.list_sites()}
            for task in tasks:
                platform_status = status_by_platform.get(task["platform"], {"busy": False, "running_task_id": 0})
                task["platform_busy"] = bool(platform_status.get("busy", False))
                task["platform_running_task_id"] = int(platform_status.get("running_task_id", 0))
                if task["platform"] == "gov":
                    gov_site = str((task.get("crawler_params") or {}).get("gov_site") or "")
                    gov_meta = gov_site_map.get(gov_site, {})
                    task["gov_site_status"] = str(gov_meta.get("status") or "")
                    task["gov_verify_error"] = str(gov_meta.get("verify_error") or "")
                checkpoint = checkpoint_rows.get(int(task["id"]))
                if checkpoint and self._is_resume_supported(task["platform"]):
                    payload = self._safe_json_loads(checkpoint.resume_payload or "")
                    task.update(self._checkpoint_fields(checkpoint.crawler_type, payload))
            return {"rows": tasks}
        except SQLAlchemyError as exc:
            raise TaskSchedulerError(f"MySQL query failed: {exc}", status_code=503) from exc

    async def create_task(self, payload: TaskUpsertRequest) -> Dict[str, Any]:
        normalized = self._normalize_task_upsert_payload(payload)
        now_ts = self._now_ts()
        next_run_at = (
            self._next_run_ts(str(normalized["cron_expr"]), now_ts)
            if (bool(normalized["is_enabled"]) and (not bool(normalized["manual_only"])))
            else 0
        )
        task = CrawlerTask(
            name=str(normalized["name"]),
            description=str(normalized["description"]),
            platform=str(normalized["platform"]),
            crawler_type=str(normalized["crawler_type"]),
            login_type=str(normalized["login_type"]),
            save_option=str(normalized["save_option"]),
            keywords=str(normalized["keywords"]),
            specified_ids=str(normalized["specified_ids"]),
            creator_ids=str(normalized["creator_ids"]),
            gov_site=str(normalized["gov_site"]),
            gov_channel=str(normalized["gov_channel"]),
            gov_max_pages=int(normalized["gov_max_pages"]),
            gov_rule_path=str(normalized["gov_rule_path"]),
            cookies=str(normalized["cookies"]),
            start_page=int(normalized["start_page"]),
            enable_comments=bool(normalized["enable_comments"]),
            enable_sub_comments=bool(normalized["enable_sub_comments"]),
            headless=bool(normalized["headless"]),
            priority=str(normalized["priority"]),
            timeout_seconds=int(normalized["timeout_seconds"]),
            cron_expr=str(normalized["cron_expr"]),
            manual_only=bool(normalized["manual_only"]),
            is_enabled=bool(normalized["is_enabled"]),
            status="idle" if bool(normalized["is_enabled"]) else "paused",
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
        normalized = self._normalize_task_upsert_payload(payload)
        now_ts = self._now_ts()
        try:
            async with self._lock:
                if task_id in self._running_processes:
                    raise TaskSchedulerError("Task is running, stop it before edit", status_code=409)
                async with self.session_factory() as session:
                    task = await session.get(CrawlerTask, task_id)
                    if not task:
                        raise TaskSchedulerError("Task not found", status_code=404)

                    task.name = str(normalized["name"])
                    task.description = str(normalized["description"])
                    task.platform = str(normalized["platform"])
                    task.crawler_type = str(normalized["crawler_type"])
                    task.login_type = str(normalized["login_type"])
                    task.save_option = str(normalized["save_option"])
                    task.keywords = str(normalized["keywords"])
                    task.specified_ids = str(normalized["specified_ids"])
                    task.creator_ids = str(normalized["creator_ids"])
                    task.gov_site = str(normalized["gov_site"])
                    task.gov_channel = str(normalized["gov_channel"])
                    task.gov_max_pages = int(normalized["gov_max_pages"])
                    task.gov_rule_path = str(normalized["gov_rule_path"])
                    task.cookies = str(normalized["cookies"])
                    task.start_page = int(normalized["start_page"])
                    task.enable_comments = bool(normalized["enable_comments"])
                    task.enable_sub_comments = bool(normalized["enable_sub_comments"])
                    task.headless = bool(normalized["headless"])
                    task.priority = str(normalized["priority"])
                    task.timeout_seconds = int(normalized["timeout_seconds"])
                    task.cron_expr = str(normalized["cron_expr"])
                    task.manual_only = bool(normalized["manual_only"])
                    task.is_enabled = bool(normalized["is_enabled"])
                    task.status = "idle" if bool(normalized["is_enabled"]) else "paused"
                    task.next_run_at = (
                        self._next_run_ts(task.cron_expr, now_ts)
                        if (bool(normalized["is_enabled"]) and (not bool(normalized["manual_only"])))
                        else 0
                    )
                    task.last_modify_ts = now_ts
                    await self._delete_checkpoint(session, task_id)
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
                    await self._delete_checkpoint(session, task_id)
                    await session.delete(task)
                    await session.commit()
        except SQLAlchemyError as exc:
            raise TaskSchedulerError(f"MySQL query failed: {exc}", status_code=503) from exc

    async def run_now(self, task_id: int, use_resume_checkpoint: bool = True) -> Dict[str, Any]:
        return await self._start_task(
            task_id,
            trigger_type="manual",
            allow_busy_skip=False,
            use_resume_checkpoint=bool(use_resume_checkpoint),
        )

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
                task.is_enabled = True
                if bool(task.manual_only):
                    task.next_run_at = 0
                else:
                    self._validate_cron_expr(task.cron_expr)
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
