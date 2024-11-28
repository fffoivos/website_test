import requests
from bs4 import BeautifulSoup
import time
from typing import Optional, Tuple, List, Dict
from urllib.parse import urljoin
import pandas as pd
from datetime import datetime

def get_authors_from_page(url: str) -> Tuple[Optional[List[dict]], Optional[str]]:
    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:132.0) Gecko/20100101 Firefox/132.0'
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find the mw-pages div
        mw_pages_div = soup.find('div', {'id': 'mw-pages'})
        if not mw_pages_div:
            print(f"Could not find mw-pages div on {url}")
            return None, None
            
        # Find all author links within mw-pages
        # We'll look specifically for links that start with "Συγγραφέας:"
        author_links = []
        for link in mw_pages_div.find_all('a'):
            href = link.get('href', '')
            if 'Συγγραφέας:' in href or 'Συγγραφέας:' in link.text:
                author_links.append({
                    'name': link.text,
                    'url': 'https://el.wikisource.org' + href
                })
        
        # Find the "next page" link if it exists
        next_page = None
        next_page_link = soup.find('a', string='επόμενη σελίδα')
        if next_page_link:
            next_page = 'https://el.wikisource.org' + next_page_link['href']
            
        return author_links, next_page
        
    except Exception as e:
        print(f"Error processing {url}: {str(e)}")
        return None, None

def extract_author_metadata(soup: BeautifulSoup) -> Dict[str, str]:
    """Extract author name and year from the authorbox."""
    metadata = {
        'author_name': None,
        'author_year': None
    }
    
    authorbox = soup.find('table', {'class': 'authorbox'})
    if authorbox:
        # Find author name
        name_element = authorbox.find('strong', {'itemprop': 'name'})
        if name_element:
            metadata['author_name'] = name_element.text.strip()
        
        # Find author year
        year_element = authorbox.find('span', {'itemprop': 'disambiguatingDescription'})
        if year_element:
            metadata['author_year'] = year_element.text.strip()
    
    return metadata

def extract_work_content(url: str) -> Dict[str, str]:
    """Extract the text content and metadata from a work's page."""
    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:132.0) Gecko/20100101 Firefox/132.0'
    }
    
    content = {
        'translator': None,
        'text': None
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Get the main content div
        content_div = soup.find('div', {'class': 'mw-content-ltr mw-parser-output'})
        if not content_div:
            return content
            
        # Extract translator from header template if exists
        header = content_div.find('table', {'id': 'headertemplate'})
        if header:
            header_text = header.get_text()
            if 'Μεταφραστής:' in header_text:
                translator_span = header.find('span', {'id': 'ws-translator'})
                if translator_span:
                    content['translator'] = translator_span.text.strip()
        
        # Extract text content from paragraphs
        paragraphs = content_div.find_all('p', recursive=True)
        text_content = []
        
        for p in paragraphs:
            # Get all text, including text within formatting tags
            paragraph_text = ''
            for element in p.descendants:
                if isinstance(element, str):
                    paragraph_text += element
                elif element.name == 'br':
                    paragraph_text += '\n'
            
            # Clean up the text
            cleaned_text = paragraph_text.strip()
            if cleaned_text:
                text_content.append(cleaned_text)
        
        # Join paragraphs with double newlines for clear separation
        content['text'] = '\n\n'.join(text_content)
        
        return content
        
    except Exception as e:
        print(f"Error processing work at {url}: {str(e)}")
        return content

def extract_author_works(soup: BeautifulSoup) -> List[Dict[str, str]]:
    """Extract works from the author's page."""
    works = []
    body_content = soup.find('div', {'id': 'bodyContent'})
    
    if not body_content:
        return works
    
    # Find all heading divs
    heading_divs = body_content.find_all('div', class_=lambda x: x and x.startswith('mw-heading'))
    
    for heading_div in heading_divs:
        # Get the next sibling element
        next_element = heading_div.find_next_sibling()
        
        # If it's a ul element, process its links
        if next_element and next_element.name == 'ul':
            for li in next_element.find_all('li', recursive=False):
                link = li.find('a')
                if link and link.get('href', '').startswith('/wiki/'):
                    work_url = urljoin('https://el.wikisource.org', link['href'])
                    # Get work content and metadata
                    work_content = extract_work_content(work_url)
                    works.append({
                        'title': link.get('title', link.text.strip()),
                        'url': work_url,
                        'translator': work_content['translator'],
                        'text': work_content['text']
                    })
                    # Reduced delay between requests
                    time.sleep(0.2)
    
    return works

def visit_author_page(url: str) -> Optional[dict]:
    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:132.0) Gecko/20100101 Firefox/132.0'
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract author metadata
        metadata = extract_author_metadata(soup)
        
        # Extract author works
        works = extract_author_works(soup)
        
        return {
            'url': url,
            'status': 'success',
            'metadata': metadata,
            'works': works,
            'content_length': len(response.text)
        }
        
    except Exception as e:
        print(f"Error visiting author page {url}: {str(e)}")
        return None

def print_author_info(author_data: dict):
    """Print formatted author information."""
    metadata = author_data['metadata']
    works = author_data['works']
    
    print("\nAuthor Information:")
    print(f"Name: {metadata['author_name'] or 'Not found'}")
    print(f"Year: {metadata['author_year'] or 'Not found'}")
    
    if works:
        print(f"\nWorks ({len(works)}):")
        for i, work in enumerate(works, 1):
            print(f"{i}. {work['title']}")
            print(f"   URL: {work['url']}")
            print(f"   Translator: {work['translator'] or 'Not found'}")
            print(f"   Text: {work['text'] or 'Not found'}")
    else:
        print("\nNo works found")
    print("-" * 50)

def create_works_dataframe(all_works_data: List[Dict]) -> pd.DataFrame:
    """Create a DataFrame from the collected works data."""
    rows = []
    for work_data in all_works_data:
        author = work_data['metadata']['author_name']
        author_year = work_data['metadata']['author_year']
        
        for work in work_data['works']:
            rows.append({
                'author': author,
                'author_year': author_year,
                'translator': work['translator'],
                'title': work['title'],
                'text': work['text'],
                'url': work['url']
            })
    
    df = pd.DataFrame(rows)
    return df

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
            
            # Process authors on this page
            for author in authors:
                if limit_authors and authors_processed >= max_authors:
                    print(f"\nReached limit of {max_authors} authors")
                    break
                
                print(f"\nVisiting author: {author['name']}")
                result = visit_author_page(author['url'])
                if result:
                    print_author_info(result)
                    all_works_data.append(result)
                
                authors_processed += 1
                time.sleep(1)  # Be nice to the server
            
            if limit_authors and authors_processed >= max_authors:
                break
        
        if not next_page:
            print("No more pages to process")
            break
            
        current_url = next_page
        page_number += 1
        time.sleep(0.2)
    
    # Create DataFrame and save to CSV
    if all_works_data:
        df = create_works_dataframe(all_works_data)
        output_file = "wikisource_corpus.csv"
        df.to_csv(output_file, index=False, encoding='utf-8')
        print(f"\nSaved {len(df)} works to {output_file}\n")
        print("\nDataFrame Preview:")
        print(df.head())
        print("\nDataFrame Info:")
        print(df.info())

if __name__ == "__main__":
    # Example usage with limit
    main(limit_authors=False, max_authors=10)