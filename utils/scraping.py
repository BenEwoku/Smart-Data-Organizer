"""
Enhanced Web Scraping Utilities - Ultra-Robust Version
Tries multiple strategies to extract data from ANY website
"""

import pandas as pd
import requests
from bs4 import BeautifulSoup
import time
import re
from io import StringIO
import json

def scrape_url(url, timeout=30, use_selenium=False):
    """
    ULTRA-ROBUST scraper with split data detection
    """
    print(f"Starting scrape of: {url}")
    
    # Strategy 0: Try to detect split data scenario first
    if not use_selenium:
        response = requests.get(url, timeout=timeout)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        split_indicators = detect_split_data_scenario(soup)
        if split_indicators:
            print(f"Detected potential split data: {split_indicators}")
            # Try specialized extraction for split data
            df = extract_with_split_awareness(soup)
            if df is not None:
                print("Success with split-aware extraction!")
                return df
    
    # Continue with original strategies...
    # [Rest of your existing code remains the same]
    
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
    
    # 3. Last resort: Full text analysis
    text = soup.get_text()
    df = parse_text_to_dataframe(text)
    return df

def try_requests_strategies(url, timeout):
    """Try multiple request strategies with different user agents and headers"""
    
    # List of user agents to try
    user_agents = [
        # Chrome on Windows
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        # Firefox on Windows
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
        # Safari on Mac
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
        # Mobile Chrome
        'Mozilla/5.0 (Linux; Android 10; SM-G973F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36',
        # Googlebot (sometimes sites show full content to bots)
        'Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)',
    ]
    
    for i, ua in enumerate(user_agents):
        print(f"  Trying user agent {i+1}/{len(user_agents)}...")
        
        headers = {
            'User-Agent': ua,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0',
        }
        
        try:
            # Try with SSL verification
            response = requests.get(url, headers=headers, timeout=timeout, allow_redirects=True)
            response.raise_for_status()
            
            df = extract_all_methods(response.content)
            if df is not None:
                return df
                
        except requests.exceptions.SSLError:
            print("    SSL error, retrying without verification...")
            try:
                # Retry without SSL verification
                response = requests.get(url, headers=headers, timeout=timeout, 
                                      allow_redirects=True, verify=False)
                response.raise_for_status()
                
                df = extract_all_methods(response.content)
                if df is not None:
                    return df
            except:
                continue
                
        except Exception as e:
            print(f"    Failed: {str(e)[:50]}")
            continue
    
    return None

def extract_all_methods(html_content):
    """Try ALL extraction methods on HTML content"""
    soup = BeautifulSoup(html_content, 'html.parser')
    
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
    
    # Method 7: Text extraction as last resort
    df = extract_text_aggressive(soup)
    if df is not None:
        print("Found data in text content")
        return df
    
    return None

def extract_tables_aggressive(soup):
    """Extract ALL tables with aggressive scoring - IMPROVED FOR SPLIT DATA"""
    tables = soup.find_all('table')
    
    if not tables:
        # Try non-table structured data
        return extract_structured_data_combined(soup)
    
    best_df = None
    best_score = 0
    extracted_tables = []  # Store all found tables
    
    for table in tables:
        try:
            # Try pandas first (fastest)
            dfs = pd.read_html(StringIO(str(table)))
            if dfs and len(dfs) > 0:
                df = dfs[0]
                
                # Clean the dataframe
                df = clean_dataframe(df)
                
                if df is not None and len(df) > 0:
                    # Score based on data quality
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
    
    # NEW: Check for split data scenarios
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
    tables = [t[0] for t in tables_with_scores]  # Extract just the DataFrames
    
    if len(tables) < 2:
        return None
    
    # Try different combination strategies
    for i, df1 in enumerate(tables):
        for j, df2 in enumerate(tables):
            if i == j:
                continue
            
            # Strategy 1: Same number of rows = likely split data
            if len(df1) == len(df2):
                # Check if they have different columns (complementary)
                common_cols = set(df1.columns) & set(df2.columns)
                if len(common_cols) == 0:
                    # They don't share columns, good candidates for merging
                    combined = pd.concat([df1, df2], axis=1)
                    
                    # Validate the combined result
                    if validate_combined_data(combined):
                        return combined
            
            # Strategy 2: One table has names, other has numbers
            if has_textual_data(df1) and has_numerical_data(df2):
                if len(df1) == len(df2):
                    combined = pd.concat([df1, df2], axis=1)
                    if validate_combined_data(combined):
                        return combined
    
    return None

def has_textual_data(df):
    """Check if DataFrame contains mostly text data"""
    if len(df) == 0:
        return False
    
    text_columns = 0
    for col in df.columns:
        try:
            # Check if column contains strings or mixed data
            sample = df[col].dropna().head(10)
            if len(sample) > 0:
                # Check if any value looks like text (not purely numeric)
                text_ratio = sum(isinstance(val, str) for val in sample) / len(sample)
                if text_ratio > 0.5:
                    text_columns += 1
        except:
            continue
    
    return text_columns / max(1, len(df.columns)) > 0.3

def has_numerical_data(df):
    """Check if DataFrame contains mostly numerical data"""
    if len(df) == 0:
        return False
    
    num_columns = 0
    for col in df.columns:
        try:
            # Try to convert to numeric
            numeric_vals = pd.to_numeric(df[col], errors='coerce')
            numeric_ratio = numeric_vals.notna().sum() / len(df)
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
    
    # Check for reasonable row count (not too small/large)
    if len(df) < 2 or len(df) > 10000:
        return False
    
    return True

def extract_structured_data_combined(soup):
    """Extract structured data that might not be in tables"""
    data_fragments = []
    
    # Strategy 1: Lists that might be column headers or data
    lists = soup.find_all(['ul', 'ol', 'dl'])
    for list_elem in lists:
        items = [li.get_text(strip=True) for li in list_elem.find_all('li')]
        if 3 <= len(items) <= 50:
            # Could be a data column
            data_fragments.append({
                'type': 'list',
                'data': items,
                'size': len(items)
            })
    
    # Strategy 2: Divs with data attributes
    data_divs = soup.find_all('div', {'data-value': True})
    if data_divs:
        values = [div.get('data-value') for div in data_divs]
        if len(values) >= 3:
            data_fragments.append({
                'type': 'data_attr',
                'data': values,
                'size': len(values)
            })
    
    # Strategy 3: Text blocks with repeating patterns
    text = soup.get_text()
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    
    # Look for patterns that might be data
    patterns = detect_data_patterns(lines)
    for pattern_name, pattern_data in patterns.items():
        if pattern_data:
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
        # Matches: "1 DET Detroit Pistons"
        match = re.match(r'^(\d+)\s+([A-Z]{2,4})\s+(.+)$', line)
        if match:
            patterns['numbered_list'].append({
                'rank': match.group(1),
                'abbrev': match.group(2),
                'name': match.group(3)
            })
    
    # Pattern 2: Key-value pairs
    for line in lines:
        if ':' in line:
            parts = line.split(':', 1)
            if len(parts) == 2:
                patterns['key_value'].append({
                    'key': parts[0].strip(),
                    'value': parts[1].strip()
                })
    
    # Pattern 3: Tabular data without table tags
    for i, line in enumerate(lines):
        # Check if line has consistent spacing/separators
        if re.search(r'\s{2,}', line):  # Multiple spaces
            parts = re.split(r'\s{2,}', line)
            if 2 <= len(parts) <= 10:
                patterns['table_like'].append(parts)
    
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
    
    # Only use fragments with matching size (or truncate to min)
    compatible_fragments = []
    for frag in fragments:
        if frag['size'] >= min_size:
            # Take first min_size items
            if isinstance(frag['data'], list):
                truncated = frag['data'][:min_size]
                compatible_fragments.append({
                    'type': frag['type'],
                    'data': truncated
                })
    
    if len(compatible_fragments) < 2:
        return None
    
    # Try to create DataFrame
    try:
        # Convert each fragment to a column
        columns = {}
        for i, frag in enumerate(compatible_fragments):
            col_name = f"Column_{i+1}"
            if frag['type'] == 'numbered_list':
                # Extract specific parts if available
                if frag['data'] and isinstance(frag['data'][0], dict):
                    # Could create multiple columns
                    if 'name' in frag['data'][0]:
                        columns['Name'] = [item.get('name', '') for item in frag['data']]
                    if 'abbrev' in frag['data'][0]:
                        columns['Abbreviation'] = [item.get('abbrev', '') for item in frag['data']]
            else:
                columns[col_name] = frag['data']
        
        if columns:
            df = pd.DataFrame(columns)
            return clean_dataframe(df)
    except Exception as e:
        print(f"Error combining fragments: {str(e)}")
    
    return None

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
                table_sizes.append(len(rows))
            except:
                continue
        
        # If tables have same or similar sizes
        if len(set(table_sizes)) == 1 and table_sizes[0] > 1:
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
            if 5 <= len(items) <= 100:  # Reasonable size for data
                list_items.extend(items)
        
        if list_items and len(list_items) > 3:
            # Check if list size matches any table size
            for table in tables:
                try:
                    rows = table.find_all('tr')
                    if len(rows) == len(list_items):
                        indicators.append({
                            'type': 'list_and_table',
                            'list_count': len(list_items),
                            'table_rows': len(rows),
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
        if 2 <= len(line) <= 50:
            # Check if looks like header
            words = line.split()
            if all(len(w) <= 15 for w in words):
                if line.isupper() or any(w.isupper() for w in words):
                    header_candidates.append(line)
                elif any(c.isdigit() for c in line):
                    data_candidates.append(line)
    
    if header_candidates and data_candidates:
        indicators.append({
            'type': 'text_data_blocks',
            'headers': len(header_candidates),
            'data_lines': len(data_candidates),
            'confidence': 60
        })
    
    return indicators

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
            
            # Check if it contains array data
            if isinstance(data, list):
                return pd.DataFrame(data)
            elif isinstance(data, dict):
                # Look for arrays in the dict
                for key, value in data.items():
                    if isinstance(value, list) and len(value) > 0:
                        try:
                            return pd.DataFrame(value)
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
        if len(items) >= 3:  # At least 3 items
            data = []
            for item in items:
                text = item.get_text(strip=True)
                if text:
                    # Try to parse as key-value
                    if ':' in text or '=' in text:
                        parts = re.split(r'[:=]', text, 1)
                        if len(parts) == 2:
                            data.append({'Key': parts[0].strip(), 'Value': parts[1].strip()})
                    else:
                        data.append({'Item': text})
            
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
    # Look for repeated patterns of divs
    containers = soup.find_all(['div', 'article', 'section'], class_=re.compile(r'(item|card|row|entry|post|product)'))
    
    if len(containers) >= 3:
        data = []
        
        for container in containers:
            row = {}
            
            # Extract all text from nested elements
            for child in container.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'span', 'div']):
                class_name = ' '.join(child.get('class', []))
                text = child.get_text(strip=True)
                
                if text and len(text) < 200:  # Reasonable length
                    if class_name:
                        col_name = class_name.replace('-', '_').replace(' ', '_')[:30]
                    else:
                        col_name = child.name
                    
                    if col_name not in row:  # Avoid duplicates
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
            # Try to parse as CSV/TSV
            try:
                from utils.parser import parse_text_to_dataframe
                df = parse_text_to_dataframe(text)
                if df is not None and len(df) > 0:
                    return df
            except:
                continue
    
    return None

def extract_code_blocks(soup):
    """Extract data from code blocks"""
    code_blocks = soup.find_all('code')
    
    for block in code_blocks:
        text = block.get_text()
        
        # Look for JSON
        if '{' in text or '[' in text:
            try:
                data = json.loads(text)
                if isinstance(data, list):
                    return pd.DataFrame(data)
                elif isinstance(data, dict):
                    return pd.DataFrame([data])
            except:
                pass
    
    return None

def extract_text_aggressive(soup):
    """Last resort: extract all text and try to structure it"""
    # Get all paragraphs
    paragraphs = soup.find_all('p')
    
    if len(paragraphs) >= 5:
        data = []
        for i, p in enumerate(paragraphs):
            text = p.get_text(strip=True)
            if text:
                data.append({'Paragraph_' + str(i+1): text})
        
        if len(data) >= 5:
            return pd.DataFrame(data)
    
    return None

def try_api_endpoints(url):
    """Try common API endpoint patterns"""
    # Parse the URL
    from urllib.parse import urlparse, urljoin
    
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
    ]
    
    for pattern in api_patterns:
        try:
            if '?' in pattern:
                api_url = url + pattern
            else:
                api_url = urljoin(base_url, pattern)
            
            response = requests.get(api_url, timeout=10)
            if response.status_code == 200:
                # Try JSON
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
                except:
                    pass
                
                # Try CSV
                try:
                    df = pd.read_csv(StringIO(response.text))
                    if len(df) > 0:
                        return df
                except:
                    pass
        except:
            continue
    
    return None

def try_embedded_data(url):
    """Try to find embedded data in page source"""
    try:
        response = requests.get(url, timeout=30)
        html = response.text
        
        # Look for JavaScript variables containing data
        patterns = [
            r'var\s+data\s*=\s*(\[.*?\]);',
            r'const\s+data\s*=\s*(\[.*?\]);',
            r'window\.data\s*=\s*(\[.*?\]);',
            r'data:\s*(\[.*?\])',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, html, re.DOTALL)
            for match in matches:
                try:
                    data = json.loads(match)
                    if isinstance(data, list) and len(data) > 0:
                        return pd.DataFrame(data)
                except:
                    continue
    except:
        pass
    
    return None

def clean_dataframe(df):
    """Clean up extracted dataframe"""
    if df is None or len(df) == 0:
        return None
    
    # Remove completely empty rows
    df = df.dropna(how='all')
    
    # Remove completely empty columns
    df = df.dropna(axis=1, how='all')
    
    # Clean column names
    df.columns = [str(col).strip() for col in df.columns]
    
    # Remove duplicate rows
    df = df.drop_duplicates()
    
    return df if len(df) > 0 else None

def score_dataframe(df):
    """Score dataframe quality"""
    if df is None or len(df) == 0:
        return 0
    
    score = 0
    
    # More rows = better
    score += min(len(df), 50)
    
    # More columns = better (up to a point)
    score += min(len(df.columns) * 5, 30)
    
    # Less missing data = better
    completeness = df.notna().sum().sum() / (len(df) * len(df.columns))
    score += completeness * 20
    
    # Has headers = better
    if not all(str(col).startswith('Unnamed') for col in df.columns):
        score += 10
    
    return score

def scrape_with_selenium(url, timeout):
    """Selenium scraper with aggressive strategies"""
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        driver = webdriver.Chrome(options=options)
        driver.set_page_load_timeout(timeout)
        
        try:
            driver.get(url)
            
            # Wait for body
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Scroll to load lazy content
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            
            # Get page source
            page_source = driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')
            
            # Try all extraction methods
            df = extract_all_methods(page_source.encode())
            
            return df
            
        finally:
            driver.quit()
            
    except ImportError:
        print("Selenium not installed")
        return None
    except Exception as e:
        print(f"Selenium error: {str(e)}")
        return None