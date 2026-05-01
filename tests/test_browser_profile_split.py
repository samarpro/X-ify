from __future__ import annotations

from pathlib import Path

from xautomation.scraper.browser import chromium_user_data_root_and_profile


def test_splits_parent_and_leaf(tmp_path: Path):
    leaf = tmp_path / "b" / "MyProfile"
    leaf.mkdir(parents=True)
    root, profile = chromium_user_data_root_and_profile(leaf)
    assert profile == "MyProfile"
    assert root == tmp_path / "b"


def test_relative_path(tmp_path: Path):
    leaf = tmp_path / "nested" / "ProfX"
    leaf.mkdir(parents=True)
    root, profile = chromium_user_data_root_and_profile(leaf)
    assert profile == "ProfX"
    assert root.name == "nested"
    assert root.parent == tmp_path
