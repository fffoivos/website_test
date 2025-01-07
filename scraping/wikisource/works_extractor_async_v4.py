# works_extractor_async_v4.py

import requests
import aiohttp
import asyncio
from concurrent.futures import ThreadPoolExecutor
from functools import partial
from bs4 import BeautifulSoup, Comment
from typing import Dict, Optional, Tuple
from urllib.parse import urljoin, unquote
import os
import itertools
import pandas as pd
import time
import ftfy
from dataclasses import dataclass
import unicodedata

def strip_accents(text):
    """Remove accents and diacritical marks from text while preserving base characters"""
    if text is None:
        return None
    return ''.join(c for c in unicodedata.normalize('NFD', text)
                  if unicodedata.category(c) != 'Mn')

class DiscoveredWork:
    def __init__(self, author: str, title: str, url: str, author_year: Optional[str] = None, source_url: Optional[str] = None):
        self.author = author
        self.title = title
        self.url = url
        self.author_year = author_year
        self.source_url = source_url  # Track where this work was discovered

class WorkQueueManager:
    def __init__(self, original_df: pd.DataFrame, known_urls: set = None):
        self.original_df = original_df
        # Initialize with both known_urls and original df urls
        self.discovered_urls = set(original_df['url'].values)
        if known_urls:
            self.discovered_urls.update(known_urls)
        self.discovered_df = pd.DataFrame(columns=['author', 'author_year', 'title', 'url', 'source_url', 'is_discovered'])
    
    async def add_work(self, url: str, title: str, author: str, source_url: str = None):
        """Add a work to the discovered DataFrame"""
        if url not in self.discovered_urls:
            self.discovered_urls.add(url)
            # Try to find author_year from original_df if author matches
            author_year = None
            matching_rows = self.original_df[self.original_df['author'] == author]
            if not matching_rows.empty:
                author_year = matching_rows.iloc[0]['author_year']
            
            new_row = pd.DataFrame({
                'author': [author],
                'author_year': [author_year],
                'title': [title],
                'url': [url],
                'source_url': [source_url],
                'is_discovered': [True]
            })
            self.discovered_df = pd.concat([self.discovered_df, new_row], ignore_index=True)
            print(f"\nAdding discovered work: {title} by {author} ({author_year if author_year else 'unknown year'})")
            print("Current discovered_df:")
            print(self.discovered_df)
            return True
        else:
            print(f"Skipping discovered work from {source_url}: URL already processed: {url}")
            return False
            
    async def process_queue(self):
        """Just return the combined dataframe"""
        return pd.concat([self.original_df, self.discovered_df], ignore_index=True)

def is_text_content(url: str) -> bool:
    """Check if the URL points to text content rather than media files."""
    media_extensions = {
        '.jpg', '.jpeg', '.png', '.gif', '.svg', '.pdf', 
        '.mp3', '.wav', '.ogg', '.mp4', '.webm', '.djvu'
    }
    return not any(url.lower().endswith(ext) for ext in media_extensions)

async def process_links(text: str, base_url: str, queue_manager: WorkQueueManager, visited_urls: set = None, timeout: int = 300) -> str:
    """Process links in the text by either removing them or extracting their content."""
    try:
        # Initialize visited_urls if not provided
        if visited_urls is None:
            visited_urls = set()
        
        # Add depth tracking to prevent excessive recursion
        if len(visited_urls) > 50:  # Limit recursive depth
            #print(f"Maximum link depth reached, stopping further link processing")
            return text.strip()

        #Split text into lines and process each line
        lines = text.split('\n')
        processed_lines = []
        
        for line in lines:
            soup = BeautifulSoup(line, 'html.parser')
            
            for link in soup.find_all('a'):
                try:
                    #print(f"Processing link \n")
                    # Skip if link is no longer in the tree (already processed)
                    if not link.parent:
                        continue
                        
                    href = link.get('href', '')
                    link_text = link.get_text().strip()
                    
                    if href.startswith('/wiki/') or href.startswith(base_url):
                        try:
                            # Resolve relative URL
                            full_url = base_url + href if href.startswith('/') else href
                            print(f"found full url {full_url} \n")
                            # Skip if we've already processed this URL or if it's not text content
                            if full_url in visited_urls or not is_text_content(full_url):
                                if link.parent:  # Check if link is still in tree
                                    replacement = f"\n{link_text}\n"
                                    link.replace_with(replacement)
                                print(f"Skipping already processed URL: {full_url}")
                                continue
                            
                            # Add URL to visited set
                            visited_urls.add(full_url)
                            print(f"Adding URL to visited set \n")
                            async with aiohttp.ClientSession() as session:
                                async with session.get(full_url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=timeout) as response:
                                    response.raise_for_status()
                                    html = await response.text()
                                    target_soup = BeautifulSoup(html, 'html.parser')
                            
                            title, author = validate_page_structure(target_soup)
                            if not title:
                                if link.parent:  # Check if link is still in tree
                                    replacement = f"\n{link_text}\n"
                                    link.replace_with(replacement)
                                print(f"Skipping non-work page: {replacement}")
                                continue
                            print("got title and author \n")
                            content = await extract_work_content(full_url, queue_manager=queue_manager, look_for_a_tags=True, is_entry_page=False, visited_urls=visited_urls, timeout=timeout)
                            if content['text']:
                                print("got content ")
                                if line.startswith("• "):
                                    if link.parent:  # Check if link is still in tree
                                        replacement = f"\n{link_text}\n{content['text']}\n"
                                        link.replace_with(replacement)
                                    continue
                                else:
                                    # Add to queue and remove link from text
                                    await queue_manager.add_work(full_url, title, author, source_url=full_url)
                                    if link.parent:  # Check if link is still in tree
                                        replacement = f" {link_text} "
                                        link.replace_with(replacement)
                                    
                        except (aiohttp.ClientError, asyncio.TimeoutError, RecursionError, MemoryError) as e:
                            print(f"Error processing link: {e}")
                            if link.parent:  # Check if link is still in tree
                                replacement = f"\n{link_text}\n"
                                link.replace_with(replacement)
                            continue
                    
                    # For external or failed links, format as title
                    if link.parent:  # Check if link is still in tree
                        replacement = f"\n{link_text}\n"
                        link.replace_with(replacement)
                    
                except Exception as e:
                    print(f"Error processing individual link: {e}")
                    continue
            
            processed_lines.append(str(soup))
        
        # Clean up multiple consecutive line breaks while preserving at least one
        text = '\n'.join(processed_lines)
        text = '\n'.join(line for line, _ in itertools.groupby(text.splitlines()))
        return text.strip()
        
    except (RecursionError, MemoryError) as e:
        print(f"Critical error in process_links: {e}")
        return text.strip()
    except Exception as e:
        print(f"Unexpected error in process_links: {e}")
        return text.strip()

def validate_page_structure(soup: BeautifulSoup) -> Tuple[Optional[str], Optional[str]]:
    """Extract title and author from header template if valid work page."""
    try:
        # Check if header template exists
        header = soup.find('table', {'id': 'headertemplate', 'class': 'headertemplate'})
        if not header:
            #print("Not a valid work page - skipping")
            return None, None
        
        # Find all spans with title and author IDs
        title_author_spans = header.find_all('span', {'id': ['ws-title', 'ws-author']})
        
        # Create dictionary of {type: content} from spans
        spans_dict = {}
        for span in title_author_spans:
            field_type = span['id'].split('-')[1]  # Get 'title' or 'author' from 'ws-title' or 'ws-author'
            content = span.get_text().strip()
            spans_dict[field_type] = content
        
        # Get title and author from spans_dict
        title = spans_dict.get('title')
        author = spans_dict.get('author') if title else None
        
        return title, author
        
    except Exception as e:
        print(f"Error validating page: {e}")
        return None, None        

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

async def extract_work_content(url: str, queue_manager: WorkQueueManager, session=None, look_for_a_tags: bool = True, is_entry_page: bool = False, visited_urls: set = None, timeout: int = 300) -> Dict[str, Optional[str]]:
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
        
        # Create a new session if one wasn't provided
        if session is None:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, timeout=timeout) as response:
                    response.raise_for_status()
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
        else:
            async with session.get(url, headers=headers, timeout=timeout) as response:
                response.raise_for_status()
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
        
        # Only validate non-entry pages
        if not is_entry_page:
            title, author = validate_page_structure(soup)
            if not title:
                #print(f"Skipping {url}: Author page or external link")
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
            content['text'] = await process_links(content['text'], 'https://el.wikisource.org', queue_manager, visited_urls, timeout)
            content['text'] = content['text'].strip()
            # Apply ftfy one final time after link processing
            content['text'] = ftfy.fix_text(content['text'])
        
        return content
        
    except (aiohttp.ClientError, asyncio.TimeoutError) as e:
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

async def process_url_async(session, semaphore, queue_manager, row, idx, timeout):
    """Process a single URL asynchronously while preserving all original logic."""
    start_time = time.time()
    
    async with semaphore:
        try:
            content = await extract_work_content(
                row['url'],
                queue_manager=queue_manager,
                session=session,
                look_for_a_tags=True, 
                is_entry_page=True, 
                timeout=timeout
            )
            
            processing_time = time.time() - start_time
            
            result = {
                'index': idx,
                'text': content['text'],
                'translator': content['translator'],
                'processing_time': processing_time,
                'error': None,
                'is_discovered': row.get('is_discovered', False),  # Track if this is a discovered work
                'source_url': row.get('source_url', None),  # Track source URL
                'status': 'success' if content['text'] else 'skipped',  # Track processing status
                **row.to_dict()
            }
            
            return result
            
        except Exception as e:
            return {
                'index': idx,
                'text': None,
                'translator': None,
                'processing_time': None,
                'error': str(e),
                'is_discovered': row.get('is_discovered', False),
                'source_url': row.get('source_url', None),
                'status': 'error',
                **row.to_dict()
            }

async def process_chunk_async(chunk_df, queue_manager, start_idx, semaphore, timeout):
    """Process a chunk of URLs concurrently while managing resources."""
    async with aiohttp.ClientSession() as session:
        tasks = []
        for idx, row in chunk_df.iterrows():
            task = process_url_async(session, semaphore, queue_manager, row, start_idx + idx, timeout)
            tasks.append(task)
        return await asyncio.gather(*tasks)

async def process_urls_async(input_parquet: str, output_parquet: str, progress_csv: str, 
                          limit_authors: bool = False, author_num: int = 10, 
                          timeout: int = 300, chunk_size: int = 50, max_concurrent: int = 10):
   """Process both original and discovered URLs through the same pipeline."""
   
   # Read input parquet
   df = pd.read_parquet(input_parquet)
   
   if 'url' not in df.columns:
       raise ValueError("Input parquet must contain 'url' column")
   
   # Initialize queue manager
   queue_manager = WorkQueueManager(df)
   
   # Create task for queue processing
   queue_processor = asyncio.create_task(queue_manager.process_queue())
   
   try:
       # Process original URLs
       results = await process_dataset(df, queue_manager, progress_csv, 
                                     limit_authors, author_num, chunk_size, 
                                     max_concurrent, timeout, "original")
       
       # Get discovered URLs that need processing
       discovered_df = queue_manager.discovered_df
       print("discovered_df", discovered_df.empty)
       print(len(discovered_df))
       new_urls_df = discovered_df
       print("new_urls_df", new_urls_df.empty)
       discovered_results = []
       
       if not new_urls_df.empty:
           print(f"\nProcessing {len(new_urls_df)} discovered URLs...")
           # Create new queue manager for discovered URLs with all known URLs
           discovered_queue_manager = WorkQueueManager(new_urls_df, known_urls=queue_manager.discovered_urls)
           discovered_processor = asyncio.create_task(discovered_queue_manager.process_queue())
           
           # Process discovered URLs
           discovered_results = await process_dataset(new_urls_df, discovered_queue_manager,
                                                    progress_csv.replace('.csv', '_discovered.csv'),
                                                    False, None, chunk_size, max_concurrent,
                                                    timeout, "discovered")
           
           # Cancel discovered queue processor
           discovered_processor.cancel()
       
       # Cancel original queue processor
       queue_processor.cancel()

       # Create separate DataFrames first
       results_df = pd.DataFrame(results)
       discovered_df = pd.DataFrame(discovered_results)
       
       print("\nBefore normalization:")
       print(f"Results unique authors: {results_df['author'].nunique()}")
       print(f"Discovered unique authors: {discovered_df['author'].nunique()}")

       # Create normalized versions of author names for matching
       results_df['author_normalized'] = results_df['author'].apply(strip_accents)
       discovered_df['author_normalized'] = discovered_df['author'].apply(strip_accents)
       
       print("\nAfter normalization:")
       print(f"Results unique normalized authors: {results_df['author_normalized'].nunique()}")
       print(f"Discovered unique normalized authors: {discovered_df['author_normalized'].nunique()}")

       # Create author mapping including both the canonical name and year
       author_mapping = results_df[results_df['author_normalized'].isin(
           discovered_df['author_normalized'].unique())][['author_normalized', 'author', 'author_year']].drop_duplicates()
       
       print(f"\nFound {len(author_mapping)} author mappings")
       
       # Create dictionaries for both author name and year
       author_year_dict = dict(zip(author_mapping['author_normalized'], author_mapping['author_year']))
       author_name_dict = dict(zip(author_mapping['author_normalized'], author_mapping['author']))
       
       # Fill both author and author_year in discovered_df using normalized mapping
       discovered_df['author_year'] = discovered_df['author_normalized'].map(author_year_dict)
       discovered_df['author'] = discovered_df['author_normalized'].map(author_name_dict)
       
       # Drop the temporary normalized column
       results_df.drop('author_normalized', axis=1, inplace=True)
       discovered_df.drop('author_normalized', axis=1, inplace=True)
       
       # Combine results
       final_df = pd.concat([results_df, discovered_df], ignore_index=True)
       
       # Initialize missing columns with None values
       if 'author_year' not in final_df.columns:
           final_df['author_year'] = None
           
       # Keep essential columns
       essential_columns = ['author', 'author_year', 'title', 'text', 'url']
       final_df = final_df[essential_columns]
       
       # Save final results
       final_df.to_parquet(output_parquet)
       print(f"\nProcessing complete. Total works:")
       print(final_df[['author', 'author_year', 'title']].head(20))
       
   except Exception as e:
       print(f"Error in main processing: {e}")
       queue_processor.cancel()
       raise

async def process_dataset(df: pd.DataFrame, queue_manager: WorkQueueManager, 
                         progress_csv: str, limit_authors: bool, author_num: int,
                         chunk_size: int, max_concurrent: int, timeout: int,
                         dataset_type: str = "original") -> list:
    """Process a dataset of URLs and return results."""
    
    results = []
    
    # Handle existing progress
    processed_indices = set()
    if os.path.exists(progress_csv):
        progress_df = pd.read_csv(progress_csv)
        processed_indices = set(progress_df['index'].values)
        results = progress_df.to_dict('records')
        print(f"Found existing progress for {dataset_type} dataset, {len(processed_indices)} entries already processed")
    
    # Apply author limit if requested and if processing original dataset
    if limit_authors and dataset_type == "original":
        df = df[df.index < author_num]
        print(f"Processing limited set of {author_num} authors")
    else:
        print(f"Processing all {len(df)} {dataset_type} works")
    
    # Filter out already processed rows
    df = df[~df.index.isin(processed_indices)]
    
    # Initialize semaphore for concurrency control
    semaphore = asyncio.Semaphore(max_concurrent)
    
    # Process in chunks
    for chunk_start in range(0, len(df), chunk_size):
        chunk_df = df.iloc[chunk_start:chunk_start + chunk_size]
        print(f"Processing {dataset_type} chunk {chunk_start//chunk_size + 1}/{(len(df) + chunk_size - 1)//chunk_size}")
        
        chunk_results = await process_chunk_async(chunk_df, queue_manager, chunk_start, semaphore, timeout)
        results.extend(chunk_results)
        
        # Save progress after each chunk
        progress_df = pd.DataFrame(results)
        progress_df.to_csv(progress_csv, index=False)
        
        # Print progress
        success_count = sum(1 for r in results if r['status'] == 'success')
        print(f"{dataset_type.capitalize()} progress: {success_count}/{len(results)} successful")
    
    return results

if __name__ == "__main__":
    input_parquet = 'wikisource_urls.parquet'  # Path for the input parquet file
    output_parquet = 'works_extractor_async_v5.parquet'  # Path for the output parquet file
    progress_csv = 'progress_async_v5.csv'  # Path for incremental progress
    
    asyncio.run(process_urls_async(input_parquet, output_parquet, progress_csv, 
                                  limit_authors=False, author_num=10,
                                  timeout=300, chunk_size=50, max_concurrent=10))