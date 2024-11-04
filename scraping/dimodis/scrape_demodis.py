import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
import re

def clean_html(raw_html):
    cleanr = re.compile('<.*?>')
    cleantext = re.sub(cleanr, '', raw_html)
    return cleantext.strip()

def clean_text(text):
    # Remove &nbsp; and replace with a single space
    cleaned = re.sub('&nbsp;', ' ', text)
    # Remove multiple spaces
    cleaned = re.sub('\s+', ' ', cleaned)
    return cleaned.strip()

def scrape_post(url):
    chrome_options = Options()
    chrome_options.add_argument('user-agent=Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:131.0) Gecko/20100101 Firefox/131.0')
    chrome_options.add_argument('--headless')
    
    driver = webdriver.Chrome(options=chrome_options)
    
    data = []  # List to store our scraped data
    
    try:
        driver.get(url)
        print(f"Navigated to {url}")
        
        # Extract title, authors, and abstract
        article_div = driver.find_element(By.CLASS_NAME, "uk-article")
        title = article_div.find_element(By.CLASS_NAME, "uk-article-title").text
        authors = [a.text for a in article_div.find_elements(By.CSS_SELECTOR, "p.uk-article-meta a")]
        abstract = article_div.find_element(By.CLASS_NAME, "uk-article-lead").text
        
        # Add abstract as the first row in frag_content
        data.append({
            'frag_title': 'Abstract',
            'frag_content': abstract,
            'footnotes': '',
            'sxolia': '',
            'title': title,
            'authors': ', '.join(authors)
        })
        
        n = 2
        while True:
            try:
                fragment_id = f"set-rl_sliders-{n}"
                fragment = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.ID, fragment_id))
                )
                print(f"\nFound fragment with ID: {fragment_id}")
                
                accordion_groups = fragment.find_elements(By.CLASS_NAME, "accordion-group")
                print(f"Found {len(accordion_groups)} accordion groups in {fragment_id}")
                
                for index, group in enumerate(accordion_groups, 1):
                    try:
                        title_element = group.find_element(By.CLASS_NAME, "accordion-toggle")
                        frag_title = title_element.get_attribute("title")
                        print(f"\nAccordion {index} - Title: {frag_title}")
                        
                        if frag_title in ["Βιβλιογραφία", "Δικτυογραφία"]:
                            print("Reached Bibliography or Webography. Stopping.")
                            return pd.DataFrame(data)
                        
                        if "collapsed" in title_element.get_attribute("class"):
                            driver.execute_script("arguments[0].click();", title_element)
                            time.sleep(1)
                        
                        content = ""
                        footnotes = []
                        sxolia = []
                        
                        content_element = group.find_element(By.CLASS_NAME, "accordion-inner")
                        
                        # First get the introductory paragraph
                        try:
                            intro_div = content_element.find_element(By.CLASS_NAME, "uk-width-medium-7-10")
                            intro_paragraphs = intro_div.find_elements(By.XPATH, "./p[following-sibling::table[@class='uk-table']]")
                            for p in intro_paragraphs:
                                p_text = clean_text(p.text)
                                if p_text:
                                    print("this is added from intro: ", p_text)
                                    content += p_text + "\n"
                            content += "\n"
                        except NoSuchElementException:
                            print("No introduction paragraph found - this might be an introduction or other type of accordion")
                            content = ""  # Initialize content as empty string if no intro paragraph exists
                         
                        # Find all table rows
                        rows = content_element.find_elements(By.TAG_NAME, "tr")
                        
                        for row in rows:
                            td_elements = row.find_elements(By.TAG_NAME, "td")
                            if len(td_elements) >= 2:  # Make sure we have at least 2 cells
                                # Process paragraphs from second and third td elements
                                for i,td in enumerate(td_elements):  
                                    paragraphs = td.find_elements(By.TAG_NAME, "p")
                                    if i == 0:
                                        for p in paragraphs:
                                            print("this is removed: ",p.text)
                                        continue # Skip the first td
                                    for p in paragraphs:
                                        p_text = clean_text(p.text)
                                        print("this is added: ", p_text)
                                        if p_text:  # Only process non-empty paragraphs                                            
                                            content += p_text + "\n"
                                            
                                            # get annotations either from in-text or from third <td>
                                            tooltips = p.find_elements(By.CSS_SELECTOR, "span.rl_tooltips-link")
                                            for tooltip in tooltips:
                                                word = clean_text(tooltip.text)
                                                explanation = clean_text(clean_html(tooltip.get_attribute("data-content")))
                                                # if there is a word annotated it means it's from in-text
                                                if word.strip():
                                                    footnotes.append(f"{word} = {explanation}")
                                                # otherwise it has to be from the third <td>
                                                else:
                                                    sxolia.append(explanation)
                                    if paragraphs:
                                        content += "\n"
                        
                        content = content.strip()
                        footnotes_text = "\n".join(footnotes)
                        sxolia_text = "\n\n".join(sxolia)  # Separate sxolia with an empty line
                        
                        if content:
                            print(f"Content: {content[:400]}...")
                            data.append({
                                'frag_title': frag_title,
                                'frag_content': content,
                                'footnotes': footnotes_text,
                                'sxolia': sxolia_text,
                                'title': title,
                                'authors': ', '.join(authors)
                            })
                        else:
                            print("No content found in this accordion.")
                        
                    except Exception as e:
                        print(f"Error processing accordion {index} in {fragment_id}: {str(e)}")
                    
                    print("-" * 50)
                
                n += 1
            
            except TimeoutException:
                print(f"No more fragments found after ID: set-rl_sliders-{n-1}")
                break
        
    except Exception as e:
        print(f"An error occurred: {str(e)}")
    
    finally:
        driver.quit()
        print("Browser closed")
    
    return pd.DataFrame(data)


def scrape_all_posts():
    base_url = "https://georgakas.lit.auth.gr"
    posts_url = f"{base_url}/dimodis/index.php?option=com_chronoforms&view=form&Itemid=277"

    chrome_options = Options()
    chrome_options.add_argument('user-agent=Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:131.0) Gecko/20100101 Firefox/131.0')
    
    driver = webdriver.Chrome(options=chrome_options)
    
    all_data = []

    try:
        driver.get(posts_url)
        print(f"Navigated to {posts_url}")

        n = 1
        while True:
            try:
                post_selector = f".uk-grid-width-1-1 > div:nth-child({n})"
                post_element = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, post_selector))
                )

                link_element = post_element.find_element(By.CSS_SELECTOR, "a[href]")
                post_url = link_element.get_attribute("href")
                full_url = base_url + post_url if post_url.startswith("/") else post_url

                print(f"Scraping post {n}: {full_url}")
                post_data = scrape_post(full_url)
                all_data.append(post_data)

                n += 1

            except TimeoutException:
                print(f"No more posts found after {n-1} posts.")
                break

    except Exception as e:
        print(f"An error occurred: {str(e)}")

    finally:
        driver.quit()
        print("Browser closed")

    # Combine all DataFrames
    combined_df = pd.concat(all_data, ignore_index=True)

    # Save to CSV
    path = '/home/fivos/Desktop/text_sources/dimodis/erga_dimodous.csv'
    combined_df.to_csv(path, index=False)
    print(f"All data saved to {path}")

    return combined_df

# Run the scraping process
if __name__ == "__main__":
    result_df = scrape_all_posts()
    print(result_df)