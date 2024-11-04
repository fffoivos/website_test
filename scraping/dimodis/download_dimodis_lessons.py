from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from urllib.parse import urljoin
import requests
import csv
import os

# Set up Selenium WebDriver (make sure you have the appropriate driver installed)
driver = webdriver.Chrome()  # or webdriver.Firefox(), etc.

# Navigate to the webpage
url = "https://georgakas.lit.auth.gr/dimodis/index.php?option=com_zoo&view=category&layout=category&Itemid=282"
driver.get(url)

# Wait for the div elements to load
wait = WebDriverWait(driver, 10)
divs = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div[class^='uk-width-medium-1-2']")))

# Create a directory to store the PDFs and CSV
pdf_dir = "downloaded_pdfs"
os.makedirs(pdf_dir, exist_ok=True)

# Prepare CSV file for metadata
csv_filename = os.path.join(pdf_dir, "lesson_metadata.csv")
csv_headers = ["Lesson Number", "Lesson Title", "PDF Filename"]

with open(csv_filename, "w", newline="", encoding="utf-8") as csvfile:
    csv_writer = csv.writer(csvfile)
    csv_writer.writerow(csv_headers)

    for index, div in enumerate(divs, start=1):
        # Extract lesson title from the title attribute
        a_element = div.find_element(By.CSS_SELECTOR, "a[title]")
        lesson_title = a_element.get_attribute("title")

        # Find download button
        download_button = div.find_element(By.CSS_SELECTOR, "a.uk-button.uk-button-primary")
        pdf_url = urljoin("https://georgakas.lit.auth.gr", download_button.get_attribute("href"))

        # Download PDF
        pdf_filename = f"lesson_{index}.pdf"
        pdf_path = os.path.join(pdf_dir, pdf_filename)

        response = requests.get(pdf_url, headers={
            "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:131.0) Gecko/20100101 Firefox/131.0",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/png,image/svg+xml,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Referer": url,
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        })

        if response.status_code == 200:
            with open(pdf_path, "wb") as pdf_file:
                pdf_file.write(response.content)
            print(f"Downloaded: {pdf_filename}")

            # Write metadata to CSV
            csv_writer.writerow([index, lesson_title, pdf_filename])
        else:
            print(f"Failed to download PDF for lesson {index}")

# Close the browser
driver.quit()

print("Scraping complete. Check the 'downloaded_pdfs' folder for PDFs and the CSV metadata file.")