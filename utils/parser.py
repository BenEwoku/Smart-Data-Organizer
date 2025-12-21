# File: utils/parser.py
"""
Text parsing utilities for converting unstructured text to DataFrames
"""

import pandas as pd
import re
from io import StringIO

def detect_delimiter(text):
    """
    Detect the most likely delimiter in text
    
    Args:
        text: String containing the data
        
    Returns:
        str: Detected delimiter or None
    """
    sample = text[:1000]  # Use first 1000 chars for detection
    
    # Count potential delimiters
    delimiters = {
        ',': sample.count(','),
        '\t': sample.count('\t'),
        '|': sample.count('|'),
        ';': sample.count(';'),
        ':': sample.count(':')
    }
    
    # Check for consistent spacing (multiple spaces)
    space_pattern = re.findall(r' {2,}', sample)
    if len(space_pattern) > 5:
        return r'\s{2,}'
    
    # Get delimiter with highest count
    max_delim = max(delimiters, key=delimiters.get)
    
    # Return if count is significant
    return max_delim if delimiters[max_delim] > 5 else None

def parse_text_to_dataframe(text):
    """
    Parse text into pandas DataFrame with automatic delimiter detection
    
    Args:
        text: String containing the data
        
    Returns:
        pd.DataFrame or None if parsing fails
    """
    try:
        text = text.strip()
        
        if not text:
            return None
        
        # Detect delimiter
        delimiter = detect_delimiter(text)
        
        if delimiter:
            # Parse with detected delimiter
            if delimiter == r'\s{2,}':
                # Handle multiple spaces as delimiter
                df = pd.read_csv(StringIO(text), sep=delimiter, engine='python')
            else:
                df = pd.read_csv(StringIO(text), sep=delimiter)
        else:
            # Fallback: try splitting by lines and whitespace
            lines = text.strip().split('\n')
            data = []
            
            for line in lines:
                if line.strip():
                    # Split by multiple spaces or tabs
                    row = re.split(r'\s{2,}|\t', line.strip())
                    data.append(row)
            
            if len(data) > 1:
                df = pd.DataFrame(data[1:], columns=data[0])
            else:
                # Single line - treat as single row
                df = pd.DataFrame([data[0]])
        
        # Clean column names
        df.columns = df.columns.str.strip()
        
        return df if len(df) > 0 else None
        
    except Exception as e:
        print(f"Error parsing text: {str(e)}")
        return None

def parse_csv_text(text, delimiter=','):
    """
    Parse CSV text with specific delimiter
    
    Args:
        text: CSV text
        delimiter: Delimiter character
        
    Returns:
        pd.DataFrame or None
    """
    try:
        df = pd.read_csv(StringIO(text), sep=delimiter)
        return df
    except:
        return None

def parse_table_text(text):
    """
    Parse text that looks like a formatted table
    
    Args:
        text: Table-like text with alignment
        
    Returns:
        pd.DataFrame or None
    """
    try:
        lines = text.strip().split('\n')
        
        # Remove separator lines (like "---" or "===")
        lines = [line for line in lines if not re.match(r'^[\s\-=_|]+$', line)]
        
        if len(lines) < 2:
            return None
        
        # Parse based on whitespace columns
        data = []
        for line in lines:
            row = re.split(r'\s{2,}', line.strip())
            data.append(row)
        
        df = pd.DataFrame(data[1:], columns=data[0])
        return df
        
    except:
        return None