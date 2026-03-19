# -*- coding: utf-8 -*-
# Copyright (c) 2025 relakkes@gmail.com
#
# This file is part of MediaCrawler project.
# Repository: https://github.com/NanmiCoder/MediaCrawler/blob/main/media_platform/gov/rule_loader.py
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

import json
from pathlib import Path
from typing import Any

from .site_registry import GovSiteRegistry


class GovRuleLoader:
    _RULE_EXTENSIONS = (".yaml", ".yml", ".json")

    @classmethod
    def _default_rule_dir(cls) -> Path:
        return Path(__file__).resolve().parent / "rules"

    @classmethod
    def _resolve_rule_path(cls, site: str, custom_rule_path: str = "") -> Path:
        if not site:
            raise ValueError("[GovRuleLoader] site cannot be empty.")

        if custom_rule_path:
            raw_path = Path(custom_rule_path).expanduser()
            path_obj = raw_path if raw_path.is_absolute() else Path.cwd() / raw_path
            if path_obj.is_file():
                return path_obj
            if path_obj.is_dir():
                for ext in cls._RULE_EXTENSIONS:
                    candidate = path_obj / f"{site}{ext}"
                    if candidate.exists():
                        return candidate
                raise FileNotFoundError(f"[GovRuleLoader] Rule not found for site={site} under {path_obj}")
            raise FileNotFoundError(f"[GovRuleLoader] custom rule path not found: {path_obj}")

        default_dir = cls._default_rule_dir()
        for ext in cls._RULE_EXTENSIONS:
            candidate = default_dir / f"{site}{ext}"
            if candidate.exists():
                return candidate
        raise FileNotFoundError(f"[GovRuleLoader] Rule not found for site={site}, rule_dir={default_dir}")

    @staticmethod
    def _parse_rule_text(text: str) -> dict[str, Any]:
        text = str(text or "").strip()
        if not text:
            raise ValueError("[GovRuleLoader] Empty rule content.")
        try:
            return dict(json.loads(text))
        except json.JSONDecodeError:
            try:
                import yaml  # type: ignore
            except Exception as exc:
                raise ValueError(
                    "[GovRuleLoader] Rule is not valid JSON, and PyYAML is not installed for YAML parsing."
                ) from exc
            data = yaml.safe_load(text)
            if not isinstance(data, dict):
                raise ValueError("[GovRuleLoader] Rule root must be object/map.")
            return dict(data)

    @staticmethod
    def _require(rule: dict[str, Any], dotted_path: str) -> None:
        current: Any = rule
        for part in dotted_path.split("."):
            if not isinstance(current, dict) or part not in current:
                raise ValueError(f"[GovRuleLoader] Missing required field: {dotted_path}")
            current = current[part]

    def load_site_rule(self, site: str, custom_rule_path: str = "") -> dict[str, Any]:
        path = self._resolve_rule_path(site=site, custom_rule_path=custom_rule_path)
        text = path.read_text(encoding="utf-8")
        rule = self._parse_rule_text(text)
        self.validate_rule(rule)
        return rule

    @staticmethod
    def get_default_channel(site: str) -> str:
        try:
            site_info = GovSiteRegistry.get_site(site_code=site)
            return str(site_info.get("default_channel") or "main").strip() or "main"
        except Exception:
            return "main"

    @staticmethod
    def get_channel_rule(rule: dict[str, Any], channel: str) -> dict[str, Any]:
        channels = rule.get("channels")
        if not isinstance(channels, dict):
            raise ValueError("[GovRuleLoader] channels must be a mapping.")
        selected = channels.get(channel)
        if not isinstance(selected, dict):
            raise ValueError(
                f"[GovRuleLoader] channel '{channel}' not found, available={','.join(sorted(channels.keys()))}"
            )
        return selected

    def validate_rule(self, rule: dict[str, Any]) -> None:
        self._require(rule, "site.code")
        self._require(rule, "site.base_url")
        self._require(rule, "channels")
        self._require(rule, "extract.list.item_xpath")
        self._require(rule, "extract.list.title_xpath")
        self._require(rule, "extract.list.link_xpath")
        self._require(rule, "extract.list.date_xpath")
        self._require(rule, "extract.detail.title_xpath")
        self._require(rule, "extract.detail.source_xpath")
        self._require(rule, "extract.detail.pub_time_xpath")
        self._require(rule, "extract.detail.content_xpath")
        self._require(rule, "extract.detail.attachments_xpath")
        site = rule.get("site") or {}
        fetch_mode = str(site.get("fetch_mode") or "http").strip().lower()
        if fetch_mode not in ("http", "browser"):
            raise ValueError(f"[GovRuleLoader] unsupported site.fetch_mode: {fetch_mode}")
        browser_cfg = site.get("browser") or {}
        if browser_cfg and not isinstance(browser_cfg, dict):
            raise ValueError("[GovRuleLoader] site.browser must be an object")
        actions = browser_cfg.get("actions") if isinstance(browser_cfg, dict) else None
        if actions is not None:
            if not isinstance(actions, list):
                raise ValueError("[GovRuleLoader] site.browser.actions must be a list")
            for idx, action in enumerate(actions):
                if not isinstance(action, dict):
                    raise ValueError(f"[GovRuleLoader] site.browser.actions[{idx}] must be an object")

        allow_inline_detail = site.get("allow_inline_detail")
        if allow_inline_detail is not None and not isinstance(allow_inline_detail, bool):
            raise ValueError("[GovRuleLoader] site.allow_inline_detail must be bool")
        if bool(allow_inline_detail):
            self._require(rule, "extract.inline_list.item_xpath")
            self._require(rule, "extract.inline_list.title_xpath")
