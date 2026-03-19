# -*- coding: utf-8 -*-
# Copyright (c) 2025 relakkes@gmail.com
#
# This file is part of MediaCrawler project.
# Repository: https://github.com/NanmiCoder/MediaCrawler/blob/main/tests/test_gov_batch_onboard.py
# GitHub: https://github.com/NanmiCoder
# Licensed under NON-COMMERCIAL LEARNING LICENSE 1.1
#

from media_platform.gov.batch_onboard import classify_error


def test_classify_error_timeout():
    assert classify_error("request timed out after 30s").startswith("timeout")


def test_classify_error_http_403():
    assert classify_error("HTTPStatusError: 403 Forbidden").startswith("http_403")


def test_classify_error_captcha():
    assert classify_error("hit captcha page").startswith("captcha")
