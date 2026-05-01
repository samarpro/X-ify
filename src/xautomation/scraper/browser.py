from __future__ import annotations

import logging
import os
from pathlib import Path
import profile

from playwright.sync_api import BrowserContext, Playwright

log = logging.getLogger(__name__)



_WEBDRIVER_INIT = (
    "Object.defineProperty(navigator, 'webdriver', {get: () => undefined});"
)


def open_persistent_context(
    playwright: Playwright,
    user_data_dir: Path,
    *,
    headless: bool,
    channel: str | None = None,
) -> BrowserContext:
    ctx = playwright.chromium.launch_persistent_context(
        user_data_dir=str(user_data_dir),
        headless=headless,
        channel="chrome",
        ignore_default_args=["--enable-automation", "--no-sandbox"],
        args=["--disable-blink-features=AutomationControlled"],
    )
    ctx.add_init_script(_WEBDRIVER_INIT)
    return ctx


def primary_page(context: BrowserContext):
    if context.pages:
        return context.pages[0]
    return context.new_page()
