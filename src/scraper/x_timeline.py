import re
from pathlib import Path

from .models import Post, ScrapeConfig, ScrapeResult
from .normalize import clean_body_text, dedupe_key, normalize_whitespace


def _normalize_age(value: str | None) -> str | None:
    if not value:
        return None
    raw = normalize_whitespace(value)
    lowered = raw.lower()
    replacements = [
        (" seconds ago", "s"),
        (" second ago", "s"),
        (" minutes ago", "m"),
        (" minute ago", "m"),
        (" hours ago", "h"),
        (" hour ago", "h"),
        (" days ago", "d"),
        (" day ago", "d"),
        (" weeks ago", "w"),
        (" week ago", "w"),
    ]
    for old, new in replacements:
        if lowered.endswith(old):
            return lowered.replace(old, new)
    if lowered == "now":
        return "Now"
    return raw


def _split_name_and_handle(text: str) -> tuple[str | None, str | None, str]:
    clean = normalize_whitespace(text)
    match = re.match(r"^(.*?)\s+(@[A-Za-z0-9_]+)\s*(.*)$", clean)
    if not match:
        return None, None, clean
    return (
        match.group(1).strip() or None,
        match.group(2).strip(),
        match.group(3).strip(),
    )


def _post_from_article(article) -> Post | None:
    summary = normalize_whitespace(article.inner_text(timeout=1000))
    if not summary:
        return None

    handle_locator = article.locator('a[href^="/"][role="link"] span').filter(
        has_text="@"
    )
    handle = None
    if handle_locator.count() > 0:
        handle = normalize_whitespace(handle_locator.first.inner_text(timeout=500))
        if not handle.startswith("@"):
            handle = None

    display_name = None
    if handle:
        probe = summary.split(handle, 1)[0].strip()
        if probe:
            display_name = probe.split("\n")[-1].strip() or None

    age = None
    time_locator = article.locator("time")
    if time_locator.count() > 0:
        raw_age = (
            time_locator.first.get_attribute("aria-label")
            or time_locator.first.inner_text()
        )
        age = _normalize_age(raw_age)

    text_nodes = article.locator('[data-testid="tweetText"]')
    body_parts = []
    count = text_nodes.count()
    for idx in range(count):
        body_parts.append(text_nodes.nth(idx).inner_text(timeout=500))
    body = clean_body_text(
        " ".join(body_parts) if body_parts else summary, display_name, handle
    )

    if not body or len(body) < 2:
        return None
    if "Subscribe to Premium" in body:
        return None

    if not handle and not display_name:
        display_name, handle, inferred_body = _split_name_and_handle(summary)
        if inferred_body and len(inferred_body) >= len(body):
            body = clean_body_text(inferred_body, display_name, handle)

    return Post(
        display_name=display_name,
        handle=handle,
        age=age,
        body=body,
        summary=summary,
    )


def scrape_x_timeline(config: ScrapeConfig) -> ScrapeResult:
    try:
        from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise RuntimeError(
            "Playwright is not installed. Run: python3 -m pip install playwright"
        ) from exc

    if not config.user_data_dir:
        raise ValueError("user_data_dir is required")

    profile_label = config.profile_directory or "default"
    output_path = str(Path(config.output_file))
    seen = set()
    posts: list[Post] = []

    launch_args = []
    if config.profile_directory:
        launch_args.append(f"--profile-directory={config.profile_directory}")

    with sync_playwright() as pw:
        context = pw.chromium.launch_persistent_context(
            user_data_dir=config.user_data_dir,
            headless=config.headless,
            args=launch_args,
        )
        try:
            page = context.pages[0] if context.pages else context.new_page()
            page.goto("https://x.com/home", wait_until="domcontentloaded")
            try:
                page.wait_for_selector("article", timeout=15000)
            except PlaywrightTimeoutError as exc:
                raise RuntimeError("Timed out waiting for X timeline articles") from exc

            for _ in range(config.max_scrolls):
                articles = page.locator("article")
                count = articles.count()
                for idx in range(count):
                    post = _post_from_article(articles.nth(idx))
                    if post is None:
                        continue
                    key = dedupe_key({"handle": post.handle, "body": post.body})
                    if key in seen:
                        continue
                    seen.add(key)
                    posts.append(post)
                    if len(posts) >= config.target_posts:
                        return ScrapeResult(
                            profile=profile_label,
                            tab_id=None,
                            post_count=len(posts),
                            target_posts=config.target_posts,
                            output_file=output_path,
                            posts=posts,
                        )
                page.keyboard.press("PageDown")
                page.wait_for_timeout(500)
        finally:
            context.close()

    return ScrapeResult(
        profile=profile_label,
        tab_id=None,
        post_count=len(posts),
        target_posts=config.target_posts,
        output_file=output_path,
        posts=posts,
    )
