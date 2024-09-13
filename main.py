from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import re
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys


# Function to click the submit button and open it in a new tab
def open_in_new_tab(driver, xpath):
    submit_button = wait_for_element_clickable(driver, By.XPATH, xpath)

    # Use ActionChains to simulate Control + Click (or Command + Click on macOS) to open the link in a new tab
    action = ActionChains(driver)

    # For Windows/Linux, use Control key. For macOS, use Command key (Keys.COMMAND).
    action.key_down(Keys.COMMAND).click(submit_button).key_up(Keys.COMMAND).perform()

    # Switch to the new tab (the last opened one)
    driver.switch_to.window(driver.window_handles[-1])


# Function to close the current tab and switch back to the original one
def close_current_tab_and_switch_back(driver):
    driver.close()  # Close the current tab
    driver.switch_to.window(driver.window_handles[0])  # Switch back to the original tab


def close_cookie_message(driver):
    try:
        # Wait for the cookie message to appear, then click the 'Accept' or 'Close' button
        click_element(driver, By.CSS_SELECTOR, "input#cookie_msg_btn_no")

    except Exception as e:
        print("Cookie message not found or not clickable.", str(e))

def wait_for_element_clickable(driver, by, locator, timeout=10):
    """Wait until the element is clickable, then return the element."""
    return WebDriverWait(driver, timeout).until(EC.element_to_be_clickable((by, locator)))


def click_element(driver, by, locator, timeout=10):
    """Wait for the element to be clickable, then click it."""
    element = wait_for_element_clickable(driver, by, locator, timeout)
    element.click()

def scrape_dortmund_anmeldung():
    service = Service(ChromeDriverManager().install())
    # headless option
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-software-rasterizer")
    options.add_argument("--log-level=3")
    options.add_argument("--disable-search-engine-choice-screen")

    # Initialize the driver with the Chrome options
    driver = webdriver.Chrome(service=service, options=options)

    # Navigate to the website
    driver.get("https://dortmund.termine-reservieren.de/")

    # Close the cookie consent message
    close_cookie_message(driver)

    try:
        # Click on "Einwohnermelde- und Kraftfahrzeugangelegenheiten"
        click_element(driver, By.NAME, "Einwohnermelde- und Kraftfahrzeugangelegenheiten")

        # Click on "Einwohnermeldeangelegenheiten"
        click_element(driver, By.ID, "header_concerns_accordion-6276")

        # Increase the number of Anmeldung (pro Person)
        click_element(driver, By.ID, "button-plus-730")

        # Click "Weiter"
        click_element(driver, By.ID, "WeiterButton")

        # Update the checkbox part
        checkboxes = [
            "doclist_item_730_299131",  # alle Personalausweise und Reisepässe der Anmeldenden
            "doclist_item_730_299132",  # Wohnungsgeberbescheinigung
            "doclist_item_730_299139",  # ggf. Heirats- und Geburtsurkunden
            "doclist_item_730_299140"  # bei EU-Staatsangehörigen zusätzlich ein Lichtbild
        ]

        for checkbox_id in checkboxes:
            checkbox_label = f"label[for='{checkbox_id}']"
            click_element(driver, By.CSS_SELECTOR, checkbox_label)

        # Click the OK button
        click_element(driver, By.ID, "OKButton")

        # Handle the available appointments section
        h3_elements = driver.find_elements(By.CSS_SELECTOR, "div#suggest_location_accordion h3[title]")

        for h3_element in h3_elements:
            if h3_element.is_displayed() and h3_element.is_enabled():
                title = h3_element.get_attribute("title")
                aria_selected = h3_element.get_attribute("aria-selected")

                if "Termin" in title:
                    office, date, time = title.split(",")
                    print(office)

                    # Only click if not already selected
                    if aria_selected != "true":
                        h3_element.click()

                    # Click the submit button for this office
                    submit_button_xpath = f"//input[@value='{office} auswählen']"
                    open_in_new_tab(driver, submit_button_xpath)

                    # Extract summary details
                    summary_element = driver.find_element(By.ID, "suggest_details_summary")
                    summary_text = summary_element.text

                    # Extract the date from the summary using regex
                    date_match = re.search(r'\d{2}\.\d{2}\.\d{4}', summary_text)
                    if date_match:
                        date = date_match.group(0)
                        print(f"Available date: {date}")
                    else:
                        print("Date not found.")

                    # Get all available times from the table
                    buttons = driver.find_elements(By.CSS_SELECTOR, "table.sugg_table button:not([disabled])")
                    available_times = [button.get_attribute("title") for button in buttons]
                    print("Available times:", available_times)

                    # Close the current tab and switch back to the original tab
                    close_current_tab_and_switch_back(driver)

    finally:
        driver.quit()

if __name__ == "__main__":
    scrape_dortmund_anmeldung()
