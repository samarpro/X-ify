import json
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass
class ScrapeConfig:
    target_posts: int = 30
    max_scrolls: int = 16
    user_data_dir: str = ""
    profile_directory: str | None = None
    output_file: str = "output/x_scrape.json"
    headless: bool = False


@dataclass
class Post:
    display_name: str | None
    handle: str | None
    age: str | None
    body: str
    summary: str


@dataclass
class ScrapeResult:
    profile: str
    tab_id: str | None
    post_count: int
    target_posts: int
    output_file: str
    posts: list[Post]

    def to_dict(self) -> dict:
        data = asdict(self)
        data["posts"] = [asdict(post) for post in self.posts]
        return data

    def write(self) -> Path:
        path = Path(self.output_file)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(self.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8"
        )
        return path
