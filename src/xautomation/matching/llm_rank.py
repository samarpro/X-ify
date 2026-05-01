from __future__ import annotations

import json
import logging
from typing import Any

import httpx
from pydantic import BaseModel, Field

from xautomation.models import PostRecord, RankedPost

log = logging.getLogger(__name__)


class LLMRankItem(BaseModel):
    post_id: str
    score: float
    rationale: str = ""


class LLMRankResponse(BaseModel):
    items: list[LLMRankItem] = Field(default_factory=list)


def rank_with_llm(
    posts: list[PostRecord],
    brief: str,
    *,
    api_key: str,
    base_url: str,
    model: str,
    timeout_s: float = 120.0,
) -> list[RankedPost]:
    if not posts:
        return []
    if not api_key:
        raise ValueError("OPENAI_API_KEY is required for LLM ranking")

    compact = [
        {"id": p.id, "author": p.author_handle, "text": p.text[:800]}
        for p in posts
    ]
    system = (
        "You rank social posts for relevance to the user's project. "
        "Return ONLY valid JSON with shape: {\"items\": [{\"post_id\": string, \"score\": number, \"rationale\": string}]} "
        "Score 0-10 where 10 is highly actionable for the project. Include every post_id from the user list."
    )
    user = json.dumps({"project_brief": brief, "posts": compact}, ensure_ascii=False)
    url = base_url.rstrip("/") + "/chat/completions"
    payload: dict[str, Any] = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": 0.2,
        "response_format": {"type": "json_object"},
    }
    headers = {"Authorization": f"Bearer {api_key}"}
    log.info("llm rank request posts=%s model=%s", len(posts), model)
    with httpx.Client(timeout=timeout_s) as client:
        r = client.post(url, json=payload, headers=headers)
        r.raise_for_status()
        data = r.json()
    content = data["choices"][0]["message"]["content"]
    parsed = LLMRankResponse.model_validate(json.loads(content))
    by_id = {p.id: p for p in posts}
    ranked: list[RankedPost] = []
    for it in parsed.items:
        post = by_id.get(it.post_id)
        if post is None:
            continue
        ranked.append(RankedPost(post=post, score=it.score, rationale=it.rationale))
    for p in posts:
        if p.id not in {x.post.id for x in ranked}:
            ranked.append(RankedPost(post=p, score=0.0, rationale="missing from model output"))
    ranked.sort(key=lambda x: x.score, reverse=True)
    return ranked
