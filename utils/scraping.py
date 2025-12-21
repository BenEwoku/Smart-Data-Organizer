"""
Web scraping utilities for extracting data from URLs
"""

import pandas as pd
import requests
from bs4 import BeautifulSoup
import time
import re
from io import StringIO

def scrape_url(url, timeout=30, use_selenium=False):
    """
    Scrape data from a URL and return as DataFrame
    
    Args:
        url: Website URL to scrape
        timeout: Request timeout in seconds
        use_selenium: Use Selenium for JavaScript-heavy sites (set to True for JS sites)
        
    Returns:
        pd.DataFrame or None if scraping fails
    """
    try:
        if use_selenium:
            return scrape_with_selenium(url, timeout)
        
        # Add user agent to avoid being blocked
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
        # Make request with retry logic
        response = make_request_with_retry(url, headers, timeout)
        if response is None:
            return None
        
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

def make_request_with_retry(url, headers, timeout, max_retries=3):
    """Make HTTP request with retry logic"""
    for attempt in range(max_retries):
        try:
            response = requests.get(url, headers=headers, timeout=timeout)
            response.raise_for_status()
            
            # Check if content looks like HTML
            content_type = response.headers.get('Content-Type', '')
            if 'text/html' not in content_type:
                print(f"Warning: URL doesn't return HTML. Content-Type: {content_type}")
            
            return response
            
        except requests.exceptions.Timeout:
            print(f"Timeout on attempt {attempt + 1} for {url}")
            if attempt == max_retries - 1:
                return None
            time.sleep(2 ** attempt)  # Exponential backoff
            
        except requests.exceptions.HTTPError as e:
            print(f"HTTP error {e.response.status_code} for {url}")
            return None
            
        except requests.exceptions.RequestException as e:
            print(f"Request failed on attempt {attempt + 1}: {str(e)}")
            if attempt == max_retries - 1:
                return None
            time.sleep(2 ** attempt)

def scrape_with_selenium(url, timeout):
    """
    Use Selenium for JavaScript-heavy websites
    
    Note: Requires selenium package and web driver
    pip install selenium
    """
    try:
        from selenium import webdriver
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        from selenium.webdriver.chrome.options import Options
        
        # Configure Chrome options
        chrome_options = Options()
        chrome_options.add_argument('--headless')  # Run in background
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        
        # Initialize driver
        driver = webdriver.Chrome(options=chrome_options)
        driver.set_page_load_timeout(timeout)
        
        try:
            # Load the page
            driver.get(url)
            
            # Wait for page to load
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Give extra time for JavaScript to load content
            time.sleep(3)
            
            # Get page source
            page_source = driver.page_source
            
            # Parse with BeautifulSoup
            soup = BeautifulSoup(page_source, 'html.parser')
            
            # Try to extract tables
            df = extract_tables(soup)
            if df is not None:
                return df
            
            # Try to find data in JavaScript variables
            df = extract_js_data(page_source)
            if df is not None:
                return df
            
            # Fallback to other methods
            df = extract_structured_content(soup)
            if df is not None:
                return df
                
            return extract_text_content(soup)
            
        finally:
            driver.quit()
            
    except ImportError:
        print("Selenium not installed. Install with: pip install selenium")
        return None
    except Exception as e:
        print(f"Selenium scraping error: {str(e)}")
        return None

def extract_js_data(page_source):
    """
    Extract data from JavaScript variables in page source
    """
    try:
        # Look for JSON data in JavaScript
        json_patterns = [
            r'var\s+data\s*=\s*(\{.*?\});',
            r'data\s*:\s*(\{.*?\})',
            r'window\.data\s*=\s*(\{.*?\});',
            r'JSON\.parse\(\s*\'(\{.*?\})\'\s*\)',
        ]
        
        for pattern in json_patterns:
            matches = re.findall(pattern, page_source, re.DOTALL)
            for match in matches:
                try:
                    import json
                    data = json.loads(match)
                    if isinstance(data, list) and len(data) > 0:
                        return pd.DataFrame(data)
                    elif isinstance(data, dict):
                        # Try to find array in dict
                        for key, value in data.items():
                            if isinstance(value, list) and len(value) > 0:
                                return pd.DataFrame(value)
                except:
                    continue
        
        return None
    except:
        return None

# Keep the existing functions but enhance them:
def extract_tables(soup):
    """Extract data from HTML tables with improved detection"""
    try:
        tables = soup.find_all('table')
        
        if not tables:
            return None
        
        best_table = None
        best_score = 0
        
        # Score tables to find the best one
        for table in tables:
            score = score_table(table)
            if score > best_score:
                best_score = score
                best_table = table
        
        if best_table and best_score > 10:  # Minimum threshold
            # Try to parse with pandas
            try:
                dfs = pd.read_html(StringIO(str(best_table)))
                if dfs and len(dfs) > 0:
                    df = dfs[0]
                    # Clean column names
                    df.columns = df.columns.astype(str).str.strip()
                    
                    # Remove empty rows
                    df = df.dropna(how='all')
                    df = df.reset_index(drop=True)
                    
                    return df if len(df) > 0 else None
            except:
                pass
        
        return None
        
    except:
        return None

def score_table(table):
    """Score a table based on structure quality"""
    score = 0
    
    # Check for rows and columns
    rows = table.find_all('tr')
    if len(rows) > 2:
        score += len(rows) * 0.5  # More rows = better
    
    # Check for headers
    headers = table.find_all(['th', 'thead'])
    if headers:
        score += 10
    
    # Check for data cells
    cells = table.find_all(['td', 'th'])
    if len(cells) > 10:
        score += 5
    
    # Check for table classes/id that suggest data
    table_html = str(table)
    data_keywords = ['data', 'table', 'grid', 'list', 'report', 'results']
    for keyword in data_keywords:
        if keyword in table_html.lower():
            score += 2
    
    return score
