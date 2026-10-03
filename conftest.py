import base64
import re
from pathlib import Path

import pytest
from selenium import webdriver
from selenium.common.exceptions import WebDriverException

from pages.login_page import LoginPage

SCREENSHOT_DIR = Path(__file__).parent / "screenshots"


def pytest_addoption(parser):
    parser.addoption("--headed", action="store_true", help="run the browser with a visible window")


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    # Runs after each test phase. When the test body fails, screenshot the browser
    # while it is still open, save it to screenshots/ and embed it in the HTML report
    outcome = yield
    report = outcome.get_result()
    drv = item.funcargs.get("driver")
    if report.when != "call" or not report.failed or drv is None:
        return

    try:
        png = drv.get_screenshot_as_png()
    except WebDriverException:
        return  # e.g. a JavaScript alert is open and blocks screenshots
    SCREENSHOT_DIR.mkdir(exist_ok=True)
    name = re.sub(r"[^\w.-]+", "_", item.nodeid)
    (SCREENSHOT_DIR / f"{name}.png").write_bytes(png)

    pytest_html = item.config.pluginmanager.getplugin("html")
    if pytest_html is not None:
        extras = getattr(report, "extras", [])
        extras.append(pytest_html.extras.png(base64.b64encode(png).decode()))
        report.extras = extras


@pytest.fixture
def driver(request):
    options = webdriver.ChromeOptions()
    if not request.config.getoption("--headed"):
        options.add_argument("--headless=new")
    options.add_argument("--window-size=1280,900")
    # Chrome flags "secret_sauce" as a breached password and pops up a dialog that
    # steals keyboard focus, so later send_keys calls silently go nowhere
    options.add_experimental_option("prefs", {
        "credentials_enable_service": False,
        "profile.password_manager_enabled": False,
        "profile.password_manager_leak_detection": False,
    })
    # Selenium Manager (built into selenium 4.6+) fetches a matching chromedriver
    drv = webdriver.Chrome(options=options)
    yield drv
    drv.quit()


@pytest.fixture
def login_as(driver):
    """Returns a function that logs in as any user and returns the inventory page."""
    from pages.inventory_page import InventoryPage

    def _login(username):
        LoginPage(driver).open().login(username, "secret_sauce")
        return InventoryPage(driver)

    return _login


@pytest.fixture
def inventory_page(login_as):
    """A browser already logged in as standard_user and sitting on the inventory page."""
    return login_as("standard_user")
