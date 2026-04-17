#!/usr/bin/env python3
import json
import re
import subprocess
from pathlib import Path

PROFILE = "user"
WORKDIR = "/Users/samkanu/.openclaw/workspace"
OUTPUT_DIR = Path(WORKDIR) / "Projects/Xautomation/output"
OUTPUT_FILE = OUTPUT_DIR / "x_scrape.json"
TARGET_POSTS = 30
MAX_SCROLLS = 16

NOISE_PHRASES = {
    "Embedded video",
    "Play Video",
    "Pause",
    "Unmute",
    "Video Settings",
    "Picture-in-Picture",
    "Full screen",
    "Quote",
    "Ad",
    "Show more",
    "Subscribe",
    "Subscribe Today’s News",
    "Terms of Service",
    "Privacy Policy",
    "Cookie Policy",
    "Accessibility",
    "Ads info",
    "Post",
    "Home",
    "Explore",
    "Notifications",
    "Follow",
    "Chat",
    "Grok",
    "Bookmarks",
    "Creator Studio",
    "Premium",
    "Profile",
}


def run(cmd: str) -> str:
    return subprocess.check_output(cmd, shell=True, text=True, cwd=WORKDIR)


def get_tabs() -> str:
    return run(f"openclaw browser --browser-profile {PROFILE} tabs")


def focus_x_tab(tabs_text: str) -> str | None:
    current_id = None
    for line in tabs_text.splitlines():
        m = re.match(r"^(\d+)\. .*", line.strip())
        if m:
            current_id = m.group(1)
        if "x.com/" in line or "x.com/home" in line:
            return current_id
    return None


def get_snapshot() -> str:
    return run(f"openclaw browser --browser-profile {PROFILE} snapshot --format ai --limit 600")


def scroll_feed() -> None:
    run(f"openclaw browser --browser-profile {PROFILE} press PageDown")


def normalize_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def strip_counts_and_media(summary: str) -> str:
    text = summary
    text = re.sub(r"\b\d+\s+(replies|reply|reposts|likes|bookmarks|views)\b.*$", "", text, flags=re.I)
    text = re.sub(r"Embedded video.*$", "", text, flags=re.I)
    text = re.sub(r"\b\d{1,2}:\d{2}\s+of\s+\d{1,2}:\d{2}.*$", "", text, flags=re.I)
    text = re.sub(r"\b\d{1,2}:\d{2}\b.*$", "", text)
    return normalize_whitespace(text)


def extract_from_summary(summary: str):
    clean = strip_counts_and_media(summary)

    display = None
    handle = None
    age = None
    body = clean

    m = re.match(r"^(.*?)\s+Verified account\s+(@[A-Za-z0-9_]+)\s+(.*)$", clean)
    if m:
        display = m.group(1).strip()
        handle = m.group(2).strip()
        rest = m.group(3).strip()
    else:
        m = re.match(r"^(.*?)\s+(@[A-Za-z0-9_]+)\s+(.*)$", clean)
        if m:
            display = m.group(1).strip()
            handle = m.group(2).strip()
            rest = m.group(3).strip()
        else:
            rest = clean

    m = re.match(r"^(\d+\s+(seconds?|minutes?|hours?|days?|weeks?)\s+ago|Now)\s+(.*)$", rest, flags=re.I)
    if m:
        raw_age = m.group(1)
        rest = m.group(3).strip()
        age = raw_age.replace(" seconds ago", "s").replace(" second ago", "s")
        age = age.replace(" minutes ago", "m").replace(" minute ago", "m")
        age = age.replace(" hours ago", "h").replace(" hour ago", "h")
        age = age.replace(" days ago", "d").replace(" day ago", "d")
        age = age.replace(" weeks ago", "w").replace(" week ago", "w")

    body = rest

    # Remove trailing quoted-post attribution or source labels when they leak in.
    body = re.split(r"\bFrom\s+[A-Za-z0-9._-]+\b", body)[0].strip()
    body = re.split(r"\bQuote\s+[A-Z]", body)[0].strip()
    body = normalize_whitespace(body)
    return display, handle, age, body


def is_noise_line(val: str) -> bool:
    if not val:
        return True
    if val in NOISE_PHRASES:
        return True
    if val.startswith('@'):
        return True
    if re.match(r'^\d+(\.\d+)?[KM]$', val):
        return True
    if re.match(r'^\d+\s+(Replies|Reply|reposts|Likes|views|bookmarks).*', val):
        return True
    if re.match(r'^\d{1,2}:\d{2}(\s*/\s*\d{1,2}:\d{2})?$', val):
        return True
    if re.match(r'^(\d+|\d+ percent)$', val):
        return True
    if val in {'|', '© 2026 X Corp.'}:
        return True
    if 'Trending' in val or 'Today’s News' in val:
        return True
    return False


def clean_body_text(body: str, display: str | None, handle: str | None) -> str:
    text = normalize_whitespace(body)
    if display:
        text = re.sub(rf'^{re.escape(display)}\s+', '', text)
    if handle:
        text = text.replace(handle, '').strip()
    text = re.sub(r'\b(\d+(\.\d+)?[KM])\b$', '', text).strip()
    text = re.sub(r'\b(Play Video|Embedded video|Quote|From\s+[A-Za-z0-9._-]+)\b.*$', '', text).strip()
    text = normalize_whitespace(text)
    return text


def dedupe_key(post: dict) -> tuple:
    norm_body = normalize_whitespace((post.get('body') or '').lower())
    norm_body = re.sub(r'[^a-z0-9@# ]+', '', norm_body)
    return (
        (post.get('handle') or '').lower(),
        norm_body[:220],
    )


def parse_snapshot(text: str):
    posts = []
    parts = text.split('- article "')
    for raw in parts[1:]:
        summary = raw.split('" [ref=', 1)[0].strip()
        display, handle, age, body = extract_from_summary(summary)

        lines = raw.splitlines()
        body_bits = []
        for line in lines:
            s = line.strip()
            if not s:
                continue
            m = re.search(r'- statictext "([^\"]+)"', s)
            if not m:
                continue
            val = m.group(1).strip()
            if is_noise_line(val):
                continue
            body_bits.append(val)

        candidate_body = clean_body_text(' '.join(body_bits), display, handle)

        # Prefer summary-derived body because it is usually closer to the visible post text.
        if body and len(body) >= 8:
            final_body = body
        else:
            final_body = candidate_body

        final_body = clean_body_text(final_body, display, handle)

        # Skip obvious junk cards that still leak through.
        if not handle and not display:
            continue
        if not final_body or len(final_body) < 2:
            continue
        if 'Subscribe to Premium' in final_body:
            continue

        posts.append({
            'display_name': display,
            'handle': handle,
            'age': age,
            'body': final_body,
            'summary': summary,
        })
    return posts


def scrape_posts(target_posts: int = TARGET_POSTS):
    tabs = get_tabs()
    tab_id = focus_x_tab(tabs)
    if tab_id:
        run(f"openclaw browser --browser-profile {PROFILE} focus {tab_id}")

    collected = []
    seen = set()

    for _ in range(MAX_SCROLLS):
        snapshot = get_snapshot()
        batch = parse_snapshot(snapshot)
        for post in batch:
            key = dedupe_key(post)
            if key in seen:
                continue
            seen.add(key)
            collected.append(post)
            if len(collected) >= target_posts:
                return tab_id, collected
        scroll_feed()
    return tab_id, collected


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    tab_id, posts = scrape_posts(TARGET_POSTS)
    out = {
        'profile': PROFILE,
        'tab_id': tab_id,
        'post_count': len(posts),
        'target_posts': TARGET_POSTS,
        'output_file': str(OUTPUT_FILE),
        'posts': posts,
    }
    OUTPUT_FILE.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding='utf-8')
    print(json.dumps(out, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()
