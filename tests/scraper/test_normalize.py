import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from scraper.normalize import (  # noqa: E402
    clean_body_text,
    dedupe_key,
    is_noise_line,
    normalize_whitespace,
    strip_counts_and_media,
)


def test_normalize_whitespace_collapses_spaces_and_newlines():
    assert normalize_whitespace(" hi   there\n\nfriend ") == "hi there friend"


def test_strip_counts_and_media_removes_engagement_tail():
    text = "someone @handle 2 hours ago hello world 23 replies, 10 likes"
    assert strip_counts_and_media(text).endswith("hello world")


def test_is_noise_line_filters_navigation_and_counts():
    assert is_noise_line("Home") is True
    assert is_noise_line("1.2K") is True
    assert is_noise_line("32 Replies") is True
    assert is_noise_line("Real post sentence") is False


def test_clean_body_text_removes_display_and_handle_artifacts():
    out = clean_body_text("Jane Doe @janedoe We shipped today", "Jane Doe", "@janedoe")
    assert out == "We shipped today"


def test_dedupe_key_uses_handle_and_normalized_body_prefix():
    post = {"handle": "@A", "body": "Hello, World!!!"}
    key = dedupe_key(post)
    assert key[0] == "@a"
    assert key[1] == "hello world"
