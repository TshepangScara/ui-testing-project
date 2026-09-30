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

# watch the browser while it runs
pytest --headed

# run one file, or one test
pytest tests/test_login.py
pytest tests/test_cart.py::test_full_checkout_flow

# run tests whose name contains a word
pytest -k checkout
```

Requirements: Python 3.10+ and Google Chrome. You do not need to install chromedriver; Selenium downloads a matching one automatically.

## Project layout

```
ui-testing-project/
├── conftest.py            # shared fixtures and hooks (browser, login, screenshots)
├── pytest.ini             # pytest settings
├── requirements.txt       # dependencies
├── pages/                 # page objects: how to talk to each page
│   ├── login_page.py
│   ├── inventory_page.py
│   └── cart_page.py       # also handles the checkout steps
├── tests/                 # the tests: what we expect to happen
│   ├── test_login.py
│   ├── test_inventory.py
│   └── test_cart.py
├── screenshots/           # created on failure, git-ignored
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
- **`inventory_page`**: builds on `driver`, logs in as `standard_user`, and returns an `InventoryPage`. Tests that need a logged-in user just ask for it:

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

pytest reports each row as its own test, so you see exactly which case failed.

### 6. Screenshots on failure

When a test fails you usually want to see what the browser was showing. [conftest.py](conftest.py) does this in two steps:

1. A hook, `pytest_runtest_makereport`, runs after each test phase and stores the result on the test (`item.rep_call`).
2. The `driver` fixture's teardown checks `rep_call.failed` and, if so, saves a PNG into `screenshots/` named after the test.

The hook is needed because a fixture cannot otherwise tell whether its test passed.

### 7. Continuous integration

[.github/workflows/tests.yml](.github/workflows/tests.yml) tells GitHub to run the suite automatically on every push to `master` and on every pull request: check out the code, install Python and the dependencies, run `pytest`. If tests fail, the `screenshots/` folder is attached to the run as a downloadable artifact. GitHub's Ubuntu runners include Chrome, so nothing extra is needed. Headless mode (the default here) is what makes this work on a machine with no display.

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

## Ideas for next steps

- Test the other saucedemo users (`problem_user`, `performance_glitch_user`) to see how the suite handles a misbehaving site.
- Add a `logout` test and a check that inventory pages redirect to login when logged out.
- Run tests in parallel with `pytest-xdist` (`pytest -n 4`) to cut the run time.
- Generate an HTML report with `pytest-html`.
