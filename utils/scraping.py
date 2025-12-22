"""
Enhanced Web Scraping Utilities - Production Ready Version
Implements anti-detection, split data handling, and robust extraction
"""

import pandas as pd
import requests
from bs4 import BeautifulSoup
import time
import random
import re
from io import StringIO
import json
import warnings
from urllib.parse import urlparse, urljoin
from urllib.robotparser import RobotFileParser
from datetime import datetime
import ssl
import urllib3
from concurrent.futures import ThreadPoolExecutor, as_completed

# Suppress warnings
warnings.filterwarnings('ignore')
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Try to import optional dependencies
try:
    from fake_useragent import UserAgent
    FAKE_USERAGENT_AVAILABLE = True
except ImportError:
    FAKE_USERAGENT_AVAILABLE = False
    print("Warning: fake-useragent not installed. Using static user agents.")

try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import TimeoutException, WebDriverException
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False
    print("Warning: Selenium not installed. JavaScript rendering disabled.")

# Global configuration
SCRAPING_CONFIG = {
    'min_delay': 1.0,
    'max_delay': 4.0,
    'max_retries': 3,
    'timeout': 30,
    'max_workers': 3,
    'respect_robots': True,
    'verify_ssl': True,
    'follow_redirects': True,
    'cache_ttl': 300,  # 5 minutes cache
}

class RateLimiter:
    """Rate limiting and delay management"""
    def __init__(self, min_delay=1.0, max_delay=4.0):
        self.min_delay = min_delay
        self.max_delay = max_delay
        self.last_request_time = 0
        
    def wait(self):
        """Wait between requests to avoid detection"""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.min_delay:
            time.sleep(self.min_delay - elapsed)
        
        # Add random delay
        delay = random.uniform(self.min_delay, self.max_delay)
        time.sleep(delay)
        self.last_request_time = time.time()

class RequestManager:
    """Manages HTTP requests with anti-detection features"""
    
    def __init__(self, rate_limiter=None):
        self.rate_limiter = rate_limiter or RateLimiter()
        self.session = requests.Session()
        self.session.verify = SCRAPING_CONFIG['verify_ssl']
        self.session.max_redirects = 5 if SCRAPING_CONFIG['follow_redirects'] else 0
        
        # Initialize user agent rotation
        if FAKE_USERAGENT_AVAILABLE:
            self.ua = UserAgent()
        else:
            self.ua = None
        
        # Cache for robots.txt
        self.robots_cache = {}
        
    def get_user_agent(self):
        """Get a random user agent"""
        if self.ua:
            return self.ua.random
        else:
            # Fallback static user agents
            user_agents = [
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
                'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1',
            ]
            return random.choice(user_agents)
    
    def check_robots_txt(self, url):
        """Check if URL is allowed by robots.txt"""
        if not SCRAPING_CONFIG['respect_robots']:
            return True
            
        parsed = urlparse(url)
        robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
        
        if robots_url in self.robots_cache:
            rp = self.robots_cache[robots_url]
        else:
            rp = RobotFileParser()
            try:
                rp.set_url(robots_url)
                rp.read()
                self.robots_cache[robots_url] = rp
            except:
                return True  # If can't read robots.txt, assume allowed
        
        return rp.can_fetch('*', url)
    
    def make_request(self, url, method='GET', **kwargs):
        """Make HTTP request with anti-detection features"""
        # Check robots.txt
        if not self.check_robots_txt(url):
            raise Exception(f"URL {url} disallowed by robots.txt")
        
        # Apply rate limiting
        self.rate_limiter.wait()
        
        # Set headers
        headers = kwargs.get('headers', {})
        if 'User-Agent' not in headers:
            headers['User-Agent'] = self.get_user_agent()
        
        # Add common headers to appear more like a browser
        default_headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0',
            'DNT': '1',  # Do Not Track
        }
        
        for key, value in default_headers.items():
            if key not in headers:
                headers[key] = value
        
        kwargs['headers'] = headers
        
        # Add timeout if not specified
        if 'timeout' not in kwargs:
            kwargs['timeout'] = SCRAPING_CONFIG['timeout']
        
        # Set verify SSL
        if 'verify' not in kwargs:
            kwargs['verify'] = SCRAPING_CONFIG['verify_ssl']
        
        # Make request with retries
        for attempt in range(SCRAPING_CONFIG['max_retries']):
            try:
                response = self.session.request(method, url, **kwargs)
                response.raise_for_status()
                return response
                
            except requests.exceptions.SSLError:
                print(f"SSL error on attempt {attempt + 1}, trying without verification...")
                kwargs['verify'] = False
                
            except requests.exceptions.Timeout:
                print(f"Timeout on attempt {attempt + 1}")
                if attempt == SCRAPING_CONFIG['max_retries'] - 1:
                    raise
                time.sleep(2 ** attempt)  # Exponential backoff
                
            except requests.exceptions.ConnectionError:
                print(f"Connection error on attempt {attempt + 1}")
                if attempt == SCRAPING_CONFIG['max_retries'] - 1:
                    raise
                time.sleep(2 ** attempt)
                
            except requests.exceptions.HTTPError as e:
                if e.response.status_code in [403, 429]:  # Forbidden or rate limited
                    print(f"Blocked or rate limited: {e.response.status_code}")
                    if attempt == SCRAPING_CONFIG['max_retries'] - 1:
                        raise
                    # Longer delay for blocking
                    time.sleep(10 * (attempt + 1))
                else:
                    raise
        
        raise Exception(f"Failed to fetch {url} after {SCRAPING_CONFIG['max_retries']} attempts")

def scrape_url(url, timeout=30, use_selenium=False, use_proxies=False):
    """
    Main scraping function with enhanced anti-detection
    """
    print(f"Starting scrape of: {url}")
    
    # Initialize request manager
    request_manager = RequestManager()
    
    try:
        # Strategy 0: Check for split data patterns first
        if not use_selenium:
            response = request_manager.make_request(url)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Clean HTML from ads and scripts
            soup = clean_html_for_scraping(soup)
            
            split_indicators = detect_split_data_scenario(soup)
            if split_indicators:
                print(f"Detected potential split data: {split_indicators}")
                df = extract_with_split_awareness(soup)
                if df is not None:
                    print("Success with split-aware extraction!")
                    return df
        
        # Strategy 1: Try direct extraction with request manager
        if not use_selenium:
            df = try_direct_extraction(url, request_manager)
            if df is not None:
                print("Success with direct extraction!")
                return df
        
        # Strategy 2: Try Selenium for JavaScript-heavy sites
        if use_selenium and SELENIUM_AVAILABLE:
            df = scrape_with_selenium_enhanced(url, timeout)
            if df is not None:
                print("Success with Selenium!")
                return df
        
        # Strategy 3: Try API endpoints
        df = try_api_endpoints(url, request_manager)
        if df is not None:
            print("Success with API endpoint!")
            return df
        
        # Strategy 4: Try embedded JavaScript data
        df = try_embedded_data(url, request_manager)
        if df is not None:
            print("Success with embedded data!")
            return df
        
        print("All strategies failed")
        return None
        
    except Exception as e:
        print(f"Scraping failed with error: {str(e)}")
        return None

def try_direct_extraction(url, request_manager):
    """Try direct extraction methods"""
    response = request_manager.make_request(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    soup = clean_html_for_scraping(soup)
    
    return extract_all_methods(soup, response.content)

def clean_html_for_scraping(soup):
    """Remove ads, scripts, and other clutter from HTML"""
    # Remove script tags
    for script in soup.find_all('script'):
        script.decompose()
    
    # Remove style tags
    for style in soup.find_all('style'):
        style.decompose()
    
    # Remove iframes (usually ads)
    for iframe in soup.find_all('iframe'):
        iframe.decompose()
    
    # Remove noscript tags
    for noscript in soup.find_all('noscript'):
        noscript.decompose()
    
    # Remove common ad containers
    ad_patterns = ['ad-', 'banner', 'promo', 'advertisement', 'ads', 'adslot']
    for element in soup.find_all(['div', 'section', 'aside']):
        classes = element.get('class', [])
        id_attr = element.get('id', '')
        
        # Check if element looks like an ad
        is_ad = False
        if classes:
            for cls in classes:
                if any(pattern in str(cls).lower() for pattern in ad_patterns):
                    is_ad = True
                    break
        
        if any(pattern in str(id_attr).lower() for pattern in ad_patterns):
            is_ad = True
        
        if is_ad:
            element.decompose()
    
    # Remove empty elements
    for element in soup.find_all():
        if len(element.get_text(strip=True)) == 0 and not element.find_all():
            element.decompose()
    
    return soup

def detect_split_data_scenario(soup):
    """Detect if page contains data split across multiple elements"""
    indicators = []
    
    # Check 1: Multiple tables with same row count
    tables = soup.find_all('table')
    if len(tables) >= 2:
        table_sizes = []
        for table in tables:
            try:
                rows = table.find_all('tr')
                # Count only rows with data (not empty)
                data_rows = [r for r in rows if r.get_text(strip=True)]
                table_sizes.append(len(data_rows))
            except:
                continue
        
        # If tables have same or similar sizes
        if table_sizes and len(set(table_sizes)) == 1 and table_sizes[0] > 1:
            indicators.append({
                'type': 'multiple_tables',
                'count': len(tables),
                'row_count': table_sizes[0],
                'confidence': 80
            })
    
    # Check 2: List of names followed by table of numbers
    lists = soup.find_all(['ul', 'ol'])
    if lists and tables:
        list_items = []
        for list_elem in lists:
            items = list_elem.find_all('li')
            if 5 <= len(items) <= 100:
                list_items.extend(items)
        
        if list_items and len(list_items) > 3:
            for table in tables:
                try:
                    rows = table.find_all('tr')
                    data_rows = [r for r in rows if r.get_text(strip=True)]
                    if len(data_rows) == len(list_items):
                        indicators.append({
                            'type': 'list_and_table',
                            'list_count': len(list_items),
                            'table_rows': len(data_rows),
                            'confidence': 70
                        })
                except:
                    continue
    
    # Check 3: Text patterns that look like data headers
    text = soup.get_text()
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    
    # Look for header-like lines (short, uppercase, no numbers)
    header_candidates = []
    data_candidates = []
    
    for line in lines:
        if 2 <= len(line) <= 100:
            words = line.split()
            if all(len(w) <= 20 for w in words):
                if line.isupper() or any(w.isupper() for w in words[:3]):
                    header_candidates.append(line)
                elif any(c.isdigit() for c in line):
                    data_candidates.append(line)
    
    if header_candidates and data_candidates:
        # Check if they might be related by proximity
        indicators.append({
            'type': 'text_data_blocks',
            'headers': len(header_candidates),
            'data_lines': len(data_candidates),
            'confidence': 60
        })
    
    # Check 4: Repeated div patterns that look like data rows
    divs = soup.find_all('div')
    div_classes = {}
    for div in divs:
        classes = div.get('class', [])
        if classes:
            for cls in classes:
                if cls not in div_classes:
                    div_classes[cls] = 0
                div_classes[cls] += 1
    
    # Look for div classes that appear multiple times (potential data rows)
    for cls, count in div_classes.items():
        if 5 <= count <= 100:
            # Check if these divs contain structured data
            matching_divs = soup.find_all('div', class_=cls)
            sample_texts = [d.get_text(strip=True) for d in matching_divs[:5]]
            
            # Check if samples have similar structure
            if len(sample_texts) >= 3 and all(len(t) > 5 for t in sample_texts):
                indicators.append({
                    'type': 'repeated_divs',
                    'class': cls,
                    'count': count,
                    'confidence': 65
                })
    
    return indicators

def extract_with_split_awareness(soup):
    """Specialized extraction for pages with split data"""
    # Try multiple extraction strategies
    
    # 1. Try to find and combine tables
    tables = soup.find_all('table')
    if len(tables) >= 2:
        extracted_dfs = []
        for table in tables:
            try:
                df = pd.read_html(StringIO(str(table)))[0]
                extracted_dfs.append(df)
            except:
                try:
                    df = extract_table_manually(table)
                    if df is not None:
                        extracted_dfs.append(df)
                except:
                    continue
        
        if len(extracted_dfs) >= 2:
            combined = attempt_table_combination(
                [(df, score_dataframe(df)) for df in extracted_dfs]
            )
            if combined is not None:
                return combined
    
    # 2. Try to extract non-table structured data
    df = extract_structured_data_combined(soup)
    if df is not None:
        return df
    
    # 3. Try to extract from text patterns
    text = soup.get_text()
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    
    # Look for tabular data in text
    data_blocks = []
    current_block = []
    
    for line in lines:
        # Check if line looks like tabular data
        if re.search(r'\s{2,}', line) or re.search(r'\d+\s+\d+', line):
            current_block.append(line)
        elif current_block:
            if len(current_block) >= 3:
                data_blocks.append(current_block)
            current_block = []
    
    if current_block and len(current_block) >= 3:
        data_blocks.append(current_block)
    
    if data_blocks:
        # Try to parse the largest block
        data_blocks.sort(key=len, reverse=True)
        for block in data_blocks:
            try:
                # Convert to DataFrame
                rows = []
                for line in block:
                    # Split by multiple spaces
                    parts = re.split(r'\s{2,}', line)
                    if len(parts) >= 2:
                        rows.append(parts)
                
                if len(rows) >= 3:
                    df = pd.DataFrame(rows)
                    df = clean_dataframe(df)
                    if df is not None and len(df) > 0:
                        return df
            except:
                continue
    
    return None

def extract_all_methods(soup, html_content=None):
    """Try ALL extraction methods on HTML content"""
    
    # Method 1: HTML Tables (most reliable)
    df = extract_tables_aggressive(soup)
    if df is not None:
        print("Found data in HTML table")
        return df
    
    # Method 2: JSON-LD structured data
    df = extract_json_ld(soup)
    if df is not None:
        print("Found data in JSON-LD")
        return df
    
    # Method 3: Lists (ul, ol, dl)
    df = extract_lists_aggressive(soup)
    if df is not None:
        print("Found data in lists")
        return df
    
    # Method 4: Divs and structured content
    df = extract_structured_content_aggressive(soup)
    if df is not None:
        print("Found data in structured divs")
        return df
    
    # Method 5: Pre-formatted text
    df = extract_preformatted(soup)
    if df is not None:
        print("Found data in preformatted text")
        return df
    
    # Method 6: Code blocks
    df = extract_code_blocks(soup)
    if df is not None:
        print("Found data in code blocks")
        return df
    
    # Method 7: Try to extract from meta tags
    df = extract_meta_data(soup)
    if df is not None:
        print("Found data in meta tags")
        return df
    
    # Method 8: Text extraction as last resort
    df = extract_text_aggressive(soup)
    if df is not None:
        print("Found data in text content")
        return df
    
    return None

def extract_tables_aggressive(soup):
    """Extract ALL tables with aggressive scoring"""
    tables = soup.find_all('table')
    
    if not tables:
        return None
    
    best_df = None
    best_score = 0
    extracted_tables = []
    
    for table in tables:
        try:
            # Try pandas first (fastest)
            dfs = pd.read_html(StringIO(str(table)))
            if dfs and len(dfs) > 0:
                df = dfs[0]
                df = clean_dataframe(df)
                
                if df is not None and len(df) > 0:
                    score = score_dataframe(df)
                    extracted_tables.append((df, score))
                    
                    if score > best_score:
                        best_score = score
                        best_df = df
        except:
            # Manual extraction if pandas fails
            try:
                df = extract_table_manually(table)
                if df is not None:
                    score = score_dataframe(df)
                    extracted_tables.append((df, score))
                    
                    if score > best_score:
                        best_score = score
                        best_df = df
            except:
                continue
    
    # Check for split data scenarios
    if len(extracted_tables) >= 2:
        combined_df = attempt_table_combination(extracted_tables)
        if combined_df is not None:
            combined_score = score_dataframe(combined_df)
            if combined_score > best_score:
                best_df = combined_df
                best_score = combined_score
    
    return best_df if best_score > 5 else None

def attempt_table_combination(tables_with_scores):
    """Attempt to combine multiple tables that might be split data"""
    tables = [t[0] for t in tables_with_scores]
    
    if len(tables) < 2:
        return None
    
    # Try different combination strategies
    for i, df1 in enumerate(tables):
        for j, df2 in enumerate(tables):
            if i == j:
                continue
            
            # Strategy 1: Same number of rows = likely split data
            if len(df1) == len(df2):
                common_cols = set(df1.columns) & set(df2.columns)
                if len(common_cols) == 0:
                    combined = pd.concat([df1, df2], axis=1)
                    if validate_combined_data(combined):
                        return combined
            
            # Strategy 2: One table has names, other has numbers
            if has_textual_data(df1) and has_numerical_data(df2):
                if len(df1) == len(df2) or len(df1) == len(df2) + 1:  # +1 for header row
                    combined = pd.concat([df1, df2], axis=1)
                    if validate_combined_data(combined):
                        return combined
    
    # Strategy 3: Try to merge by index if DataFrames have different lengths
    # but one might be a subset of the other
    for df1, df2 in [(tables[0], tables[1]), (tables[1], tables[0])]:
        if len(df1) > len(df2) and len(df2) > 0:
            # Try to align by matching column patterns
            df1_text_cols = [col for col in df1.columns if has_textual_data(pd.DataFrame({col: df1[col]}))]
            df2_num_cols = [col for col in df2.columns if has_numerical_data(pd.DataFrame({col: df2[col]}))]
            
            if df1_text_cols and df2_num_cols:
                # Take the first len(df2) rows from df1
                df1_subset = df1.head(len(df2)).reset_index(drop=True)
                df2_reset = df2.reset_index(drop=True)
                
                combined = pd.concat([df1_subset, df2_reset], axis=1)
                if validate_combined_data(combined):
                    return combined
    
    return None

def has_textual_data(df):
    """Check if DataFrame contains mostly text data"""
    if df is None or len(df) == 0:
        return False
    
    text_columns = 0
    sample_size = min(10, len(df))
    
    for col in df.columns:
        try:
            sample = df[col].dropna().head(sample_size)
            if len(sample) > 0:
                text_count = sum(isinstance(val, str) for val in sample)
                if text_count / len(sample) > 0.5:
                    text_columns += 1
        except:
            continue
    
    return text_columns / max(1, len(df.columns)) > 0.3

def has_numerical_data(df):
    """Check if DataFrame contains mostly numerical data"""
    if df is None or len(df) == 0:
        return False
    
    num_columns = 0
    sample_size = min(10, len(df))
    
    for col in df.columns:
        try:
            numeric_vals = pd.to_numeric(df[col].head(sample_size), errors='coerce')
            numeric_ratio = numeric_vals.notna().sum() / sample_size
            if numeric_ratio > 0.5:
                num_columns += 1
        except:
            continue
    
    return num_columns / max(1, len(df.columns)) > 0.3

def validate_combined_data(df):
    """Validate if combined data makes sense"""
    if df is None or len(df) == 0:
        return False
    
    # Check for duplicate column names
    if len(df.columns) != len(set(df.columns)):
        return False
    
    # Check if any column is all NaN
    if df.isna().all().any():
        return False
    
    # Check for reasonable row count
    if len(df) < 2 or len(df) > 10000:
        return False
    
    # Check that we have a mix of text and numeric columns
    text_cols = sum(1 for col in df.columns if has_textual_data(pd.DataFrame({col: df[col].head(10)})))
    num_cols = sum(1 for col in df.columns if has_numerical_data(pd.DataFrame({col: df[col].head(10)})))
    
    # Good combined data should have both text and numbers
    if text_cols > 0 and num_cols > 0:
        return True
    
    return False

def extract_structured_data_combined(soup):
    """Extract structured data that might not be in tables"""
    data_fragments = []
    
    # Strategy 1: Lists that might be column headers or data
    lists = soup.find_all(['ul', 'ol', 'dl'])
    for list_elem in lists:
        items = [li.get_text(strip=True) for li in list_elem.find_all('li')]
        if 3 <= len(items) <= 100:
            data_fragments.append({
                'type': 'list',
                'data': items,
                'size': len(items)
            })
    
    # Strategy 2: Divs with data attributes
    data_divs = soup.find_all(lambda tag: tag.name == 'div' and 
                              any(attr.startswith('data-') for attr in tag.attrs))
    if data_divs:
        values = []
        for div in data_divs:
            for attr, value in div.attrs.items():
                if attr.startswith('data-'):
                    values.append(value)
        
        if len(values) >= 3:
            data_fragments.append({
                'type': 'data_attr',
                'data': values,
                'size': len(values)
            })
    
    # Strategy 3: Text blocks with repeating patterns
    text = soup.get_text()
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    
    patterns = detect_data_patterns(lines)
    for pattern_name, pattern_data in patterns.items():
        if pattern_data and len(pattern_data) >= 3:
            data_fragments.append({
                'type': 'pattern',
                'pattern': pattern_name,
                'data': pattern_data,
                'size': len(pattern_data)
            })
    
    # Try to combine fragments into a DataFrame
    if len(data_fragments) >= 2:
        return combine_data_fragments(data_fragments)
    
    return None

def detect_data_patterns(lines):
    """Detect common data patterns in text"""
    patterns = {
        'numbered_list': [],
        'key_value': [],
        'table_like': []
    }
    
    # Pattern 1: Numbered items (like NBA rankings)
    for line in lines:
        # Matches: "1 DET Detroit Pistons" or "1. Detroit Pistons"
        match = re.match(r'^(\d+)[\.\)]?\s+([A-Z]{2,4})?\s*(.+)$', line)
        if match:
            patterns['numbered_list'].append({
                'rank': match.group(1),
                'abbrev': match.group(2) if match.group(2) else '',
                'name': match.group(3)
            })
    
    # Pattern 2: Key-value pairs
    for line in lines:
        if ':' in line:
            parts = line.split(':', 1)
            if len(parts) == 2 and len(parts[0].strip()) < 50:
                patterns['key_value'].append({
                    'key': parts[0].strip(),
                    'value': parts[1].strip()
                })
    
    # Pattern 3: Tabular data without table tags
    table_like_lines = []
    for line in lines:
        if 20 <= len(line) <= 500:
            # Check for consistent separators
            if re.search(r'\s{2,}', line) or '|' in line or '\t' in line:
                table_like_lines.append(line)
    
    if table_like_lines and len(table_like_lines) >= 3:
        # Try to detect columns
        first_line = table_like_lines[0]
        if '|' in first_line:
            separator = '|'
        elif '\t' in first_line:
            separator = '\t'
        else:
            separator = r'\s{2,}'
        
        rows = []
        for line in table_like_lines:
            parts = re.split(separator, line)
            if 2 <= len(parts) <= 20:
                rows.append([p.strip() for p in parts])
        
        if rows and len(rows) >= 3:
            patterns['table_like'] = rows
    
    return patterns

def combine_data_fragments(fragments):
    """Combine multiple data fragments into a DataFrame"""
    if not fragments:
        return None
    
    # Sort by size (number of rows)
    fragments.sort(key=lambda x: x['size'])
    
    # Find common size
    sizes = [f['size'] for f in fragments]
    min_size = min(sizes)
    max_size = max(sizes)
    
    # Only combine if sizes are similar
    if max_size - min_size > min_size * 0.5:  # More than 50% difference
        return None
    
    # Use the minimum size
    compatible_fragments = []
    for frag in fragments:
        if frag['size'] >= min_size:
            truncated = frag['data'][:min_size]
            compatible_fragments.append({
                'type': frag['type'],
                'data': truncated
            })
    
    if len(compatible_fragments) < 2:
        return None
    
    # Try to create DataFrame
    try:
        columns = {}
        col_index = 1
        
        for frag in compatible_fragments:
            if frag['type'] == 'numbered_list':
                if frag['data'] and isinstance(frag['data'][0], dict):
                    if 'name' in frag['data'][0]:
                        columns['Name'] = [item.get('name', '') for item in frag['data']]
                    if 'abbrev' in frag['data'][0] and any(item.get('abbrev') for item in frag['data']):
                        columns['Abbreviation'] = [item.get('abbrev', '') for item in frag['data']]
                    if 'rank' in frag['data'][0]:
                        columns['Rank'] = [item.get('rank', '') for item in frag['data']]
            elif frag['type'] == 'key_value':
                if frag['data'] and isinstance(frag['data'][0], dict):
                    # This is trickier - key-value pairs need different handling
                    keys = [item.get('key', '') for item in frag['data']]
                    values = [item.get('value', '') for item in frag['data']]
                    
                    # Check if keys look like column headers
                    if len(set(keys)) == 1:  # All same key = likely column values
                        columns[keys[0]] = values
                    else:
                        # Different keys = might be a two-column table
                        columns[f'Column_{col_index}'] = keys
                        columns[f'Column_{col_index+1}'] = values
                        col_index += 2
            else:
                col_name = f'Column_{col_index}'
                columns[col_name] = frag['data']
                col_index += 1
        
        if columns:
            df = pd.DataFrame(columns)
            return clean_dataframe(df)
    except Exception as e:
        print(f"Error combining fragments: {str(e)}")
    
    return None

def extract_table_manually(table):
    """Manually extract table data when pandas fails"""
    rows = []
    
    # Get headers
    headers = []
    header_row = table.find('thead')
    if header_row:
        headers = [th.get_text(strip=True) for th in header_row.find_all(['th', 'td'])]
    else:
        # Try first row as header
        first_row = table.find('tr')
        if first_row:
            headers = [th.get_text(strip=True) for th in first_row.find_all(['th', 'td'])]
    
    # Get data rows
    tbody = table.find('tbody') or table
    for tr in tbody.find_all('tr'):
        # Skip if this was used as header
        if headers and tr == first_row:
            continue
            
        cells = tr.find_all(['td', 'th'])
        if cells:
            row = [cell.get_text(strip=True) for cell in cells]
            if len(row) > 0 and not all(cell == '' for cell in row):
                rows.append(row)
    
    if rows:
        if headers and len(headers) == len(rows[0]):
            return pd.DataFrame(rows, columns=headers)
        else:
            return pd.DataFrame(rows)
    
    return None

def extract_json_ld(soup):
    """Extract structured data from JSON-LD"""
    scripts = soup.find_all('script', type='application/ld+json')
    
    for script in scripts:
        try:
            data = json.loads(script.string)
            
            if isinstance(data, list):
                return pd.DataFrame(data)
            elif isinstance(data, dict):
                for key, value in data.items():
                    if isinstance(value, list) and len(value) > 0:
                        try:
                            return pd.DataFrame(value)
                        except:
                            continue
                
                # If no array found, try to flatten the dict
                try:
                    return pd.DataFrame([data])
                except:
                    continue
        except:
            continue
    
    return None

def extract_lists_aggressive(soup):
    """Extract data from all types of lists"""
    # Try unordered lists
    uls = soup.find_all('ul')
    for ul in uls:
        items = ul.find_all('li')
        if len(items) >= 3:
            data = []
            for item in items:
                text = item.get_text(strip=True)
                if text:
                    if ':' in text or '=' in text:
                        parts = re.split(r'[:=]', text, 1)
                        if len(parts) == 2:
                            data.append({'Key': parts[0].strip(), 'Value': parts[1].strip()})
                    else:
                        data.append({'Item': text})
            
            if len(data) >= 3:
                return pd.DataFrame(data)
    
    # Try ordered lists
    ols = soup.find_all('ol')
    for ol in ols:
        items = ol.find_all('li')
        if len(items) >= 3:
            data = []
            for i, item in enumerate(items):
                text = item.get_text(strip=True)
                if text:
                    data.append({'Rank': i+1, 'Item': text})
            
            if len(data) >= 3:
                return pd.DataFrame(data)
    
    # Try definition lists
    dls = soup.find_all('dl')
    for dl in dls:
        dts = dl.find_all('dt')
        dds = dl.find_all('dd')
        
        if len(dts) >= 3 and len(dts) == len(dds):
            data = []
            for dt, dd in zip(dts, dds):
                key = dt.get_text(strip=True)
                value = dd.get_text(strip=True)
                if key or value:
                    data.append({'Key': key, 'Value': value})
            
            if len(data) >= 3:
                return pd.DataFrame(data)
    
    return None

def extract_structured_content_aggressive(soup):
    """Extract from divs, articles, sections with data attributes"""
    # Look for repeated patterns
    containers = soup.find_all(['div', 'article', 'section', 'tr', 'li'])
    
    if len(containers) >= 3:
        data = []
        
        for container in containers:
            row = {}
            
            # Extract text from key elements
            for child in container.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'span', 'div', 'td']):
                text = child.get_text(strip=True)
                if text and len(text) < 200:
                    # Create column name from element attributes
                    col_name_parts = []
                    
                    if child.get('class'):
                        col_name_parts.extend(child.get('class'))
                    
                    if child.get('id'):
                        col_name_parts.append(child.get('id'))
                    
                    if child.name:
                        col_name_parts.append(child.name)
                    
                    if col_name_parts:
                        col_name = '_'.join(col_name_parts)[:30]
                    else:
                        col_name = f'element_{len(row)}'
                    
                    if col_name not in row:
                        row[col_name] = text
            
            if row:
                data.append(row)
        
        if len(data) >= 3:
            return pd.DataFrame(data)
    
    return None

def extract_preformatted(soup):
    """Extract from <pre> and <code> tags"""
    pres = soup.find_all(['pre', 'code'])
    
    for pre in pres:
        text = pre.get_text()
        if text and len(text) > 50:
            # Try common formats
            for sep in [',', '\t', '|', ';']:
                lines = text.split('\n')
                if len(lines) >= 3:
                    try:
                        # Check if first few lines have consistent separator count
                        sep_counts = [line.count(sep) for line in lines[:5] if line.strip()]
                        if sep_counts and len(set(sep_counts)) == 1:
                            # Try to parse as DataFrame
                            import csv
                            from io import StringIO
                            
                            if sep == '\t':
                                df = pd.read_csv(StringIO(text), sep='\t')
                            else:
                                df = pd.read_csv(StringIO(text), sep=sep)
                            
                            if df is not None and len(df) > 0:
                                return clean_dataframe(df)
                    except:
                        continue
    
    return None

def extract_code_blocks(soup):
    """Extract data from code blocks"""
    code_blocks = soup.find_all('code')
    
    for block in code_blocks:
        text = block.get_text()
        
        # Look for JSON
        text_clean = text.strip()
        if (text_clean.startswith('{') and text_clean.endswith('}')) or \
           (text_clean.startswith('[') and text_clean.endswith(']')):
            try:
                data = json.loads(text_clean)
                if isinstance(data, list):
                    return pd.DataFrame(data)
                elif isinstance(data, dict):
                    return pd.DataFrame([data])
            except:
                pass
    
    return None

def extract_meta_data(soup):
    """Extract data from meta tags"""
    meta_tags = soup.find_all('meta')
    data = {}
    
    for meta in meta_tags:
        name = meta.get('name') or meta.get('property')
        content = meta.get('content')
        
        if name and content:
            data[name] = content
    
    if data:
        return pd.DataFrame([data])
    
    return None

def extract_text_aggressive(soup):
    """Last resort: extract all text and try to structure it"""
    # Get all text elements
    text_elements = []
    
    for tag in ['p', 'div', 'span', 'td', 'li']:
        elements = soup.find_all(tag)
        for elem in elements:
            text = elem.get_text(strip=True)
            if text and 10 <= len(text) <= 500:
                text_elements.append(text)
    
    if len(text_elements) >= 5:
        data = []
        for i, text in enumerate(text_elements[:50]):  # Limit to 50 elements
            data.append({'Text_Block_' + str(i+1): text})
        
        return pd.DataFrame(data)
    
    return None

def try_api_endpoints(url, request_manager):
    """Try common API endpoint patterns"""
    parsed = urlparse(url)
    base_url = f"{parsed.scheme}://{parsed.netloc}"
    
    # Common API patterns
    api_patterns = [
        '/api/data',
        '/api/v1/data',
        '/data.json',
        '/data.csv',
        '/export/csv',
        '/export/json',
        '?format=json',
        '?format=csv',
        '?output=json',
        '?output=csv',
    ]
    
    for pattern in api_patterns:
        try:
            if '?' in pattern:
                api_url = url + pattern
            else:
                api_url = urljoin(base_url, pattern)
            
            response = request_manager.make_request(api_url, timeout=10)
            
            if response.status_code == 200:
                content_type = response.headers.get('Content-Type', '')
                
                # Try JSON
                if 'json' in content_type or 'javascript' in content_type:
                    try:
                        data = response.json()
                        if isinstance(data, list):
                            df = pd.DataFrame(data)
                            if len(df) > 0:
                                return df
                        elif isinstance(data, dict):
                            for value in data.values():
                                if isinstance(value, list):
                                    df = pd.DataFrame(value)
                                    if len(df) > 0:
                                        return df
                            # Try to flatten dict
                            df = pd.DataFrame([data])
                            if len(df) > 0:
                                return df
                    except:
                        pass
                
                # Try CSV
                if 'csv' in content_type or '.csv' in api_url:
                    try:
                        df = pd.read_csv(StringIO(response.text))
                        if len(df) > 0:
                            return df
                    except:
                        pass
                
                # Try HTML (might be an API that returns HTML)
                if 'html' in content_type:
                    try:
                        soup = BeautifulSoup(response.content, 'html.parser')
                        df = extract_tables_aggressive(soup)
                        if df is not None:
                            return df
                    except:
                        pass
                        
        except:
            continue
    
    return None

def try_embedded_data(url, request_manager):
    """Try to find embedded data in page source"""
    try:
        response = request_manager.make_request(url)
        html = response.text
        
        # Look for JavaScript variables containing data
        patterns = [
            r'var\s+data\s*=\s*(\[.*?\])\s*;',
            r'const\s+data\s*=\s*(\[.*?\])\s*;',
            r'let\s+data\s*=\s*(\[.*?\])\s*;',
            r'window\.data\s*=\s*(\[.*?\])\s*;',
            r'data:\s*(\[.*?\])',
            r'"data"\s*:\s*(\[.*?\])',
            r"'data'\s*:\s*(\[.*?\])",
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, html, re.DOTALL)
            for match in matches:
                try:
                    # Clean up the match
                    match_clean = match.strip()
                    if match_clean.endswith(','):
                        match_clean = match_clean[:-1]
                    
                    data = json.loads(match_clean)
                    if isinstance(data, list) and len(data) > 0:
                        return pd.DataFrame(data)
                except:
                    continue
    except:
        pass
    
    return None

def scrape_with_selenium_enhanced(url, timeout):
    """Enhanced Selenium scraper with better anti-detection"""
    if not SELENIUM_AVAILABLE:
        return None
    
    try:
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        # Additional stealth options
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--disable-notifications')
        options.add_argument('--disable-popup-blocking')
        
        # Set user agent
        if FAKE_USERAGENT_AVAILABLE:
            ua = UserAgent()
            user_agent = ua.random
        else:
            user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        
        options.add_argument(f'user-agent={user_agent}')
        
        driver = webdriver.Chrome(options=options)
        driver.set_page_load_timeout(timeout)
        
        # Execute CDP commands to hide automation
        driver.execute_cdp_cmd('Network.setUserAgentOverride', {
            "userAgent": user_agent,
            "platform": "Windows"
        })
        
        driver.execute_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        )
        
        try:
            driver.get(url)
            
            # Wait for page to load
            wait = WebDriverWait(driver, 20)
            wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            
            # Scroll to load lazy content
            scroll_pause_time = 1
            last_height = driver.execute_script("return document.body.scrollHeight")
            
            for _ in range(3):  # Scroll 3 times
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(scroll_pause_time)
                
                new_height = driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    break
                last_height = new_height
            
            # Wait a bit more for dynamic content
            time.sleep(2)
            
            # Get page source
            page_source = driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')
            
            # Clean HTML
            soup = clean_html_for_scraping(soup)
            
            # Try extraction
            df = extract_all_methods(soup, page_source.encode())
            
            return df
            
        finally:
            driver.quit()
            
    except TimeoutException:
        print("Selenium timed out waiting for page to load")
        return None
    except WebDriverException as e:
        print(f"Selenium WebDriver error: {str(e)}")
        return None
    except Exception as e:
        print(f"Selenium error: {str(e)}")
        return None

def clean_dataframe(df):
    """Clean up extracted dataframe"""
    if df is None or len(df) == 0:
        return None
    
    # Make a copy
    df = df.copy()
    
    # Remove completely empty rows
    df = df.dropna(how='all')
    
    # Remove completely empty columns
    df = df.dropna(axis=1, how='all')
    
    # Reset index
    df = df.reset_index(drop=True)
    
    # Clean column names
    new_columns = []
    for i, col in enumerate(df.columns):
        if pd.isna(col) or str(col).strip() == '':
            new_columns.append(f'Column_{i+1}')
        else:
            # Clean the column name
            col_str = str(col).strip()
            # Remove special characters but keep underscores
            col_str = re.sub(r'[^\w\s_]', '', col_str)
            # Replace multiple spaces with single underscore
            col_str = re.sub(r'\s+', '_', col_str)
            # Limit length
            col_str = col_str[:50]
            
            if not col_str:
                col_str = f'Column_{i+1}'
            
            new_columns.append(col_str)
    
    df.columns = new_columns
    
    # Handle duplicate column names
    cols = pd.Series(df.columns)
    for dup in cols[cols.duplicated()].unique():
        dup_indices = [i for i, x in enumerate(cols) if x == dup]
        for idx, i in enumerate(dup_indices):
            if idx > 0:
                cols.iloc[i] = f'{dup}_{idx}'
    
    df.columns = cols
    
    # Remove duplicate rows
    df = df.drop_duplicates()
    
    # Convert object columns to string to avoid categorical issues
    for col in df.columns:
        if df[col].dtype == 'object':
            df[col] = df[col].astype(str)
    
    return df if len(df) > 0 else None

def score_dataframe(df):
    """Score dataframe quality"""
    if df is None or len(df) == 0:
        return 0
    
    score = 0
    
    # More rows = better (up to a point)
    row_score = min(len(df), 100)
    score += row_score * 0.3
    
    # More columns = better (up to a point)
    col_score = min(len(df.columns) * 2, 30)
    score += col_score
    
    # Less missing data = better
    total_cells = len(df) * len(df.columns)
    if total_cells > 0:
        completeness = df.notna().sum().sum() / total_cells
        score += completeness * 30
    
    # Has proper headers = better
    has_named_headers = not any(str(col).startswith('Unnamed') or 
                               str(col).startswith('Column_') or 
                               str(col).isdigit() 
                               for col in df.columns)
    if has_named_headers:
        score += 15
    
    # Mix of data types = better (indicates structured data)
    text_cols = sum(1 for col in df.columns if has_textual_data(pd.DataFrame({col: df[col].head(10)})))
    num_cols = sum(1 for col in df.columns if has_numerical_data(pd.DataFrame({col: df[col].head(10)})))
    
    if text_cols > 0 and num_cols > 0:
        score += 20
    elif text_cols > 0 or num_cols > 0:
        score += 10
    
    return score

# Batch scraping function
def scrape_multiple_urls(urls, use_selenium=False, max_workers=None):
    """Scrape multiple URLs in parallel"""
    if max_workers is None:
        max_workers = SCRAPING_CONFIG['max_workers']
    
    results = {}
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_url = {
            executor.submit(scrape_url, url, SCRAPING_CONFIG['timeout'], use_selenium): url 
            for url in urls
        }
        
        for future in as_completed(future_to_url):
            url = future_to_url[future]
            try:
                df = future.result()
                results[url] = df
                print(f"Completed: {url}")
            except Exception as e:
                results[url] = None
                print(f"Failed {url}: {str(e)}")
    
    return results
