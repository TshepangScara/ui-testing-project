from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait


class InventoryPage:
    ITEMS = (By.CSS_SELECTOR, ".inventory_item")
    ITEM_NAMES = (By.CSS_SELECTOR, ".inventory_item_name")
    ITEM_PRICES = (By.CSS_SELECTOR, ".inventory_item_price")
    ADD_BUTTONS = (By.CSS_SELECTOR, "button[data-test^='add-to-cart']")
    REMOVE_BUTTONS = (By.CSS_SELECTOR, "button[data-test^='remove']")
    CART_BADGE = (By.CSS_SELECTOR, ".shopping_cart_badge")
    CART_LINK = (By.CSS_SELECTOR, ".shopping_cart_link")
    SORT = (By.CSS_SELECTOR, "[data-test='product-sort-container']")

    def __init__(self, driver):
        self.driver = driver
        self.wait = WebDriverWait(driver, 10)
        self.wait.until(EC.visibility_of_element_located(self.ITEMS))

    def item_count(self):
        return len(self.driver.find_elements(*self.ITEMS))

    def item_names(self):
        return [e.text for e in self.driver.find_elements(*self.ITEM_NAMES)]

    def item_prices(self):
        return [float(e.text.lstrip("$")) for e in self.driver.find_elements(*self.ITEM_PRICES)]

    def add_first(self, n=1):
        # Buttons flip from "add" to "remove" on click, so re-query each time
        for _ in range(n):
            self.driver.find_elements(*self.ADD_BUTTONS)[0].click()

    def remove_first(self):
        self.driver.find_elements(*self.REMOVE_BUTTONS)[0].click()

    def cart_count(self):
        badges = self.driver.find_elements(*self.CART_BADGE)
        return int(badges[0].text) if badges else 0

    def sort_by(self, visible_text):
        Select(self.driver.find_element(*self.SORT)).select_by_visible_text(visible_text)

    def open_cart(self):
        from pages.cart_page import CartPage

        self.driver.find_element(*self.CART_LINK).click()
        return CartPage(self.driver)
