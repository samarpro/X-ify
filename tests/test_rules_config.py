from __future__ import annotations

from pathlib import Path

import pytest

from xautomation.rules_config import RulesConfig, load_rules_config


def test_load_example_config(tmp_path: Path):
    p = tmp_path / "rules.yaml"
    p.write_text(
        """
include_keywords: [Python, LLM]
exclude_keywords: [spam]
required_hashtags: ["#dev"]
blocked_authors: ["Bot"]
url_domains_allowlist: ["github.com"]
url_domains_blocklist: ["evil.com"]
min_post_age_hours: 1
max_post_age_hours: 48
patterns: ["foo.*bar"]
""",
        encoding="utf-8",
    )
    cfg = load_rules_config(p)
    assert cfg.include_keywords == ["python", "llm"]
    assert "spam" in cfg.exclude_keywords
    assert cfg.required_hashtags  # lowercased
    assert cfg.compiled_patterns[0].pattern == "foo.*bar"


def test_invalid_yaml_root(tmp_path: Path):
    p = tmp_path / "bad.yaml"
    p.write_text("- not\n- a\n- mapping\n", encoding="utf-8")
    with pytest.raises(ValueError, match="mapping"):
        load_rules_config(p)


def test_rules_validate_empty():
    cfg = RulesConfig.model_validate({})
    assert cfg.include_keywords == []
