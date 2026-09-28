import re
from pathlib import Path

import pytest
from selenium import webdriver

from pages.login_page import LoginPage

SCREENSHOT_DIR = Path(__file__).parent / "screenshots"


def pytest_addoption(parser):
    parser.addoption("--headed", action="store_true", help="run the browser with a visible window")


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    # Attach each phase's report to the test item so fixtures can see if the test failed
    outcome = yield
    report = outcome.get_result()
    setattr(item, f"rep_{report.when}", report)


@pytest.fixture
def driver(request):
    options = webdriver.ChromeOptions()
    if not request.config.getoption("--headed"):
        options.add_argument("--headless=new")
    options.add_argument("--window-size=1280,900")
    # Selenium Manager (built into selenium 4.6+) fetches a matching chromedriver
    drv = webdriver.Chrome(options=options)
    yield drv

    # Teardown runs after the test, so rep_call is set by now
    report = getattr(request.node, "rep_call", None)
    if report is not None and report.failed:
        SCREENSHOT_DIR.mkdir(exist_ok=True)
        name = re.sub(r"[^\w.-]+", "_", request.node.nodeid)
        drv.save_screenshot(str(SCREENSHOT_DIR / f"{name}.png"))
    drv.quit()


@pytest.fixture
def inventory_page(driver):
    """A browser already logged in as standard_user and sitting on the inventory page."""
    from pages.inventory_page import InventoryPage

    LoginPage(driver).open().login("standard_user", "secret_sauce")
    return InventoryPage(driver)
