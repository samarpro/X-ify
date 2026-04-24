import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from scraper.models import Post, ScrapeResult  # noqa: E402


def test_output_contract_contains_expected_keys(tmp_path):
    output_file = tmp_path / "x_scrape.json"
    result = ScrapeResult(
        profile="default",
        tab_id=None,
        post_count=1,
        target_posts=30,
        output_file=str(output_file),
        posts=[
            Post(
                display_name="Jane",
                handle="@jane",
                age="1h",
                body="Hello world",
                summary="Jane @jane 1h Hello world",
            )
        ],
    )
    result.write()
    payload = json.loads(output_file.read_text(encoding="utf-8"))

    assert set(payload.keys()) == {
        "profile",
        "tab_id",
        "post_count",
        "target_posts",
        "output_file",
        "posts",
    }
    assert set(payload["posts"][0].keys()) == {
        "display_name",
        "handle",
        "age",
        "body",
        "summary",
    }
    assert payload["tab_id"] is None
