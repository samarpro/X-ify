from __future__ import annotations

import re
from datetime import UTC, datetime
from urllib.parse import urlparse

from xautomation.models import PostRecord, RejectedPost
from xautomation.rules_config import RulesConfig

_URL_RE = re.compile(r"https?://[^\s]+", re.IGNORECASE)


def _domains_in_text(text: str) -> set[str]:
    domains: set[str] = set()
    for m in _URL_RE.findall(text):
        try:
            host = urlparse(m).hostname or ""
            if host:
                domains.add(host.lower().lstrip("."))
        except ValueError:
            continue
    return domains


def _author_norm(handle: str) -> str:
    return handle.strip().lstrip("@").lower()


def _hashtags_in_text(text: str) -> set[str]:
    return {m.group(1).lower() for m in re.finditer(r"#([\w]+)", text, flags=re.UNICODE)}


def rule_filter(posts: list[PostRecord], rules: RulesConfig) -> tuple[list[PostRecord], list[RejectedPost]]:
    passed: list[PostRecord] = []
    rejected: list[RejectedPost] = []
    now = datetime.now(UTC)
    blocked = {_author_norm(a) for a in rules.blocked_authors if a}

    for post in posts:
        text = post.text
        tl = text.lower()
        author = _author_norm(post.author_handle)

        if author and author in blocked:
            rejected.append(RejectedPost(post=post, reason_code="BLOCKED_AUTHOR", detail=author))
            continue

        hit_exclude = next((kw for kw in rules.exclude_keywords if kw and kw in tl), None)
        if hit_exclude is not None:
            rejected.append(RejectedPost(post=post, reason_code="EXCLUDE_KEYWORD", detail=hit_exclude))
            continue

        if rules.include_keywords:
            if not any(kw and kw in tl for kw in rules.include_keywords):
                rejected.append(
                    RejectedPost(post=post, reason_code="INCLUDE_KEYWORD_MISS", detail="no include_keywords match")
                )
                continue

        if rules.required_hashtags:
            tags = _hashtags_in_text(text)
            needed = {h.lstrip("#").lower() for h in rules.required_hashtags if h}
            missing = [h for h in needed if h not in tags]
            if missing:
                rejected.append(
                    RejectedPost(post=post, reason_code="REQUIRED_HASHTAG_MISS", detail=",".join(missing))
                )
                continue

        domains = _domains_in_text(text)
        if rules.url_domains_blocklist:
            blocked_domains = domains & {d.lower() for d in rules.url_domains_blocklist if d}
            if blocked_domains:
                rejected.append(
                    RejectedPost(
                        post=post, reason_code="URL_BLOCKLIST_HIT", detail=",".join(sorted(blocked_domains))
                    )
                )
                continue

        if rules.url_domains_allowlist:
            allow = {d.lower() for d in rules.url_domains_allowlist if d}
            if domains and not (domains & allow):
                rejected.append(
                    RejectedPost(
                        post=post,
                        reason_code="URL_ALLOWLIST_MISS",
                        detail=f"domains={sorted(domains)}",
                    )
                )
                continue

        if post.created_at is not None:
            age_h = (now - post.created_at.astimezone(UTC)).total_seconds() / 3600.0
            if rules.min_post_age_hours is not None and age_h < rules.min_post_age_hours:
                rejected.append(RejectedPost(post=post, reason_code="TOO_NEW", detail=f"age_h={age_h:.2f}"))
                continue
            if rules.max_post_age_hours is not None and age_h > rules.max_post_age_hours:
                rejected.append(RejectedPost(post=post, reason_code="TOO_OLD", detail=f"age_h={age_h:.2f}"))
                continue

        if rules.compiled_patterns:
            if not any(p.search(text) for p in rules.compiled_patterns):
                rejected.append(RejectedPost(post=post, reason_code="PATTERN_MISS", detail="no pattern match"))
                continue

        passed.append(post)

    return passed, rejected
