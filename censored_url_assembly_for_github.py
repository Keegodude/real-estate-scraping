import csv
import time
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
import undetected_chromedriver as uc

# ALGORITHM FOR COVERING THE MAP:
# Start at southeastern most sector(south = ~41.77, east ~ 87.57), increment south and north by .0136 to cover each sector until the north bound is crossed. After it has been crossed,
# start from the sector to the west of the southeastern most one from before(south = ~41.77, east = 87.57 + .0247, west + .0247) and repeat the increment to move northward again.
# Everytime the northern boundary is reached, continue to start from the southernmost and move to the left sector of the previous starting point, i.e. add (x * .0247) to the initial east and west values where x is the number of times the north bound has been crossed.

# Set up webdriver for selenium
def init_driver():
    options = uc.ChromeOptions()
    options.binary_location = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"
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

# Scrolls the length of the page to allow all listings to load
def scroll_full_page(driver, container):
    max_attempts = 8
    for _ in range(max_attempts):
        handle_captcha(driver)
        driver.execute_script("arguments[0].scrollTop += arguments[0].offsetHeight;", container)


def save_to_csv(filename, data):
    with open(filename, "a", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(data)


def get_sector_url(north, south, east, west):
    return (
        "Source url goes here"
    )


def scrape_sector(driver, north, south, east, west, sector_count):
    url = get_sector_url(north, south, east, west)
    print(f"Scraping sector {sector_count}: {url}")
    driver.get(url)
    handle_captcha(driver)
    time.sleep(0.25)

    save_to_csv("all_sector_coords.csv", [sector_count, north, south, east, west])

    pagenum = 1
    while pagenum <= 20:
        page_url = f"{url}&p={pagenum}" if pagenum > 1 else url
        driver.get(page_url)
        handle_captcha(driver)
        time.sleep(0.25)

        try:
            container = driver.find_element(By.CSS_SELECTOR, "div.search-page-list-container")
            scroll_full_page(driver, container)
            listings = driver.find_elements(By.CSS_SELECTOR, "a[data-test='property-card-link']")

            for elem in listings:
                link = elem.get_attribute("href")
                if link and "name of website goes here" not in link:
                    link = "name of website" + link
                save_to_csv("all_listing_urls_period.csv", [link])
        except NoSuchElementException:
            print("No listings found on this page.")

        try:
            next_button = driver.find_element(By.XPATH, '//a[@title="Next page"]')
            if next_button.get_attribute("aria-disabled") == "true":
                break
        except NoSuchElementException:
            print("No next button found; stopping pagination.")
            break

        pagenum += 1


def main():
    driver = init_driver()

    # Define initial sector coordinates
    south, east = 41.77745065417775, 87.57740945959905
    north, west = 42.02336223272467, 87.84717569575676
    start_north, start_south = 41.803473084655366, 41.78979563291221
    start_east, start_west = 87.7016957756308, 87.72639355623993

    current_north, current_south = start_north, start_south
    current_east, current_west = start_east, start_west
    sector_count, column_count = 0, 0

    while current_west < west:
        scrape_sector(driver, current_north, current_south, current_east, current_west, sector_count)
        sector_count += 1

        current_north += 0.0136
        current_south += 0.0136

        if current_north > north:
            column_count += 1
            current_north, current_south = start_north, start_south
            current_east = start_east + (column_count * 0.0247)
            current_west = start_west + (column_count * 0.0247)

    driver.quit()


if __name__ == "__main__":
    main()