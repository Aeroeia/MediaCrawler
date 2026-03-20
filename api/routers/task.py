# -*- coding: utf-8 -*-
# Copyright (c) 2025 relakkes@gmail.com
#
# This file is part of MediaCrawler project.
# Repository: https://github.com/NanmiCoder/MediaCrawler/blob/main/api/routers/task.py
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

from fastapi import APIRouter, Path, Query
from fastapi.responses import JSONResponse

from ..schemas import TaskUpsertRequest
from ..services.task_scheduler_service import TaskSchedulerError, task_scheduler_service

router = APIRouter(prefix="/tasks", tags=["tasks"])


def _ok(data=None, message: str = "ok"):
    return {"success": True, "data": data, "message": message}


def _error(exc: Exception, status_code: int = 500):
    if isinstance(exc, TaskSchedulerError):
        return JSONResponse(
            status_code=exc.status_code,
            content={"success": False, "message": str(exc)},
        )
    return JSONResponse(
        status_code=status_code,
        content={"success": False, "message": f"Internal error: {exc}"},
    )


@router.get("")
async def list_tasks():
    try:
        return _ok(data=await task_scheduler_service.list_tasks())
    except Exception as exc:
        return _error(exc)


@router.get("/platform-status")
async def get_platform_status():
    try:
        return _ok(data=await task_scheduler_service.get_platform_status())
    except Exception as exc:
        return _error(exc)


@router.post("")
async def create_task(payload: TaskUpsertRequest):
    try:
        return _ok(data=await task_scheduler_service.create_task(payload), message="task created")
    except Exception as exc:
        return _error(exc)


@router.put("/{task_id}")
async def update_task(
    payload: TaskUpsertRequest,
    task_id: int = Path(..., ge=1),
):
    try:
        return _ok(data=await task_scheduler_service.update_task(task_id, payload), message="task updated")
    except Exception as exc:
        return _error(exc)


@router.delete("/{task_id}")
async def delete_task(task_id: int = Path(..., ge=1)):
    try:
        await task_scheduler_service.delete_task(task_id)
        return _ok(data={"task_id": task_id}, message="task deleted")
    except Exception as exc:
        return _error(exc)


@router.post("/{task_id}/run-now")
async def run_now(
    task_id: int = Path(..., ge=1),
    resume: bool = Query(default=True, description="Use saved checkpoint to resume when available"),
):
    try:
        return _ok(data=await task_scheduler_service.run_now(task_id, use_resume_checkpoint=resume), message="task started")
    except Exception as exc:
        return _error(exc)


@router.post("/{task_id}/pause")
async def pause_task(task_id: int = Path(..., ge=1)):
    try:
        return _ok(data=await task_scheduler_service.pause_task(task_id), message="task paused")
    except Exception as exc:
        return _error(exc)


@router.post("/{task_id}/resume")
async def resume_task(task_id: int = Path(..., ge=1)):
    try:
        return _ok(data=await task_scheduler_service.resume_task(task_id), message="task resumed")
    except Exception as exc:
        return _error(exc)


@router.post("/{task_id}/stop")
async def stop_task(task_id: int = Path(..., ge=1)):
    try:
        return _ok(data=await task_scheduler_service.stop_task(task_id), message="task stopped")
    except Exception as exc:
        return _error(exc)


@router.get("/{task_id}/runs")
async def get_task_runs(
    task_id: int = Path(..., ge=1),
    limit: int = Query(default=50, ge=1, le=200),
):
    try:
        return _ok(data=await task_scheduler_service.get_task_runs(task_id, limit))
    except Exception as exc:
        return _error(exc)


@router.get("/{task_id}/logs")
async def get_task_logs(
    task_id: int = Path(..., ge=1),
    limit: int = Query(default=200, ge=1, le=1000),
):
    try:
        return _ok(data=await task_scheduler_service.get_task_logs(task_id, limit))
    except Exception as exc:
        return _error(exc)
