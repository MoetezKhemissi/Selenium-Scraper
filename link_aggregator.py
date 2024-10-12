from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import time

# Set up options for headless browsing
options = Options()

# Create a new instance of the Chrome driver
driver = webdriver.Chrome(options=options)

try:
    # Navigate to the LeetCode problem page
    driver.get("https://leetcode.com/problems/two-sum/description/")
    time.sleep(3)  # Wait for the page to load

    # Locate the "Problem List" button and click it
    problem_list_button = driver.find_element(By.XPATH, "//div[contains(text(), 'Problem List')]")
    problem_list_button.click()
    time.sleep(3)  # Wait for the problem list to appear

    # Locate the container with the problem links
    container = driver.find_element(By.CSS_SELECTOR, "div.z-base-1.relative.flex.min-h-full.flex-col")

    # Find all <a> elements within the container
    problem_links = container.find_elements(By.TAG_NAME, 'a')

    # Extract and print the links, and store them in a list
    links = []
    for link in problem_links:
        href = link.get_attribute('href')
        if href and '/problems/' in href:
            full_link = 'https://leetcode.com' + href
            links.append(full_link)
            print(full_link)

    # Save the links to a file
    with open('problem_links.txt', 'w') as f:
        for link in links:
            f.write(link + '\n')

finally:
    # Close the browser
    driver.quit()
