# -*- coding: utf-8 -*-
# Copyright (c) 2025 relakkes@gmail.com
#
# This file is part of MediaCrawler project.
# Repository: https://github.com/NanmiCoder/MediaCrawler/blob/main/api/routers/dashboard.py
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

from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse

from ..services.dashboard_service import DashboardServiceError, dashboard_service

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


def _error_response(message: str, status_code: int = 503) -> JSONResponse:
    return JSONResponse(status_code=status_code, content={"success": False, "message": message})


@router.get("/overview")
async def get_dashboard_overview(days: int = Query(default=7)):
    try:
        data = await dashboard_service.get_overview(days)
        return {"success": True, "data": data}
    except DashboardServiceError as exc:
        return _error_response(str(exc))
    except Exception as exc:
        return _error_response(f"Internal error: {exc}", status_code=500)


@router.get("/channels")
async def get_dashboard_channel_stats(days: int = Query(default=7)):
    try:
        data = await dashboard_service.get_channel_stats(days)
        return {"success": True, "data": data}
    except DashboardServiceError as exc:
        return _error_response(str(exc))
    except Exception as exc:
        return _error_response(f"Internal error: {exc}", status_code=500)


@router.get("/trend")
async def get_dashboard_trend(days: int = Query(default=7)):
    try:
        data = await dashboard_service.get_trend(days)
        return {"success": True, "data": data}
    except DashboardServiceError as exc:
        return _error_response(str(exc))
    except Exception as exc:
        return _error_response(f"Internal error: {exc}", status_code=500)


@router.get("/keywords")
async def get_dashboard_keywords(days: int = Query(default=7), limit: int = Query(default=10)):
    try:
        data = await dashboard_service.get_top_keywords(days, limit)
        return {"success": True, "data": data}
    except DashboardServiceError as exc:
        return _error_response(str(exc))
    except Exception as exc:
        return _error_response(f"Internal error: {exc}", status_code=500)


@router.get("/recent")
async def get_dashboard_recent(days: int = Query(default=7), limit: int = Query(default=50)):
    try:
        data = await dashboard_service.get_recent_contents(days, limit)
        return {"success": True, "data": data}
    except DashboardServiceError as exc:
        return _error_response(str(exc))
    except Exception as exc:
        return _error_response(f"Internal error: {exc}", status_code=500)


@router.get("/comment-groups")
async def get_dashboard_comment_groups(days: int = Query(default=7), limit: int = Query(default=20)):
    try:
        data = await dashboard_service.get_comment_groups(days, limit)
        return {"success": True, "data": data}
    except DashboardServiceError as exc:
        return _error_response(str(exc))
    except Exception as exc:
        return _error_response(f"Internal error: {exc}", status_code=500)


@router.get("/comment-group-detail")
async def get_dashboard_comment_group_detail(
    days: int = Query(default=7),
    channel: str = Query(default=""),
    content_id: str = Query(default=""),
    limit: int = Query(default=50),
):
    try:
        data = await dashboard_service.get_comment_group_detail(days, channel, content_id, limit)
        return {"success": True, "data": data}
    except DashboardServiceError as exc:
        msg = str(exc)
        status_code = 400 if msg.startswith("Invalid channel:") or msg == "content_id is required" else 503
        return _error_response(msg, status_code=status_code)
    except Exception as exc:
        return _error_response(f"Internal error: {exc}", status_code=500)
