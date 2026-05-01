from playwright.sync_api import Page, sync_playwright
import time


def run_trial(page: Page):
    page.goto("https://www.playwright.dev/")
    time.sleep(120)


with sync_playwright() as p:
    user_data_dir = "./automation-chrome"  # Replace with your desired path
    browser = p.chromium.launch_persistent_context(
        user_data_dir=user_data_dir,
        headless=False,
        channel="chrome",
        ignore_default_args=["--enable-automation","--no-sandbox"],
        args=["--disable-blink-features=AutomationControlled"],
    )
    browser.add_init_script(
        "Object.defineProperty(navigator, 'webdriver', {get: () => undefined});"
    )
    page = browser.new_page()
    try:
        run_trial(page)
    finally:
        browser.close()
