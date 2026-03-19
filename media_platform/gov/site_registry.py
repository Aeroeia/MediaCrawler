# -*- coding: utf-8 -*-
# Copyright (c) 2025 relakkes@gmail.com
#
# This file is part of MediaCrawler project.
# Repository: https://github.com/NanmiCoder/MediaCrawler/blob/main/media_platform/gov/site_registry.py
# GitHub: https://github.com/NanmiCoder
# Licensed under NON-COMMERCIAL LEARNING LICENSE 1.1
#

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


def _safe_float(value: Any) -> float:
    try:
        return float(value or 0.0)
    except Exception:
        return 0.0


class GovSiteRegistry:
    """Site registry for gov crawler with ready/pending statuses."""

    MANIFEST_FILE = "sites_manifest.json"

    @classmethod
    def default_manifest_path(cls) -> Path:
        return Path(__file__).resolve().parent / cls.MANIFEST_FILE

    @classmethod
    def load_manifest(cls, manifest_path: str = "") -> dict[str, Any]:
        path = Path(manifest_path).expanduser() if manifest_path else cls.default_manifest_path()
        if not path.is_absolute():
            path = Path.cwd() / path
        if not path.exists():
            raise FileNotFoundError(f"[GovSiteRegistry] manifest not found: {path}")

        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("[GovSiteRegistry] manifest root must be object")
        sites = payload.get("sites")
        if not isinstance(sites, list):
            raise ValueError("[GovSiteRegistry] manifest field 'sites' must be list")
        return payload

    @classmethod
    def list_sites(cls, manifest_path: str = "") -> list[dict[str, Any]]:
        payload = cls.load_manifest(manifest_path)
        rows = payload.get("sites") or []
        output: list[dict[str, Any]] = []
        for row in rows:
            if not isinstance(row, dict):
                continue
            output.append(
                {
                    "site_code": str(row.get("site_code") or "").strip(),
                    "site_name": str(row.get("site_name") or "").strip(),
                    "base_url": str(row.get("base_url") or "").strip(),
                    "status": str(row.get("status") or "pending_dynamic").strip() or "pending_dynamic",
                    "default_channel": str(row.get("default_channel") or "main").strip() or "main",
                    "verified_mode": str(row.get("verified_mode") or "").strip(),
                    "verify_error": str(row.get("verify_error") or "").strip(),
                    "last_verified_at": str(row.get("last_verified_at") or "").strip(),
                    "verify_success_rate": _safe_float(row.get("verify_success_rate")),
                }
            )
        return [row for row in output if row["site_code"]]

    @classmethod
    def get_site(cls, site_code: str, manifest_path: str = "") -> dict[str, Any]:
        code = str(site_code or "").strip().lower()
        if not code:
            raise ValueError("[GovSiteRegistry] site_code cannot be empty")

        for row in cls.list_sites(manifest_path):
            if row["site_code"].lower() == code:
                return row
        raise ValueError(f"[GovSiteRegistry] site '{site_code}' not found in manifest")

    @classmethod
    def update_sites(
        cls,
        updates: dict[str, dict[str, Any]],
        manifest_path: str = "",
    ) -> dict[str, Any]:
        payload = cls.load_manifest(manifest_path)
        rows = payload.get("sites") or []
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        for row in rows:
            if not isinstance(row, dict):
                continue
            code = str(row.get("site_code") or "").strip()
            if not code:
                continue
            update_row = updates.get(code)
            if not isinstance(update_row, dict):
                continue
            for field in (
                "status",
                "default_channel",
                "verified_mode",
                "verify_error",
                "last_verified_at",
                "verify_success_rate",
            ):
                if field in update_row:
                    row[field] = update_row[field]
            if "last_verified_at" not in update_row:
                row["last_verified_at"] = now

        path = Path(manifest_path).expanduser() if manifest_path else cls.default_manifest_path()
        if not path.is_absolute():
            path = Path.cwd() / path
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return payload
