"""
Data validation utilities
"""

import pandas as pd
import re

def validate_data_input(text):
    """
    Validate data input before processing
    
    Args:
        text: Input text to validate
        
    Returns:
        dict: Validation results with issues and warnings
    """
    issues = []
    warnings = []
    
    if not text or len(text.strip()) < 10:
        issues.append("Input is too short (minimum 10 characters required)")
        return {"valid": False, "issues": issues, "warnings": warnings}
    
    # Check if it looks like a table
    lines = text.strip().split('\n')
    
    if len(lines) < 2:
        issues.append("Need at least 2 lines of data")
        return {"valid": False, "issues": issues, "warnings": warnings}
    
    # Check for consistent delimiters
    delimiter_counts = {
        ',': sum(line.count(',') for line in lines[:10]),
        '\t': sum(line.count('\t') for line in lines[:10]),
        '|': sum(line.count('|') for line in lines[:10]),
        ';': sum(line.count(';') for line in lines[:10])
    }
    
    max_delimiter = max(delimiter_counts, key=delimiter_counts.get)
    max_count = delimiter_counts[max_delimiter]
    
    if max_count == 0:
        # Check for spaces
        space_lines = sum(1 for line in lines[:10] if re.search(r'\s{2,}', line))
        if space_lines < 5:
            issues.append("No clear delimiter detected (comma, tab, pipe, or multiple spaces)")
    
    # Check for potential header
    first_line = lines[0]
    if not any(char.isdigit() for char in first_line):
        # First line likely contains headers (no digits)
        warnings.append("Detected header row")
    
    # Check for missing values pattern
    empty_cells = sum(line.count('""') + line.count("''") + line.count('NA') + line.count('null') 
                      for line in lines[:20])
    if empty_cells > 0:
        warnings.append(f"Found {empty_cells} potential missing values")
    
    # Check data size
    total_chars = len(text)
    if total_chars > 100000:  # 100KB limit
        warnings.append("Large dataset detected (over 100KB)")
    
    return {
        "valid": True,
        "issues": issues,
        "warnings": warnings,
        "line_count": len(lines),
        "char_count": total_chars,
        "likely_delimiter": max_delimiter if max_count > 0 else "space"
    }

def validate_dataframe(df):
    """
    Validate DataFrame quality
    
    Args:
        df: pandas DataFrame to validate
        
    Returns:
        dict: Validation results
    """
    results = {
        "row_count": len(df),
        "column_count": len(df.columns),
        "missing_values": int(df.isna().sum().sum()),
        "missing_percentage": float((df.isna().sum().sum() / (len(df) * len(df.columns))) * 100),
        "duplicate_rows": int(df.duplicated().sum()),
        "numeric_columns": len(df.select_dtypes(include=['number']).columns),
        "text_columns": len(df.select_dtypes(include=['object']).columns),
        "date_columns": 0,
        "issues": [],
        "warnings": []
    }
    
    # Check for date columns
    for col in df.columns:
        try:
            pd.to_datetime(df[col], errors='coerce')
            if df[col].notna().sum() > 0:
                results["date_columns"] += 1
        except:
            pass
    
    # Quality checks
    if results["missing_percentage"] > 50:
        results["issues"].append(f"High missing data ({results['missing_percentage']:.1f}%)")
    elif results["missing_percentage"] > 20:
        results["warnings"].append(f"Moderate missing data ({results['missing_percentage']:.1f}%)")
    
    if results["duplicate_rows"] > 0:
        results["warnings"].append(f"Found {results['duplicate_rows']} duplicate rows")
    
    if results["row_count"] < 3:
        results["issues"].append("Very few rows (less than 3)")
    
    if results["column_count"] < 2:
        results["issues"].append("Very few columns (less than 2)")
    
    return results

def get_data_quality_score(df):
    """
    Calculate a data quality score (0-100)
    
    Args:
        df: pandas DataFrame
        
    Returns:
        float: Quality score
    """
    if df is None or len(df) == 0:
        return 0
    
    validation = validate_dataframe(df)
    
    score = 100
    
    # Penalize for issues
    score -= min(50, validation["missing_percentage"])  # Up to 50 points for missing data
    score -= validation["duplicate_rows"] * 2  # 2 points per duplicate row
    
    # Bonus for good structure
    if validation["date_columns"] > 0:
        score += 5
    if validation["numeric_columns"] > 0:
        score += 5
    
    # Ensure score is within bounds
    return max(0, min(100, score))