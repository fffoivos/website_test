import re
import time
import requests
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    WebDriverException,
)

# Set up Selenium with Chrome
chrome_options = Options()
# Uncomment the line below to run the browser in headless mode
# chrome_options.add_argument("--headless")
chrome_options.add_argument(
    "user-agent=Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:131.0) Gecko/20100101 Firefox/131.0"
)
driver = webdriver.Chrome(options=chrome_options)

# Base URL
base_url = "https://www.gutenberg.org"

# Custom headers for requests
headers = {
    "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:131.0) Gecko/20100101 Firefox/131.0"
}

# Navigate to the main page
driver.get("https://www.gutenberg.org/browse/languages/el#a33472")

# Initialize an empty list to store data
data = []


def collect_book_links():
    # Wait until the page content is loaded
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//div[@class='pgdbbylanguage']"))
        )
    except TimeoutException:
        print("Timeout waiting for page to load")
        return []

    # Find all <h2> elements followed by <ul> within .pgdbbylanguage
    h2_ul_pairs = driver.find_elements(
        By.XPATH,
        "//div[@class='pgdbbylanguage']/h2[following-sibling::*[1][self::ul]]",
    )
    print(f"Found {len(h2_ul_pairs)} author-booklist pairs")

    book_list = []

    for h2 in h2_ul_pairs:
        # Extract author name
        try:
            author_element = h2.find_element(By.XPATH, ".//a[contains(@href, '/browse/authors/')]")
            author = author_element.text.strip()
        except NoSuchElementException:
            author = h2.text.strip()  # In case there is no <a> tag
        # Find the following <ul> element
        try:
            ul = h2.find_element(By.XPATH, "following-sibling::ul[1]")
        except NoSuchElementException:
            continue  # If no <ul> after <h2>, skip

        # Find all <li> elements within the <ul>
        li_elements = ul.find_elements(By.XPATH, "./li")
        for li in li_elements:
            # Extract book title and link
            try:
                a_tag = li.find_element(By.XPATH, "./a")
                book_title = a_tag.text.strip()
                book_link = a_tag.get_attribute("href")
                if not book_link.startswith(base_url):
                    book_link = base_url + book_link
                print(f"Found book: {author} - {book_title} ({book_link})")
                book_list.append(
                    {"author": author, "title": book_title, "book_link": book_link}
                )
            except NoSuchElementException:
                print(f"Error extracting book info for {author}")
                continue

    return book_list


def process_books(book_list):
    for book in book_list:
        book_link = book["book_link"]
        author = book["author"]
        book_title = book["title"]
        # Visit the book page
        try:
            driver.get(book_link)
        except WebDriverException as e:
            print(f"Error accessing {book_link}: {e}")
            continue

        try:
            # Wait for the page to load
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))

            # Locate the link to the Plain Text UTF-8 file directly
            try:
                text_link_element = driver.find_element(
                    By.XPATH,
                    "//a[@type='text/plain'][contains(text(), 'Plain Text UTF-8')]",
                )
            except NoSuchElementException:
                # Try alternative locator
                text_link_element = driver.find_element(
                    By.XPATH, "//a[contains(text(), 'Plain Text UTF-8')]"
                )
            text_file_href = text_link_element.get_attribute("href")
            text_file_url = (
                text_file_href
                if text_file_href.startswith("http")
                else (base_url + text_file_href)
            )
            print(f"Downloading from: {text_file_url}")

            # Download the text file with custom headers
            response = requests.get(text_file_url, headers=headers)
            response.encoding = "utf-8"
            full_text = response.text

            # Clean the text
            start_match = re.search(
                r"\*\*\* START OF THE PROJECT GUTENBERG EBOOK.*\*\*\*", full_text
            )
            end_match = re.search(
                r"\*\*\* END OF THE PROJECT GUTENBERG EBOOK.*\*\*\*", full_text
            )
            if start_match and end_match:
                start_index = start_match.end()
                end_index = end_match.start()
                book_text = full_text[start_index:end_index].strip()
            else:
                book_text = full_text.strip()

        except Exception as e:
            print(f"Error processing {book_title}: {e}")
            book_text = ""

        # Append the data to the list
        data.append(
            {
                "author": author,
                "title": book_title,
                "book_link": book_link,
                "text": book_text,
            }
        )

        print(f"Processed: {author} - {book_title}")

        # Add a small delay to avoid overwhelming the server
        time.sleep(2)


# Main execution
book_list = collect_book_links()
process_books(book_list)

# Close the driver
driver.quit()

# Create a DataFrame
df = pd.DataFrame(data)

# Display the DataFrame
print(df)

# Save the DataFrame to a CSV file
df.to_csv("gutenberg_greek_books.csv", index=False, encoding="utf-8-sig")
print("Data saved to 'gutenberg_greek_books.csv'")
