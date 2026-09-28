import pytest
from selenium import webdriver


def pytest_addoption(parser):
    parser.addoption("--headed", action="store_true", help="run the browser with a visible window")


@pytest.fixture
def driver(request):
    options = webdriver.ChromeOptions()
    if not request.config.getoption("--headed"):
        options.add_argument("--headless=new")
    options.add_argument("--window-size=1280,900")
    # Selenium Manager (built into selenium 4.6+) fetches a matching chromedriver
    drv = webdriver.Chrome(options=options)
    yield drv
    drv.quit()
