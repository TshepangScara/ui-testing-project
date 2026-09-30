from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

from pages.base_page import BasePage


class LoginPage(BasePage):
    URL = "https://www.saucedemo.com/"

    USERNAME = (By.ID, "user-name")
    PASSWORD = (By.ID, "password")
    SUBMIT = (By.ID, "login-button")
    ERROR = (By.CSS_SELECTOR, "[data-test='error']")
    INVENTORY = (By.CLASS_NAME, "inventory_list")

    def open(self):
        self.driver.get(self.URL)
        return self

    def login(self, username, password):
        self.type(self.USERNAME, username)
        self.type(self.PASSWORD, password)
        self.click(self.SUBMIT)

    def error_text(self):
        return self.wait.until(EC.visibility_of_element_located(self.ERROR)).text

    def inventory_visible(self):
        return self.wait.until(EC.visibility_of_element_located(self.INVENTORY)).is_displayed()

    def login_form_visible(self):
        return self.is_visible(self.USERNAME) and self.is_visible(self.PASSWORD) and self.is_visible(self.SUBMIT)
