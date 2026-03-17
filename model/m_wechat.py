# -*- coding: utf-8 -*-
# Copyright (c) 2025 relakkes@gmail.com
#
# This file is part of MediaCrawler project.
# Repository: https://github.com/NanmiCoder/MediaCrawler/blob/main/model/m_wechat.py
# GitHub: https://github.com/NanmiCoder
# Licensed under NON-COMMERCIAL LEARNING LICENSE 1.1
#

from pydantic import BaseModel, Field


class WxAccount(BaseModel):
    biz: str = Field(..., description="公众号biz")
    account: str = Field(default="", description="公众号名称")
    head_url: str = Field(default="", description="头像")
    summary: str = Field(default="", description="简介")
    qr_code: str = Field(default="", description="二维码")
    verify: str = Field(default="", description="认证信息")
    spider_time: str = Field(default="", description="抓取时间")


class WxArticle(BaseModel):
    article_id: str = Field(..., description="文章唯一ID")
    sn: str = Field(default="", description="文章sn")
    biz: str = Field(default="", description="公众号biz")
    account: str = Field(default="", description="公众号名称")
    title: str = Field(default="", description="标题")
    url: str = Field(default="", description="链接")
    author: str = Field(default="", description="作者")
    publish_time: str = Field(default="", description="发布时间")
    digest: str = Field(default="", description="摘要")
    cover: str = Field(default="", description="封面")
    pics_url: str = Field(default="", description="图片列表")
    content_html: str = Field(default="", description="正文HTML")
    source_url: str = Field(default="", description="原文链接")
    comment_id: str = Field(default="", description="评论ID")
    read_num: int = Field(default=0, description="阅读数")
    like_num: int = Field(default=0, description="点赞数")
    comment_count: int = Field(default=0, description="评论数")
    spider_time: str = Field(default="", description="抓取时间")
    source_keyword: str = Field(default="", description="来源关键词")


class WxArticleDynamic(BaseModel):
    sn: str = Field(default="", description="文章sn")
    biz: str = Field(default="", description="公众号biz")
    read_num: int = Field(default=0, description="阅读数")
    like_num: int = Field(default=0, description="点赞数")
    comment_count: int = Field(default=0, description="评论数")
    spider_time: str = Field(default="", description="抓取时间")


class WxArticleComment(BaseModel):
    content_id: str = Field(..., description="评论内容ID")
    comment_id: str = Field(default="", description="文章评论ID")
    sn: str = Field(default="", description="文章sn")
    biz: str = Field(default="", description="公众号biz")
    nick_name: str = Field(default="", description="昵称")
    logo_url: str = Field(default="", description="头像")
    content: str = Field(default="", description="评论内容")
    create_time: str = Field(default="", description="评论时间")
    like_num: int = Field(default=0, description="点赞数")
    is_top: int = Field(default=0, description="是否置顶")
    spider_time: str = Field(default="", description="抓取时间")
