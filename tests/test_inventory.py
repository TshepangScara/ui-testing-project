def test_inventory_lists_six_products(inventory_page):
    assert inventory_page.item_count() == 6


def test_sort_by_price_low_to_high(inventory_page):
    inventory_page.sort_by("Price (low to high)")
    prices = inventory_page.item_prices()
    assert prices == sorted(prices)


def test_sort_by_name_z_to_a(inventory_page):
    inventory_page.sort_by("Name (Z to A)")
    names = inventory_page.item_names()
    assert names == sorted(names, reverse=True)
