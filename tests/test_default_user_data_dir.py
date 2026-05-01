from __future__ import annotations

from pathlib import Path

from xautomation.settings import default_user_data_dir


def test_default_under_home():
    d = default_user_data_dir()
    assert d.is_absolute()
    home = Path.home().resolve()
    assert str(d.resolve()).startswith(str(home))
    assert "xautomation" in {p.lower() for p in d.parts}
