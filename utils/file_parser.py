"""
File parsing utilities for PDF, DOCX, and Excel files
Extracts tables and text data for conversion
"""

import pandas as pd
import streamlit as st
from io import BytesIO
import re

def parse_uploaded_file(uploaded_file):
    """
    Parse uploaded file based on type
    
    Args:
        uploaded_file: Streamlit UploadedFile object
        
    Returns:
        pd.DataFrame or list of DataFrames
    """
    file_ext = uploaded_file.name.split('.')[-1].lower()
    
    try:
        if file_ext == 'csv':
            return parse_csv(uploaded_file)
        elif file_ext == 'txt':
            return parse_txt(uploaded_file)
        elif file_ext in ['xlsx', 'xls']:
            return parse_excel(uploaded_file)
        elif file_ext == 'pdf':
            return parse_pdf(uploaded_file)
        elif file_ext in ['docx', 'doc']:
            return parse_docx(uploaded_file)
        else:
            st.error(f"Unsupported file type: {file_ext}")
            return None
    except Exception as e:
        st.error(f"Error parsing {file_ext.upper()} file: {str(e)}")
        return None

def parse_csv(file):
    """Parse CSV file"""
    try:
        df = pd.read_csv(file)
        return df
    except Exception as e:
        # Try different encodings
        try:
            df = pd.read_csv(file, encoding='latin-1')
            return df
        except:
            st.error(f"CSV parsing error: {str(e)}")
            return None

def parse_txt(file):
    """Parse TXT file"""
    try:
        content = file.read().decode('utf-8')
        
        # Try to detect structure
        from utils.parser import parse_text_to_dataframe
        df = parse_text_to_dataframe(content)
        
        return df
    except Exception as e:
        st.error(f"TXT parsing error: {str(e)}")
        return None

def parse_excel(file):
    """Parse Excel file (both .xlsx and .xls)"""
    try:
        # Try openpyxl first (for .xlsx)
        try:
            df = pd.read_excel(file, engine='openpyxl')
            return df
        except:
            # Fall back to xlrd (for .xls)
            df = pd.read_excel(file, engine='xlrd')
            return df
    except Exception as e:
        st.error(f"Excel parsing error: {str(e)}")
        st.info("Tip: Make sure the file isn't password-protected")
        return None

def parse_pdf(file):
    """
    Parse PDF file and extract tables
    
    Returns:
        DataFrame or list of DataFrames if multiple tables found
    """
    st.info("📄 Extracting data from PDF...")
    
    tables = []
    
    # Method 1: Try pdfplumber (best for most PDFs)
    try:
        import pdfplumber
        
        with pdfplumber.open(file) as pdf:
            for page_num, page in enumerate(pdf.pages, 1):
                page_tables = page.extract_tables()
                
                if page_tables:
                    for table in page_tables:
                        if table and len(table) > 1:
                            # Convert to DataFrame
                            df = pd.DataFrame(table[1:], columns=table[0])
                            df = df.dropna(how='all', axis=1)  # Remove empty columns
                            df = df.dropna(how='all', axis=0)  # Remove empty rows
                            
                            if len(df) > 0:
                                tables.append(df)
                                st.success(f"✅ Found table on page {page_num}")
        
        if tables:
            if len(tables) == 1:
                return tables[0]
            else:
                st.info(f"Found {len(tables)} tables. Combining them...")
                return combine_tables(tables)
    
    except ImportError:
        st.warning("pdfplumber not installed. Trying alternative method...")
    except Exception as e:
        st.warning(f"pdfplumber extraction failed: {str(e)}")
    
    # Method 2: Try tabula-py (good for complex PDFs)
    try:
        import tabula
        
        # Reset file pointer
        file.seek(0)
        
        # Extract tables
        tables = tabula.read_pdf(file, pages='all', multiple_tables=True)
        
        if tables:
            st.success(f"✅ Found {len(tables)} table(s) using Tabula")
            
            if len(tables) == 1:
                return tables[0]
            else:
                return combine_tables(tables)
    
    except ImportError:
        st.warning("tabula-py not installed. Trying text extraction...")
    except Exception as e:
        st.warning(f"Tabula extraction failed: {str(e)}")
    
    # Method 3: Extract text and try to parse
    try:
        import PyPDF2
        
        file.seek(0)
        pdf_reader = PyPDF2.PdfReader(file)
        
        all_text = ""
        for page in pdf_reader.pages:
            all_text += page.extract_text() + "\n"
        
        if all_text.strip():
            st.info("No tables found. Attempting to parse text content...")
            
            from utils.parser import parse_text_to_dataframe
            df = parse_text_to_dataframe(all_text)
            
            if df is not None and len(df) > 0:
                st.success("✅ Successfully parsed text content")
                return df
    
    except Exception as e:
        st.error(f"Text extraction failed: {str(e)}")
    
    st.error("❌ Could not extract structured data from PDF")
    st.info("""
    **Tips for better PDF parsing:**
    - Ensure PDF contains actual tables (not images)
    - Use PDFs with clear table borders
    - Consider using OCR for scanned documents
    """)
    
    return None

def parse_docx(file):
    """
    Parse DOCX file and extract tables
    
    Returns:
        DataFrame or list of DataFrames
    """
    try:
        from docx import Document
        
        doc = Document(file)
        tables = []
        
        st.info("📝 Extracting tables from Word document...")
        
        # Extract all tables
        for table_num, table in enumerate(doc.tables, 1):
            data = []
            
            for row in table.rows:
                row_data = []
                for cell in row.cells:
                    row_data.append(cell.text.strip())
                data.append(row_data)
            
            if len(data) > 1:
                # First row as header
                df = pd.DataFrame(data[1:], columns=data[0])
                df = df.dropna(how='all', axis=1)
                df = df.dropna(how='all', axis=0)
                
                if len(df) > 0:
                    tables.append(df)
                    st.success(f"✅ Found table {table_num}")
        
        if tables:
            if len(tables) == 1:
                return tables[0]
            else:
                st.info(f"Found {len(tables)} tables. Combining them...")
                return combine_tables(tables)
        else:
            # No tables found, try to extract text
            st.info("No tables found. Extracting text content...")
            
            all_text = ""
            for para in doc.paragraphs:
                all_text += para.text + "\n"
            
            if all_text.strip():
                from utils.parser import parse_text_to_dataframe
                df = parse_text_to_dataframe(all_text)
                
                if df is not None:
                    st.success("✅ Successfully parsed text content")
                    return df
            
            st.warning("No structured data found in document")
            return None
    
    except ImportError:
        st.error("python-docx not installed. Cannot parse DOCX files.")
        return None
    except Exception as e:
        st.error(f"DOCX parsing error: {str(e)}")
        return None

def combine_tables(tables):
    """
    Combine multiple DataFrames intelligently
    
    Args:
        tables: List of DataFrames
        
    Returns:
        pd.DataFrame: Combined DataFrame
    """
    if not tables:
        return None
    
    if len(tables) == 1:
        return tables[0]
    
    st.write("### Multiple Tables Found")
    
    # Show preview of each table
    for i, df in enumerate(tables, 1):
        with st.expander(f"Table {i} - {len(df)} rows × {len(df.columns)} columns"):
            st.dataframe(df.head())
    
    # Ask user how to combine
    combine_method = st.radio(
        "How should we combine these tables?",
        [
            "Use first table only",
            "Concatenate all tables (stack vertically)",
            "Merge all tables (combine columns)",
            "Keep separate - export individually"
        ]
    )
    
    if combine_method == "Use first table only":
        return tables[0]
    
    elif combine_method == "Concatenate all tables (stack vertically)":
        try:
            # Try to align columns
            combined = pd.concat(tables, ignore_index=True)
            st.success(f"✅ Combined {len(tables)} tables")
            return combined
        except:
            st.error("Could not concatenate tables (different structures)")
            return tables[0]
    
    elif combine_method == "Merge all tables (combine columns)":
        try:
            combined = tables[0]
            for df in tables[1:]:
                combined = pd.concat([combined, df], axis=1)
            st.success(f"✅ Merged {len(tables)} tables")
            return combined
        except:
            st.error("Could not merge tables")
            return tables[0]
    
    else:  # Keep separate
        st.info("Tables will be processed separately")
        # For now, return first table
        # In future, could allow user to select which one
        return tables[0]

def extract_text_from_pdf(file):
    """Extract raw text from PDF (no table detection)"""
    try:
        import PyPDF2
        
        pdf_reader = PyPDF2.PdfReader(file)
        text = ""
        
        for page in pdf_reader.pages:
            text += page.extract_text()
        
        return text
    except:
        return None

def extract_text_from_docx(file):
    """Extract raw text from DOCX"""
    try:
        from docx import Document
        
        doc = Document(file)
        text = ""
        
        for para in doc.paragraphs:
            text += para.text + "\n"
        
        return text
    except:
        return None