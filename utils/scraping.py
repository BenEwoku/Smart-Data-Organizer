# File: utils/scraping.py
"""
Web scraping utilities for extracting data from URLs
"""

import pandas as pd
import requests
from bs4 import BeautifulSoup
import time

def scrape_url(url, timeout=10):
    """
    Scrape data from a URL and return as DataFrame
    
    Args:
        url: Website URL to scrape
        timeout: Request timeout in seconds
        
    Returns:
        pd.DataFrame or None if scraping fails
    """
    try:
        # Add user agent to avoid being blocked
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # Make request
        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()
        
        # Parse HTML
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Try different extraction methods in order of preference
        
        # Method 1: Extract HTML tables (most structured)
        df = extract_tables(soup)
        if df is not None:
            return df
        
        # Method 2: Extract lists
        df = extract_lists(soup)
        if df is not None:
            return df
        
        # Method 3: Extract structured divs/spans
        df = extract_structured_content(soup)
        if df is not None:
            return df
        
        # Method 4: Fallback - extract all text paragraphs
        df = extract_text_content(soup)
        return df
        
    except requests.exceptions.RequestException as e:
        print(f"Request error: {str(e)}")
        return None
    except Exception as e:
        print(f"Scraping error: {str(e)}")
        return None

def extract_tables(soup):
    """Extract data from HTML tables"""
    try:
        tables = soup.find_all('table')
        
        if not tables:
            return None
        
        # Try to parse the first table with pandas
        dfs = pd.read_html(str(tables[0]))
        
        if dfs and len(dfs) > 0:
            df = dfs[0]
            # Clean column names
            df.columns = df.columns.astype(str).str.strip()
            return df
        
        return None
        
    except:
        return None

def extract_lists(soup):
    """Extract data from HTML lists (ul, ol)"""
    try:
        lists = soup.find_all(['ul', 'ol'])
        
        if not lists:
            return None
        
        # Extract items from first significant list
        items = []
        for lst in lists[:3]:  # Check first 3 lists
            list_items = [li.get_text(strip=True) for li in lst.find_all('li')]
            
            if len(list_items) > 3:  # Must have at least 3 items
                items.extend(list_items)
                break
        
        if items:
            return pd.DataFrame({'Items': items})
        
        return None
        
    except:
        return None

def extract_structured_content(soup):
    """Extract data from structured divs or sections"""
    try:
        # Look for common data container patterns
        containers = soup.find_all(['div', 'section'], class_=lambda x: x and any(
            keyword in x.lower() for keyword in ['data', 'content', 'item', 'row', 'entry']
        ))
        
        if len(containers) < 3:
            return None
        
        # Extract text from containers
        data = []
        for container in containers[:20]:  # Limit to first 20
            text = container.get_text(strip=True)
            if text and len(text) > 10:  # Meaningful content
                data.append({'Content': text})
        
        if len(data) > 2:
            return pd.DataFrame(data)
        
        return None
        
    except:
        return None

def extract_text_content(soup):
    """Fallback: extract paragraphs as last resort"""
    try:
        paragraphs = soup.find_all('p')
        
        if not paragraphs:
            return None
        
        # Extract non-empty paragraphs
        content = []
        for p in paragraphs[:15]:  # Limit to first 15
            text = p.get_text(strip=True)
            if text and len(text) > 20:  # Meaningful content
                content.append({'Content': text})
        
        if len(content) > 2:
            return pd.DataFrame(content)
        
        return None
        
    except:
        return None

def scrape_multiple_pages(base_url, max_pages=5):
    """
    Scrape multiple pages (for pagination)
    
    Args:
        base_url: Base URL pattern
        max_pages: Maximum number of pages to scrape
        
    Returns:
        pd.DataFrame with combined data
    """
    all_data = []
    
    for page_num in range(1, max_pages + 1):
        url = base_url.format(page=page_num)
        df = scrape_url(url)
        
        if df is not None:
            all_data.append(df)
            time.sleep(1)  # Be polite - wait between requests
        else:
            break
    
    if all_data:
        return pd.concat(all_data, ignore_index=True)
    
    return None