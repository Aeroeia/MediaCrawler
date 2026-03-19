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
from pathlib import Path
from typing import Any


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
                    "status": str(row.get("status") or "pending_dynamic").strip(),
                    "default_channel": str(row.get("default_channel") or "main").strip() or "main",
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

