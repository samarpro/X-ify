from __future__ import annotations

from datetime import datetime
from pathlib import Path


def json_path_with_time(path: Path, *, when: datetime | None = None) -> Path:
    """
    Return a .json path that includes local wall time before the extension,
    e.g. ``output/scrape.json`` -> ``output/scrape_14-30-05.json``.
    """
    when = when or datetime.now()
    stamp = when.strftime("%H-%M-%S")
    path = path.expanduser()
    if path.suffix.lower() == ".json":
        return path.with_name(f"{path.stem}_{stamp}{path.suffix}")
    return path.with_name(f"{path.name}_{stamp}.json")
