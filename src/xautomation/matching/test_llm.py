from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from openai import OpenAI

from xautomation.settings import Settings

_DEFAULT_SAMPLE = Path(__file__).resolve().parent.parent / "output" / "output_16-46-50.json"

TREND_SYSTEM = """You analyze a batch of posts from an X (Twitter) timeline scrape (single session, partial feed — not all of X).

Task: infer narrative trends and themes from text + engagement + timestamps. Use only provided posts; do not invent off-platform context.

Rules:
- Cite evidence with post `id` values from the payload (not permalinks unless id missing).
- When `created_at` is null, say timing unknown for that post; do not guess order beyond given list order.
- Weight high-engagement posts as stronger signals only when text supports a theme (avoid "viral but unrelated" as a trend).
- Call out noise: one-liners, ads, duplicates, quote-truncation, non-English if relevant.
- If themes are weak or sample too mixed, say so in data_caveats.

Return ONLY valid JSON with this exact top-level shape (all keys required; use null or [] where nothing applies):
{
  "executive_summary": "string, 2-4 sentences",
  "primary_themes": [
    {
      "name": "short label",
      "description": "what ties posts together",
      "example_post_ids": ["id", "..."],
      "strength": "dominant|notable|minor",
      "engagement_note": "e.g. mostly high likes, or mixed"
    }
  ],
  "secondary_signals": ["stray patterns, single posts worth noting"],
  "temporal_notes": "string or null — patterns vs time if timestamps support it, else null",
  "audience_or_domain_focus": "who/what this slice looks aimed at, or null if unclear",
  "data_caveats": ["limits of this scrape, missing fields, selection bias"]
}
"""


def _default_posts_path() -> Path:
    return _DEFAULT_SAMPLE


def _load_timeline(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise FileNotFoundError(f"timeline JSON not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def _compact_for_llm(data: dict[str, Any], *, text_max: int = 700) -> dict[str, Any]:
    meta = data.get("meta") or {}
    posts: list[dict[str, Any]] = data.get("posts") or []
    return {
        "meta": {
            "target_url": meta.get("target_url"),
            "collected_at": meta.get("collected_at"),
            "post_count": meta.get("post_count"),
            "scroll_iterations": meta.get("scroll_iterations"),
            "warnings": meta.get("warnings") or [],
        },
        "posts": [
            {
                "id": p.get("id"),
                "author_handle": p.get("author_handle"),
                "created_at": p.get("created_at"),
                "text": (p.get("text") or "")[:text_max],
                "likes": p.get("likes"),
                "reposts": p.get("reposts"),
                "replies": p.get("replies"),
            }
            for p in posts
        ],
    }


class LLMrun:
    def __init__(self, args: argparse.Namespace):
        self.args = args
        self.settings = Settings()

    def run(self) -> int:
        raw_posts = getattr(self.args, "posts", None)
        path = Path(raw_posts) if raw_posts else _default_posts_path()
        data = _load_timeline(path)
        compact = _compact_for_llm(data)

        user_blob = json.dumps(
            {
                "instruction": "Analyze trends for this timeline sample.",
                "timeline": compact,
            },
            ensure_ascii=False,
        )

        client = OpenAI(
            base_url=self.settings.openai_base_url,
            api_key=self.settings.openai_api_key,
        )
        resp = client.chat.completions.create(
            model=self.settings.llm_model,
            temperature=0.35,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": TREND_SYSTEM},
                {"role": "user", "content": user_blob},
            ],
        )
        content = resp.choices[0].message.content
        if content:
            parsed = json.loads(content)
            print(json.dumps(parsed, ensure_ascii=False, indent=2))
        return 0
