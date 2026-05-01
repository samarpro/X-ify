from __future__ import annotations

import logging
from pathlib import Path
from typing import Annotated

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.responses import JSONResponse

from xautomation.api.schemas import ScrapeRequest
from xautomation.pipeline import PipelineOptions, run_pipeline
from xautomation.settings import Settings

log = logging.getLogger(__name__)

app = FastAPI(title="xautomation", version="0.1.0")
_settings = Settings()


def require_api_token(x_api_token: str | None = Header(default=None, alias="X-API-Token")) -> None:
    if _settings.api_token and x_api_token != _settings.api_token:
        raise HTTPException(status_code=401, detail="invalid or missing X-API-Token")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/scrape")
def scrape(
    body: ScrapeRequest,
    _: Annotated[None, Depends(require_api_token)],
):
    rules_path = Path(body.rules_path)
    if not rules_path.is_file():
        raise HTTPException(status_code=400, detail=f"rules_path not found: {rules_path}")

    brief = body.brief_text
    if body.brief_path:
        bp = Path(body.brief_path)
        if not bp.is_file():
            raise HTTPException(status_code=400, detail=f"brief_path not found: {bp}")
        brief = bp.read_text(encoding="utf-8")

    user_data = Path(body.user_data_dir) if body.user_data_dir else _settings.x_user_data_dir

    opts = PipelineOptions(
        target_url=body.target_url,
        rules_path=rules_path,
        user_data_dir=user_data,
        max_posts=body.max_posts,
        max_scroll_iterations=body.max_scroll_iterations,
        headless=body.headless,
        use_llm=body.use_llm,
        brief_text=brief,
        openai_api_key=_settings.openai_api_key,
        openai_base_url=_settings.openai_base_url,
        llm_model=_settings.llm_model,
    )
    log.info("api scrape target=%s", body.target_url)
    result = run_pipeline(opts)
    return JSONResponse(content=result.model_dump(mode="json"))
