import requests
import aiohttp
import asyncio
from concurrent.futures import ThreadPoolExecutor
from functools import partial
from bs4 import BeautifulSoup, Comment
from typing import Dict, Optional
from urllib.parse import urljoin, unquote
import os
import itertools
import pandas as pd
import time
import ftfy

def process_links(text: str, base_url: str, visited_urls: set = None, timeout: int = 300) -> str:
    """Process links in the text by either removing them or extracting their content."""
    try:
        # Initialize visited_urls if not provided
        if visited_urls is None:
            visited_urls = set()
        
        # Add depth tracking to prevent excessive recursion
        if len(visited_urls) > 50:  # Limit recursive depth
            print(f"Maximum link depth reached, stopping further link processing")
            return text.strip()
            
        soup = BeautifulSoup(text, 'html.parser')
        
        for link in soup.find_all('a'):
            try:
                href = link.get('href', '')
                link_text = link.get_text().strip()
                
                if href.startswith('/wiki/') or href.startswith(base_url):
                    try:
                        # Resolve relative URL
                        full_url = base_url + href if href.startswith('/') else href
                        
                        # Skip if we've already processed this URL or if it's not text content
                        if full_url in visited_urls or not is_text_content(full_url):
                            replacement = f"\n{link_text}\n"
                            link.replace_with(replacement)
                            continue
                        
                        # Add URL to visited set
                        visited_urls.add(full_url)
                        
                        # First validate the target page structure
                        response = requests.get(full_url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=timeout)
                        response.raise_for_status()
                        target_soup = BeautifulSoup(response.text, 'html.parser')
                        
                        if not validate_page_structure(target_soup):
                            replacement = f"\n{link_text}\n"
                            link.replace_with(replacement)
                            continue
                        
                        content = extract_work_content(full_url, look_for_a_tags=True, is_entry_page=False, visited_urls=visited_urls, timeout=timeout)
                        if content['text']:
                            replacement = f"\n{link_text}\n{content['text']}\n"
                            link.replace_with(replacement)
                            continue
                    except (requests.RequestException, requests.Timeout, RecursionError, MemoryError) as e:
                        print(f"Error processing link: {e}")
                        replacement = f"\n{link_text}\n"
                        link.replace_with(replacement)
                        continue
                
                # For external or failed links, format as title
                replacement = f"\n{link_text}\n"
                link.replace_with(replacement)
                
            except Exception as e:
                print(f"Error processing individual link: {e}")
                continue
        
        # Clean up multiple consecutive line breaks while preserving at least one
        text = str(soup)
        text = '\n'.join(line for line, _ in itertools.groupby(text.splitlines()))
        return text.strip()
        
    except (RecursionError, MemoryError) as e:
        print(f"Critical error in process_links: {e}")
        return text.strip()
    except Exception as e:
        print(f"Unexpected error in process_links: {e}")
        return text.strip()

def validate_page_structure(soup: BeautifulSoup) -> bool:
    """Validate that the page is a valid wikisource page and not an author page."""
    try:
        authorbox = soup.find('table', {'class': 'authorbox'})
        if authorbox:
            return False
        return True
    except Exception as e:
        print(f"Error validating page structure: {e}")
        return False

def sanitize_filename(url: str) -> str:
    """Convert a URL into a readable filename."""
    # Get the last part of the URL and decode URL encoding
    filename = unquote(url.split('/')[-1])
    
    # Replace problematic characters
    filename = filename.replace('_', ' ')
    
    # Add .txt extension if not present
    if not filename.endswith('.txt'):
        filename += '.txt'
        
    return filename

def extract_work_content(url: str, look_for_a_tags: bool = True, is_entry_page: bool = False, visited_urls: set = None, timeout: int = 300) -> Dict[str, Optional[str]]:
    """Extract the text content and metadata from a work's page."""
    content = {
        'translator': None,
        'text': None
    }
    
    try:
        # Initialize visited_urls if not provided
        if visited_urls is None:
            visited_urls = set()
        
        # Add current URL to visited set
        visited_urls.add(url)
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:132.0) Gecko/20100101 Firefox/132.0'
        }
        
        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Only validate non-entry pages
        if not is_entry_page and not validate_page_structure(soup):
            print(f"Skipping {url}: Author page or external link")
            return content
            
        # Get the main content div
        content_div = soup.find('div', {'class': 'mw-content-ltr mw-parser-output'})
        if not content_div:
            return content
            
        # Remove style tags first
        for style in content_div.find_all('style'):
            style.decompose()
            
        # Extract translator from header template if exists and then remove header
        header = content_div.find('table', {'id': 'headertemplate'})
        if header:
            header_text = header.get_text()
            if 'Μεταφραστής:' in header_text:
                translator_span = header.find('span', {'id': 'ws-translator'})
                if translator_span:
                    content['translator'] = translator_span.text.strip()
            header.decompose()
        
        # Remove unwanted elements
        unwanted_elements = [
            ('table', {'class': 'header_notes'}),
            ('div', {'class': ['ws-noexport', 'noprint', 'navigation-not-searchable']}),
            ('span', {'class': 'mw-editsection'}),
            ('sup', {'class': 'reference'}),
            ('ol', {'class': 'references'}),
            ('style', {}),
            ('hr', {})
        ]
        
        for tag, attrs in unwanted_elements:
            for element in content_div.find_all(tag, attrs):
                element.decompose()
        
        # Remove HTML comments
        for comment in content_div.find_all(string=lambda text: isinstance(text, Comment)):
            comment.extract()
        
        def process_element(element):
            if isinstance(element, str):
                return element.strip()
            
            # Special handling for inline formatting tags
            if element.name in ['i', 'b', 'em', 'strong']:
                text = ''.join(process_element(child) for child in element.children)
                next_sibling = element.next_sibling
                
                # If next sibling is text and starts with punctuation
                if isinstance(next_sibling, str) and next_sibling.strip() and next_sibling.strip()[0] in '.,;:!?)]}':
                    # Return just the text, the punctuation itself will add necessary space after
                    return text
                    
                # If it's not followed by punctuation, add space after
                return text + ' '
            
            if element.name == 'dl':
                    parts = []
                    for child in element.children:
                        if child.name == 'dd':  # Only process dd elements
                            text = process_element(child)
                            if text.strip():  # Only add non-empty lines
                                parts.append(text)
                    return '\n'.join(parts) + '\n'  # Join with newlines and add final newline

            if element.name == 'dd':
                text = ''.join(process_element(child) for child in element.children)
                return text.strip()  # Return stripped text, letting dl handle the newlines
            
            # Handle links
            if element.name == 'a':
                if look_for_a_tags:
                    return str(element)
                else:
                    return element.get_text()
            
            # Skip certain elements
            if element.name in ['sup', 'span'] and 'reference' in element.get('class', []):
                return ''
            if element.name == 'span' and any(cls in element.get('class', []) for cls in ['pagenum', 'mw-editsection']):
                return ''
            
            # Handle line breaks
            if element.name == 'br':
                return '\n'
            
            # Handle block elements
            if element.name in ['p', 'div', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                text = ''.join(process_element(child) for child in element.children)
                return f'\n{text}\n' if text.strip() else '\n'
            
            # Handle lists
            if element.name in ['ul', 'ol']:
                items = []
                for li in element.find_all('li', recursive=False):
                    item_text = process_element(li)
                    if item_text:
                        items.append(f"• {item_text}")
                return '\n'.join(items) + '\n\n' if items else ''
            
            # Default: process all children
            return ''.join(process_element(child) for child in element.children)
        
        # Process the content
        processed_text = ''.join(process_element(element) for element in content_div.children)
        
        # Clean up multiple consecutive line breaks while preserving structure
        lines = []
        for line in processed_text.split('\n'):
            stripped = line.strip()
            if stripped:
                lines.append(stripped)
            else:
                lines.append('')
        
        # Join lines and apply ftfy
        content['text'] = '\n'.join(lines).strip()
        content['text'] = ftfy.fix_text(content['text'])
        
        # Process links if required
        if look_for_a_tags and content['text']:
            content['text'] = process_links(content['text'], 'https://el.wikisource.org', visited_urls, timeout)
            content['text'] = content['text'].strip()
            # Apply ftfy one final time after link processing
            content['text'] = ftfy.fix_text(content['text'])
        
        return content
        
    except (requests.RequestException, requests.Timeout) as e:
        print(f"Network error processing URL {url}: {e}")
        return content
    except RecursionError as e:
        print(f"Recursion depth exceeded for URL {url}: {e}")
        return content
    except MemoryError as e:
        print(f"Memory limit exceeded for URL {url}: {e}")
        return content
    except Exception as e:
        print(f"Unexpected error processing URL {url}: {e}")
        return content

def is_text_content(url: str) -> bool:
    """Check if the URL points to text content rather than media files."""
    media_extensions = {
        '.jpg', '.jpeg', '.png', '.gif', '.svg', '.pdf', 
        '.mp3', '.wav', '.ogg', '.mp4', '.webm', '.djvu'
    }
    return not any(url.lower().endswith(ext) for ext in media_extensions)

async def process_url_async(session, semaphore, row, idx, timeout):
    """Process a single URL asynchronously while preserving all original logic."""
    start_time = time.time()
    
    async with semaphore:
        try:
            # Use ThreadPoolExecutor for CPU-bound operations
            loop = asyncio.get_running_loop()
            with ThreadPoolExecutor() as pool:
                content = await loop.run_in_executor(
                    pool,
                    partial(extract_work_content, 
                           row['url'], 
                           look_for_a_tags=True, 
                           is_entry_page=True, 
                           timeout=timeout)
                )
            
            processing_time = time.time() - start_time
            
            return {
                'index': idx,
                'text': content['text'],
                'translator': content['translator'],
                'processing_time': processing_time,
                'error': None,
                **row.to_dict()
            }
            
        except Exception as e:
            print(f"Error processing row {idx + 1}: {e}")
            return {
                'index': idx,
                'text': None,
                'translator': None,
                'processing_time': None,
                'error': str(e),
                **row.to_dict()
            }

async def process_chunk_async(chunk_df, start_idx, semaphore, timeout):
    """Process a chunk of URLs concurrently while managing resources."""
    async with aiohttp.ClientSession() as session:
        tasks = []
        for idx, row in chunk_df.iterrows():
            task = process_url_async(session, semaphore, row, start_idx + idx, timeout)
            tasks.append(task)
        return await asyncio.gather(*tasks)

async def process_urls_async(input_parquet: str, output_parquet: str, progress_csv: str, 
                           limit_authors: bool = False, author_num: int = 10, 
                           timeout: int = 300, chunk_size: int = 50, max_concurrent: int = 10):
    """Asynchronous version of process_urls_from_parquet with preserved functionality."""
    # Read input parquet
    df = pd.read_parquet(input_parquet)
    
    if 'url' not in df.columns:
        raise ValueError("Input parquet must contain 'url' column")
    
    # Handle existing progress
    processed_indices = set()
    results = []
    if os.path.exists(progress_csv):
        progress_df = pd.read_csv(progress_csv)
        processed_indices = set(progress_df['index'].values)
        results = progress_df.to_dict('records')
        print(f"Found existing progress, {len(processed_indices)} entries already processed")
    
    # Apply author limit if requested
    if limit_authors:
        df = df[df.index < author_num]
        print(f"Processing limited set of {author_num} authors")
    else:
        print(f"Processing all {len(df)} authors")
    
    # Filter out already processed rows
    df = df[~df.index.isin(processed_indices)]
    
    # Initialize semaphore for concurrency control
    semaphore = asyncio.Semaphore(max_concurrent)
    
    # Process in chunks to manage memory
    for chunk_start in range(0, len(df), chunk_size):
        chunk_df = df.iloc[chunk_start:chunk_start + chunk_size]
        print(f"Processing chunk {chunk_start//chunk_size + 1}/{(len(df) + chunk_size - 1)//chunk_size}")
        
        chunk_results = await process_chunk_async(chunk_df, chunk_start, semaphore, timeout)
        results.extend(chunk_results)
        
        # Save progress after each chunk
        progress_df = pd.DataFrame(results)
        progress_df.to_csv(progress_csv, index=False)
        
        # Periodic parquet save
        if len(results) % 100 == 0:
            output_df = pd.DataFrame(results)
            output_df.to_parquet(output_parquet)
    
    # Final save
    output_df = pd.DataFrame(results)
    output_df.to_parquet(output_parquet)

if __name__ == "__main__":
    input_parquet = 'wikisource_urls.parquet'  # Path for the input parquet file
    output_parquet = 'wikisource_complete_async.parquet'  # Path for the output parquet file
    progress_csv = 'processing_progress_async.csv'  # Path for incremental progress
    # Set timeout to 5 minutes (300 seconds)
    asyncio.run(process_urls_async(input_parquet, output_parquet, progress_csv, limit_authors=True, author_num=900, timeout=300))