from __future__ import annotations

from pydantic import BaseModel, Field


class ScrapeRequest(BaseModel):
    target_url: str
    rules_path: str = Field(..., description="Path to rules YAML on the server host")
    max_posts: int = 50
    max_scroll_iterations: int = 25
    headless: bool = True
    use_llm: bool = True
    brief_text: str = ""
    brief_path: str = ""
    user_data_dir: str = ""
