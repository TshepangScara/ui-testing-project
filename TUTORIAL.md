# What we just did, and why

This walks through the session in order — not as a reference (that's [README.md](README.md)), but as a lesson: each step, what problem it solved, and the concept behind it.

## Step 0: Check before building

Before writing anything, we checked three things:

```powershell
venv\Scripts\python.exe --version
venv\Scripts\python.exe -m pip list   # confirm selenium and pytest are actually installed
```

...and whether Chrome was installed. This matters because `requirements.txt` listing a package doesn't mean it's *installed* — someone has to have run `pip install -r requirements.txt` into the venv. And Selenium doesn't test anything on its own; it drives a real browser, so one has to exist on the machine. Checking first avoids writing code against tools that turn out not to be there.

**Lesson:** verify your environment before writing code that depends on it. A missing dependency shows up as a confusing runtime error otherwise, far from its real cause.

## Step 1: The smallest possible test (login)

We didn't start with the whole site. We started with one page — login — because it's the front door: every other test needs a logged-in session, so getting login right first pays off immediately.

Three files went in together:

- **`conftest.py`** — a `driver` fixture: opens Chrome, hands it to the test, closes it afterward.
- **`pages/login_page.py`** — a class wrapping the login page's HTML.
- **`tests/test_login.py`** — the actual assertions.

Why a *class* for the page, instead of just writing Selenium calls straight into the test? Because a test should read like a spec of *behaviour*:

```python
page.login("standard_user", "secret_sauce")
assert page.inventory_visible()
```

not like a transcript of clicks:

```python
driver.find_element(By.ID, "user-name").send_keys("standard_user")
driver.find_element(By.ID, "password").send_keys("secret_sauce")
driver.find_element(By.ID, "login-button").click()
```

Both do the same thing, but only the first survives the login page's HTML being redesigned. This split — page objects hold "how", tests hold "what" — is the **Page Object Model**, and it's the single most load-bearing idea in this whole project.

We also used **explicit waits** (`WebDriverWait(...).until(...)`) instead of guessing a sleep time, because the page needs a moment to render the error message, and a fixed `time.sleep(2)` is either wastefully slow or, on a slow day, still too short.

We ran it: 5/5 passed. Then — and only then — we committed. **Lesson:** commit working code, not code you assume works.

## Step 2: Build outward from what works (inventory & cart)

With login proven, the next step was the shopping flow. Two new page objects (`InventoryPage`, `CartPage`) and their tests, following the exact same pattern as step 1 — same locator style, same wait style, same "methods named after actions" style. Nothing new conceptually; more surface area covered.

One thing worth noticing: `InventoryPage.open_cart()` returns a `CartPage`:

```python
def open_cart(self):
    self.driver.find_element(*self.CART_LINK).click()
    return CartPage(self.driver)
```

This lets tests **chain** across pages the way a user actually moves through the site:

```python
cart = inventory_page.open_cart()
cart.start_checkout()
```

We also added a fixture that *builds on* the first one:

```python
@pytest.fixture
def inventory_page(driver):
    LoginPage(driver).open().login("standard_user", "secret_sauce")
    return InventoryPage(driver)
```

`inventory_page` asks for `driver` as an argument, so pytest supplies a fresh browser, logs it in, and *then* hands the ready-to-use page to the test. Every cart/inventory test just asks for `inventory_page` and skips writing the login step nine separate times. **Lesson:** fixtures compose — build small ones, then bigger ones out of them, instead of repeating setup in every test.

## Step 3: Make failures show themselves (screenshots)

A test failing with `TimeoutException: element not found` doesn't tell you *what the page actually looked like*. So we added: on failure, save a screenshot.

The tricky part is that a fixture's teardown code (the part after `yield`) doesn't automatically know whether the test it served passed or failed — pytest doesn't hand that to fixtures by default. The fix is a **hook**, a function pytest calls at fixed moments:

```python
@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()
    drv = item.funcargs.get("driver")
    if report.when != "call" or not report.failed or drv is None:
        return
    png = drv.get_screenshot_as_png()
    ...  # save to screenshots/ and embed in the HTML report
```

This runs after every test phase. When the test body (`call`) has failed, it borrows the test's own browser (`item.funcargs["driver"]`) while it is still open and takes the screenshot. (An earlier version saved the result on the test and let the `driver` fixture take the screenshot during teardown; doing it in the hook means it can also attach the image to the HTML report.) We verified it actually worked by writing a throwaway test that does `assert False`, running it, confirming a PNG landed in `screenshots/`, then deleting that throwaway test — we didn't just trust the code compiled.

**Lesson:** when you can't observe something directly (does teardown know about a failure?), find the mechanism that exposes it (a hook), and *test the test infrastructure itself* before trusting it.

## Step 4: Let a machine run it on every push (CI)

The workflow file tells GitHub: on every push or pull request, spin up a Linux machine, install Python and the dependencies, run `pytest`. If it fails, attach the screenshots folder so you can see the failure without reproducing it locally.

This is the payoff of everything before it: because we never used a fixed sleep, always waited explicitly, and ran headless by default, the exact same test suite runs unmodified on a headless Ubuntu machine we've never touched. If the tests had depended on a visible window or a hardcoded pause, this step would have needed rework.

**Lesson:** decisions made early (headless-by-default, explicit waits) determine whether "just run it in CI" is trivial or painful later.

## Step 5: Debug a failure you can't see (the Chrome popup)

Later, two tests started failing: checkout couldn't continue, and logout did nothing. The failure screenshot showed the checkout form with only "Test" in First Name; Last Name and Postal Code were empty, as if the typing had vanished.

Rather than adding sleeps and hoping, we narrowed it down one fact at a time:

1. **Is the field focused?** Yes, `document.activeElement` was the input.
2. **Does the page receive key events?** We attached JavaScript listeners for `keydown`, `input`, and so on. Only `focus` fired; not a single key event arrived, even at the `window` level.
3. **Is the site's code blocking input?** We read the site's JavaScript for the form. It was ordinary React, nothing special for `standard_user`.

So the keystrokes weren't reaching the page at all, and only after login. That pointed at the browser itself: Chrome recognises `secret_sauce` as a password from a data breach and opens a "Change your password" dialog after login. In headless mode you never see it, but it owns the keyboard. Disabling the password manager in the `driver` fixture's Chrome options fixed both tests.

**Lesson:** when a test fails strangely, collect evidence (screenshots, event logs, the page's own code) until the cause is a fact, not a guess. A `time.sleep()` here would have hidden nothing and fixed nothing.

## Step 6: Grow coverage with parametrize, and handle known bugs

With the suite stable, we widened it without writing many new functions:

- One checkout test, parametrized, now leaves each required field blank in turn.
- A **factory fixture**, `login_as`, returns a function, so a test can log in as whichever user it needs. `inventory_page` became a one-line wrapper around it.
- [tests/test_users.py](tests/test_users.py) runs four flows as all five saucedemo users: 20 tests from 4 functions.

Some users are broken on purpose, so 8 of those tests fail. Deleting them would throw away useful checks; leaving them red would make the suite useless (people stop looking at a build that is always red). Instead each known bug is marked `xfail(strict=True)` with a reason. The build stays green, the report lists every known bug, and if a bug is ever fixed the test passes unexpectedly and goes red, so the marker can't go stale.

Finally, `pytest-html` produces a report with failure screenshots embedded, and `pytest-xdist` (`pytest -n auto`) runs several browsers at once, cutting the run from about 6 minutes to 2. Parallel running only works because every test has always had its own browser and shared nothing; that decision from step 1 paid off again.

**Lesson:** a suite should tell the truth. Green has to mean "nothing unexpected", which is why known bugs are recorded, not deleted or ignored.

## The shape of the whole thing

```
environment check
      │
      ▼
login (proves the pattern) ──► inventory/cart (repeats the pattern)
      │                              │
      └──────────────┬───────────────┘
                      ▼
         screenshot on failure (see what broke)
                      │
                      ▼
              CI (run it automatically)
                      │
                      ▼
       debug from evidence (the Chrome popup)
                      │
                      ▼
   wider coverage: parametrize, users, known bugs
                      │
                      ▼
       HTML report + parallel runs
```

Each step only added *one* new idea on top of a pattern that already worked: page objects → fixtures composing → hooks → automation → evidence-based debugging → parametrized coverage. That's generally how to grow a test suite — get one thing solid, then repeat its shape rather than inventing a new one each time.

## Try it yourself

The fastest way to make this stick: break something on purpose and watch the pieces react.

1. In `pages/login_page.py`, change `USERNAME = (By.ID, "user-name")` to `(By.ID, "wrong-id")`. Run `pytest tests/test_login.py`. Read the error — it should be a `NoSuchElementException`, and it should point at the page object, not the test.
2. Undo that, then in `pages/inventory_page.py` temporarily make `add_first` not re-query elements (loop over a list captured once) and add two items — see whether it still works, and think about why re-querying mattered.
3. In [tests/test_users.py](tests/test_users.py), delete the `"problem_user"` line from one test's known bugs and run that file. Watch the test fail for real, then put the line back and watch it become `xfailed`.
4. Write one new test yourself: `problem_user` shows the same broken image for every product. Use `login_as("problem_user")` and assert that the product images are all different (you'll need a small new method on `InventoryPage`). Mark it as a known bug, the same way the other user tests do.
