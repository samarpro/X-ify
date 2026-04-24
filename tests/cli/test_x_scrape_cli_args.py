import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from cli.x_scrape_cli import build_parser  # noqa: E402


def test_parser_defaults():
    parser = build_parser()
    args = parser.parse_args(["--user-data-dir", "/tmp/profile-root"])

    assert args.target_posts == 30
    assert args.max_scrolls == 16
    assert args.profile_directory is None
    assert args.output_file == "output/x_scrape.json"
    assert args.headless is False
