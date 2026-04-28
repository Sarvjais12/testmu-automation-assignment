import os
import json
import urllib.parse
import random
import pytest
from playwright.sync_api import sync_playwright, Page


def _get_random_user_agent():
    agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
    ]
    return random.choice(agents)

def _get_stealth_scripts():
    return """
    Object.defineProperty(navigator, 'webdriver', {
        get: () => undefined,
        configurable: true
    });
    Object.defineProperty(navigator, 'plugins', {
        get: () => [1, 2, 3, 4, 5]
    });
    Object.defineProperty(navigator, 'languages', {
        get: () => ['en-US', 'en']
    });
    const origQuery = window.navigator.permissions.query;
    window.navigator.permissions.query = (p) => 
        p.name === 'notifications' 
            ? Promise.resolve({state: Notification.permission}) 
            : origQuery(p);
    """

@pytest.fixture(scope="function")
def browser():
    lt_username = os.getenv("LT_USERNAME")
    lt_access_key = os.getenv("LT_ACCESS_KEY")

    with sync_playwright() as p:
        if lt_username and lt_access_key:
            capabilities = {
                "browserName": "Chrome",
                "browserVersion": "latest",
                "LT:Options": {
                    "platform": "Windows 11",
                    "build": "TestMu AI Assignment",
                    "name": "Amazon Cart Tests",
                    "user": lt_username,
                    "accessKey": lt_access_key,
                    "network": True,
                    "video": True,
                    "console": True,
                    "resolution": "1920x1080",
                },
            }
            cdp_url = (
                f"wss://cdp.lambdatest.com/playwright?"
                f"capabilities={urllib.parse.quote(json.dumps(capabilities))}"
            )
            print("\n[INFO] Connecting to LambdaTest Cloud...")
            browser = p.chromium.connect(cdp_url)
            yield browser
            browser.close()
        else:
            print("\n[INFO] Running tests locally...")
            browser = p.chromium.launch(
                headless=False,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--disable-dev-shm-usage",
                    "--no-sandbox",
                ],
            )
            yield browser
            browser.close()

@pytest.fixture(scope="function")
def page(browser) -> Page:
    context = browser.new_context(
        viewport={"width": 1920, "height": 1080},
        user_agent=_get_random_user_agent(),
        locale="en-US",
        timezone_id="Asia/Kolkata",
    )
    context.add_init_script(_get_stealth_scripts())
    page = context.new_page()
    
    # Apply the heavy-duty stealth cloak
    yield page
    context.close()