# File: utils/detection.py
"""
Data structure detection utilities
Identifies: Time Series, Panel Data, Cross-Sectional, Email Data, or General data
"""

import pandas as pd
import re

def detect_email_data(df):
    """
    Detect if data represents email data
    
    Args:
        df: pandas DataFrame
        
    Returns:
        tuple: (is_email, confidence_score, email_columns_found)
    """
    email_keywords = [
        # Core email headers
        'from', 'to', 'subject', 'date', 'message', 'cc', 'bcc',
        # Email-specific terms
        'sender', 'recipient', 'sent', 'received', 'body', 'content',
        'attachment', 'reply', 'forward', 'thread', 'email', 'mail'
    ]
    
    columns_found = []
    confidence_score = 0
    
    for col in df.columns:
        col_lower = str(col).lower()
        
        # Check for exact matches (higher confidence)
        exact_matches = ['from', 'to', 'subject', 'date']
        if col_lower in exact_matches:
            columns_found.append(col)
            confidence_score += 25  # 25% per exact match
        
        # Check for partial matches
        for keyword in email_keywords:
            if keyword in col_lower and col_lower != keyword:
                # Check if it's likely an email column
                if re.search(rf'\b{keyword}\b', col_lower):
                    columns_found.append(col)
                    confidence_score += 10
                    break
    
    # Check data patterns
    if 'From' in df.columns and 'To' in df.columns:
        # Check if columns contain email-like patterns
        from_samples = df['From'].dropna().head(10)
        to_samples = df['To'].dropna().head(10)
        
        email_pattern = r'[\w\.-]+@[\w\.-]+\.\w+'
        
        email_in_from = any(from_samples.astype(str).str.contains(email_pattern, na=False))
        email_in_to = any(to_samples.astype(str).str.contains(email_pattern, na=False))
        
        if email_in_from or email_in_to:
            confidence_score += 20
    
    # Check for date column with email timestamps
    date_col = detect_date_column(df)
    if date_col:
        confidence_score += 15
    
    # Check for message/body content
    body_keywords = ['body', 'content', 'message', 'text']
    for col in df.columns:
        col_lower = str(col).lower()
        if any(keyword == col_lower for keyword in body_keywords):
            # Check if column has text content
            if df[col].dtype == 'object' and df[col].str.len().mean() > 50:
                confidence_score += 15
                break
    
    is_email = confidence_score >= 50  # Threshold for email detection
    return is_email, confidence_score, columns_found

def detect_date_column(df):
    """
    Detect column containing dates
    
    Args:
        df: pandas DataFrame
        
    Returns:
        str: Column name with dates, or None
    """
    for col in df.columns:
        try:
            # Skip columns that are clearly not dates
            col_lower = str(col).lower()
            if any(word in col_lower for word in ['id', 'name', 'code', 'email', 'phone']):
                continue
            
            # Attempt to parse as datetime
            test_series = pd.to_datetime(df[col], errors='coerce')
            
            # Check if at least 50% are valid dates
            valid_ratio = test_series.notna().sum() / len(df)
            
            if valid_ratio > 0.5:
                # Additional check: dates should be within reasonable range
                min_date = test_series.min()
                max_date = test_series.max()
                
                # Reasonable date range (1900 to future)
                if pd.notna(min_date) and pd.notna(max_date):
                    if min_date.year >= 1900 and max_date.year <= 2100:
                        return col
                
        except:
            continue
    
    return None

def detect_numeric_columns(df):
    """
    Detect numeric columns in DataFrame
    
    Args:
        df: pandas DataFrame
        
    Returns:
        list: List of numeric column names
    """
    numeric_cols = []
    
    for col in df.columns:
        try:
            # Skip email-related columns
            col_lower = str(col).lower()
            if any(keyword in col_lower for keyword in ['from', 'to', 'subject', 'body', 'message']):
                continue
            
            # Try to convert to numeric
            test_series = pd.to_numeric(df[col], errors='coerce')
            
            # Check if at least 50% are valid numbers
            valid_ratio = test_series.notna().sum() / len(df)
            
            if valid_ratio > 0.5:
                numeric_cols.append(col)
                
        except:
            continue
    
    return numeric_cols

def detect_entity_column(df):
    """
    Detect column that represents entities (ID, company, country, etc.)
    
    Args:
        df: pandas DataFrame
        
    Returns:
        str: Column name of entity identifier, or None
    """
    # Keywords that suggest entity columns
    entity_keywords = [
        'id', 'name', 'company', 'entity', 'country', 
        'state', 'region', 'city', 'customer', 'product',
        'symbol', 'ticker', 'code', 'identifier', 'user'
    ]
    
    for col in df.columns:
        col_lower = str(col).lower()
        
        # Skip email-specific columns
        if col_lower in ['from', 'to', 'subject', 'date', 'body']:
            continue
        
        # Check if column name contains entity keywords
        if any(keyword in col_lower for keyword in entity_keywords):
            # Check uniqueness ratio
            unique_ratio = df[col].nunique() / len(df)
            
            # Should have repeated values (not all unique, not all same)
            if 0.1 < unique_ratio < 1.0:
                return col
    
    # If no keyword match, look for columns with moderate uniqueness
    for col in df.columns:
        col_lower = str(col).lower()
        
        # Skip email-specific columns
        if col_lower in ['from', 'to', 'subject', 'date', 'body']:
            continue
        
        unique_ratio = df[col].nunique() / len(df)
        
        # Between 10% and 80% unique (suggests grouping variable)
        if 0.1 < unique_ratio < 0.8:
            return col
    
    return None

def detect_data_structure(df):
    """
    Detect the overall structure of the data
    
    Args:
        df: pandas DataFrame
        
    Returns:
        tuple: (structure_type, date_column, entity_column)
        ALWAYS returns a valid tuple, never raises exception
    """
    try:
        # First, check if it's email data
        is_email, confidence_score, email_columns = detect_email_data(df)
        
        if is_email and confidence_score >= 60:
            # This is likely email data
            date_col = detect_date_column(df)
            # For email data, entity column could be 'From' or 'To'
            entity_col = 'From' if 'From' in df.columns else 'To' if 'To' in df.columns else None
            return "Email Data", date_col, entity_col
        
        # Original detection logic for non-email data
        date_col = detect_date_column(df)
        numeric_cols = detect_numeric_columns(df)
        entity_col = detect_entity_column(df)
        
        # Decision logic
        if date_col and len(numeric_cols) > 0:
            # Has dates and numeric data
            
            if entity_col:
                # Multiple entities over time = Panel Data
                return "Panel Data", date_col, entity_col
            else:
                # Single entity over time = Time Series
                return "Time Series", date_col, None
                
        elif not date_col or all_dates_same(df, date_col):
            # No date column or all dates are the same = Cross-Sectional
            return "Cross-Sectional", None, None
            
        else:
            # Everything else
            return "General Data", None, None
            
    except Exception as e:
        # CRITICAL: Always return a valid tuple even if detection fails
        print(f"⚠️ Detection error: {str(e)}")
        return "General Data", None, None
    
    # Safety fallback (should never reach here)
    return "General Data", None, None

def all_dates_same(df, date_col):
    """Check if all dates in a column are the same"""
    if date_col is None or date_col not in df.columns:
        return False
    
    try:
        dates = pd.to_datetime(df[date_col], errors='coerce')
        unique_dates = dates.nunique()
        return unique_dates == 1
    except:
        return False

def detect_time_frequency(df, date_col):
    """
    Detect the frequency of time series data
    
    Args:
        df: pandas DataFrame
        date_col: Name of date column
        
    Returns:
        str: "Daily", "Weekly", "Monthly", "Quarterly", "Yearly", or "Irregular"
    """
    try:
        dates = pd.to_datetime(df[date_col], errors='coerce').dropna()
        
        if len(dates) < 2:
            return "Irregular"
        
        # Sort dates
        dates = dates.sort_values()
        
        # Calculate differences between consecutive dates
        diffs = dates.diff().dropna()
        
        # Get median difference
        median_diff = diffs.median()
        
        # Classify frequency
        if median_diff <= pd.Timedelta(days=1):
            return "Daily"
        elif median_diff <= pd.Timedelta(days=7):
            return "Weekly"
        elif median_diff <= pd.Timedelta(days=31):
            return "Monthly"
        elif median_diff <= pd.Timedelta(days=92):
            return "Quarterly"
        elif median_diff <= pd.Timedelta(days=366):
            return "Yearly"
        else:
            return "Irregular"
            
    except:
        return "Irregular"

def is_balanced_panel(df, entity_col, date_col):
    """
    Check if panel data is balanced (same time periods for all entities)
    
    Args:
        df: pandas DataFrame
        entity_col: Entity identifier column
        date_col: Date column
        
    Returns:
        bool: True if balanced, False otherwise
    """
    try:
        # Count observations per entity
        counts = df.groupby(entity_col).size()
        
        # Balanced if all entities have same number of observations
        return counts.nunique() == 1
        
    except:
        return False

def detect_email_threads(df):
    """
    Detect email threads based on subject lines
    
    Args:
        df: pandas DataFrame with email data
        
    Returns:
        dict: Thread detection results
    """
    if 'Subject' not in df.columns:
        return {"has_threads": False, "thread_count": 0}
    
    try:
        # Clean subject lines
        subjects = df['Subject'].astype(str).str.lower()
        
        # Remove reply/forward prefixes
        clean_subjects = subjects.str.replace(r'^(re:|fwd:|fw:|re\[\d+\]:|fwd\[\d+\]:)\s*', '', regex=True)
        
        # Count unique clean subjects
        unique_clean = clean_subjects.nunique()
        total_emails = len(df)
        
        # Thread detection logic
        has_threads = unique_clean < total_emails * 0.8  # If less than 80% unique
        
        return {
            "has_threads": has_threads,
            "thread_count": unique_clean,
            "total_emails": total_emails,
            "avg_thread_size": total_emails / max(1, unique_clean)
        }
        
    except:
        return {"has_threads": False, "thread_count": 0}