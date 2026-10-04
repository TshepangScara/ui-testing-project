import pytest

from pages.login_page import LoginPage


def test_valid_login_shows_inventory(driver):
    page = LoginPage(driver).open()
    page.login("standard_user", "secret_sauce")
    assert "inventory" in driver.current_url
    assert page.inventory_visible()


def test_locked_out_user_is_rejected(driver):
    page = LoginPage(driver).open()
    page.login("locked_out_user", "secret_sauce")
    assert "locked out" in page.error_text().lower()


def test_logout_returns_to_login_page(inventory_page):
    login_page = inventory_page.logout()
    assert "inventory" not in login_page.driver.current_url
    assert login_page.login_form_visible()


@pytest.mark.parametrize(
    "username, password, expected",
    [
        ("standard_user", "wrong_password", "do not match"),
        ("", "secret_sauce", "Username is required"),
        ("standard_user", "", "Password is required"),
    ],
)
def test_invalid_login_shows_error(driver, username, password, expected):
    page = LoginPage(driver).open()
    page.login(username, password)
    assert expected in page.error_text()
