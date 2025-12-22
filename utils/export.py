# File: utils/export.py
"""
Export utilities for various file formats
"""

import pandas as pd
from io import BytesIO
import streamlit as st

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
        # DEBUG: Log what we're receiving
        import streamlit as st
        st.write(f"DEBUG: export_to_excel called with df type: {type(df)}")
        
        if df is None:
            st.error("Excel export: df is None")
            return None
            
        if df.empty:
            st.warning("Excel export: df is empty, creating empty workbook")
            # Create empty Excel file
            from openpyxl import Workbook
            buffer = BytesIO()
            wb = Workbook()
            wb.save(buffer)
            return buffer.getvalue()
        
        st.write(f"DEBUG: DataFrame shape: {df.shape}")
        
        # Make a copy to avoid modifying original
        df_safe = df.copy()
        
        # Fix datetime columns with timezone
        datetime_fixed = False
        for col in df_safe.columns:
            if pd.api.types.is_datetime64_any_dtype(df_safe[col]):
                try:
                    # Check if datetime has timezone
                    sample = df_safe[col].dropna().iloc[0] if not df_safe[col].dropna().empty else None
                    if sample is not None and hasattr(sample, 'tz') and sample.tz is not None:
                        # Remove timezone for Excel compatibility
                        df_safe[col] = df_safe[col].dt.tz_localize(None)
                        datetime_fixed = True
                        st.info(f"Fixed timezone in column: {col}")
                except Exception as col_e:
                    # If can't fix, convert to string
                    st.warning(f"Converting datetime column '{col}' to string")
                    df_safe[col] = df_safe[col].astype(str)
        
        # Convert any problematic columns to string
        for col in df_safe.columns:
            try:
                # Check if column has problematic data types
                if df_safe[col].dtype == 'object':
                    # Check if it contains datetime strings with timezone
                    try:
                        # Try to parse as datetime to check for timezone
                        sample = df_safe[col].dropna().iloc[0] if not df_safe[col].dropna().empty else None
                        if sample and isinstance(sample, str) and ('+' in sample or '-' in sample[-6:]):
                            # Likely has timezone, convert to naive datetime
                            parsed = pd.to_datetime(df_safe[col], errors='coerce', utc=True)
                            if not parsed.isna().all():
                                df_safe[col] = parsed.dt.tz_convert(None)
                                datetime_fixed = True
                    except:
                        pass
                elif df_safe[col].dtype.name == 'category':
                    # Convert categorical to string
                    df_safe[col] = df_safe[col].astype(str)
            except Exception as col_e:
                st.warning(f"Column {col} conversion error: {str(col_e)}")
                # If conversion fails, try a different approach
                df_safe[col] = df_safe[col].apply(lambda x: str(x) if pd.notna(x) else '')
        
        buffer = BytesIO()
        
        # Try export with error handling
        try:
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                df_safe.to_excel(writer, sheet_name=sheet_name, index=index)
        except Exception as e1:
            st.warning(f"Excel export with formatting failed: {str(e1)}")
            # Try without writer context
            buffer.seek(0)  # Reset buffer
            try:
                df_safe.to_excel(buffer, sheet_name=sheet_name, index=index, engine='openpyxl')
            except Exception as e2:
                st.error(f"Simple Excel export also failed: {str(e2)}")
                # Last resort: create simple CSV
                buffer.seek(0)
                df_safe.to_csv(buffer, index=index)
        
        excel_data = buffer.getvalue()
        buffer.close()
        
        if len(excel_data) == 0:
            st.error("Generated empty Excel data")
            return None
            
        if datetime_fixed:
            st.success(f"Excel export successful (timezone fixed): {len(excel_data)} bytes")
        else:
            st.success(f"Excel export successful: {len(excel_data)} bytes")
            
        return excel_data
        
    except Exception as e:
        import streamlit as st
        st.error(f"Excel export error: {str(e)}")
        import traceback
        st.error(f"Traceback: {traceback.format_exc()}")
        return None

def export_to_excel_simple(df, sheet_name='Data'):
    """Super simple Excel export - minimal error checking"""
    try:
        if df is None or df.empty:
            return b''  # Return empty bytes
        
        # Create a new DataFrame with all columns as strings
        df_simple = pd.DataFrame()
        for col in df.columns:
            df_simple[col] = df[col].astype(str)
        
        buffer = BytesIO()
        df_simple.to_excel(buffer, index=False, sheet_name=sheet_name)
        return buffer.getvalue()
    except:
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