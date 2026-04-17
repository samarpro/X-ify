# X scrape hook

Purpose: reusable notes for scraping the live X home timeline through OpenClaw's browser profile `user`.

## What it captures
- visible posts on the current timeline
- author display name
- handle
- age/timestamp text
- post body text
- engagement labels when present

## Workflow
1. Ensure ChromeMCP is attached:
   - `openclaw browser --browser-profile user status`
2. Focus the X tab if needed:
   - `openclaw browser --browser-profile user tabs`
   - `openclaw browser --browser-profile user focus <id>`
3. Capture page structure:
   - `openclaw browser --browser-profile user snapshot --format ai --limit 400`
4. Parse the snapshot output or use the helper script in `Projects/Xautomation/scripts/x_scrape.py`.

## Notes
- This relies on the current accessible snapshot structure of X and may need updates if X changes its DOM/accessibility tree.
- Prefer read-only scraping. Do not like, repost, follow, or post unless explicitly asked.
