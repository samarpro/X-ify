from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from scraper.models import ScrapeConfig
from scraper.x_timeline import scrape_x_timeline


class ScrapeRequest(BaseModel):
    target_posts: int = Field(default=30, ge=1, le=500)
    max_scrolls: int = Field(default=16, ge=1, le=200)
    user_data_dir: str
    profile_directory: str | None = None
    output_file: str = "output/x_scrape.json"
    headless: bool = False


app = FastAPI(title="X Scrape Service")


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/scrape")
def scrape(request: ScrapeRequest) -> dict:
    config = ScrapeConfig(
        target_posts=request.target_posts,
        max_scrolls=request.max_scrolls,
        user_data_dir=request.user_data_dir,
        profile_directory=request.profile_directory,
        output_file=request.output_file,
        headless=request.headless,
    )
    try:
        result = scrape_x_timeline(config)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    result.write()
    return result.to_dict()
