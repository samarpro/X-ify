from __future__ import annotations

from datetime import UTC, datetime, timedelta

from xautomation.matching.rules import rule_filter
from xautomation.models import PostRecord
from xautomation.rules_config import RulesConfig


def _post(**kwargs) -> PostRecord:
    base = dict(
        id="1",
        text="hello world",
        author_handle="alice",
        created_at=datetime.now(UTC) - timedelta(hours=12),
        permalink="https://x.com/alice/status/1",
    )
    base.update(kwargs)
    return PostRecord.model_validate(base)


def test_blocked_author():
    rules = RulesConfig(blocked_authors=["alice"])
    passed, rej = rule_filter([_post()], rules)
    assert not passed
    assert rej[0].reason_code == "BLOCKED_AUTHOR"


def test_exclude_keyword():
    rules = RulesConfig(exclude_keywords=["spam"])
    passed, rej = rule_filter([_post(text="this is spam")], rules)
    assert not passed
    assert rej[0].reason_code == "EXCLUDE_KEYWORD"


def test_include_required():
    rules = RulesConfig(include_keywords=["python"])
    passed, rej = rule_filter([_post(text="no match here")], rules)
    assert not passed
    assert rej[0].reason_code == "INCLUDE_KEYWORD_MISS"
    passed, _ = rule_filter([_post(text="I love python")], rules)
    assert len(passed) == 1


def test_required_hashtag():
    rules = RulesConfig(required_hashtags=["dev"])
    passed, rej = rule_filter([_post(text="no tag")], rules)
    assert rej[0].reason_code == "REQUIRED_HASHTAG_MISS"
    passed, _ = rule_filter([_post(text="hi #dev")], rules)
    assert len(passed) == 1


def test_url_blocklist():
    rules = RulesConfig(url_domains_blocklist=["evil.com"])
    passed, rej = rule_filter([_post(text="see https://evil.com/x")], rules)
    assert rej[0].reason_code == "URL_BLOCKLIST_HIT"


def test_url_allowlist_miss():
    rules = RulesConfig(url_domains_allowlist=["github.com"])
    passed, rej = rule_filter([_post(text="https://example.com/a")], rules)
    assert rej[0].reason_code == "URL_ALLOWLIST_MISS"


def test_age_too_new():
    rules = RulesConfig(min_post_age_hours=24)
    passed, rej = rule_filter([_post(created_at=datetime.now(UTC) - timedelta(hours=1))], rules)
    assert rej[0].reason_code == "TOO_NEW"


def test_pattern_miss():
    rules = RulesConfig(patterns=[r"foo\d+"])
    passed, rej = rule_filter([_post(text="bar")], rules)
    assert rej[0].reason_code == "PATTERN_MISS"
    passed, _ = rule_filter([_post(text="foo42")], rules)
    assert len(passed) == 1
