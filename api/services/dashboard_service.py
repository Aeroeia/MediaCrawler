# -*- coding: utf-8 -*-
# Copyright (c) 2025 relakkes@gmail.com
#
# This file is part of MediaCrawler project.
# Repository: https://github.com/NanmiCoder/MediaCrawler/blob/main/api/services/dashboard_service.py
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

from collections import Counter
from dataclasses import dataclass
from datetime import datetime, time, timedelta, timezone
import logging
from typing import Any, Dict, List, Optional
from zoneinfo import ZoneInfo

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncEngine, create_async_engine
from sqlalchemy.pool import NullPool

from config.db_config import mysql_db_config

logger = logging.getLogger(__name__)


class DashboardServiceError(RuntimeError):
    """Dashboard query error."""


@dataclass(frozen=True)
class ChannelTableMap:
    channel: str
    content_table: str
    comment_table: str
    creator_table: Optional[str]


@dataclass(frozen=True)
class RecentQueryConfig:
    channel: str
    table: str
    id_col: str
    title_col: str
    summary_col: str
    like_expr: str
    comment_expr: str
    share_expr: str


@dataclass(frozen=True)
class CommentQueryConfig:
    channel: str
    content_table: str
    comment_table: str
    content_id_col: str
    comment_content_id_col: str
    title_col: str
    summary_col: str
    comment_id_col: str
    comment_text_col: str
    comment_user_col: str
    comment_like_expr: str


class DashboardService:
    """Dashboard aggregation service based on MySQL."""

    _TS_EXPR = "CAST(CASE WHEN add_ts > 1000000000000 THEN add_ts / 1000 ELSE add_ts END AS SIGNED)"
    _SH_TZ = ZoneInfo("Asia/Shanghai")
    _TZ_OFFSET_SECONDS = 8 * 3600

    _CHANNEL_TABLES: List[ChannelTableMap] = [
        ChannelTableMap("xhs", "xhs_note", "xhs_note_comment", "xhs_creator"),
        ChannelTableMap("dy", "douyin_aweme", "douyin_aweme_comment", "dy_creator"),
        ChannelTableMap("ks", "kuaishou_video", "kuaishou_video_comment", None),  # no ks_creator table
        ChannelTableMap("bili", "bilibili_video", "bilibili_video_comment", "bilibili_up_info"),
        ChannelTableMap("wb", "weibo_note", "weibo_note_comment", "weibo_creator"),
        ChannelTableMap("tieba", "tieba_note", "tieba_comment", "tieba_creator"),
        ChannelTableMap("zhihu", "zhihu_content", "zhihu_comment", "zhihu_creator"),
    ]

    _RECENT_QUERIES: List[RecentQueryConfig] = [
        RecentQueryConfig(
            channel="xhs",
            table="xhs_note",
            id_col="`note_id`",
            title_col="`title`",
            summary_col="`desc`",
            like_expr="CAST(IFNULL(liked_count, '0') AS UNSIGNED)",
            comment_expr="CAST(IFNULL(comment_count, '0') AS UNSIGNED)",
            share_expr="CAST(IFNULL(share_count, '0') AS UNSIGNED)",
        ),
        RecentQueryConfig(
            channel="dy",
            table="douyin_aweme",
            id_col="`aweme_id`",
            title_col="`title`",
            summary_col="`desc`",
            like_expr="CAST(IFNULL(liked_count, '0') AS UNSIGNED)",
            comment_expr="CAST(IFNULL(comment_count, '0') AS UNSIGNED)",
            share_expr="CAST(IFNULL(share_count, '0') AS UNSIGNED)",
        ),
        RecentQueryConfig(
            channel="ks",
            table="kuaishou_video",
            id_col="`video_id`",
            title_col="`title`",
            summary_col="`desc`",
            like_expr="CAST(IFNULL(liked_count, '0') AS UNSIGNED)",
            comment_expr="CAST(IFNULL(viewd_count, '0') AS UNSIGNED)",
            share_expr="0",
        ),
        RecentQueryConfig(
            channel="bili",
            table="bilibili_video",
            id_col="`video_id`",
            title_col="`title`",
            summary_col="`desc`",
            like_expr="CAST(IFNULL(liked_count, 0) AS UNSIGNED)",
            comment_expr="CAST(IFNULL(video_comment, '0') AS UNSIGNED)",
            share_expr="CAST(IFNULL(video_share_count, '0') AS UNSIGNED)",
        ),
        RecentQueryConfig(
            channel="wb",
            table="weibo_note",
            id_col="`note_id`",
            title_col="`content`",
            summary_col="`content`",
            like_expr="CAST(IFNULL(liked_count, '0') AS UNSIGNED)",
            comment_expr="CAST(IFNULL(comments_count, '0') AS UNSIGNED)",
            share_expr="CAST(IFNULL(shared_count, '0') AS UNSIGNED)",
        ),
        RecentQueryConfig(
            channel="tieba",
            table="tieba_note",
            id_col="`note_id`",
            title_col="`title`",
            summary_col="`desc`",
            like_expr="0",
            comment_expr="CAST(IFNULL(total_replay_num, 0) AS UNSIGNED)",
            share_expr="0",
        ),
        RecentQueryConfig(
            channel="zhihu",
            table="zhihu_content",
            id_col="`content_id`",
            title_col="`title`",
            summary_col="`content_text`",
            like_expr="CAST(IFNULL(voteup_count, 0) AS UNSIGNED)",
            comment_expr="CAST(IFNULL(comment_count, 0) AS UNSIGNED)",
            share_expr="0",
        ),
    ]

    _COMMENT_QUERIES: List[CommentQueryConfig] = [
        CommentQueryConfig(
            channel="xhs",
            content_table="xhs_note",
            comment_table="xhs_note_comment",
            content_id_col="`note_id`",
            comment_content_id_col="`note_id`",
            title_col="`title`",
            summary_col="`desc`",
            comment_id_col="`comment_id`",
            comment_text_col="`content`",
            comment_user_col="`nickname`",
            comment_like_expr="CAST(IFNULL(`like_count`, '0') AS SIGNED)",
        ),
        CommentQueryConfig(
            channel="dy",
            content_table="douyin_aweme",
            comment_table="douyin_aweme_comment",
            content_id_col="`aweme_id`",
            comment_content_id_col="`aweme_id`",
            title_col="`title`",
            summary_col="`desc`",
            comment_id_col="`comment_id`",
            comment_text_col="`content`",
            comment_user_col="`nickname`",
            comment_like_expr="CAST(IFNULL(`like_count`, '0') AS SIGNED)",
        ),
        CommentQueryConfig(
            channel="ks",
            content_table="kuaishou_video",
            comment_table="kuaishou_video_comment",
            content_id_col="`video_id`",
            comment_content_id_col="`video_id`",
            title_col="`title`",
            summary_col="`desc`",
            comment_id_col="`comment_id`",
            comment_text_col="`content`",
            comment_user_col="`nickname`",
            comment_like_expr="0",
        ),
        CommentQueryConfig(
            channel="bili",
            content_table="bilibili_video",
            comment_table="bilibili_video_comment",
            content_id_col="`video_id`",
            comment_content_id_col="`video_id`",
            title_col="`title`",
            summary_col="`desc`",
            comment_id_col="`comment_id`",
            comment_text_col="`content`",
            comment_user_col="`nickname`",
            comment_like_expr="CAST(IFNULL(`like_count`, '0') AS SIGNED)",
        ),
        CommentQueryConfig(
            channel="wb",
            content_table="weibo_note",
            comment_table="weibo_note_comment",
            content_id_col="`note_id`",
            comment_content_id_col="`note_id`",
            title_col="`content`",
            summary_col="`content`",
            comment_id_col="`comment_id`",
            comment_text_col="`content`",
            comment_user_col="`nickname`",
            comment_like_expr="CAST(IFNULL(`comment_like_count`, '0') AS SIGNED)",
        ),
        CommentQueryConfig(
            channel="tieba",
            content_table="tieba_note",
            comment_table="tieba_comment",
            content_id_col="`note_id`",
            comment_content_id_col="`note_id`",
            title_col="`title`",
            summary_col="`desc`",
            comment_id_col="`comment_id`",
            comment_text_col="`content`",
            comment_user_col="`user_nickname`",
            comment_like_expr="0",
        ),
        CommentQueryConfig(
            channel="zhihu",
            content_table="zhihu_content",
            comment_table="zhihu_comment",
            content_id_col="`content_id`",
            comment_content_id_col="`content_id`",
            title_col="`title`",
            summary_col="`content_text`",
            comment_id_col="`comment_id`",
            comment_text_col="`content`",
            comment_user_col="`user_nickname`",
            comment_like_expr="CAST(IFNULL(`like_count`, 0) AS SIGNED)",
        ),
    ]

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

    @staticmethod
    def normalize_days(days: int) -> int:
        return days if days in (7, 30) else 7

    @staticmethod
    def normalize_limit(limit: int, default: int, max_limit: int) -> int:
        if limit <= 0:
            return default
        return min(limit, max_limit)

    def _get_period_bounds(self, days: int) -> tuple[int, int, datetime]:
        now_sh = datetime.now(self._SH_TZ)
        start_day = (now_sh.date() - timedelta(days=days - 1))
        start_dt = datetime.combine(start_day, time.min, tzinfo=self._SH_TZ)
        start_ts = int(start_dt.timestamp())
        end_ts = int(now_sh.timestamp()) + 1
        return start_ts, end_ts, now_sh

    def _get_today_bounds(self, now_sh: datetime) -> tuple[int, int]:
        start_of_today = datetime.combine(now_sh.date(), time.min, tzinfo=self._SH_TZ)
        start_of_tomorrow = start_of_today + timedelta(days=1)
        return int(start_of_today.timestamp()), int(start_of_tomorrow.timestamp())

    @classmethod
    def _ts_expr_with_alias(cls, alias: str) -> str:
        return (
            "CAST(CASE WHEN "
            f"{alias}.add_ts > 1000000000000 THEN {alias}.add_ts / 1000 "
            f"ELSE {alias}.add_ts END AS SIGNED)"
        )

    def _to_sh_time_str(self, ts: int) -> str:
        if ts <= 0:
            return ""
        dt = datetime.fromtimestamp(ts, tz=timezone.utc).astimezone(self._SH_TZ)
        return dt.strftime("%Y-%m-%d %H:%M:%S")

    def _find_comment_query(self, channel: str) -> Optional[CommentQueryConfig]:
        for query in self._COMMENT_QUERIES:
            if query.channel == channel:
                return query
        return None

    async def _fetch_scalar(self, conn: AsyncConnection, sql: str, params: Dict[str, Any] | None = None) -> int:
        result = await conn.execute(text(sql), params or {})
        value = result.scalar()
        return int(value or 0)

    async def _safe_scalar(self, conn: AsyncConnection, table: str, period: bool, start_ts: int = 0, end_ts: int = 0) -> int:
        if period:
            sql = (
                f"SELECT COUNT(1) FROM {table} "
                f"WHERE {self._TS_EXPR} >= :start_ts AND {self._TS_EXPR} < :end_ts"
            )
            return await self._fetch_scalar(conn, sql, {"start_ts": start_ts, "end_ts": end_ts})
        sql = f"SELECT COUNT(1) FROM {table}"
        return await self._fetch_scalar(conn, sql)

    async def get_overview(self, days: int) -> Dict[str, Any]:
        days = self.normalize_days(days)
        start_ts, end_ts, now_sh = self._get_period_bounds(days)
        today_start_ts, tomorrow_start_ts = self._get_today_bounds(now_sh)

        try:
            async with self.engine.connect() as conn:
                total_contents = 0
                total_comments = 0
                total_creators = 0
                period_contents = 0
                period_comments = 0
                period_creators = 0
                today_new_contents = 0
                today_new_comments = 0

                for channel in self._CHANNEL_TABLES:
                    total_contents += await self._safe_scalar(conn, channel.content_table, period=False)
                    total_comments += await self._safe_scalar(conn, channel.comment_table, period=False)
                    if channel.creator_table:
                        total_creators += await self._safe_scalar(conn, channel.creator_table, period=False)

                    period_contents += await self._safe_scalar(conn, channel.content_table, period=True, start_ts=start_ts, end_ts=end_ts)
                    period_comments += await self._safe_scalar(conn, channel.comment_table, period=True, start_ts=start_ts, end_ts=end_ts)
                    if channel.creator_table:
                        period_creators += await self._safe_scalar(
                            conn, channel.creator_table, period=True, start_ts=start_ts, end_ts=end_ts
                        )

                    today_new_contents += await self._safe_scalar(
                        conn,
                        channel.content_table,
                        period=True,
                        start_ts=today_start_ts,
                        end_ts=tomorrow_start_ts,
                    )
                    today_new_comments += await self._safe_scalar(
                        conn,
                        channel.comment_table,
                        period=True,
                        start_ts=today_start_ts,
                        end_ts=tomorrow_start_ts,
                    )

                return {
                    "period_days": days,
                    "today_new_contents": today_new_contents,
                    "today_new_comments": today_new_comments,
                    "today_new_crawled": today_new_contents + today_new_comments,
                    "totals": {
                        "contents": total_contents,
                        "comments": total_comments,
                        "creators": total_creators,
                        "crawled": total_contents + total_comments,
                    },
                    "period": {
                        "contents": period_contents,
                        "comments": period_comments,
                        "creators": period_creators,
                        "crawled": period_contents + period_comments,
                    },
                }
        except SQLAlchemyError as exc:
            raise DashboardServiceError(f"MySQL query failed: {exc}") from exc

    async def get_channel_stats(self, days: int) -> Dict[str, Any]:
        days = self.normalize_days(days)
        start_ts, end_ts, _ = self._get_period_bounds(days)

        try:
            async with self.engine.connect() as conn:
                rows: List[Dict[str, Any]] = []
                for channel in self._CHANNEL_TABLES:
                    rows.append(
                        {
                            "channel": channel.channel,
                            "content_count": (content_count := await self._safe_scalar(
                                conn, channel.content_table, period=True, start_ts=start_ts, end_ts=end_ts
                            )),
                            "comment_count": (comment_count := await self._safe_scalar(
                                conn, channel.comment_table, period=True, start_ts=start_ts, end_ts=end_ts
                            )),
                            "creator_count": (
                                await self._safe_scalar(
                                    conn, channel.creator_table, period=True, start_ts=start_ts, end_ts=end_ts
                                )
                                if channel.creator_table
                                else 0
                            ),
                            "crawled_count": content_count + comment_count,
                        }
                    )
                return {"period_days": days, "rows": rows}
        except SQLAlchemyError as exc:
            raise DashboardServiceError(f"MySQL query failed: {exc}") from exc

    async def get_trend(self, days: int) -> Dict[str, Any]:
        days = self.normalize_days(days)
        start_ts, end_ts, now_sh = self._get_period_bounds(days)
        start_day = now_sh.date() - timedelta(days=days - 1)
        day_list = [(start_day + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(days)]

        by_day_total = {d: 0 for d in day_list}
        by_day_channel = {d: {c.channel: 0 for c in self._CHANNEL_TABLES} for d in day_list}

        try:
            async with self.engine.connect() as conn:
                for channel in self._CHANNEL_TABLES:
                    sql = (
                        f"SELECT FLOOR(({self._TS_EXPR} + :offset_seconds) / 86400) AS day_key, COUNT(1) AS cnt "
                        f"FROM {channel.content_table} "
                        f"WHERE {self._TS_EXPR} >= :start_ts AND {self._TS_EXPR} < :end_ts "
                        "GROUP BY day_key"
                    )
                    result = await conn.execute(
                        text(sql),
                        {
                            "offset_seconds": self._TZ_OFFSET_SECONDS,
                            "start_ts": start_ts,
                            "end_ts": end_ts,
                        },
                    )
                    for row in result:
                        day_key = int(row.day_key)
                        day_utc = datetime.fromtimestamp(
                            day_key * 86400 - self._TZ_OFFSET_SECONDS, tz=timezone.utc
                        )
                        day_str = day_utc.astimezone(self._SH_TZ).strftime("%Y-%m-%d")
                        if day_str in by_day_total:
                            count = int(row.cnt or 0)
                            by_day_total[day_str] += count
                            by_day_channel[day_str][channel.channel] += count

            series = [
                {
                    "date": day,
                    "total": by_day_total[day],
                    "channels": by_day_channel[day],
                }
                for day in day_list
            ]
            return {"period_days": days, "series": series}
        except SQLAlchemyError as exc:
            raise DashboardServiceError(f"MySQL query failed: {exc}") from exc

    async def get_top_keywords(self, days: int, limit: int) -> Dict[str, Any]:
        days = self.normalize_days(days)
        limit = self.normalize_limit(limit, default=10, max_limit=50)
        start_ts, end_ts, _ = self._get_period_bounds(days)
        counter: Counter[str] = Counter()

        try:
            async with self.engine.connect() as conn:
                for channel in self._CHANNEL_TABLES:
                    sql = (
                        f"SELECT source_keyword, COUNT(1) AS cnt "
                        f"FROM {channel.content_table} "
                        f"WHERE source_keyword IS NOT NULL AND source_keyword <> '' "
                        f"AND {self._TS_EXPR} >= :start_ts AND {self._TS_EXPR} < :end_ts "
                        "GROUP BY source_keyword"
                    )
                    result = await conn.execute(text(sql), {"start_ts": start_ts, "end_ts": end_ts})
                    for row in result:
                        keyword = str(row.source_keyword).strip()
                        if keyword:
                            counter[keyword] += int(row.cnt or 0)

                top = counter.most_common(limit)
                return {
                    "period_days": days,
                    "limit": limit,
                    "rows": [{"keyword": keyword, "count": count} for keyword, count in top],
                }
        except SQLAlchemyError as exc:
            raise DashboardServiceError(f"MySQL query failed: {exc}") from exc

    async def get_recent_contents(self, days: int, limit: int) -> Dict[str, Any]:
        days = self.normalize_days(days)
        limit = self.normalize_limit(limit, default=50, max_limit=200)
        start_ts, end_ts, _ = self._get_period_bounds(days)

        rows: List[Dict[str, Any]] = []
        try:
            async with self.engine.connect() as conn:
                for query in self._RECENT_QUERIES:
                    sql = (
                        f"SELECT :channel AS channel, "
                        f"{query.id_col} AS content_id, "
                        f"{query.title_col} AS title, "
                        f"{query.summary_col} AS summary, "
                        f"{self._TS_EXPR} AS collected_ts, "
                        f"{query.like_expr} AS like_count, "
                        f"{query.comment_expr} AS comment_count, "
                        f"{query.share_expr} AS share_count "
                        f"FROM {query.table} "
                        f"WHERE {self._TS_EXPR} >= :start_ts AND {self._TS_EXPR} < :end_ts "
                        f"ORDER BY {self._TS_EXPR} DESC "
                        "LIMIT :limit"
                    )
                    result = await conn.execute(
                        text(sql),
                        {
                            "channel": query.channel,
                            "start_ts": start_ts,
                            "end_ts": end_ts,
                            "limit": limit,
                        },
                    )
                    for row in result:
                        collected_ts = int(row.collected_ts or 0)
                        collected_dt = datetime.fromtimestamp(collected_ts, tz=timezone.utc).astimezone(self._SH_TZ)
                        rows.append(
                            {
                                "channel": row.channel,
                                "content_id": str(row.content_id or ""),
                                "title": str(row.title or ""),
                                "summary": str(row.summary or ""),
                                "collected_ts": collected_ts,
                                "collected_at": collected_dt.strftime("%Y-%m-%d %H:%M:%S"),
                                "like_count": int(row.like_count or 0),
                                "comment_count": int(row.comment_count or 0),
                                "share_count": int(row.share_count or 0),
                            }
                        )

            rows.sort(key=lambda item: item["collected_ts"], reverse=True)
            rows = rows[:limit]
            for row in rows:
                row.pop("collected_ts", None)

            return {"period_days": days, "limit": limit, "rows": rows}
        except SQLAlchemyError as exc:
            raise DashboardServiceError(f"MySQL query failed: {exc}") from exc

    async def get_comment_groups(self, days: int, limit: int) -> Dict[str, Any]:
        days = self.normalize_days(days)
        limit = self.normalize_limit(limit, default=20, max_limit=200)
        start_ts, end_ts, _ = self._get_period_bounds(days)
        rows: List[Dict[str, Any]] = []

        try:
            async with self.engine.connect() as conn:
                for query in self._COMMENT_QUERIES:
                    comment_ts_expr = self._ts_expr_with_alias("c")
                    sql = (
                        "SELECT :channel AS channel, "
                        f"CAST(c.{query.comment_content_id_col} AS CHAR) AS content_id, "
                        f"MAX(COALESCE(NULLIF(TRIM(p.{query.title_col}), ''), NULLIF(TRIM(p.{query.summary_col}), ''), '(无标题)')) AS title, "
                        "COUNT(1) AS comment_count, "
                        f"MAX({comment_ts_expr}) AS latest_comment_ts "
                        f"FROM {query.comment_table} c "
                        f"LEFT JOIN {query.content_table} p ON p.{query.content_id_col} = c.{query.comment_content_id_col} "
                        f"WHERE {comment_ts_expr} >= :start_ts AND {comment_ts_expr} < :end_ts "
                        f"AND c.{query.comment_content_id_col} IS NOT NULL "
                        f"GROUP BY c.{query.comment_content_id_col} "
                        "ORDER BY comment_count DESC, latest_comment_ts DESC "
                        "LIMIT :limit"
                    )
                    result = await conn.execute(
                        text(sql),
                        {
                            "channel": query.channel,
                            "start_ts": start_ts,
                            "end_ts": end_ts,
                            "limit": limit,
                        },
                    )
                    for row in result:
                        latest_comment_ts = int(row.latest_comment_ts or 0)
                        rows.append(
                            {
                                "channel": row.channel,
                                "content_id": str(row.content_id or ""),
                                "title": str(row.title or "(无标题)"),
                                "comment_count": int(row.comment_count or 0),
                                "latest_comment_at": self._to_sh_time_str(latest_comment_ts) or "-",
                                "latest_comment_ts": latest_comment_ts,
                            }
                        )

            rows.sort(
                key=lambda item: (
                    int(item.get("comment_count", 0)),
                    int(item.get("latest_comment_ts", 0)),
                ),
                reverse=True,
            )
            rows = rows[:limit]
            for row in rows:
                row.pop("latest_comment_ts", None)
            return {"period_days": days, "limit": limit, "rows": rows}
        except SQLAlchemyError as exc:
            raise DashboardServiceError(f"MySQL query failed: {exc}") from exc

    async def get_comment_group_detail(self, days: int, channel: str, content_id: str, limit: int) -> Dict[str, Any]:
        days = self.normalize_days(days)
        limit = self.normalize_limit(limit, default=50, max_limit=200)
        start_ts, end_ts, _ = self._get_period_bounds(days)
        channel = str(channel or "").strip()
        content_id = str(content_id or "").strip()
        if not content_id:
            raise DashboardServiceError("content_id is required")

        query = self._find_comment_query(channel)
        if not query:
            raise DashboardServiceError(f"Invalid channel: {channel}")

        try:
            async with self.engine.connect() as conn:
                comment_ts_expr = self._ts_expr_with_alias("c")
                sql = (
                    "SELECT :channel AS channel, "
                    f"CAST(c.{query.comment_id_col} AS CHAR) AS comment_id, "
                    f"COALESCE(c.{query.comment_user_col}, '') AS user_name, "
                    f"COALESCE(c.{query.comment_text_col}, '') AS content, "
                    f"{query.comment_like_expr} AS like_count, "
                    f"{comment_ts_expr} AS collected_ts "
                    f"FROM {query.comment_table} c "
                    f"WHERE CAST(c.{query.comment_content_id_col} AS CHAR) = :content_id "
                    f"AND {comment_ts_expr} >= :start_ts AND {comment_ts_expr} < :end_ts "
                    f"ORDER BY {comment_ts_expr} DESC "
                    "LIMIT :limit"
                )
                result = await conn.execute(
                    text(sql),
                    {
                        "channel": channel,
                        "content_id": content_id,
                        "start_ts": start_ts,
                        "end_ts": end_ts,
                        "limit": limit,
                    },
                )

                rows: List[Dict[str, Any]] = []
                for row in result:
                    collected_ts = int(row.collected_ts or 0)
                    rows.append(
                        {
                            "channel": row.channel,
                            "comment_id": str(row.comment_id or ""),
                            "user_name": str(row.user_name or ""),
                            "content": str(row.content or ""),
                            "like_count": int(row.like_count or 0),
                            "collected_at": self._to_sh_time_str(collected_ts) or "-",
                        }
                    )
                return {
                    "period_days": days,
                    "limit": limit,
                    "channel": channel,
                    "content_id": content_id,
                    "rows": rows,
                }
        except SQLAlchemyError as exc:
            raise DashboardServiceError(f"MySQL query failed: {exc}") from exc

    async def backfill_tieba_add_ts(self) -> Dict[str, int]:
        now_ts = int(datetime.now(self._SH_TZ).timestamp())
        sql_tpl = (
            "UPDATE {table} "
            "SET add_ts = CASE "
            "WHEN IFNULL(last_modify_ts, 0) > 0 THEN last_modify_ts "
            "ELSE :now_ts END "
            "WHERE IFNULL(add_ts, 0) <= 0"
        )
        try:
            async with self.engine.begin() as conn:
                note_res = await conn.execute(text(sql_tpl.format(table="tieba_note")), {"now_ts": now_ts})
                comment_res = await conn.execute(text(sql_tpl.format(table="tieba_comment")), {"now_ts": now_ts})
                creator_res = await conn.execute(text(sql_tpl.format(table="tieba_creator")), {"now_ts": now_ts})
            return {
                "tieba_note": int(note_res.rowcount or 0),
                "tieba_comment": int(comment_res.rowcount or 0),
                "tieba_creator": int(creator_res.rowcount or 0),
            }
        except SQLAlchemyError as exc:
            raise DashboardServiceError(f"MySQL query failed: {exc}") from exc


dashboard_service = DashboardService()
