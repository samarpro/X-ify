from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from xautomation.matching.llm_rank import rank_with_llm
from xautomation.matching.rules import rule_filter
from xautomation.models import RankedPost, ScrapeMeta, ScrapeResult
from xautomation.rules_config import RulesConfig, load_rules_config
from xautomation.scraper.collect import collect_posts

log = logging.getLogger(__name__)


@dataclass
class PipelineOptions:
    target_url: str
    rules_path: Path
    user_data_dir: Path
    max_posts: int = 50
    max_scroll_iterations: int = 25
    headless: bool = True
    use_llm: bool = True
    brief_text: str = ""
    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"
    llm_model: str = "gpt-4o-mini"


def run_pipeline(opts: PipelineOptions) -> ScrapeResult:
    rules: RulesConfig = load_rules_config(opts.rules_path)
    posts, scrolls, warnings = collect_posts(
        opts.user_data_dir,
        opts.target_url,
        max_posts=opts.max_posts,
        max_scroll_iterations=opts.max_scroll_iterations,
        headless=opts.headless,
    )
    passed, rejected = rule_filter(posts, rules)

    ranked: list[RankedPost] = []
    if opts.use_llm and passed:
        if not opts.brief_text.strip():
            warnings.append("LLM enabled but empty brief; skipping LLM rank.")
        elif not opts.openai_api_key:
            warnings.append("LLM enabled but no API key; skipping LLM rank.")
        else:
            try:
                ranked = rank_with_llm(
                    passed,
                    opts.brief_text,
                    api_key=opts.openai_api_key,
                    base_url=opts.openai_base_url,
                    model=opts.llm_model,
                )
            except Exception as e:
                log.exception("llm rank failed")
                warnings.append(f"LLM rank failed: {e}")
    elif opts.use_llm is False and passed:
        ranked = [RankedPost(post=p, score=1.0, rationale="llm disabled") for p in passed]

    meta = ScrapeMeta(
        target_url=opts.target_url,
        collected_at=datetime.now(UTC),
        post_count=len(posts),
        scroll_iterations=scrolls,
        warnings=warnings,
    )
    return ScrapeResult(
        meta=meta,
        posts=posts,
        passed_rules=passed,
        rejected=rejected,
        ranked=ranked,
    )
