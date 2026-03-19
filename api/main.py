# -*- coding: utf-8 -*-
# Copyright (c) 2025 relakkes@gmail.com
#
# This file is part of MediaCrawler project.
# Repository: https://github.com/NanmiCoder/MediaCrawler/blob/main/api/main.py
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

"""
MediaCrawler WebUI API Server
Start command: uvicorn api.main:app --port 8080 --reload
Or: python -m api.main
"""
import asyncio
import logging
import os
import subprocess
import uvicorn
from fastapi import FastAPI
from fastapi import Query
from fastapi import HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, RedirectResponse

from .routers import crawler_router, data_router, dashboard_router, task_router, websocket_router
from .services import dashboard_service, task_scheduler_service
from media_platform.gov.rule_loader import GovRuleLoader
from media_platform.gov.site_registry import GovSiteRegistry

app = FastAPI(
    title="数据采集中台 API",
    description="API for controlling crawler tasks and dashboard",
    version="1.0.0"
)
logger = logging.getLogger(__name__)

# Get webui static files directory
WEBUI_DIR = os.path.join(os.path.dirname(__file__), "webui")


def _asset_version(candidates: list[str]) -> str:
    latest_mtime = 0
    for path in candidates:
        if os.path.exists(path):
            latest_mtime = max(latest_mtime, int(os.path.getmtime(path)))
    return str(latest_mtime or 1)


def _render_html(file_name: str, replacements: dict[str, str] | None = None):
    file_path = os.path.join(WEBUI_DIR, file_name)
    if not os.path.exists(file_path):
        return None
    with open(file_path, "r", encoding="utf-8") as fp:
        html = fp.read()
    for key, value in (replacements or {}).items():
        html = html.replace(key, value)
    return HTMLResponse(content=html)

# CORS configuration - allow frontend dev server access
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite dev server
        "http://localhost:3000",  # Backup port
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(crawler_router, prefix="/api")
app.include_router(data_router, prefix="/api")
app.include_router(dashboard_router, prefix="/api")
app.include_router(task_router, prefix="/api")
app.include_router(websocket_router, prefix="/api")


@app.on_event("startup")
async def startup_event():
    try:
        await task_scheduler_service.start()
    except Exception as exc:
        logger.exception("Task scheduler startup failed: %s", exc)
    try:
        result = await dashboard_service.backfill_tieba_add_ts()
        logger.info("Tieba add_ts backfill finished: %s", result)
    except Exception as exc:
        logger.exception("Tieba add_ts backfill failed: %s", exc)


@app.on_event("shutdown")
async def shutdown_event():
    try:
        await task_scheduler_service.stop()
    except Exception as exc:
        logger.exception("Task scheduler shutdown failed: %s", exc)


@app.get("/")
async def serve_home():
    return await serve_overview()


@app.get("/overview")
async def serve_overview():
    """Return overview page."""
    response = _render_html(
        "overview.html",
        replacements={
            "__DASHBOARD_ASSET_VERSION__": _asset_version(
                [
                    os.path.join(WEBUI_DIR, "overview.html"),
                    os.path.join(WEBUI_DIR, "dashboard.js"),
                    os.path.join(WEBUI_DIR, "dashboard.css"),
                ]
            )
        },
    )
    if response:
        return response
    return {
        "message": "Overview page not found",
        "note": "Missing file: api/webui/overview.html",
    }


@app.get("/details")
async def serve_details():
    """Return details page."""
    response = _render_html(
        "details.html",
        replacements={
            "__DASHBOARD_ASSET_VERSION__": _asset_version(
                [
                    os.path.join(WEBUI_DIR, "details.html"),
                    os.path.join(WEBUI_DIR, "dashboard.js"),
                    os.path.join(WEBUI_DIR, "dashboard.css"),
                ]
            )
        },
    )
    if response:
        return response
    return {
        "message": "Details page not found",
        "note": "Missing file: api/webui/details.html",
    }


@app.get("/tasks")
async def serve_tasks():
    """Return task management page."""
    response = _render_html(
        "tasks.html",
        replacements={
            "__TASK_MANAGER_ASSET_VERSION__": _asset_version(
                [
                    os.path.join(WEBUI_DIR, "tasks.html"),
                    os.path.join(WEBUI_DIR, "task_manager.js"),
                    os.path.join(WEBUI_DIR, "task_manager.css"),
                ]
            )
        },
    )
    if response:
        return response
    return {
        "message": "Task page not found",
        "note": "Missing file: api/webui/tasks.html",
    }


@app.get("/dashboard")
async def redirect_dashboard():
    """Keep old dashboard entry as alias."""
    return RedirectResponse(url="/overview", status_code=307)


@app.get("/api/health")
async def health_check():
    return {"status": "ok"}


@app.get("/api/env/check")
async def check_environment():
    """Check if MediaCrawler environment is configured correctly"""
    try:
        # Run uv run main.py --help command to check environment
        process = await asyncio.create_subprocess_exec(
            "uv", "run", "main.py", "--help",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd="."  # Project root directory
        )
        stdout, stderr = await asyncio.wait_for(
            process.communicate(),
            timeout=30.0  # 30 seconds timeout
        )

        if process.returncode == 0:
            return {
                "success": True,
                "message": "MediaCrawler environment configured correctly",
                "output": stdout.decode("utf-8", errors="ignore")[:500]  # Truncate to first 500 characters
            }
        else:
            error_msg = stderr.decode("utf-8", errors="ignore") or stdout.decode("utf-8", errors="ignore")
            return {
                "success": False,
                "message": "Environment check failed",
                "error": error_msg[:500]
            }
    except asyncio.TimeoutError:
        return {
            "success": False,
            "message": "Environment check timeout",
            "error": "Command execution exceeded 30 seconds"
        }
    except FileNotFoundError:
        return {
            "success": False,
            "message": "uv command not found",
            "error": "Please ensure uv is installed and configured in system PATH"
        }
    except Exception as e:
        return {
            "success": False,
            "message": "Environment check error",
            "error": str(e)
        }


@app.get("/api/config/platforms")
async def get_platforms():
    """Get list of supported platforms"""
    return {
        "platforms": [
            {"value": "xhs", "label": "Xiaohongshu", "icon": "book-open"},
            {"value": "dy", "label": "Douyin", "icon": "music"},
            {"value": "ks", "label": "Kuaishou", "icon": "video"},
            {"value": "bili", "label": "Bilibili", "icon": "tv"},
            {"value": "wb", "label": "Weibo", "icon": "message-circle"},
            {"value": "tieba", "label": "Baidu Tieba", "icon": "messages-square"},
            {"value": "zhihu", "label": "Zhihu", "icon": "help-circle"},
            {"value": "wx", "label": "WeChat OA", "icon": "newspaper"},
            {"value": "gov", "label": "Government", "icon": "landmark"},
        ]
    }


@app.get("/api/config/options")
async def get_config_options():
    """Get all configuration options"""
    return {
        "login_types": [
            {"value": "qrcode", "label": "QR Code Login"},
            {"value": "cookie", "label": "Cookie Login"},
        ],
        "crawler_types": [
            {"value": "search", "label": "Search Mode"},
            {"value": "detail", "label": "Detail Mode"},
            {"value": "creator", "label": "Creator Mode"},
        ],
        "save_options": [
            {"value": "jsonl", "label": "JSONL File"},
            {"value": "json", "label": "JSON File"},
            {"value": "csv", "label": "CSV File"},
            {"value": "excel", "label": "Excel File"},
            {"value": "sqlite", "label": "SQLite Database"},
            {"value": "db", "label": "MySQL Database"},
            {"value": "mongodb", "label": "MongoDB Database"},
            {"value": "postgres", "label": "PostgreSQL Database"},
        ],
    }


@app.get("/api/config/gov/sites")
async def get_gov_sites():
    rows = []
    for site in GovSiteRegistry.list_sites():
        code = str(site.get("site_code") or "").strip()
        status = str(site.get("status") or "pending_dynamic").strip()
        rows.append(
            {
                "value": code,
                "label": str(site.get("site_name") or code),
                "status": status,
                "default_channel": str(site.get("default_channel") or "main"),
                "base_url": str(site.get("base_url") or ""),
                "verified_mode": str(site.get("verified_mode") or ""),
                "verify_error": str(site.get("verify_error") or ""),
                "last_verified_at": str(site.get("last_verified_at") or ""),
                "verify_success_rate": float(site.get("verify_success_rate") or 0.0),
            }
        )
    return {"sites": rows}


@app.get("/api/config/gov/channels")
async def get_gov_channels(site: str = Query(..., min_length=1)):
    try:
        site_info = GovSiteRegistry.get_site(site_code=site)
    except Exception as exc:
        raise HTTPException(status_code=404, detail=f"Unknown gov site: {site}") from exc
    default_channel = str(site_info.get("default_channel") or "main")
    status = str(site_info.get("status") or "pending_dynamic")
    rows = []

    if status == "ready":
        try:
            rule = GovRuleLoader().load_site_rule(site=site)
            channels = rule.get("channels") or {}
            if isinstance(channels, dict):
                for channel_name in sorted(channels.keys()):
                    rows.append({"value": str(channel_name), "label": str(channel_name), "status": status})
        except Exception:
            rows = []

    if not rows:
        rows = [{"value": default_channel, "label": default_channel, "status": status}]

    return {
        "site": site,
        "status": status,
        "default_channel": default_channel,
        "channels": rows,
    }


# Mount static resources - must be placed after all routes
if os.path.exists(WEBUI_DIR):
    assets_dir = os.path.join(WEBUI_DIR, "assets")
    if os.path.exists(assets_dir):
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")
    # Mount logos directory
    logos_dir = os.path.join(WEBUI_DIR, "logos")
    if os.path.exists(logos_dir):
        app.mount("/logos", StaticFiles(directory=logos_dir), name="logos")
    # Mount other static files (e.g., vite.svg)
    app.mount("/static", StaticFiles(directory=WEBUI_DIR), name="webui-static")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
