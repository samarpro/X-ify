# Standalone X Scrape

This scraper no longer depends on OpenClaw browser snapshot commands.

## One-shot CLI

```bash
python3 scripts/x_scrape.py \
  --user-data-dir "$HOME/Library/Application Support/Google/Chrome" \
  --profile-directory "Profile 1" \
  --target-posts 30 \
  --max-scrolls 16 \
  --output-file output/x_scrape.json
```

## Loopback service (local only)

```bash
python3 -m service.server --host 127.0.0.1 --port 8797
```

Health check:

```bash
curl http://127.0.0.1:8797/health
```

Scrape request:

```bash
curl -X POST http://127.0.0.1:8797/scrape \
  -H "Content-Type: application/json" \
  -d '{
    "user_data_dir": "/Users/samkanu/Library/Application Support/Google/Chrome",
    "profile_directory": "Profile 1",
    "target_posts": 30,
    "max_scrolls": 16,
    "output_file": "output/x_scrape.json",
    "headless": false
  }'
```

## Notes

- Service host is restricted to `127.0.0.1`.
- Scraper is read-only and does not perform actions such as like/repost/follow/post.
- Output contract remains compatible with `llm.py` (`output/x_scrape.json`).
