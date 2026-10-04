from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

from pages.base_page import BasePage


class CartPage(BasePage):
    """The cart page plus the checkout steps that follow it."""

    CART_ITEMS = (By.CSS_SELECTOR, ".cart_item")
    ITEM_NAMES = (By.CSS_SELECTOR, ".inventory_item_name")
    ITEM_PRICES = (By.CSS_SELECTOR, ".inventory_item_price")
    REMOVE_BUTTONS = (By.CSS_SELECTOR, "button[data-test^='remove']")
    CHECKOUT = (By.ID, "checkout")
    FIRST_NAME = (By.ID, "first-name")
    LAST_NAME = (By.ID, "last-name")
    POSTAL_CODE = (By.ID, "postal-code")
    CONTINUE = (By.ID, "continue")
    ERROR = (By.CSS_SELECTOR, "[data-test='error']")
    SUBTOTAL = (By.CSS_SELECTOR, "[data-test='subtotal-label']")
    TAX = (By.CSS_SELECTOR, "[data-test='tax-label']")
    TOTAL = (By.CSS_SELECTOR, "[data-test='total-label']")
    FINISH = (By.ID, "finish")
    COMPLETE_HEADER = (By.CSS_SELECTOR, ".complete-header")

    def __init__(self, driver):
        super().__init__(driver)
        self.wait.until(EC.url_contains("cart"))

    # --- Cart ---

    def item_names(self):
        return [e.text for e in self.driver.find_elements(*self.ITEM_NAMES)]

    def item_count(self):
        return len(self.driver.find_elements(*self.CART_ITEMS))

    def remove_first(self):
        self.driver.find_elements(*self.REMOVE_BUTTONS)[0].click()

    def start_checkout(self):
        self.click(self.CHECKOUT)

    # --- Checkout step one: your information ---

    def fill_details(self, first, last, postal):
        self.type(self.FIRST_NAME, first)
        self.type(self.LAST_NAME, last)
        self.type(self.POSTAL_CODE, postal)
        self.click(self.CONTINUE)
        # Either we move on to the overview, or a validation error appears
        self.wait.until(EC.any_of(
            EC.url_contains("checkout-step-two"),
            EC.visibility_of_element_located(self.ERROR),
        ))

    def error_text(self):
        return self.text_of(self.ERROR)

    # --- Checkout step two: overview ---

    def item_prices(self):
        return [float(e.text.lstrip("$")) for e in self.driver.find_elements(*self.ITEM_PRICES)]

    def subtotal(self):
        return self._amount(self.SUBTOTAL)

    def tax(self):
        return self._amount(self.TAX)

    def total(self):
        return self._amount(self.TOTAL)

    def _amount(self, locator):
        # Labels read like "Item total: $39.98"; keep only the number after the "$"
        return float(self.text_of(locator).split("$")[-1])

    def finish(self):
        self.click(self.FINISH)

    # --- Checkout complete ---

    def confirmation_text(self):
        return self.text_of(self.COMPLETE_HEADER)
