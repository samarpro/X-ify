from __future__ import annotations

import logging
import re
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlparse

from playwright.sync_api import Locator, Page, sync_playwright

from xautomation.models import PostRecord
from xautomation.scraper import selectors as sel
from xautomation.scraper.browser import open_persistent_context, primary_page
from xautomation.settings import Settings

log = logging.getLogger(__name__)

_STATUS_RE = re.compile(r"^/([^/]+)/status/(\d+)", re.UNICODE)


def _parse_status_href(href: str | None) -> tuple[str, str]:
    if not href:
        return "", ""
    path = urlparse(href).path or href
    m = _STATUS_RE.match(path)
    if not m:
        return "", ""
    return m.group(1), m.group(2)


def _abs_url(href: str | None) -> str:
    if not href:
        return ""
    if href.startswith("http"):
        return href
    return "https://x.com" + (href if href.startswith("/") else "/" + href)


def _parse_count(raw: str) -> int | None:
    raw = raw.strip().replace(",", "")
    if not raw:
        return None
    multipliers = {"K": 1_000, "M": 1_000_000}
    if raw[-1] in multipliers and raw[:-1].replace(".", "", 1).isdigit():
        return int(float(raw[:-1]) * multipliers[raw[-1]])
    if raw.isdigit():
        return int(raw)
    return None


def _metric_from_cell(locator: Locator) -> int | None:
    try:
        if locator.count() == 0:
            return None
        txt = locator.first.inner_text(timeout=500)
    except Exception:
        return None
    return _parse_count(txt)


def post_from_tweet_locator(article: Locator) -> PostRecord | None:
    try:
        text_el = article.locator(sel.TWEET_TEXT).first
        text = text_el.inner_text(timeout=2_000) if text_el.count() else ""
    except Exception:
        text = ""

    status_link = article.locator(sel.STATUS_LINK).first
    href = status_link.get_attribute("href") if status_link.count() else None
    handle, status_id = _parse_status_href(href)
    if not status_id:
        return None
    permalink = _abs_url(href)

    author_handle = handle
    try:
        user_block = article.locator(sel.USER_NAME_BLOCK).first
        if user_block.count():
            link = user_block.locator('a[href^="/"]').first
            if link.count():
                ah = _parse_status_href(link.get_attribute("href"))[0]
                if ah:
                    author_handle = ah
    except Exception:
        pass

    created_at: datetime | None = None
    try:
        t = article.locator(sel.TIME).first
        if t.count():
            dt = t.get_attribute("datetime")
            if dt:
                created_at = datetime.fromisoformat(dt.replace("Z", "+00:00"))
    except Exception:
        pass

    likes = _metric_from_cell(article.locator(sel.LIKE))
    reposts = _metric_from_cell(article.locator(sel.REPOST))
    replies = _metric_from_cell(article.locator(sel.REPLY))

    return PostRecord(
        id=status_id,
        text=text.strip(),
        author_handle=author_handle,
        created_at=created_at,
        permalink=permalink,
        likes=likes,
        reposts=reposts,
        replies=replies,
        raw={"href": href or ""},
    )


def _collect_visible_tweets(page: Page) -> list[PostRecord]:
    articles = page.locator(sel.TWEET_ARTICLE)
    n = articles.count()
    out: list[PostRecord] = []
    for i in range(n):
        rec = post_from_tweet_locator(articles.nth(i))
        if rec:
            out.append(rec)
    return out


def collect_posts(
    user_data_dir: Path,
    target_url: str,
    *,
    max_posts: int = 50,
    max_scroll_iterations: int = 25,
    headless: bool = True,
    navigation_timeout_ms: int = 60_000,
) -> tuple[list[PostRecord], int, list[str]]:
    """Return posts, scroll_iterations used, and warnings."""
    warnings: list[str] = []
    seen: dict[str, PostRecord] = {}
    scrolls = 0

    s = Settings()
    with sync_playwright() as pw:
        ctx = open_persistent_context(
            pw,
            user_data_dir,
            headless=headless,
            channel=s.playwright_channel.strip() or None,
        )
        try:
            page = primary_page(ctx)
            page.set_default_timeout(navigation_timeout_ms)
            log.info("navigating to %s", target_url)
            page.goto(target_url, wait_until="domcontentloaded", timeout=navigation_timeout_ms)
            page.wait_for_timeout(2_000)

            if "login" in (page.url or "").lower() or page.locator('input[autocomplete="username"]').count() > 0:
                warnings.append(
                    "X may be showing a login wall. Open a headed scrape once, sign in with username/password "
                    "(not 'Sign in with Google' if Google blocks it), reuse the same profile path. "
                    "See docs/google-x-signin.md."
                )

            while len(seen) < max_posts and scrolls < max_scroll_iterations:
                for p in _collect_visible_tweets(page):
                    seen[p.id] = p
                if len(seen) >= max_posts:
                    break
                page.keyboard.press("End")
                page.wait_for_timeout(1_200)
                scrolls += 1

        finally:
            ctx.close()

    posts = list(seen.values())[:max_posts]
    meta_scrolls = scrolls
    return posts, meta_scrolls, warnings


def collect_posts_meta_time() -> datetime:
    return datetime.now(UTC)
