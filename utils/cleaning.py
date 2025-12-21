# File: utils/cleaning.py
"""
Data cleaning utilities for preprocessing DataFrames
"""

import pandas as pd
import re

def clean_dataframe(df):
    """
    Perform comprehensive data cleaning
    
    Args:
        df: pandas DataFrame
        
    Returns:
        pd.DataFrame: Cleaned DataFrame
    """
    if df is None or len(df) == 0:
        return df
    
    df = df.copy()
    
    # 1. Remove completely empty rows and columns
    df = df.dropna(how='all', axis=0)  # Empty rows
    df = df.dropna(how='all', axis=1)  # Empty columns
    
    # 2. Clean column names
    df = clean_column_names(df)
    
    # 3. Strip whitespace from string columns
    df = strip_whitespace(df)
    
    # 4. Convert numeric columns
    df = convert_numeric_columns(df)
    
    # 5. Standardize text case (optional - be careful)
    # df = standardize_text_case(df)
    
    # 6. Remove duplicate rows
    df = df.drop_duplicates()
    
    return df

def clean_column_names(df):
    """
    Clean and standardize column names
    
    Args:
        df: pandas DataFrame
        
    Returns:
        pd.DataFrame: DataFrame with cleaned column names
    """
    # Strip whitespace
    df.columns = df.columns.str.strip()
    
    # Replace multiple spaces with single space
    df.columns = df.columns.str.replace(r'\s+', ' ', regex=True)
    
    # Remove special characters (optional - keep only alphanumeric and spaces)
    # df.columns = df.columns.str.replace(r'[^a-zA-Z0-9\s_]', '', regex=True)
    
    return df

def strip_whitespace(df):
    """
    Strip leading/trailing whitespace from all string columns
    
    Args:
        df: pandas DataFrame
        
    Returns:
        pd.DataFrame: DataFrame with stripped strings
    """
    for col in df.columns:
        if df[col].dtype == 'object':
            try:
                df[col] = df[col].astype(str).str.strip()
            except:
                pass
    
    return df

def convert_numeric_columns(df):
    """
    Attempt to convert string columns to numeric where appropriate
    
    Args:
        df: pandas DataFrame
        
    Returns:
        pd.DataFrame: DataFrame with converted numeric columns
    """
    for col in df.columns:
        if df[col].dtype == 'object':
            try:
                # Remove common numeric formatting (commas, currency symbols)
                cleaned = df[col].astype(str).str.replace(',', '', regex=False)
                cleaned = cleaned.str.replace('$', '', regex=False)
                cleaned = cleaned.str.replace('€', '', regex=False)
                cleaned = cleaned.str.replace('£', '', regex=False)
                cleaned = cleaned.str.replace('%', '', regex=False)
                cleaned = cleaned.str.strip()
                
                # Try to convert to numeric
                df[col] = pd.to_numeric(cleaned, errors='ignore')
            except:
                pass
    
    return df

def standardize_text_case(df):
    """
    Standardize text case (use with caution - may not be desired)
    
    Args:
        df: pandas DataFrame
        
    Returns:
        pd.DataFrame: DataFrame with standardized text case
    """
    for col in df.columns:
        if df[col].dtype == 'object':
            try:
                # Title case for names, proper nouns
                # Only apply to short strings (likely names/categories)
                if df[col].str.len().mean() < 30:
                    df[col] = df[col].str.title()
            except:
                pass
    
    return df

def remove_outliers(df, columns=None, method='iqr', threshold=1.5):
    """
    Remove outliers from numeric columns
    
    Args:
        df: pandas DataFrame
        columns: List of columns to check (None = all numeric)
        method: 'iqr' or 'zscore'
        threshold: IQR multiplier or z-score threshold
        
    Returns:
        pd.DataFrame: DataFrame with outliers removed
    """
    df = df.copy()
    
    if columns is None:
        columns = df.select_dtypes(include=['number']).columns
    
    for col in columns:
        if col in df.columns and pd.api.types.is_numeric_dtype(df[col]):
            if method == 'iqr':
                Q1 = df[col].quantile(0.25)
                Q3 = df[col].quantile(0.75)
                IQR = Q3 - Q1
                lower = Q1 - threshold * IQR
                upper = Q3 + threshold * IQR
                df = df[(df[col] >= lower) & (df[col] <= upper)]
                
            elif method == 'zscore':
                from scipy import stats
                z_scores = stats.zscore(df[col].dropna())
                abs_z_scores = abs(z_scores)
                df = df[abs_z_scores < threshold]
    
    return df

def fill_missing_values(df, method='ffill', columns=None):
    """
    Fill missing values in DataFrame
    
    Args:
        df: pandas DataFrame
        method: 'ffill' (forward fill), 'bfill' (backward fill), 
                'mean', 'median', or specific value
        columns: List of columns to fill (None = all)
        
    Returns:
        pd.DataFrame: DataFrame with filled values
    """
    df = df.copy()
    
    if columns is None:
        columns = df.columns
    
    for col in columns:
        if col in df.columns:
            if method == 'ffill':
                df[col] = df[col].fillna(method='ffill')
            elif method == 'bfill':
                df[col] = df[col].fillna(method='bfill')
            elif method == 'mean' and pd.api.types.is_numeric_dtype(df[col]):
                df[col] = df[col].fillna(df[col].mean())
            elif method == 'median' and pd.api.types.is_numeric_dtype(df[col]):
                df[col] = df[col].fillna(df[col].median())
            else:
                df[col] = df[col].fillna(method)
    
    return df

def standardize_date_formats(df, date_columns=None, target_format='%Y-%m-%d'):
    """
    Standardize date formats across columns
    
    Args:
        df: pandas DataFrame
        date_columns: List of date columns (None = auto-detect)
        target_format: Target date format string
        
    Returns:
        pd.DataFrame: DataFrame with standardized dates
    """
    df = df.copy()
    
    if date_columns is None:
        # Auto-detect date columns
        date_columns = []
        for col in df.columns:
            try:
                pd.to_datetime(df[col], errors='coerce')
                if df[col].notna().sum() > len(df) * 0.5:
                    date_columns.append(col)
            except:
                pass
    
    for col in date_columns:
        if col in df.columns:
            try:
                df[col] = pd.to_datetime(df[col], errors='coerce')
                df[col] = df[col].dt.strftime(target_format)
            except:
                pass
    
    return df