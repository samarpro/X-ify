# xAutomation overview

The app loads an X timeline in a persistent Chromium profile (default path is OS-specific under your home directory, like Chrome’s “Application Support” layout; override with `--user-data-dir` or `X_USER_DATA_DIR`), normalizes visible tweets, applies YAML rules (keywords, hashtags, URLs, age, regex), then optionally calls an OpenAI-compatible chat API to score and explain what remains. The same pipeline runs from the `xauto` CLI and from `POST /scrape` on the local FastAPI app.

For Google blocking sign-in on X, see [google-x-signin.md](google-x-signin.md).
