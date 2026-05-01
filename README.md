# xAutomation

Scrape an X (Twitter) timeline with Playwright (persistent browser profile), filter with YAML rules, optionally rank matches with an LLM, and expose the same pipeline via CLI or a small local API.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
playwright install chromium
cp .env.example .env
```

First run: use the default profile directory (or set `X_USER_DATA_DIR` in `.env`), run a **headed** scrape once, sign in to X in the browser, then reuse the same profile for headless runs.

Google blocking **Sign in with Google** on X (“app is not safe”, etc.): see **[docs/google-x-signin.md](docs/google-x-signin.md)**.

### Browser profile (`--user-data-dir`)

Playwright keeps a separate Chromium user profile (not your installed Google Chrome profile). If you omit `--user-data-dir`, the app uses `X_USER_DATA_DIR` from the environment when set, otherwise a **default path** in the same style as Chrome’s OS locations:

| OS | Default directory |
| --- | --- |
| macOS | `~/Library/Application Support/xautomation/ChromiumProfile` |
| Windows | `%LOCALAPPDATA%\xautomation\ChromiumProfile` |
| Linux | `~/.local/share/xautomation/chromium-profile` |

Override on the CLI with `--user-data-dir /path/to/dir` (takes precedence over `.env`).

## CLI

```bash
xauto doctor --config examples/rules.example.yaml
xauto doctor --config examples/rules.example.yaml --user-data-dir "$HOME/custom-x-profile"

xauto scrape \
  --target https://x.com/home \
  --config examples/rules.example.yaml \
  --user-data-dir "$HOME/Library/Application Support/xautomation/ChromiumProfile" \
  --max-posts 50 \
  --output output/scrape.json \
  --no-llm

xauto scrape --target https://x.com/home --config examples/rules.example.yaml \
  --user-data-dir "$HOME/Library/Application Support/xautomation/ChromiumProfile" \
  --headed --no-llm --output output/scrape.json

xauto scrape --target https://x.com/someuser --config examples/rules.example.yaml \
  --brief examples/project_brief.example.txt --no-llm
```

## Local API

```bash
python -m uvicorn xautomation.api.app:app --host 127.0.0.1 --port 8765
```

`POST /scrape` with JSON body matching `ScrapeRequest` (see `xautomation.api.schemas`).

## Legal

Automating X may violate their terms. Use a dedicated account and accept the risk.
