import requests
from bs4 import BeautifulSoup
import time
from typing import Optional, Tuple, List, Dict

def get_authors_from_page(url: str) -> Tuple[Optional[List[dict]], Optional[str]]:
    """Extract author names and next page link from a category page."""
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

def main():
    start_url = 'https://el.wikisource.org/wiki/Κατηγορία:Συγγραφείς'
    current_url = start_url
    page_number = 1
    total_authors = 0
    all_authors = []
    
    print("Starting author collection...")
    
    while current_url:
        print(f"\nProcessing page {page_number}")
        print(f"URL: {current_url}")
        
        authors, next_page = get_authors_from_page(current_url)
        
        if authors:
            print(f"Found {len(authors)} authors on this page:")
            for author in authors:
                print(f"- {author['name']}")
                all_authors.append(author)
            total_authors += len(authors)
        else:
            print("No authors found on this page")
            
        if not next_page:
            print("\nNo more pages to process")
            break
            
        current_url = next_page
        page_number += 1
        time.sleep(0.5)  # Be nice to the server
    
    print(f"\nCollection complete!")
    print(f"Total pages processed: {page_number}")
    print(f"Total authors found: {total_authors}")
    
    # Save results to a file
    with open('wikisource_authors.txt', 'w', encoding='utf-8') as f:
        for author in all_authors:
            f.write(f"{author['name']}\t{author['url']}\n")
    
    print(f"\nResults saved to 'wikisource_authors.txt'")

if __name__ == "__main__":
    main()