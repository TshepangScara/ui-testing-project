# UI Testing Project

Automated browser tests for [saucedemo.com](https://www.saucedemo.com/), a practice shop built for learning test automation. The tests use **Selenium** to drive a real Chrome browser and **pytest** to organise and run them.

## Learning guide

Start with [LEARNING_GUIDE.md](LEARNING_GUIDE.md) for the project walkthrough and the Selenium + pytest concepts used here.

## Quick start

```powershell
# one-time setup (from the project folder)
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

# run everything (headless, no window)
pytest

# run everything in parallel, one browser per CPU core (about 3x faster)
pytest -n auto

# watch the browser while it runs
pytest --headed

# run one file, or one test
pytest tests/test_login.py
pytest tests/test_cart.py::test_full_checkout_flow

# run tests whose name contains a word
pytest -k checkout
```

Every run writes an HTML report to `report/report.html` (git-ignored). Open it in a browser to see each test's result, with a screenshot attached to any failure.

Requirements: Python 3.10+ and Google Chrome. You do not need to install chromedriver; Selenium downloads a matching one automatically.

## Project layout

```
ui-testing-project/
├── conftest.py            # shared fixtures and hooks (browser, login, screenshots)
├── pytest.ini             # pytest settings
├── requirements.txt       # dependencies
├── pages/                 # page objects: how to talk to each page
│   ├── base_page.py       # shared wait-then-act helpers
│   ├── login_page.py
│   ├── inventory_page.py
│   └── cart_page.py       # also handles the checkout steps
├── tests/                 # the tests: what we expect to happen
│   ├── test_login.py
│   ├── test_inventory.py
│   ├── test_cart.py
│   └── test_users.py      # same flows run as each saucedemo user
├── screenshots/           # created on failure, git-ignored
├── report/                # HTML report from the last run, git-ignored
└── .github/workflows/tests.yml   # CI
```

The key idea is the split between **`pages/`** and **`tests/`**:

- A *page object* knows **how** to use a page: which elements exist and how to click them.
- A *test* says **what** should happen, and reads almost like plain English.

## The core concepts

### 1. Page Object Model

Compare a test written without and with a page object:

```python
# Without: the test is full of selector details
driver.find_element(By.ID, "user-name").send_keys("standard_user")
driver.find_element(By.ID, "password").send_keys("secret_sauce")
driver.find_element(By.ID, "login-button").click()

# With: the test states intent
LoginPage(driver).open().login("standard_user", "secret_sauce")
```

If the site changes the login button's id, you fix it in **one place** ([pages/login_page.py](pages/login_page.py)) instead of in every test. Each page class keeps its locators as class constants at the top (`USERNAME = (By.ID, "user-name")`) and exposes methods named after user actions (`login`, `add_first`, `open_cart`).

Methods that navigate to a new page return that page's object (`open_cart()` returns a `CartPage`), so tests chain naturally.

Every page object inherits from `BasePage` ([pages/base_page.py](pages/base_page.py)), whose helpers (`click`, `type`, `text_of`, `is_visible`) always wait for the element first. Page objects use those helpers instead of raw Selenium calls, so no page can forget to wait.

### 2. Locators

A locator is a `(strategy, value)` pair that tells Selenium how to find an element. This project uses:

| Strategy | Example | Use when |
|---|---|---|
| `By.ID` | `(By.ID, "login-button")` | the element has a unique id (most stable) |
| `By.CSS_SELECTOR` | `(By.CSS_SELECTOR, "[data-test='error']")` | you need attributes or class combinations |
| `By.CLASS_NAME` | `(By.CLASS_NAME, "inventory_list")` | a single, meaningful class |

Prefer ids and `data-test` attributes: they exist for testing and rarely change. Avoid long chains of positions (`div > div > div:nth-child(3)`), which break when the layout shifts.

The selector `button[data-test^='add-to-cart']` uses `^=`, meaning "attribute *starts with*", because each product's button has a different suffix (`add-to-cart-sauce-labs-backpack`).

### 3. Waiting

Web pages load asynchronously, so an element may not exist the instant you look for it. Never use `time.sleep()`. Use an **explicit wait**, which polls until a condition is true or a timeout (10s here) expires:

```python
self.wait.until(EC.visibility_of_element_located(self.ERROR))
```

It returns as soon as the condition holds, so tests are fast when the page is fast and still reliable when it is slow. Missing waits are the most common cause of "flaky" tests that pass sometimes and fail others.

`find_element` (singular) raises an error if nothing matches. `find_elements` (plural) returns a possibly-empty list, which is why `cart_count()` uses it: the cart badge disappears entirely when the cart is empty.

### 4. Fixtures

A pytest **fixture** is setup (and teardown) code that a test receives by naming it as a parameter. Everything before `yield` is setup; everything after is teardown, which runs even if the test fails.

- **`driver`**: starts Chrome, hands it to the test, then closes it. Each test gets a fresh browser, so tests cannot interfere with each other.
- **`login_as`**: builds on `driver` and returns a *function*: `login_as("problem_user")` logs in as that user and returns an `InventoryPage`. A fixture that returns a function is called a *factory fixture*; use one when the test needs to choose a setup value.
- **`inventory_page`**: shorthand for `login_as("standard_user")`. Tests that need a logged-in user just ask for it:

```python
def test_inventory_lists_six_products(inventory_page):
    assert inventory_page.item_count() == 6
```

Fixtures can depend on other fixtures (`inventory_page` uses `driver`), and pytest wires them together by name.

### 5. Parametrized tests

[tests/test_login.py](tests/test_login.py) runs one test function against several inputs:

```python
@pytest.mark.parametrize("username, password, expected", [
    ("standard_user", "wrong_password", "do not match"),
    ("", "secret_sauce", "Username is required"),
    ("standard_user", "", "Password is required"),
])
def test_invalid_login_shows_error(driver, username, password, expected): ...
```

pytest reports each row as its own test, so you see exactly which case failed. The checkout form uses the same idea: `test_checkout_requires_all_details` in [tests/test_cart.py](tests/test_cart.py) leaves each field blank in turn.

### 6. Known bugs and expected failures

saucedemo has users that are broken on purpose: `problem_user` can't sort or check out, `error_user` hits crashes, and `visual_user` shows wrong prices. [tests/test_users.py](tests/test_users.py) runs the same flows as every user and marks the known bugs with `xfail` ("expected to fail"):

```python
pytest.param("problem_user", marks=pytest.mark.xfail(reason="sorting does nothing", strict=True))
```

The suite stays green while the bugs exist, and the report still lists them as `xfailed` with the reason. `strict=True` means that if a bug is ever fixed, the test *unexpectedly passes* and turns red, reminding you to remove the marker. Without `strict`, a stale marker could hide a real regression later.

### 7. Screenshots and the HTML report

When a test fails you usually want to see what the browser was showing. [conftest.py](conftest.py) uses a hook, `pytest_runtest_makereport`, which pytest calls after each phase of each test. When the test body (the `call` phase) fails, the hook grabs the test's `driver`, takes a screenshot while the browser is still open, saves it to `screenshots/`, and embeds it in the HTML report.

The report itself comes from the `pytest-html` plugin, switched on in [pytest.ini](pytest.ini) with `--html=report/report.html --self-contained-html` (one file, images included, easy to share).

### 8. Continuous integration

[.github/workflows/tests.yml](.github/workflows/tests.yml) tells GitHub to run the suite automatically on every push to `master` and on every pull request: check out the code, install Python and the dependencies, run `pytest`. It runs four browsers at once (`pytest -n 4`, from the `pytest-xdist` plugin), which is safe because every test gets its own browser and shares nothing. Every run attaches the HTML report as a downloadable artifact, and failed runs also attach the `screenshots/` folder. GitHub's Ubuntu runners include Chrome, so nothing extra is needed. Headless mode (the default here) is what makes this work on a machine with no display.

## Writing a new test

1. **Is there a page object for the page?** If not, add a class in `pages/` with locators and action methods.
2. **Add a test** in `tests/` named `test_<something>.py`, with functions named `test_<behaviour>`.
3. **Ask for the fixture you need:** `driver` for a blank browser, `inventory_page` for a logged-in one.
4. **Assert on outcomes the user would notice** (text on screen, URL, item count), not on implementation details.

Example:

```python
def test_removing_item_updates_cart_badge(inventory_page):
    inventory_page.add_first(2)
    inventory_page.remove_first()
    assert inventory_page.cart_count() == 1
```

## Troubleshooting

| Symptom | Likely cause |
|---|---|
| `TimeoutException` | The element never appeared: check the locator, or that the earlier step really happened. The failure screenshot shows what the page looked like. |
| `NoSuchElementException` | The locator matches nothing, or you looked before the page finished loading (use a wait). |
| `ElementClickInterceptedException` | Something (a popup, overlay) covers the element. |
| Test passes alone but fails in the full run | Tests are sharing state. Each test should set up everything it needs. |
| First run is slow | Selenium is downloading chromedriver. Later runs reuse it. |
| Typing silently does nothing after login | Chrome's password-leak warning is stealing focus. [conftest.py](conftest.py) disables it; keep those `prefs` if you copy the setup elsewhere. |

## Ideas for next steps

- Add a check that inventory pages redirect to login when logged out.
- Run the suite in Firefox as well as Chrome by parametrizing the `driver` fixture.
