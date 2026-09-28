from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


class LoginPage:
    URL = "https://www.saucedemo.com/"

    USERNAME = (By.ID, "user-name")
    PASSWORD = (By.ID, "password")
    SUBMIT = (By.ID, "login-button")
    ERROR = (By.CSS_SELECTOR, "[data-test='error']")
    INVENTORY = (By.CLASS_NAME, "inventory_list")

    def __init__(self, driver):
        self.driver = driver
        self.wait = WebDriverWait(driver, 10)

    def open(self):
        self.driver.get(self.URL)
        return self

    def login(self, username, password):
        self.driver.find_element(*self.USERNAME).send_keys(username)
        self.driver.find_element(*self.PASSWORD).send_keys(password)
        self.driver.find_element(*self.SUBMIT).click()

    def error_text(self):
        return self.wait.until(EC.visibility_of_element_located(self.ERROR)).text

    def inventory_visible(self):
        return self.wait.until(EC.visibility_of_element_located(self.INVENTORY)).is_displayed()
