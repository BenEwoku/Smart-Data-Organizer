# File: utils/export.py
"""
Export utilities for various file formats
"""

import pandas as pd
from io import BytesIO

def export_to_csv(df, index=False, encoding='utf-8'):
    """
    Export DataFrame to CSV format
    
    Args:
        df: pandas DataFrame
        index: Include index in export
        encoding: File encoding
        
    Returns:
        bytes: CSV data as bytes
    """
    try:
        csv_data = df.to_csv(index=index, encoding=encoding)
        return csv_data.encode(encoding)
    except Exception as e:
        print(f"CSV export error: {str(e)}")
        return None

def export_to_excel(df, sheet_name='Data', index=False):
    """
    Export DataFrame to Excel format
    
    Args:
        df: pandas DataFrame
        sheet_name: Name of the worksheet
        index: Include index in export
        
    Returns:
        bytes: Excel data as bytes
    """
    try:
        buffer = BytesIO()
        
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name=sheet_name, index=index)
            
            # Optional: Add formatting
            workbook = writer.book
            worksheet = writer.sheets[sheet_name]
            
            # Auto-adjust column widths
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                
                adjusted_width = min(max_length + 2, 50)
                worksheet.column_dimensions[column_letter].width = adjusted_width
        
        return buffer.getvalue()
        
    except Exception as e:
        print(f"Excel export error: {str(e)}")
        return None

def export_to_json(df, orient='records'):
    """
    Export DataFrame to JSON format
    
    Args:
        df: pandas DataFrame
        orient: JSON orientation ('records', 'index', 'columns', 'values')
        
    Returns:
        str: JSON string
    """
    try:
        return df.to_json(orient=orient, indent=2)
    except Exception as e:
        print(f"JSON export error: {str(e)}")
        return None

def export_to_sql_insert(df, table_name='data'):
    """
    Export DataFrame as SQL INSERT statements
    
    Args:
        df: pandas DataFrame
        table_name: Name of the SQL table
        
    Returns:
        str: SQL INSERT statements
    """
    try:
        sql_statements = []
        
        # Create column names
        columns = ', '.join([f'"{col}"' for col in df.columns])
        
        # Create INSERT statements for each row
        for _, row in df.iterrows():
            values = []
            for val in row:
                if pd.isna(val):
                    values.append('NULL')
                elif isinstance(val, str):
                    # Escape single quotes
                    escaped = val.replace("'", "''")
                    values.append(f"'{escaped}'")
                else:
                    values.append(str(val))
            
            values_str = ', '.join(values)
            sql_statements.append(f"INSERT INTO {table_name} ({columns}) VALUES ({values_str});")
        
        return '\n'.join(sql_statements)
        
    except Exception as e:
        print(f"SQL export error: {str(e)}")
        return None

def export_metadata(df, structure_info=None):
    """
    Export metadata about the DataFrame
    
    Args:
        df: pandas DataFrame
        structure_info: Tuple of (structure, date_col, entity_col)
        
    Returns:
        str: Metadata as text
    """
    metadata = []
    
    metadata.append("=== DATA DICTIONARY ===\n")
    metadata.append(f"Total Rows: {len(df)}")
    metadata.append(f"Total Columns: {len(df.columns)}\n")
    
    if structure_info:
        structure, date_col, entity_col = structure_info
        metadata.append(f"Data Structure: {structure}")
        if date_col:
            metadata.append(f"Date Column: {date_col}")
        if entity_col:
            metadata.append(f"Entity Column: {entity_col}")
        metadata.append("")
    
    metadata.append("=== COLUMNS ===\n")
    
    for col in df.columns:
        metadata.append(f"Column: {col}")
        metadata.append(f"  Type: {df[col].dtype}")
        metadata.append(f"  Non-Null: {df[col].notna().sum()}")
        metadata.append(f"  Null: {df[col].isna().sum()}")
        metadata.append(f"  Unique Values: {df[col].nunique()}")
        
        if pd.api.types.is_numeric_dtype(df[col]):
            metadata.append(f"  Min: {df[col].min()}")
            metadata.append(f"  Max: {df[col].max()}")
            metadata.append(f"  Mean: {df[col].mean():.2f}")
        
        metadata.append("")
    
    return '\n'.join(metadata)