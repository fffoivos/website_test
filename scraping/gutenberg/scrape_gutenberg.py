import re
import asyncio
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import os
import time

# Set up output directory in script location
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(SCRIPT_DIR, 'gutenberg_output')
TEXTS_DIR = os.path.join(OUTPUT_DIR, 'texts')

# Create directories
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(TEXTS_DIR, exist_ok=True)

# Load existing metadata if it exists
metadata_file = os.path.join(OUTPUT_DIR, "gutenberg_metadata.csv")
if os.path.exists(metadata_file):
    existing_df = pd.read_csv(metadata_file)
    # Create set of existing books for faster lookup
    existing_books = {(str(row['author']).lower().strip(), str(row['title']).lower().strip()) 
                     for _, row in existing_df.iterrows()}
    current_index = existing_df['index'].max() + 1
else:
    existing_df = pd.DataFrame()
    existing_books = set()
    current_index = 1

print(f"Found {len(existing_books)} existing books")

# Set up Selenium with Chrome
chrome_options = Options()
chrome_options.add_argument("user-agent=Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:131.0) Gecko/20100101 Firefox/131.0")
driver = webdriver.Chrome(options=chrome_options)

# Base URL
base_url = "https://www.gutenberg.org"

def clean_filename(text):
    if not text:
        return "unknown"
    clean = re.sub(r'[^a-zA-Z0-9]', '_', text)
    clean = re.sub(r'_+', '_', clean)
    clean = clean.strip('_')
    return clean

def extract_year(text):
    if not text:
        return None, text
    
    year_pattern = r'(?:\d+(?:\s*BCE)?(?:-\d+(?:\s*BCE)?|\?\s*BCE?)?)'
    match = re.search(year_pattern, text)
    
    if match:
        year = match.group(0)
        clean_text = text[:match.start()].strip().rstrip(',')
        return year, clean_text
    return None, text

def collect_book_links():
    driver.get("https://www.gutenberg.org/browse/languages/el#a33472")
    time.sleep(1)
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//div[@class='pgdbbylanguage']"))
        )
    except TimeoutException:
        print("Timeout waiting for page to load")
        return []

    h2_ul_pairs = driver.find_elements(
        By.XPATH,
        "//div[@class='pgdbbylanguage']/h2[following-sibling::*[1][self::ul]]"
    )
    print(f"Found {len(h2_ul_pairs)} author-booklist pairs")

    book_list = []
    for h2 in h2_ul_pairs:
        try:
            ul = h2.find_element(By.XPATH, "following-sibling::ul[1]")
            li_elements = ul.find_elements(By.XPATH, "./li")
            for li in li_elements:
                try:
                    a_tag = li.find_element(By.XPATH, "./a")
                    book_link = a_tag.get_attribute("href")
                    if not book_link.startswith(base_url):
                        book_link = base_url + book_link
                    print(f"Found book: {book_link}")
                    book_list.append({"book_link": book_link})
                except NoSuchElementException:
                    continue
        except NoSuchElementException:
            continue

    return book_list

async def process_book(book_link):
    global current_index
    
    try:
        driver.get(book_link)
        time.sleep(1)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))

        # Extract metadata
        author_elements = driver.find_elements(By.XPATH, "//tr[th[text()='Author']]")
        translator_element = driver.find_element(By.XPATH, "//tr[th[text()='Translator']]") if len(driver.find_elements(By.XPATH, "//tr[th[text()='Translator']]")) > 0 else None
        
        # Get author
        if author_elements:
            text = author_elements[0].find_element(By.TAG_NAME, "td").text.strip()
            year, author = extract_year(text)
            etos_author = year
        else:
            author = None
            etos_author = None

        # Get title
        try:
            title_element = driver.find_element(By.XPATH, "//tr[th[text()='Title']]")
            title = title_element.find_element(By.TAG_NAME, "td").text.strip()
        except NoSuchElementException:
            title = None

        # Check for duplicate before proceeding
        if (str(author).lower().strip(), str(title).lower().strip()) in existing_books:
            print(f"Skipping duplicate: {author} - {title}")
            return None

        # Get translator
        if translator_element:
            text = translator_element.find_element(By.TAG_NAME, "td").text.strip()
            year, translator = extract_year(text)
            etos_translator = year
        elif len(author_elements) > 1:
            text = author_elements[1].find_element(By.TAG_NAME, "td").text.strip()
            year, translator = extract_year(text)
            etos_translator = year
        else:
            translator = None
            etos_translator = None

        # Get text content link and navigate to it
        text_link_element = driver.find_element(
            By.XPATH,
            "//a[contains(text(), 'Plain Text UTF-8')]"
        )
        text_file_href = text_link_element.get_attribute("href")
        
        # Navigate to the text page and wait for content
        driver.get(text_file_href)
        
        # Wait for the pre element containing the text
        wait = WebDriverWait(driver, 20)
        pre_element = wait.until(
            EC.presence_of_element_located((By.XPATH, "//body/pre"))
        )
        
        # Get the full text content
        full_text = pre_element.text

        # Clean the text
        start_match = re.search(r"\*\*\* START OF THE PROJECT GUTENBERG EBOOK.*\*\*\*", full_text)
        end_match = re.search(r"\*\*\* END OF THE PROJECT GUTENBERG EBOOK.*\*\*\*", full_text)
        if start_match and end_match:
            book_text = full_text[start_match.end():end_match.start()].strip()
        else:
            book_text = full_text.strip()

        # Save text file
        author_name = clean_filename(author) if author else 'unknown'
        filename = f"book_{current_index}_{author_name}.txt"
        
        with open(os.path.join(TEXTS_DIR, filename), 'w', encoding='utf-8') as f:
            f.write(book_text)

        # Create metadata entry
        metadata = {
            'index': current_index,
            'author': author,
            'etos_author': etos_author,
            'translator': translator,
            'etos_translator': etos_translator,
            'title': title,
            'text_filename': filename
        }
        
        current_index += 1
        print(f"Processed: {author} - {title}")
        return metadata

    except Exception as e:
        print(f"Error processing book: {e}")
        return None

async def process_books(book_list):
    tasks = []
    for book in book_list:
        await asyncio.sleep(1)
        task = asyncio.create_task(process_book(book["book_link"]))
        tasks.append(task)
    
    results = await asyncio.gather(*tasks)
    return [r for r in results if r is not None]

# Main execution
print(f"Starting scraping from index: {current_index}")
book_list = collect_book_links()

# Run async processing
new_data = asyncio.run(process_books(book_list))

# Close the driver
driver.quit()

# Combine existing and new data
if new_data:
    new_df = pd.DataFrame(new_data)
    df = pd.concat([existing_df, new_df], ignore_index=True) if not existing_df.empty else new_df
    
    # Save the combined DataFrame
    columns = ['index', 'author', 'etos_author', 'translator', 'etos_translator', 
               'title', 'text_filename']
    df = df[columns]
    df.to_csv(metadata_file, index=False, encoding="utf-8-sig")
    
    print(f"\nScraping completed!")
    print(f"Added {len(new_data)} new books")
    print(f"Results saved in: {OUTPUT_DIR}")
else:
    print("\nNo new books were added")