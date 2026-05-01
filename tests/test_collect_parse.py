from __future__ import annotations

from xautomation.scraper.collect import _abs_url, _parse_count, _parse_status_href


def test_parse_status_href():
    assert _parse_status_href("/user/status/123") == ("user", "123")
    assert _parse_status_href("https://x.com/user/status/123?s=1") == ("user", "123")
    assert _parse_status_href("/bad") == ("", "")


def test_abs_url():
    assert _abs_url("/x") == "https://x.com/x"
    assert _abs_url("https://x.com/a") == "https://x.com/a"


def test_parse_count():
    assert _parse_count("12") == 12
    assert _parse_count("1.2K") == 1200
    assert _parse_count("") is None
