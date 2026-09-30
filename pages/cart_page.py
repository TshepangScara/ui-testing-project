from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


class CartPage:
    CART_ITEMS = (By.CSS_SELECTOR, ".cart_item")
    ITEM_NAMES = (By.CSS_SELECTOR, ".inventory_item_name")
    REMOVE_BUTTONS = (By.CSS_SELECTOR, "button[data-test^='remove']")
    CHECKOUT = (By.ID, "checkout")
    FIRST_NAME = (By.ID, "first-name")
    LAST_NAME = (By.ID, "last-name")
    POSTAL_CODE = (By.ID, "postal-code")
    CONTINUE = (By.ID, "continue")
    FINISH = (By.ID, "finish")
    COMPLETE_HEADER = (By.CSS_SELECTOR, ".complete-header")
    ERROR = (By.CSS_SELECTOR, "[data-test='error']")

    def __init__(self, driver):
        self.driver = driver
        self.wait = WebDriverWait(driver, 10)
        self.wait.until(EC.url_contains("cart"))

    def item_names(self):
        return [e.text for e in self.driver.find_elements(*self.ITEM_NAMES)]

    def item_count(self):
        return len(self.driver.find_elements(*self.CART_ITEMS))

    def remove_first(self):
        self.driver.find_elements(*self.REMOVE_BUTTONS)[0].click()

    def start_checkout(self):
        self.wait.until(EC.element_to_be_clickable(self.CHECKOUT)).click()

    def fill_details(self, first, last, postal):
        self.wait.until(EC.visibility_of_element_located(self.FIRST_NAME)).send_keys(first)
        self.wait.until(EC.visibility_of_element_located(self.LAST_NAME)).send_keys(last)
        self.wait.until(EC.visibility_of_element_located(self.POSTAL_CODE)).send_keys(postal)
        self.wait.until(EC.element_to_be_clickable(self.CONTINUE)).click()

        try:
            self.wait.until(EC.url_contains("checkout-step-two"))
        except TimeoutException:
            self.wait.until(EC.visibility_of_element_located(self.ERROR))

    def finish(self):
        self.wait.until(EC.element_to_be_clickable(self.FINISH)).click()

    def confirmation_text(self):
        return self.wait.until(EC.visibility_of_element_located(self.COMPLETE_HEADER)).text

    def error_text(self):
        return self.wait.until(EC.visibility_of_element_located(self.ERROR)).text
