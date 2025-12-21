# File: utils/detection.py
"""
Data structure detection utilities
Identifies: Time Series, Panel Data, Cross-Sectional, or General data
"""

import pandas as pd
import re

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
            # Attempt to parse as datetime
            test_series = pd.to_datetime(df[col], errors='coerce')
            
            # Check if at least 50% are valid dates
            valid_ratio = test_series.notna().sum() / len(df)
            
            if valid_ratio > 0.5:
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
        'symbol', 'ticker', 'code', 'identifier'
    ]
    
    for col in df.columns:
        col_lower = str(col).lower()
        
        # Check if column name contains entity keywords
        if any(keyword in col_lower for keyword in entity_keywords):
            # Check uniqueness ratio
            unique_ratio = df[col].nunique() / len(df)
            
            # Should have repeated values (not all unique, not all same)
            if 0.1 < unique_ratio < 1.0:
                return col
    
    # If no keyword match, look for columns with moderate uniqueness
    for col in df.columns:
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
        structure_type: "Time Series", "Panel Data", "Cross-Sectional", or "General Data"
    """
    # Detect key columns
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