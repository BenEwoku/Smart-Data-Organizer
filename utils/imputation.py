"""
Missing value imputation utilities
"""

import pandas as pd
import numpy as np
import streamlit as st
from scipy import stats

def detect_missing_values(df):
    """
    Detect missing values in DataFrame
    
    Args:
        df: pandas DataFrame
        
    Returns:
        dict: Missing value statistics
    """
    missing_stats = {
        'total_rows': len(df),
        'total_columns': len(df.columns),
        'missing_by_column': {},
        'missing_percentage': {},
        'column_types': {},
        'suggested_methods': {}
    }
    
    for col in df.columns:
        missing_count = df[col].isna().sum()
        missing_percent = (missing_count / len(df)) * 100
        
        missing_stats['missing_by_column'][col] = missing_count
        missing_stats['missing_percentage'][col] = missing_percent
        
        # Detect column type
        col_type = 'unknown'
        if pd.api.types.is_numeric_dtype(df[col]):
            col_type = 'numeric'
        elif pd.api.types.is_string_dtype(df[col]) or pd.api.types.is_object_dtype(df[col]):
            col_type = 'categorical'
        elif pd.api.types.is_datetime64_any_dtype(df[col]):
            col_type = 'datetime'
        elif pd.api.types.is_bool_dtype(df[col]):
            col_type = 'boolean'
        
        missing_stats['column_types'][col] = col_type
        
        # Suggest imputation method
        if missing_count > 0:
            if col_type == 'numeric':
                # Check distribution for mean vs median
                if missing_percent < 30:  # Low missingness
                    try:
                        # Test for normality
                        numeric_vals = df[col].dropna()
                        if len(numeric_vals) > 3:
                            _, p_value = stats.shapiro(numeric_vals.sample(min(5000, len(numeric_vals))))
                            if p_value > 0.05:
                                missing_stats['suggested_methods'][col] = 'mean'
                            else:
                                missing_stats['suggested_methods'][col] = 'median'
                        else:
                            missing_stats['suggested_methods'][col] = 'median'
                    except:
                        missing_stats['suggested_methods'][col] = 'median'
                else:
                    missing_stats['suggested_methods'][col] = 'median'
                    
            elif col_type == 'categorical':
                missing_stats['suggested_methods'][col] = 'mode'
            elif col_type == 'datetime':
                missing_stats['suggested_methods'][col] = 'forward_fill'
            else:
                missing_stats['suggested_methods'][col] = 'custom'
    
    missing_stats['total_missing'] = sum(missing_stats['missing_by_column'].values())
    missing_stats['overall_missing_percent'] = (missing_stats['total_missing'] / 
                                                (len(df) * len(df.columns))) * 100
    
    return missing_stats

def impute_column(df, column, method='auto', custom_value=None):
    """
    Impute missing values in a single column
    
    Args:
        df: pandas DataFrame
        column: Column name
        method: Imputation method ('mean', 'median', 'mode', 'forward_fill', 
                                   'backward_fill', 'interpolate', 'constant', 'delete')
        custom_value: Custom value for 'constant' method
        
    Returns:
        pd.DataFrame: DataFrame with imputed values
    """
    df = df.copy()
    
    if column not in df.columns:
        raise ValueError(f"Column '{column}' not found in DataFrame")
    
    if df[column].isna().sum() == 0:
        return df  # No missing values
    
    original_missing = df[column].isna().sum()
    
    if method == 'auto':
        # Auto-select based on column type
        if pd.api.types.is_numeric_dtype(df[column]):
            method = 'median'
        elif pd.api.types.is_categorical_dtype(df[column]) or pd.api.types.is_object_dtype(df[column]):
            method = 'mode'
        elif pd.api.types.is_datetime64_any_dtype(df[column]):
            method = 'forward_fill'
        else:
            method = 'mode'
    
    # Apply imputation
    if method == 'delete':
        # Delete rows with missing values in this column
        df = df.dropna(subset=[column])
        
    elif method == 'mean':
        df[column] = df[column].fillna(df[column].mean())
        
    elif method == 'median':
        df[column] = df[column].fillna(df[column].median())
        
    elif method == 'mode':
        mode_value = df[column].mode()
        if len(mode_value) > 0:
            df[column] = df[column].fillna(mode_value[0])
        else:
            # If no mode (all unique), use most frequent
            most_frequent = df[column].value_counts().index[0] if len(df[column].value_counts()) > 0 else 'Unknown'
            df[column] = df[column].fillna(most_frequent)
            
    elif method == 'forward_fill':
        df[column] = df[column].ffill()
        
    elif method == 'backward_fill':
        df[column] = df[column].bfill()
        
    elif method == 'interpolate':
        if pd.api.types.is_numeric_dtype(df[column]):
            df[column] = df[column].interpolate(method='linear')
        else:
            df[column] = df[column].ffill()  # Fallback for non-numeric
            
    elif method == 'constant':
        if custom_value is not None:
            df[column] = df[column].fillna(custom_value)
        else:
            if pd.api.types.is_numeric_dtype(df[column]):
                df[column] = df[column].fillna(0)
            else:
                df[column] = df[column].fillna('Missing')
                
    elif method == 'knn':
        # Simple KNN imputation (for numeric columns)
        from sklearn.impute import KNNImputer
        if pd.api.types.is_numeric_dtype(df[column]):
            imputer = KNNImputer(n_neighbors=5)
            df[[column]] = imputer.fit_transform(df[[column]])
    
    new_missing = df[column].isna().sum()
    imputed_count = original_missing - new_missing
    
    return df, imputed_count, method

def batch_impute(df, imputation_map):
    """
    Apply multiple imputations at once
    
    Args:
        df: pandas DataFrame
        imputation_map: Dict of {column: method} or {column: (method, custom_value)}
        
    Returns:
        pd.DataFrame: Imputed DataFrame
    """
    df = df.copy()
    results = {}
    
    for column, method_info in imputation_map.items():
        if column in df.columns:
            if isinstance(method_info, tuple):
                method, custom_value = method_info
                df, imputed_count, used_method = impute_column(df, column, method, custom_value)
            else:
                df, imputed_count, used_method = impute_column(df, column, method_info)
            
            results[column] = {
                'imputed_count': imputed_count,
                'method': used_method
            }
    
    return df, results

def get_imputation_preview(df, column, method='auto', custom_value=None, preview_rows=5):
    """
    Show preview of imputation before applying
    
    Args:
        df: pandas DataFrame
        column: Column name
        method: Imputation method
        custom_value: Custom value for constant method
        preview_rows: Number of preview rows
        
    Returns:
        dict: Preview information
    """
    preview = {
        'original_sample': [],
        'imputed_sample': [],
        'stats': {},
        'method_used': method
    }
    
    # Get rows with missing values
    missing_rows = df[df[column].isna()].head(preview_rows)
    
    if len(missing_rows) == 0:
        return preview
    
    # Apply imputation to a copy for preview
    df_preview = df.copy()
    df_preview, imputed_count, method_used = impute_column(df_preview, column, method, custom_value)
    
    preview['method_used'] = method_used
    
    # Get before/after samples
    for idx in missing_rows.index[:preview_rows]:
        original_val = df.loc[idx, column]
        imputed_val = df_preview.loc[idx, column]
        
        preview['original_sample'].append({
            'index': idx,
            'value': original_val
        })
        preview['imputed_sample'].append({
            'index': idx,
            'value': imputed_val
        })
    
    # Calculate statistics
    if pd.api.types.is_numeric_dtype(df[column]):
        preview['stats'] = {
            'mean': df[column].mean(),
            'median': df[column].median(),
            'std': df[column].std(),
            'min': df[column].min(),
            'max': df[column].max()
        }
    elif pd.api.types.is_categorical_dtype(df[column]) or pd.api.types.is_object_dtype(df[column]):
        value_counts = df[column].value_counts()
        preview['stats'] = {
            'mode': value_counts.index[0] if len(value_counts) > 0 else None,
            'unique_values': df[column].nunique(),
            'top_categories': value_counts.head(5).to_dict()
        }
    
    return preview