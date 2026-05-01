from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field, field_validator


class RulesConfig(BaseModel):
    """YAML-driven rule filter configuration."""

    include_keywords: list[str] = Field(default_factory=list)
    exclude_keywords: list[str] = Field(default_factory=list)
    required_hashtags: list[str] = Field(default_factory=list)
    blocked_authors: list[str] = Field(default_factory=list)
    url_domains_allowlist: list[str] = Field(default_factory=list)
    url_domains_blocklist: list[str] = Field(default_factory=list)
    min_post_age_hours: float | None = None
    max_post_age_hours: float | None = None
    patterns: list[str] = Field(default_factory=list)

    @field_validator(
        "include_keywords",
        "exclude_keywords",
        "required_hashtags",
        "blocked_authors",
        "url_domains_allowlist",
        "url_domains_blocklist",
        mode="before",
    )
    @classmethod
    def _lower_list(cls, v: Any) -> list[str]:
        if v is None:
            return []
        return [str(x).strip().lower() for x in v if str(x).strip()]

    @property
    def compiled_patterns(self) -> list[re.Pattern[str]]:
        return [re.compile(p, re.IGNORECASE) for p in self.patterns]


def load_rules_config(path: Path) -> RulesConfig:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValueError("rules config root must be a mapping")
    return RulesConfig.model_validate(data)
