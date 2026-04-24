# X scrape hook

Purpose: reusable notes for scraping the live X home timeline through standalone Playwright.

## What it captures
- visible posts on the current timeline
- author display name
- handle
- age/timestamp text
- post body text
- engagement labels when present

## Workflow
1. Run one-shot scraper:
   - `python3 scripts/x_scrape.py --user-data-dir "$HOME/Library/Application Support/Google/Chrome" --profile-directory "Profile 1" --output-file output/x_scrape.json`
2. Optional: run loopback service:
   - `python3 -m service.server --host 127.0.0.1 --port 8797`
3. Trigger scrape over HTTP:
   - `POST http://127.0.0.1:8797/scrape`

## Notes
- This relies on current X timeline structure and may need extractor updates if X changes DOM/ARIA behavior.
- Prefer read-only scraping. Do not like, repost, follow, or post unless explicitly asked.
- Output remains `output/x_scrape.json` for compatibility with `llm.py`.
