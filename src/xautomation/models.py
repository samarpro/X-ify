from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class PostRecord(BaseModel):
    """Normalized post from the timeline."""

    id: str
    text: str
    author_handle: str = ""
    created_at: datetime | None = None
    permalink: str = ""
    likes: int | None = None
    reposts: int | None = None
    replies: int | None = None
    raw: dict[str, Any] = Field(default_factory=dict)


class RejectedPost(BaseModel):
    post: PostRecord
    reason_code: str
    detail: str = ""


class RankedPost(BaseModel):
    post: PostRecord
    score: float
    rationale: str = ""


class ScrapeMeta(BaseModel):
    target_url: str
    collected_at: datetime
    post_count: int
    scroll_iterations: int = 0
    warnings: list[str] = Field(default_factory=list)


class ScrapeResult(BaseModel):
    meta: ScrapeMeta
    posts: list[PostRecord] = Field(default_factory=list)
    passed_rules: list[PostRecord] = Field(default_factory=list)
    rejected: list[RejectedPost] = Field(default_factory=list)
    ranked: list[RankedPost] = Field(default_factory=list)
