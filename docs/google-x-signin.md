# Google says the app is not safe / won’t let you sign in (X + Playwright)

Google **intentionally blocks** many sign-in flows inside **controlled or embedded browsers** (including Playwright’s **Chrome for Testing**, and sometimes the **“Sign in with Google”** button on other sites like X). Messages vary (“This browser or app may not be secure”, “Couldn’t sign you in”, etc.). This is **not a bug in xAutomation**; it is Google’s abuse protection.

## What usually works for X

1. **Do not use “Continue with Google”** on X inside the automation browser if Google blocks it.
2. Use **X username + password** (or **phone / email** if X offers that path) in a **headed** run (`xauto scrape … --headed`) so you can complete any captcha or 2FA once.
3. Keep using the **same dedicated profile** (`--user-data-dir` / `X_USER_DATA_DIR`) so the session cookie is reused on later headless runs.

If X only shows Google OAuth and no password option, you may need to attach a **normal** password to the account in X settings from a regular browser first, or use another login method X supports.

## Optional: installed Chrome

In `.env`, **`PLAYWRIGHT_CHANNEL=chrome`** launches **installed Google Chrome** instead of Chrome-for-Testing. Google is still strict, but this sometimes behaves better. **Quit** normal Chrome before scraping if you reuse paths.

## What we do not recommend

- Circumventing Google’s sign-in protections with “stealth” frameworks or credential stuffing — often violates **Google’s** and **X’s** terms and is fragile.

## Summary

For this project, the **reliable** path is: **X credentials that are not “Sign in with Google”** inside the Playwright profile, plus **headed** login once, then headless scrapes on the same profile.
