# UI Testing Learning Guide

This guide explains how the project works and gives you the patterns to reuse in future Selenium + pytest projects.

## 1. What this project is doing

The app under test is SauceDemo, a small e-commerce website used for practice automation.

The project follows a clean structure:

- `pages/` contains page objects
- `tests/` contains test scenarios
- `conftest.py` contains shared browser setup
- `pytest.ini` controls the test runner

The general pattern is:

1. open the browser
2. login to the app
3. use a page object to interact with the page
4. assert on the result
5. close the browser

## 2. Why page objects matter

Page objects keep your test code simple and reusable.

Instead of writing selectors everywhere in the test, we hide that logic inside a page class.

Example:

```python
page = LoginPage(driver).open()
page.login("standard_user", "secret_sauce")
```

This is much easier to maintain than:

```python
driver.find_element(By.ID, "user-name").send_keys("standard_user")
```

When the UI changes, you usually only update one place: the page object class.

## 3. Selenium basics used here

### Locators

The project uses locator tuples like:

```python
USERNAME = (By.ID, "user-name")
ERROR = (By.CSS_SELECTOR, "[data-test='error']")
```

Common locator strategies:

- `By.ID` for unique ids
- `By.CSS_SELECTOR` for attribute and class selectors
- `By.CLASS_NAME` for simple class-based identification

### Waiting

A common Selenium mistake is using `time.sleep()`. This project uses `WebDriverWait` and `expected_conditions` instead.

```python
self.wait.until(EC.visibility_of_element_located(self.ERROR))
```

Why this matters:

- pages load asynchronously
- UI elements appear after time
- waits make tests stable and less flaky

## 4. Fixtures

Pytest fixtures are the reusable setup code in the project.

In `conftest.py`:

- `driver` creates a browser for each test
- `inventory_page` logs in and returns the ready inventory page
- failure screenshots are captured automatically

This gives every test an isolated browser session.

## 5. How the main flow works

### Login flow

The `LoginPage` handles:

- opening the URL
- entering username/password
- clicking login
- checking for error messages
- verifying inventory is visible

### Inventory flow

The `InventoryPage` handles:

- listing products
- adding/removing items
- sorting products
- opening the cart
- logging out

### Cart and checkout flow

The `CartPage` handles:

- viewing added items
- starting checkout
- entering customer details
- continuing to the next step
- placing the order
- reading confirmation text

This is a good example of how page objects model real user actions.

## 6. Important testing decisions in this project

### Good test style

Tests assert on user-facing outcomes such as:

- URL changes
- product count
- cart badge updates
- success and error messages

They do not overfit to implementation details.

### Good automation style

- use stable locators
- prefer waits over sleep
- keep test names descriptive
- use fixtures to reduce duplication
- keep selectors in page objects, not in tests

## 7. Common mistakes and how this project avoids them

### Mistake: no waits

Result: flaky tests that fail intermittently.

Fix: use `WebDriverWait` with meaningful conditions.

### Mistake: selector duplication

Result: hard-to-maintain tests.

Fix: keep selectors in page objects.

### Mistake: tests depending on each other

Result: order-dependent failures.

Fix: use fresh browser fixtures for each test.

### Mistake: directly testing browser internals

Result: brittle tests.

Fix: assert on page content and URLs.

## 8. How to build more tests

Logout, every missing checkout field, the checkout totals and the different users are already covered. Good next tests might be:

- opening the inventory page while logged out redirects to login
- the "Continue Shopping" button returns from the cart to the inventory
- sorting by price high to low

Use this pattern:

```python
def test_some_user_flow(inventory_page):
    inventory_page.add_first()
    cart = inventory_page.open_cart()
    assert cart.item_count() == 1
```

<!--
## 9. Practice tasks

Try these on your own:

1. Add a test for logout from the burger menu.
2. Add a test for removing an item from the cart page.
3. Add a test that checks product sorting by price.
4. Create a page object for a new page or form.
5. Re-run the suite and fix any failing waits.

## 10. Keep learning

The best next topics are:

- explicit waits vs implicit waits
- page object design patterns
- pytest fixtures and parametrization
- browser debugging and screenshots
- CI and GitHub Actions for automation

This project is a strong base for learning real UI automation.
-->
