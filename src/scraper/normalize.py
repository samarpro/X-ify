import re


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
    "Subscribe Today's News",
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


def normalize_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def strip_counts_and_media(summary: str) -> str:
    text = summary
    text = re.sub(
        r"\b\d+\s+(replies|reply|reposts|likes|bookmarks|views)\b.*$",
        "",
        text,
        flags=re.I,
    )
    text = re.sub(r"Embedded video.*$", "", text, flags=re.I)
    text = re.sub(r"\b\d{1,2}:\d{2}\s+of\s+\d{1,2}:\d{2}.*$", "", text, flags=re.I)
    text = re.sub(r"\b\d{1,2}:\d{2}\b.*$", "", text)
    return normalize_whitespace(text)


def is_noise_line(val: str) -> bool:
    if not val:
        return True
    if val in NOISE_PHRASES:
        return True
    if val.startswith("@"):
        return True
    if re.match(r"^\d+(\.\d+)?[KM]$", val):
        return True
    if re.match(r"^\d+\s+(Replies|Reply|reposts|Likes|views|bookmarks).*", val):
        return True
    if re.match(r"^\d{1,2}:\d{2}(\s*/\s*\d{1,2}:\d{2})?$", val):
        return True
    if re.match(r"^(\d+|\d+ percent)$", val):
        return True
    if val in {"|", "(c) 2026 X Corp."}:
        return True
    if "Trending" in val or "Today's News" in val:
        return True
    return False


def clean_body_text(body: str, display: str | None, handle: str | None) -> str:
    text = normalize_whitespace(body)
    if display:
        text = re.sub(rf"^{re.escape(display)}\s+", "", text)
    if handle:
        text = text.replace(handle, "").strip()
    text = re.sub(r"\b(\d+(\.\d+)?[KM])\b$", "", text).strip()
    text = re.sub(
        r"\b(Play Video|Embedded video|Quote|From\s+[A-Za-z0-9._-]+)\b.*$", "", text
    ).strip()
    return normalize_whitespace(text)


def dedupe_key(post: dict) -> tuple:
    norm_body = normalize_whitespace((post.get("body") or "").lower())
    norm_body = re.sub(r"[^a-z0-9@# ]+", "", norm_body)
    return ((post.get("handle") or "").lower(), norm_body[:220])
