import re
import time
import random
import csv
import pandas as pd
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support.ui import Select
import undetected_chromedriver as uc

def init_driver():
    options = uc.ChromeOptions()
    return uc.Chrome(options=options)


def is_captcha_present(driver):
    try:
        driver.find_element(By.ID, "px-captcha")
        return True
    except NoSuchElementException:
        return False


def handle_captcha(driver):
    while is_captcha_present(driver):
        print("CAPTCHA detected! Waiting for it to be solved...")
        time.sleep(2)   # check for completion every 2 seconds
    print("CAPTCHA solved!")
    time.sleep(2)


def human_like_delay():
    time.sleep(random.uniform(2, 5))


def save_to_csv(filename, data):
    with open(filename, "a", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(data)


def scrape_listing(driver, url, current_url_num):
    # Navigate to current listing url and handle captcha
    driver.get(url)
    handle_captcha(driver)

    # Get neighborhood scores info (present in every type of listing)
    scores_container = driver.find_element(By.CSS_SELECTOR, "div.ScoresWrapper-sc-1d3uot0-0")
    if scores_container:
        score_divs = scores_container.find_elements(By.CSS_SELECTOR, "div.neighborhood-score")
        time.sleep(random.uniform(1, 2))
        walk_score = re.search(r"\d+", score_divs[0].text).group() if len(score_divs) > 0 else "N/A"
        transit_score = re.search(r"\d+", score_divs[1].text).group() if len(score_divs) > 1 else "N/A"
        bike_score = re.search(r"\d+", score_divs[2].text).group() if len(score_divs) > 2 else "N/A"
    else:
        walk_score, transit_score, bike_score = "N/A", "N/A", "N/A"

    # Handle rental dropdown selection (some listings default to "for sale" instead of "for rent"
    dropdown = driver.find_elements(By.CSS_SELECTOR, "select.styled__UnitsTableTypeSelector-sc-10hw6ue-6")
    if dropdown:
        select = Select(dropdown[0])
        selected_option = select.first_selected_option.text.strip()
        if selected_option != "For rent":
            select.select_by_visible_text("For rent")
            time.sleep(2)

    unit_container = driver.find_elements(By.CSS_SELECTOR, "div[data-test-id='bdp-property-card-container']")

    # If unit container exists
    if unit_container:
        human_like_delay()
        title_elem = driver.find_element(By.CSS_SELECTOR, "h1[data-test-id='bdp-building-title']")
        title = title_elem.text.strip() if title_elem else "N/A"

        # Extract address
        address_elem = driver.find_elements(By.CSS_SELECTOR, "h2[data-test-id='bdp-building-address']")
        if not address_elem:
            address_elem = driver.find_elements(By.CSS_SELECTOR, "p[data-test-id='bdp-building-address']")

        if address_elem:
            address = address_elem[0].text.strip()
            address_parts = address.split(", ")
            if len(address_parts) == 3:
                address, city, state_zip = address_parts
                state, zip_code = state_zip.split(" ")
            elif len(address_parts) == 2:
                address, city = title, address_parts[0]
                state, zip_code = address_parts[1].split(" ")
            else:
                address, city, state, zip_code = "N/A", "N/A", "N/A", "N/A"
        else:
            address, city, state, zip_code = "N/A", "N/A", "N/A", "N/A"

        # Extract up to 20 unit details from current listing
        unit_blocks = driver.find_elements(By.XPATH,
                                           "//div[@data-test-id='bdp-property-card-container']//div[contains(@class, 'styled-floorplan-card') or contains(@class, 'unit-card__unit-info')]")

        for unit in unit_blocks[:20]:
            unit_text = unit.text
            price_match = re.findall(r"\$\d{1,3}(?:,\d{3})*(?:\.\d{2})?", unit_text)
            prices = [int(price.replace('$', '').replace(',', '')) for price in price_match]
            price = sum(prices) // len(prices) if prices else "N/A"

            beds = re.search(r"(\d+|Studio) bd", unit_text)
            baths = re.search(r"(\d+) ba", unit_text)
            area = re.search(r"([\d,]+) sqft", unit_text)

            beds = beds.group(1) if beds else "0"
            baths = baths.group(1) if baths else "N/A"
            area = area.group(1).replace(",", "") if area else "0"

            row = [title, address, city, state, zip_code, price, beds, baths, area, walk_score, transit_score,
                     bike_score]
            save_to_csv("real_est_data_rent.csv", row)
            print(
                f"Row {current_url_num} Extracted: {title}, {address}, {city}, {state}, {zip_code}, {price}, {beds}, {baths}, {area}, {walk_score}, {transit_score}, {bike_score}")

    else:
        print("No unit info found, trying alternative configuration")
        human_like_delay()
        title = "N/A"

        # Alternative address extraction
        address_elem = driver.find_element(By.CSS_SELECTOR,
                                           "div.styles__AddressWrapper-fshdp-8-106-0__sc-13x5vko-0")
        address = address_elem.text.strip() if address_elem else "N/A"
        address_parts = address.split(", ")
        address, city, state_zip = address_parts if len(address_parts) == 3 else ("N/A", "N/A", "N/A")
        state, zip_code = state_zip.split(" ") if " " in state_zip else ("N/A", "N/A")

        # Extract price
        price_elem = driver.find_element(By.CSS_SELECTOR, "span[data-testid='price']")
        price = re.search(r"\$([\d,]+)", price_elem.text).group(1).replace(",", "") if price_elem else "N/A"

        # Extract bed, bath, and area
        facts_elem = driver.find_element(By.CSS_SELECTOR, "div[data-testid='bed-bath-sqft-facts']")
        if facts_elem:
            facts_text = facts_elem.text
            facts_list = facts_text.split("\n")  # Split by new lines

            # Extract values based on known order
            beds = facts_list[0] if len(facts_list) > 0 and facts_list[0] != "--" else "N/A"
            baths = facts_list[2] if len(facts_list) > 2 and facts_list[2] != "--" else "N/A"
            area = facts_list[4] if len(facts_list) > 4 and facts_list[4] != "--" else "N/A"

            # Remove commas from area to keep it numeric
            area = area.replace(",", "") if area != "N/A" else area
        else:
            beds, baths, area = "N/A", "N/A", "N/A"

        row = [title, address, city, state, zip_code, price, beds, baths, area, walk_score, transit_score,
                 bike_score]
        save_to_csv("real_est_data_rent.csv", row)

        print(
            f"Row {current_url_num} Extracted: {title}, {address}, {city}, {state}, {zip_code}, {price}, {beds},"
            f" {baths}, {area}, {walk_score}, {transit_score}, {bike_score}")


def main():
    driver = init_driver()
    # Load listing URLs
    url_csv = pd.read_csv('cleaned_listing_urls_period.csv')
    listing_urls = url_csv['URL'].tolist()

    current_url_num = 0
    for url in listing_urls:
        current_url_num += 1
        try:
            scrape_listing(driver, url, current_url_num)
        except Exception as e:
            print(f"Error extracting data from {url}: {e}")
            continue

    driver.quit()

if __name__ == "__main__":
    main()
