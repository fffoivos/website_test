import requests
from bs4 import BeautifulSoup
import time
from typing import Optional, Tuple, List, Dict
from urllib.parse import urljoin
import pandas as pd

def get_authors_from_page(url: str) -> Tuple[Optional[List[dict]], Optional[str]]:
    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:132.0) Gecko/20100101 Firefox/132.0'
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        mw_pages_div = soup.find('div', {'id': 'mw-pages'})
        if not mw_pages_div:
            print(f"Could not find mw-pages div on {url}")
            return None, None
            
        author_links = []
        for link in mw_pages_div.find_all('a'):
            href = link.get('href', '')
            if 'Συγγραφέας:' in href or 'Συγγραφέας:' in link.text:
                name = link.text.replace('Συγγραφέας:', '').strip()
                author_links.append({
                    'name': name,
                    'url': 'https://el.wikisource.org' + href
                })
        
        next_page = None
        next_page_link = soup.find('a', string='επόμενη σελίδα')
        if next_page_link:
            next_page = 'https://el.wikisource.org' + next_page_link['href']
            
        return author_links, next_page
        
    except Exception as e:
        print(f"Error processing {url}: {str(e)}")
        return None, None

def extract_author_works(soup: BeautifulSoup) -> List[Dict[str, str]]:
    """Extract all work URLs from the author's page."""
    works = []
    body_content = soup.find('div', {'id': 'bodyContent'})
    
    if not body_content:
        return works
    
    # 1. Find works under mw-heading divs or dl/p elements followed by ul/ol
    elements = body_content.find_all(['div', 'dl', 'p'])
    for element in elements:
        is_heading = element.get('class') and any(c.startswith('mw-heading') for c in element.get('class', []))
        if is_heading or element.name in ['dl', 'p']:
            next_element = element.find_next_sibling()
            if next_element and next_element.name in ['ul', 'ol']:
                for li in next_element.find_all('li'):
                    first_link = li.find('a')  # Get only the first link in each li
                    if first_link and first_link.get('href', '').startswith('/wiki/'):
                        work_url = urljoin('https://el.wikisource.org', first_link['href'])
                        works.append({
                            'title': first_link.get('title', first_link.text.strip()),
                            'url': work_url
                        })
    
    # 2. Find works under p > br structure
    paragraphs = body_content.find_all('p')
    for p in paragraphs:
        if p.find('br'):  # Only process paragraphs containing br tags
            for link in p.find_all('a'):
                if link.get('href', '').startswith('/wiki/'):
                    work_url = urljoin('https://el.wikisource.org', link['href'])
                    works.append({
                        'title': link.get('title', link.text.strip()),
                        'url': work_url
                    })
    
    return works

def visit_author_page(url: str, author_name: str) -> Optional[dict]:
    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:132.0) Gecko/20100101 Firefox/132.0'
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        authorbox = soup.find('table', class_='authorbox')
        if authorbox:
            main_cell = authorbox.find('td', class_='authormain')
            if main_cell:
                name = main_cell.find('strong').text.strip() if main_cell.find('strong') else author_name
                year = main_cell.find('span').text.strip() if main_cell.find('span') else ''
                author_name = name
                author_year = year
        
        works = extract_author_works(soup)
        
        return {
            'url': url,
            'author': author_name,
            'author_year': author_year,
            'works': works
        }
        
    except Exception as e:
        print(f"Error visiting author page {url}: {str(e)}")
        return None

def create_works_dataframe(all_works_data: List[Dict]) -> pd.DataFrame:
    """Create a DataFrame from the collected works URLs."""
    rows = []
    for work_data in all_works_data:
        for work in work_data['works']:
            rows.append({
                'author': work_data['author'],
                'author_year': work_data.get('author_year', ''),
                'title': work['title'],
                'url': work['url']
            })
    
    return pd.DataFrame(rows)

def main(limit_authors: bool = False, max_authors: int = 10):
    start_url = 'https://el.wikisource.org/wiki/Κατηγορία:Συγγραφείς'
    current_url = start_url
    page_number = 1
    authors_processed = 0
    all_works_data = []
    
    while current_url:
        print(f"\nProcessing page {page_number}")
        print(f"URL: {current_url}")
        
        authors, next_page = get_authors_from_page(current_url)
        
        if authors:
            print(f"Number of authors on this page: {len(authors)}")
            
            for author in authors:
                if limit_authors and authors_processed >= max_authors:
                    print(f"\nReached limit of {max_authors} authors")
                    break
                
                print(f"\nVisiting author: {author['name']}")
                result = visit_author_page(author['url'], author['name'])
                if result:
                    print(f"Found {len(result['works'])} works for {author['name']}")
                    all_works_data.append(result)
                
                authors_processed += 1
                time.sleep(0.5)
            
            if limit_authors and authors_processed >= max_authors:
                break
        
        if not next_page:
            print("No more pages to process")
            break
            
        current_url = next_page
        page_number += 1
        time.sleep(0.2)
    
    if all_works_data:
        df = create_works_dataframe(all_works_data)
        output_file = "wikisource_urls.parquet"
        df.to_parquet(output_file, index=False)
        print(f"\nSaved {len(df)} URLs to {output_file}")
        print("\nDataFrame Preview:")
        print(df.head())
        print("\nDataFrame Info:")
        print(df.info())

if __name__ == "__main__":
    main(limit_authors=False, max_authors=10)