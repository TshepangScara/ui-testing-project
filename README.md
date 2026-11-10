# Selenium + pytest UI Test Automation Framework

[![UI tests](https://github.com/TshepangScara/ui-testing-project/actions/workflows/tests.yml/badge.svg)](https://github.com/TshepangScara/ui-testing-project/actions/workflows/tests.yml)

End-to-end UI test automation for [saucedemo.com](https://www.saucedemo.com/), a demo e-commerce site. Built with **Python, Selenium WebDriver 4 and pytest**, structured as a Page Object Model and run in **GitHub Actions CI** on every push and pull request.

**38 test cases** cover login, inventory, cart and checkout. **8 known defects** across SauceDemo's deliberately broken user types are documented as strict `xfail` tests.

## Tech stack

| Area | Tools |
|---|---|
| Language | Python 3.13 |
| Browser automation | Selenium WebDriver 4 (Selenium Manager, headless Chrome) |
| Test runner | pytest, pytest-xdist (parallel runs), pytest-html (reports) |
| Design | Page Object Model, explicit waits, fixtures, parametrization |
| CI | GitHub Actions |

## Test coverage

| Area | What is tested |
|---|---|
| Login | Valid login, locked-out user, logout, invalid credentials and empty fields (parametrized) |
| Inventory | Product count, sort by price (low to high), sort by name (Z to A) |
| Cart | Cart badge updates, cart contents, removing items |
| Checkout | Full purchase flow, required-field validation (parametrized), order total maths |
| User types | Sorting, cart, checkout and pricing flows run as all 5 SauceDemo users |

## Defects found

SauceDemo ships users that are broken on purpose. The suite runs the same flows as every user and records each failure as a strict `xfail` with the reason:

| User | Defect |
|---|---|
| `problem_user` | Sorting does nothing |
| `problem_user` | Remove button does nothing |
| `problem_user` | Typing in Last Name overwrites First Name, so checkout can't continue |
| `problem_user` | Checkout can't get past the details step |
| `error_user` | Sorting raises a "Sorting is broken!" alert |
| `error_user` | Remove button does nothing |
| `error_user` | Last Name field crashes and Finish does nothing |
| `visual_user` | Inventory shows different prices than checkout charges |

`strict=True` means a fixed defect turns the build red, so stale markers can't hide a regression.

## Design decisions

- **Page Object Model.** Each page class holds its locators and exposes user actions (`login`, `add_first`, `open_cart`). Tests state intent; a locator change is fixed in one place.
- **One wait-aware base class.** Every page object inherits from `BasePage`, whose `click`, `type`, `text_of` and `is_visible` helpers wait with `WebDriverWait` and expected conditions. No `time.sleep()` anywhere.
- **Stable locators.** IDs and `data-test` attributes first, CSS selectors where needed, no positional chains.
- **Isolated tests.** The `driver` fixture gives every test a fresh browser, which is what makes parallel runs safe.
- **Factory fixture.** `login_as("problem_user")` returns a logged-in `InventoryPage` for any user, so the same test runs across user types.
- **Evidence on failure.** A `pytest_runtest_makereport` hook takes a screenshot when a test fails and embeds it in the self-contained HTML report.

## Continuous integration

[`.github/workflows/tests.yml`](.github/workflows/tests.yml) runs on every push to `master` and every pull request: it installs dependencies, runs the suite headless across 4 parallel workers (`pytest -n 4`), uploads the HTML report as a build artifact, and uploads failure screenshots when a run fails.

## Run it locally

Requirements: Python 3.10+ and Google Chrome. Selenium Manager downloads the matching driver automatically.

```powershell
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

pytest                 # full suite, headless
pytest -n auto         # parallel, one browser per CPU core
pytest --headed        # watch the browser
pytest -k checkout     # tests whose name contains "checkout"
```

Each run writes `report/report.html`, with a screenshot attached to every failure.

## Project structure

```
ui-testing-project/
├── conftest.py            # driver and login fixtures, screenshot-on-failure hook
├── pytest.ini             # pytest and report settings
├── requirements.txt       # pinned dependencies
├── pages/                 # page objects
│   ├── base_page.py       # shared wait-then-act helpers
│   ├── login_page.py
│   ├── inventory_page.py
│   └── cart_page.py       # cart and checkout steps
├── tests/
│   ├── test_login.py
│   ├── test_inventory.py
│   ├── test_cart.py
│   └── test_users.py      # same flows run as each SauceDemo user
└── .github/workflows/tests.yml
```

## Next steps

- Cross-browser runs by parametrizing the `driver` fixture for Firefox and Edge.
- A check that protected pages redirect to login when logged out.
