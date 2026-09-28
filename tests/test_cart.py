def test_adding_items_updates_cart_badge(inventory_page):
    assert inventory_page.cart_count() == 0
    inventory_page.add_first(2)
    assert inventory_page.cart_count() == 2


def test_removing_item_updates_cart_badge(inventory_page):
    inventory_page.add_first(2)
    inventory_page.remove_first()
    assert inventory_page.cart_count() == 1


def test_cart_page_shows_added_items(inventory_page):
    first_name = inventory_page.item_names()[0]
    inventory_page.add_first()
    cart = inventory_page.open_cart()
    assert cart.item_names() == [first_name]


def test_removing_from_cart_page_empties_cart(inventory_page):
    inventory_page.add_first()
    cart = inventory_page.open_cart()
    cart.remove_first()
    assert cart.item_count() == 0


def test_full_checkout_flow(inventory_page):
    inventory_page.add_first()
    cart = inventory_page.open_cart()
    cart.start_checkout()
    cart.fill_details("Test", "User", "12345")
    cart.finish()
    assert "thank you" in cart.confirmation_text().lower()


def test_checkout_requires_first_name(inventory_page):
    inventory_page.add_first()
    cart = inventory_page.open_cart()
    cart.start_checkout()
    cart.fill_details("", "User", "12345")
    assert "First Name is required" in cart.error_text()
