import argparse
import json
from pathlib import Path

from scraper.models import ScrapeConfig
from scraper.x_timeline import scrape_x_timeline


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Standalone X timeline scraper")
    parser.add_argument("--target-posts", type=int, default=30)
    parser.add_argument("--max-scrolls", type=int, default=16)
    parser.add_argument("--user-data-dir", required=True)
    parser.add_argument("--profile-directory", default=None)
    parser.add_argument("--output-file", default="output/x_scrape.json")
    parser.add_argument("--headless", action="store_true")
    return parser


def run_with_args(args: argparse.Namespace) -> dict:
    config = ScrapeConfig(
        target_posts=args.target_posts,
        max_scrolls=args.max_scrolls,
        user_data_dir=args.user_data_dir,
        profile_directory=args.profile_directory,
        output_file=args.output_file,
        headless=args.headless,
    )
    result = scrape_x_timeline(config)
    result.write()
    return result.to_dict()


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    data = run_with_args(args)
    print(json.dumps(data, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
