from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from xautomation.output import json_path_with_time
from xautomation.pipeline import PipelineOptions, run_pipeline
from xautomation.rules_config import load_rules_config
from xautomation.settings import Settings, default_user_data_dir


def _configure_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=level, format="%(levelname)s %(name)s %(message)s")


def run_llm(args:argparse.Namespace) -> int:
    from xautomation.matching import test_llm
    llm = test_llm.LLMrun(args)
    llm.run()
    return 0
    

def cmd_doctor(args: argparse.Namespace) -> int:
    s = Settings()
    issues: list[str] = []
    cfg_path = Path(args.config)
    if not cfg_path.is_file():
        issues.append(f"config not found: {cfg_path}")
    else:
        try:
            load_rules_config(cfg_path)
        except Exception as e:
            issues.append(f"config parse error: {e}")
    ud = Path(args.user_data_dir) if getattr(args, "user_data_dir", None) is not None else s.x_user_data_dir
    if not ud.exists():
        try:
            ud.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            issues.append(f"cannot create user data dir {ud}: {e}")
    elif not ud.is_dir():
        issues.append(f"user data path is not a directory: {ud}")
    else:
        try:
            test = ud / ".write_test"
            test.write_text("ok", encoding="utf-8")
            test.unlink()
        except OSError as e:
            issues.append(f"user data dir not writable {ud}: {e}")

    try:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as p:
            _ = p.chromium
    except Exception as e:
        issues.append(f"playwright import/browser check failed: {e}")

    if issues:
        for i in issues:
            print("ERROR:", i, file=sys.stderr)
        return 1
    print("OK: config parses, user_data_dir usable, playwright available.")
    return 0


def _write_markdown(path: Path, result) -> None:
    lines = [
        f"# Scrape summary",
        f"",
        f"- Target: `{result.meta.target_url}`",
        f"- Collected: `{result.meta.collected_at.isoformat()}`",
        f"- Posts: {result.meta.post_count}",
        f"- Passed rules: {len(result.passed_rules)}",
        f"- Ranked: {len(result.ranked)}",
        f"",
    ]
    if result.meta.warnings:
        lines.append("## Warnings")
        for w in result.meta.warnings:
            lines.append(f"- {w}")
        lines.append("")
    lines.append("## Top ranked")
    for r in result.ranked[:20]:
        lines.append(f"- **{r.score:.1f}** @{r.post.author_handle}: {r.post.text[:200]}…")
        if r.rationale:
            lines.append(f"  - {r.rationale}")
    path.write_text("\n".join(lines), encoding="utf-8")


def cmd_scrape(args: argparse.Namespace) -> int:
    s = Settings()
    user_data = Path(args.user_data_dir) if getattr(args, "user_data_dir", None) is not None else s.x_user_data_dir
    brief = ""
    if args.brief:
        brief = Path(args.brief).read_text(encoding="utf-8")
    opts = PipelineOptions(
        target_url=args.target,
        rules_path=Path(args.config),
        user_data_dir=user_data,
        max_posts=args.max_posts,
        max_scroll_iterations=args.max_scrolls,
        headless=not args.headed,
        use_llm=not args.no_llm,
        brief_text=brief,
        openai_api_key=s.openai_api_key,
        openai_base_url=s.openai_base_url,
        llm_model=s.llm_model,
    )
    result = run_pipeline(opts)
    out = json_path_with_time(Path(args.output))
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(result.model_dump_json(indent=2), encoding="utf-8")
    if args.format == "md" or args.markdown:
        md_path = out.with_suffix(".md")
        _write_markdown(md_path, result)
    print(out)
    return 0


def _user_data_dir_help() -> str:
    d = default_user_data_dir()
    return (
        "Playwright persistent Chromium profile (login/session cookies live here). "
        f"If omitted, uses env X_USER_DATA_DIR when set, otherwise the default for this OS ({d})."
    )


def _add_user_data_dir_arg(subparser: argparse.ArgumentParser) -> None:
    """Each subcommand has its own parser; argparse does not inherit parent flags."""
    subparser.add_argument(
        "--user-data-dir",
        dest="user_data_dir",
        default=argparse.SUPPRESS,
        metavar="DIR",
        help=_user_data_dir_help(),
    )


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="xauto", description="X timeline scrape + filter + optional LLM rank")
    p.add_argument("-v", "--verbose", action="store_true")
    sub = p.add_subparsers(dest="command", required=True)

    d = sub.add_parser("doctor", help="verify config, paths, playwright")
    d.add_argument("--config", required=True, help="rules YAML path")
    _add_user_data_dir_arg(d)
    d.set_defaults(func=cmd_doctor)

    s = sub.add_parser("scrape", help="run scrape pipeline")
    s.add_argument("--target", required=True, help="e.g. https://x.com/home or profile URL")
    s.add_argument("--config", required=True, help="rules YAML path")
    _add_user_data_dir_arg(s)
    s.add_argument("--max-posts", type=int, default=50)
    s.add_argument("--max-scrolls", type=int, default=25)
    s.add_argument("--output", default="output/output.json")
    s.add_argument("--brief", default="", help="project brief text file for LLM")
    s.add_argument("--no-llm", action="store_true")
    s.add_argument("--headed", action="store_true", help="show browser (for login / debugging)")
    s.add_argument("--format", choices=["json", "md"], default="json")
    s.add_argument("--markdown", action="store_true", help="also write summary .md next to json")
    s.set_defaults(func=cmd_scrape)
    
    llm = sub.add_parser("llm", help="LLM trend analysis on timeline JSON")
    llm.add_argument(
        "--posts",
        default=None,
        metavar="PATH",
        help="timeline JSON (omit → bundled sample next to xautomation package: output_16-46-50.json)",
    )
    llm.set_defaults(func=run_llm)

    return p


def main(argv: list[str] | None = None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    parser = build_parser()
    args = parser.parse_args(argv)
    _configure_logging(args.verbose)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
