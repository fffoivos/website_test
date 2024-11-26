import requests
from bs4 import BeautifulSoup
from loguru import logger
import json
from pathlib import Path
import time
import re
import pandas as pd
from urllib.parse import urljoin

class WikisourceScraper:
    def __init__(self):
        self.base_url = "https://el.wikisource.org"
        self.authors_url = f"{self.base_url}/wiki/Κατηγορία:Συγγραφείς"
        self.setup_logging()
        self.data_dir = Path("scraped_data")
        self.data_dir.mkdir(exist_ok=True)
        
        # Create subdirectories for different types of data
        self.authors_dir = self.data_dir / "authors"
        self.works_dir = self.data_dir / "works"
        self.texts_dir = self.data_dir / "texts"
        self.authors_dir.mkdir(exist_ok=True)
        self.works_dir.mkdir(exist_ok=True)
        self.texts_dir.mkdir(exist_ok=True)
        
        # Initialize session with proper encoding and retry strategy
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        # Rate limiting settings
        self.request_delay = 0.5  # seconds between requests
        self.last_request_time = 0
        self.max_retries = 3
        self.retry_delay = 5
        
        # Initialize corpus data
        self.corpus_data = {
            'author': [],
            'author_year': [],  # Combined birth-death years
            'translator': [],  # Moved next to author_year
            'title': [],
            'text': [],
            'url': [],
            'year': [],
            'publication_info': [],
            'section': []
        }

    def setup_logging(self):
        logger.add("scraper.log", rotation="100 MB", level="INFO")

    def make_request(self, url, method='get', **kwargs):
        """Make a rate-limited request with retries"""
        # Ensure we wait between requests
        time_since_last = time.time() - self.last_request_time
        if time_since_last < self.request_delay:
            time.sleep(self.request_delay - time_since_last)
        
        for attempt in range(self.max_retries):
            try:
                if method.lower() == 'get':
                    response = self.session.get(url, **kwargs)
                else:
                    response = self.session.post(url, **kwargs)
                
                response.raise_for_status()
                self.last_request_time = time.time()
                return response
                
            except requests.exceptions.RequestException as e:
                if attempt == self.max_retries - 1:
                    raise
                logger.warning(f"Request failed (attempt {attempt + 1}/{self.max_retries}): {str(e)}")
                time.sleep(self.retry_delay * (attempt + 1))
        
        raise Exception(f"Failed to make request to {url} after {self.max_retries} attempts")

    def get_authors_list(self, limit=20):
        """Get authors from the mw-pages section where they are listed alphabetically"""
        try:
            logger.info(f"Accessing authors page: {self.authors_url}")
            response = self.make_request(self.authors_url)
            
            # Store the page HTML for analysis
            with open(self.data_dir / "authors_page.html", "w", encoding="utf-8") as f:
                f.write(response.text)
            
            soup = BeautifulSoup(response.text, 'html.parser')
            authors = []
            
            # Find the mw-category-group divs which contain the author links
            category_groups = soup.find_all('div', class_='mw-category-group')
            
            for group in category_groups:
                # Get all links in this group
                links = group.find_all('a')
                for link in links:
                    if len(authors) >= limit:
                        break
                        
                    author_name = link.text.strip()
                    if author_name.startswith('Συγγραφέας:'):
                        author_url = urljoin(self.base_url, link.get('href', ''))
                        if author_name and author_url:
                            authors.append({
                                'name': author_name.replace('Συγγραφέας:', '').strip(),
                                'url': author_url
                            })
                            logger.info(f"Found author: {author_name}")
                
                if len(authors) >= limit:
                    break
            
            return authors
            
        except Exception as e:
            logger.error(f"Error getting authors list: {str(e)}")
            return []

    def extract_author_lifespan(self, soup):
        """Extract author's birth and death years from the page."""
        try:
            author_info = soup.find('td', class_='authormain')
            if author_info:
                lifespan = author_info.find('span', itemprop='disambiguatingDescription')
                if lifespan:
                    years_text = lifespan.text.strip('()')
                    return years_text if years_text else None
            return None
        except Exception as e:
            logger.error(f"Error extracting author lifespan: {str(e)}")
            return None

    def extract_translator(self, soup):
        """Extract translator information from the work page."""
        try:
            # First try to find translator in header_title
            header = soup.find('td', class_='header_title')
            if header:
                translator_span = header.find('span', id='ws-translator')
                if translator_span:
                    return translator_span.text.strip()
                
                # Try to find translator in italicized text
                for i in header.find_all('i'):
                    text = i.text.strip()
                    if 'Μεταφραστής:' in text:
                        translator = text.replace('Μεταφραστής:', '').strip()
                        return translator
            
            # Fallback to content search if not found in header
            content = soup.find('div', class_='mw-parser-output')
            if content:
                translator_patterns = [
                    r'μετάφραση(?:\s+(?:από|του|της|των))?\s+([^,\.]+)',
                    r'μτφρ\.\s+([^,\.]+)',
                    r'μεταφραστής?:?\s+([^,\.]+)',
                    r'translated by\s+([^,\.]+)'
                ]
                
                text = content.get_text()
                for pattern in translator_patterns:
                    match = re.search(pattern, text, re.IGNORECASE | re.UNICODE)
                    if match:
                        return match.group(1).strip()
            
            return None
        except Exception as e:
            logger.error(f"Error extracting translator: {str(e)}")
            return None

    def analyze_html_structure(self, soup, author_name):
        """Analyze the HTML structure of an author's page."""
        try:
            logger.info(f"Analyzing HTML structure for {author_name}")
            works = []
            current_section = None
            
            # Extract author's years
            author_years = self.extract_author_lifespan(soup)
            
            # Initialize author data
            author_data = {
                'name': author_name,
                'years': author_years,
                'works': works
            }
            
            # Find the main content div
            content_div = soup.find('div', class_='mw-parser-output')
            if not content_div:
                logger.error(f"Could not find main content for {author_name}")
                return None

            # Find all sections by looking for headings
            sections = []
            current_section = {'title': 'Main', 'works': []}
            
            for element in content_div.children:
                # Check if this is a heading
                if element.name in ['h2', 'h3', 'h4']:
                    # If we have works in the current section, save it
                    if current_section['works']:
                        sections.append(current_section)
                    # Start a new section
                    current_section = {
                        'title': element.get_text(strip=True),
                        'level': int(element.name[1]),
                        'works': []
                    }
                # If it's a UL element, process its works
                elif element.name == 'ul':
                    # Skip ULs that contain external links or references
                    if any(li.find('a', {'class': 'external'}) for li in element.find_all('li')):
                        continue
                    
                    # Skip ULs that contain database references
                    if any(text in li.text for li in element.find_all('li') 
                          for text in ['VIAF:', 'WorldCat', 'LCCN:', 'ISNI:', 'BNF:', 'GND:']):
                        continue

                    for li in element.find_all('li', recursive=False):
                        # Get all links in this li element
                        links = li.find_all('a')
                        if links:
                            # Only consider the first link as the main work link
                            main_link = links[0]
                            href = main_link.get('href', '')
                            
                            # Skip certain types of links
                            if any(x in href for x in ['Special:', 'w:', 'commons:', 'wikt:', 'edit', 'redlink', 
                                                     'action=', 'index.php', 'Category:', 'File:', 'Αρχείο:']):
                                continue
                                
                            # Extract year and other metadata
                            text = li.text.strip()
                            
                            # Try different year patterns
                            year = None
                            year_patterns = [
                                r'\((\d{4})\)',  # Standard (YYYY)
                                r'(\d{4})',      # Just YYYY
                                r'(\d{4})-\d{4}',  # YYYY-YYYY (take first)
                                r'\d{4}-(\d{4})',  # YYYY-YYYY (take second)
                            ]
                            
                            for pattern in year_patterns:
                                match = re.search(pattern, text)
                                if match:
                                    try:
                                        year = int(match.group(1))
                                        if 1000 <= year <= 2100:  # Sanity check
                                            break
                                    except ValueError:
                                        continue
                            
                            # Extract publication info if present
                            pub_info = None
                            if ',' in text and text.count(',') >= 2:
                                pub_info = ','.join(text.split(',')[1:]).strip()
                            
                            work = {
                                'text': text,
                                'link_text': main_link.text.strip(),
                                'href': href,
                                'year': year,
                                'publication_info': pub_info,
                                'section': current_section['title'],
                                'url': urljoin(self.base_url, href),
                                'title': main_link.text.strip()
                            }
                            current_section['works'].append(work)

            # Add the last section if it has works
            if current_section['works']:
                sections.append(current_section)

            # Convert sections to the old format for compatibility
            works_uls = []
            for section in sections:
                if section['works']:
                    works_uls.append({
                        'index': len(works_uls),
                        'section': section['title'],
                        'items': section['works'],
                        'years': author_years  # Add author years
                    })

            return works_uls
        except Exception as e:
            logger.error(f"Error analyzing HTML structure: {str(e)}")
            return None

    def extract_work_text(self, work_url, author_name, work_title):
        """Extract the text content of a work."""
        try:
            logger.info(f"Extracting text from {work_url}")
            response = self.make_request(work_url)
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find the main content div
            content_div = soup.find('div', class_='mw-parser-output')
            if not content_div:
                logger.error(f"Could not find main content for work: {work_title}")
                return None

            # Save the raw HTML for inspection
            debug_html_path = self.data_dir / "debug_html"
            debug_html_path.mkdir(exist_ok=True)
            safe_title = "".join(c for c in work_title if c.isalnum() or c in (' ', '-', '_'))
            with open(debug_html_path / f"{safe_title}_raw.html", 'w', encoding='utf-8') as f:
                f.write(response.text)

            # Check if this is a navigation/index page
            links = content_div.find_all('a')
            content_links = [link for link in links if link.get('href') 
                           and not any(x in link['href'] for x in 
                                     ['Special:', 'w:', 'commons:', 'wikt:', 'edit', 'redlink', 
                                      'action=', 'index.php', 'Category:', 'File:', 'Αρχείο:'])
                           and not link.find_parent('div', class_=['noprint', 'navigation-not-searchable'])]

            # If we find multiple content links and very little text, this might be a navigation page
            text_content = content_div.get_text(strip=True)
            if len(content_links) > 3 and len(text_content) < 1000:
                logger.info(f"This appears to be a navigation page: {work_url}")
                return None  # We'll skip this and let the individual pages be processed separately
                
            # Remove unwanted elements
            for unwanted in content_div.find_all(['table', 'sup', 'div.noprint', 'div.navigation-not-searchable',
                                                'div.mw-editsection', 'div.mw-references-wrap', 'div.reflist',
                                                'div.references', 'div.navigation']):
                unwanted.decompose()
                
            # Get all text content sections
            text_sections = []
            
            # First look for the main text content
            main_content_elements = []
            
            # Look for poem sections first
            poem_sections = content_div.find_all('div', class_='poem')
            if poem_sections:
                main_content_elements.extend(poem_sections)
                logger.info(f"Found {len(poem_sections)} poem sections")
            
            # Look for paragraphs that are likely to contain the main text
            paragraphs = content_div.find_all('p')
            for p in paragraphs:
                # Skip if paragraph is too short (less than 10 chars) or contains mostly links
                if len(p.get_text(strip=True)) < 10:
                    continue
                    
                # Skip if paragraph has certain classes or parents
                if (p.get('class') and any(cls in ['noprint', 'mw-empty-elt'] for cls in p.get('class', []))) or \
                   any(parent.get('class') and any(cls in ['noprint', 'navigation-not-searchable', 'mw-references-wrap'] 
                                                 for cls in parent.get('class', [])) 
                       for parent in p.parents):
                    continue
                
                # Skip if paragraph is inside a poem section
                if any(parent.get('class') and 'poem' in parent.get('class', []) 
                      for parent in p.parents):
                    continue
                    
                main_content_elements.append(p)
            
            logger.info(f"Found {len(main_content_elements)} main content elements")
            
            # Extract text from main content elements
            for element in main_content_elements:
                # If it's a paragraph, add newlines before and after
                if element.name == 'p':
                    text = element.get_text(strip=True, separator=' ')
                    if text:
                        # Add double newlines for paragraph separation
                        text_sections.append(f"\n\n{text}")
                else:
                    # For poems, preserve line breaks
                    text = element.get_text(separator='\n')
                    # Remove extra whitespace but preserve line breaks
                    text = '\n'.join(line.strip() for line in text.split('\n') if line.strip())
                    if text:
                        text_sections.append(f"\n\n{text}\n")
            
            # Combine all text sections
            if text_sections:
                text = ''.join(text_sections)  # Join without extra spaces
                
                # Clean up the text
                text = re.sub(r'\n{3,}', '\n\n', text)  # Replace 3+ newlines with 2
                text = re.sub(r'\s{2,}', ' ', text)     # Replace multiple spaces with one
                text = re.sub(r'»\s*«', '»\n\n«', text) # Add newlines between quote blocks
                text = re.sub(r'»\s*\.', '».\n\n', text) # Add newlines after quote blocks ending with period
                text = re.sub(r'\.\s+([Α-ΩΆΈΉΊΌΎΏΪΫ])', '.\n\n\\1', text) # Add newlines after sentences
                text = re.sub(r'([.;])\s+', '\\1\n\n', text)  # Add newlines after periods and semicolons
                text = re.sub(r'\n{3,}', '\n\n', text)  # Clean up any excess newlines
                
                # Special handling for poem titles
                text = re.sub(r'([Α-ΩΆΈΉΊΌΎΏΪΫ][Α-ΩΆΈΉΊΌΎΏΪΫα-ωάέήίόύώϊϋ\s]+)\n', r'\1\n\n', text)
                
                text = text.strip()  # Remove leading/trailing whitespace
                
                # Only save if we have substantial text
                if len(text) > 200:  # Minimum length threshold
                    # Save raw text to file
                    safe_title = "".join(c for c in work_title if c.isalnum() or c in (' ', '-', '_'))
                    safe_author = "".join(c for c in author_name if c.isalnum() or c in (' ', '-', '_'))
                    text_file = self.texts_dir / f"{safe_author}_{safe_title}.txt"
                    
                    with open(text_file, 'w', encoding='utf-8') as f:
                        f.write(text)
                        
                    logger.info(f"Saved text with length {len(text)} characters")
                    return text
                else:
                    logger.warning(f"Text too short ({len(text)} chars) for {work_title}")
                    return None
            
            logger.warning(f"No text content found for {work_title}")
            return None
            
        except Exception as e:
            logger.error(f"Error extracting text from {work_url}: {str(e)}")
            return None

    def scrape_author_page(self, author_url):
        """Scrape individual author page with text extraction"""
        try:
            logger.info(f"Scraping author page: {author_url}")
            response = self.make_request(author_url)
            
            # Store the raw HTML for analysis
            page_name = author_url.split('/')[-1]
            html_path = self.authors_dir / f"{page_name}.html"
            with open(html_path, "w", encoding="utf-8") as f:
                f.write(response.text)
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Get author info from the page title
            title_heading = soup.find('h1', id='firstHeading')
            if not title_heading:
                logger.error(f"Could not find title for {author_url}")
                return None
                
            author_name = title_heading.text.replace('Συγγραφέας:', '').strip()
            
            # Analyze HTML structure to find works
            works_uls = self.analyze_html_structure(soup, author_name)
            if not works_uls:
                logger.warning(f"No work lists found for {author_name}")
                return None

            # Extract works and their texts
            works = []
            for ul_info in works_uls:
                for item in ul_info['items']:
                    work = {
                        'title': item['link_text'],
                        'url': f"{self.base_url}{item['href']}" if not item['href'].startswith('http') else item['href'],
                        'full_text': item['text'],
                        'year': item['year'],
                        'publication_info': item['publication_info'],
                        'section': item['section']
                    }
                    
                    # Extract the work's text content
                    text_content = self.extract_work_text(work['url'], author_name, work['title'])
                    if text_content:
                        work['text_content'] = text_content
                        # Add to corpus data
                        self.corpus_data['author'].append(author_name)
                        self.corpus_data['author_year'].append(works_uls[0]['years'])
                        self.corpus_data['title'].append(work['title'])
                        self.corpus_data['text'].append(text_content)
                        self.corpus_data['url'].append(work['url'])
                        self.corpus_data['year'].append(work['year'])
                        self.corpus_data['publication_info'].append(work['publication_info'])
                        self.corpus_data['section'].append(work['section'])
                        
                        # Extract translator from the work's page
                        response = self.make_request(work['url'])
                        work_soup = BeautifulSoup(response.text, 'html.parser')
                        translator = self.extract_translator(work_soup)
                        self.corpus_data['translator'].append(translator)
                    
                    # Only add if we don't already have this work (by URL)
                    if not any(w['url'] == work['url'] for w in works):
                        works.append(work)

            author_data = {
                'name': author_name,
                'url': author_url,
                'works': works,
                'works_count': len(works)
            }
            
            # Save author data
            with open(self.authors_dir / f"{page_name}.json", 'w', encoding='utf-8') as f:
                json.dump(author_data, f, ensure_ascii=False, indent=2)
            
            return author_data
            
        except Exception as e:
            logger.error(f"Error scraping author page: {str(e)}")
            return None

    def save_corpus(self):
        """Save the corpus data to CSV and Excel files"""
        df = pd.DataFrame(self.corpus_data)
        
        # Save as CSV with proper encoding
        df.to_csv(self.data_dir / 'corpus.csv', index=False, encoding='utf-8-sig')
        
        # Save as Excel
        df.to_excel(self.data_dir / 'corpus.xlsx', index=False)
        
        logger.info(f"Saved corpus with {len(df)} entries")

    def run(self):
        """Main execution method"""
        try:
            authors = self.get_authors_list()
            logger.info(f"Found {len(authors)} authors to process")
            
            for author in authors:
                try:
                    author_data = self.scrape_author_page(author['url'])
                    if author_data:
                        logger.info(f"Successfully scraped author: {author_data['name']}")
                        logger.info(f"Found {len(author_data['works'])} works")
                except Exception as e:
                    logger.error(f"Error processing author {author['name']}: {str(e)}")
                    continue
                    
            self.save_corpus()
                
        except Exception as e:
            logger.error(f"Error in main execution: {str(e)}")
            raise

if __name__ == "__main__":
    scraper = WikisourceScraper()
    scraper.run()
