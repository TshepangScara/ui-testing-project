"""Run the same flows as each SauceDemo user.

Some users are deliberately broken. Their failures are marked xfail ("expected
to fail") with strict=True, so the suite stays green while the bugs exist, and
turns red if one of them is ever fixed, telling us to remove the marker.
"""
import pytest

USERS = ["standard_user", "problem_user", "performance_glitch_user", "error_user", "visual_user"]


def users(known_bugs):
    """All USERS, with each user listed in known_bugs marked as an expected failure."""
    return [
        pytest.param(u, marks=pytest.mark.xfail(reason=known_bugs[u], strict=True)) if u in known_bugs else u
        for u in USERS
    ]


@pytest.mark.parametrize("username", users({
    "problem_user": "sorting does nothing",
    "error_user": "sorting raises a 'Sorting is broken!' alert",
}))
def test_sort_by_name_z_to_a(login_as, username):
    inventory = login_as(username)
    inventory.sort_by("Name (Z to A)")
    names = inventory.item_names()
    assert names == sorted(names, reverse=True)


@pytest.mark.parametrize("username", users({
    "problem_user": "Remove button does nothing",
    "error_user": "Remove button does nothing",
}))
def test_add_and_remove_updates_badge(login_as, username):
    inventory = login_as(username)
    inventory.add_first(2)
    inventory.remove_first()
    assert inventory.cart_count() == 1


@pytest.mark.parametrize("username", users({
    "problem_user": "typing in Last Name overwrites First Name, so checkout can't continue",
    "error_user": "Last Name field crashes and Finish does nothing",
}))
def test_checkout_completes(login_as, username):
    inventory = login_as(username)
    inventory.add_first()
    cart = inventory.open_cart()
    cart.start_checkout()
    cart.fill_details("Test", "User", "12345")
    cart.finish()
    assert "thank you" in cart.confirmation_text().lower()


@pytest.mark.parametrize("username", users({
    "problem_user": "checkout can't get past the details step",
    "visual_user": "inventory shows different prices than checkout charges",
}))
def test_overview_total_matches_item_price(login_as, username):
    inventory = login_as(username)
    expected = inventory.item_prices()[0]
    inventory.add_first()
    cart = inventory.open_cart()
    cart.start_checkout()
    cart.fill_details("Test", "User", "12345")
    assert cart.subtotal() == pytest.approx(expected)
