# Standalone Playwright X Scraper Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace OpenClaw-coupled scraping with a standalone Playwright scraper that supports profile selection and optional loopback-only service mode.

**Architecture:** Introduce a shared scraper core (`src/scraper`) that opens persistent browser profiles via Playwright, extracts timeline posts with robust selectors/semantics, and emits the same JSON schema. Wrap the core with a CLI entrypoint and a local HTTP service bound to `127.0.0.1` only.

**Tech Stack:** Python 3.13, Playwright (sync API), argparse, FastAPI/uvicorn (or stdlib `http.server`), pytest.

---

### Task 1: Create standalone scraper core boundaries

**Files:**
- Create: `src/scraper/models.py`
- Create: `src/scraper/normalize.py`
- Create: `src/scraper/x_timeline.py`
- Modify: `scripts/x_scrape.py`
- Test: `tests/scraper/test_normalize.py`

- [ ] **Step 1: Define typed models**
Create dataclasses:
- `ScrapeConfig(target_posts, max_scrolls, user_data_dir, profile_directory, output_file, headless)`
- `Post(display_name, handle, age, body, summary)`
- `ScrapeResult(profile, tab_id, post_count, target_posts, output_file, posts)`

- [ ] **Step 2: Port normalization helpers**
Move helpers from `scripts/x_scrape.py` into `src/scraper/normalize.py`:
- `normalize_whitespace`
- `strip_counts_and_media`
- `is_noise_line`
- `clean_body_text`
- `dedupe_key`

- [ ] **Step 3: Add failing normalization tests**
Write tests using representative strings from current output samples to lock behavior.

- [ ] **Step 4: Implement minimal normalization to pass tests**
Keep behavior parity first; no additional cleanup rules beyond current logic.

- [ ] **Step 5: Run tests**
Run: `pytest tests/scraper/test_normalize.py -v`
Expected: PASS.


### Task 2: Implement Playwright timeline scraper

**Files:**
- Modify: `src/scraper/x_timeline.py`
- Test: `tests/scraper/test_extract_posts.py`

- [ ] **Step 1: Add failing extraction tests (fixture-based)**
Create static HTML fixtures that mimic X timeline cards and assert extracted fields.

- [ ] **Step 2: Implement browser bootstrap with profile selection**
Use Playwright persistent context:
- required `user_data_dir`
- optional Chromium arg `--profile-directory=<name>`
- open `https://x.com/home`

- [ ] **Step 3: Implement post extraction from visible `article` cards**
Extract `display_name`, `handle`, `age`, `body`, and `summary` fallback.

- [ ] **Step 4: Implement scroll+collect loop**
Collect until `target_posts` or `max_scrolls`; dedupe with `dedupe_key`.

- [ ] **Step 5: Run tests**
Run: `pytest tests/scraper/test_extract_posts.py -v`
Expected: PASS.


### Task 3: Add one-shot CLI mode (default)

**Files:**
- Create: `src/cli/x_scrape_cli.py`
- Modify: `scripts/x_scrape.py`
- Test: `tests/cli/test_x_scrape_cli_args.py`

- [ ] **Step 1: Add CLI args**
Support:
- `--target-posts` (default `30`)
- `--max-scrolls` (default `16`)
- `--user-data-dir`
- `--profile-directory`
- `--output-file` (default `output/x_scrape.json`)
- `--headless`

- [ ] **Step 2: Wire wrapper script**
Make `scripts/x_scrape.py` delegate to CLI module for backwards compatibility.

- [ ] **Step 3: Preserve output JSON contract**
Emit top-level keys exactly:
- `profile`, `tab_id`, `post_count`, `target_posts`, `output_file`, `posts`

- [ ] **Step 4: Set standalone `tab_id` semantics**
Set `tab_id` to `null`/`None` in standalone output.

- [ ] **Step 5: Run CLI tests**
Run: `pytest tests/cli/test_x_scrape_cli_args.py -v`
Expected: PASS.


### Task 4: Add loopback-only service mode

**Files:**
- Create: `src/service/app.py`
- Create: `src/service/server.py`
- Test: `tests/service/test_loopback_binding.py`
- Test: `tests/service/test_scrape_endpoint_contract.py`

- [ ] **Step 1: Add failing API contract tests**
Test `POST /scrape` request/response schema and `GET /health`.

- [ ] **Step 2: Implement service endpoints**
`POST /scrape` accepts runtime args and returns scrape JSON.

- [ ] **Step 3: Enforce loopback-only binding**
Bind server to `127.0.0.1` by default and validate host config to avoid `0.0.0.0`.

- [ ] **Step 4: Add timeout and safe defaults**
Set request timeout and keep read-only scraping behavior.

- [ ] **Step 5: Run service tests**
Run: `pytest tests/service -v`
Expected: PASS.


### Task 5: Integrate with existing consumer and docs

**Files:**
- Modify: `llm.py` (only if needed for path handling)
- Modify: `hooks/x-scrape.md`
- Create: `docs/x-scrape-standalone.md`
- Test: `tests/integration/test_output_contract.py`

- [ ] **Step 1: Lock output contract test**
Assert JSON shape used by `llm.py` remains valid.

- [ ] **Step 2: Ensure output path compatibility**
Default to repo-local `output/x_scrape.json` so `llm.py` works unchanged where possible.

- [ ] **Step 3: Rewrite hook docs**
Replace OpenClaw command workflow with Playwright CLI/service usage.

- [ ] **Step 4: Add standalone usage docs**
Document profile selection, one-shot mode, service mode, and loopback-only guarantee.

- [ ] **Step 5: Run integration test**
Run: `pytest tests/integration/test_output_contract.py -v`
Expected: PASS.


### Task 6: Dependency, smoke checks, and cleanup

**Files:**
- Modify: dependency manifest (`requirements.txt` or `pyproject.toml`)
- Modify: `.gitignore` (if needed for Playwright artifacts)

- [ ] **Step 1: Add dependencies**
Install/configure `playwright` and service deps (if FastAPI path chosen).

- [ ] **Step 2: Install browser runtime**
Run: `python -m playwright install chromium`
Expected: Chromium installed.

- [ ] **Step 3: Run full test suite**
Run: `pytest -v`
Expected: PASS.

- [ ] **Step 4: Run one local smoke scrape**
Run CLI in headful mode with real profile and verify output file is produced.

- [ ] **Step 5: Verify decoupling complete**
Search codebase for runtime `openclaw browser` usage in scraper path; expected none.


## Non-functional requirements

- Read-only behavior only (no likes/reposts/follows/posts).
- Loopback-only network exposure for service mode.
- Stable output schema for downstream consumers.
- Avoid hardcoded OpenClaw workspace paths.


## Risks and mitigations

- X DOM changes can break selectors.
  - Mitigation: use role/text-based fallbacks, keep fixture tests, keep extractor isolated.
- Local profile mismatch can fail session reuse.
  - Mitigation: explicit `--user-data-dir` and `--profile-directory` flags with validation.
- Large timeline noise can reduce extraction quality.
  - Mitigation: preserve/expand noise filters with regression tests.


## Commit cadence (frequent commits)

- Commit after each task with focused messages:
  - `feat(scraper): add normalization core and tests`
  - `feat(scraper): add playwright timeline extraction`
  - `feat(cli): add standalone scrape command`
  - `feat(service): add loopback-only scrape API`
  - `docs(scrape): migrate hook docs to playwright flow`
