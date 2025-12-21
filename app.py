"""
Smart Data Organizer - Phase 2 with Authentication & Payments
Entry Point: streamlit run app.py
"""

import streamlit as st
from utils.scraping import scrape_url
from utils.parser import parse_text_to_dataframe
from utils.detection import detect_data_structure
from utils.cleaning import clean_dataframe
from utils.organization import organize_time_series, organize_panel_data, organize_cross_sectional
from utils.export import export_to_csv, export_to_excel
from utils.auth import (
    show_login_page, is_logged_in, get_current_user, 
    show_user_sidebar, can_convert, increment_conversion_count, is_admin
)
from utils.payment import show_pricing_page, show_billing_portal
from admin_panel import show_admin_panel
from utils.validation import validate_data_input, validate_dataframe, get_data_quality_score
import pandas as pd


# Page configuration
st.set_page_config(
    page_title="Smart Data Organizer",
    page_icon="📊",  # You can remove this or keep it - Streamlit needs an icon
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for larger fonts and left alignment
st.markdown("""
    <style>
    /* Main header styling - larger and left-aligned */
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: left;
        margin-bottom: 1rem;
    }
    
    /* Subheader styling */
    .subheader {
        font-size: 1.8rem;
        font-weight: 600;
        color: #2c3e50;
        text-align: left;
        margin-top: 1.5rem;
        margin-bottom: 1rem;
    }
    
    /* Regular text */
    .stMarkdown, .stText {
        font-size: 1.1rem !important;
        text-align: left;
    }
    
    /* Metric cards - larger text */
    [data-testid="stMetricValue"] {
        font-size: 2.2rem !important;
        font-weight: bold !important;
    }
    
    [data-testid="stMetricLabel"] {
        font-size: 1.2rem !important;
        font-weight: 600 !important;
    }
    
    /* Button text */
    .stButton > button {
        font-size: 1.1rem !important;
        font-weight: 600 !important;
    }
    
    /* Tab text */
    .stTabs [data-baseweb="tab-list"] {
        font-size: 1.2rem !important;
        font-weight: 600 !important;
    }
    
    /* Dataframe headers */
    .dataframe th {
        font-size: 1.1rem !important;
        font-weight: 600 !important;
    }
    
    /* Dataframe cells */
    .dataframe td {
        font-size: 1rem !important;
    }
    
    /* Input labels */
    .stTextInput label, .stTextArea label, .stSelectbox label {
        font-size: 1.2rem !important;
        font-weight: 600 !important;
    }
    
    /* Success/Info/Warning/Error messages */
    .stAlert {
        font-size: 1.1rem !important;
    }
    
    /* Sidebar text */
    .css-1d391kg {
        font-size: 1.1rem !important;
    }
    
    /* Force left alignment for all containers */
    .main .block-container {
        padding-left: 2rem;
        padding-right: 2rem;
    }
    
    /* Remove right padding to push content left */
    .css-1v0mbdj {
        padding-right: 0 !important;
    }
    
    /* Download buttons */
    .stDownloadButton button {
        width: 100%;
        font-size: 1.1rem;
    }
    
    /* Make the title in browser tab larger */
    .css-10trblm {
        font-size: 1.3rem !important;
    }
    </style>
""", unsafe_allow_html=True)

# Initialize session state
# Initialize session state - Add this RIGHT AFTER your page config
# This prevents continuous re-processing

# Core data states
if 'df' not in st.session_state:
    st.session_state.df = None
if 'data_structure' not in st.session_state:
    st.session_state.data_structure = None
if 'df_organized' not in st.session_state:
    st.session_state.df_organized = None
if 'show_pricing' not in st.session_state:
    st.session_state.show_pricing = False

# Processing flags to prevent re-running
if 'file_processed' not in st.session_state:
    st.session_state.file_processed = False
if 'data_cleaned' not in st.session_state:
    st.session_state.data_cleaned = False
if 'structure_detected' not in st.session_state:
    st.session_state.structure_detected = False

# File upload tracking
if 'last_uploaded_file' not in st.session_state:
    st.session_state.last_uploaded_file = None

# Check if user is logged in
if not is_logged_in():
    # Show login page
    show_login_page()
    st.stop()

# User is logged in - show main app
user = get_current_user()

# Sidebar with user info
show_user_sidebar()

# Navigation
st.sidebar.markdown("---")
st.sidebar.header("Navigation")

# Show admin option if user is admin
if is_admin(st.session_state.user_email):
    page_options = ["Home", "Admin Panel", "Pricing", "Billing"]
    st.sidebar.markdown('<div style="background-color: #ff4b4b; color: white; padding: 2px 8px; border-radius: 12px; font-size: 0.8rem; font-weight: bold;">ADMIN</div>', unsafe_allow_html=True)
else:
    page_options = ["Home", "Pricing", "Billing"]

page = st.sidebar.radio(
    "Go to:",
    page_options,
    label_visibility="collapsed"
)

# Handle different pages
if page == "Admin Panel" and is_admin(st.session_state.user_email):
    show_admin_panel()
    st.stop()
elif page == "Pricing":
    show_pricing_page()
    st.stop()
elif page == "Billing":
    show_billing_portal()
    st.stop()

# Main Home Page
# Main Home Page - Replace line ~100 in your app.py
st.markdown('<p class="main-header">Smart Data Organizer</p>', unsafe_allow_html=True)
st.markdown("<div style='font-size: 1.3rem; text-align: left;'>Transform messy data into clean, organized tables with intelligent structure detection</div>", unsafe_allow_html=True)
st.markdown("---")

# Check if user can perform conversions
if not can_convert(user):
    st.error("""
    ⚠️ **Conversion Limit Reached**
    
    You've used all your free conversions this month.
    
    Upgrade to Pro for unlimited conversions!
    """)
    
    if st.button("Upgrade Now", type="primary"):
        st.session_state.show_pricing = True
        st.rerun()
    
    st.stop()

# Add demo button for admin
if is_admin(st.session_state.user_email):
    st.sidebar.markdown("---")
    if st.sidebar.button("Load Demo Data", use_container_width=True, type="secondary"):
        sample_data = """Date,Sales,Region,Product
2024-01-01,1500,North,Widget A
2024-01-01,2300,South,Widget B
2024-01-02,1800,North,Widget A
2024-01-02,2100,South,Widget B
2024-01-03,1200,North,Widget A
2024-01-03,1900,South,Widget B
2024-01-04,2100,North,Widget A
2024-01-04,1800,South,Widget B
2024-01-05,1700,North,Widget A
2024-01-05,2200,South,Widget B"""
        
        df_raw = parse_text_to_dataframe(sample_data)
        if df_raw is not None:
            st.session_state.df = df_raw
            st.success("Demo data loaded successfully!")
            st.rerun()

# Sidebar - Input method
with st.sidebar:
    st.markdown("---")
    st.header("Settings")
    input_method = st.radio(
        "Input Method:",
        ["Paste Text", "Web Scraping", "Upload File"],
        help="Choose how you want to input your data"
    )

# Main content area
tab1, tab2, tab3, tab4 = st.tabs(["Input", "Detect", "Organize", "Export"])

# TAB 1: INPUT
with tab1:
    st.markdown('<h2 class="subheader">Step 1: Input Your Data</h2>', unsafe_allow_html=True)
    
    df_raw = None
    
    if input_method == "Paste Text":
        st.markdown("**Paste your messy data below**")
        st.caption("Supports: CSV, TSV, space-separated, pipe-separated, etc.")
        
        text_input = st.text_area(
            "Data Input:",
            height=300,
            placeholder="Date       Sales  Region\n2024-01-01  1500  North\n2024-01-02  2300  South\n...",
            label_visibility="collapsed"
        )
        
        # Live preview for large inputs
        if text_input and len(text_input) > 50:
            with st.expander("Live Preview", expanded=False):
                try:
                    preview_df = parse_text_to_dataframe(text_input[:5000])
                    if preview_df is not None:
                        st.dataframe(preview_df.head(5))
                        st.caption(f"Preview showing 5 of {len(preview_df)} rows")
                except:
                    st.info("Preview not available for this format")
        
        col1, col2, col3 = st.columns([1, 1, 2])
        with col1:
            process_btn = st.button("Process Text", type="primary", use_container_width=True)

        if process_btn:
            if text_input:
                # Validate input first
                validation_result = validate_data_input(text_input)
                
                if not validation_result["valid"]:
                    st.error("Validation failed:")
                    for issue in validation_result["issues"]:
                        st.error(f"• {issue}")
                    
                    if validation_result["warnings"]:
                        st.warning("Warnings:")
                        for warning in validation_result["warnings"]:
                            st.warning(f"• {warning}")
                else:
                    # Show validation summary
                    with st.expander("Validation Results", expanded=True):
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Lines", validation_result["line_count"])
                        with col2:
                            st.metric("Characters", validation_result["char_count"])
                        with col3:
                            st.metric("Delimiter", validation_result["likely_delimiter"])
                        
                        if validation_result["warnings"]:
                            for warning in validation_result["warnings"]:
                                st.info(f"{warning}")
                    
                    # Then process if user confirms
                    if st.button("Confirm and Process", type="primary"):
                        with st.spinner("Processing text..."):
                            # Show progress
                            progress_text = st.empty()
                            progress_bar = st.progress(0)
                            
                            progress_text.text("Analyzing text format...")
                            progress_bar.progress(30)
                            
                            df_raw = parse_text_to_dataframe(text_input)
                            
                            progress_text.text("Creating DataFrame...")
                            progress_bar.progress(70)
                            
                            if df_raw is not None:
                                st.session_state.df = df_raw
                                # Increment conversion count
                                increment_conversion_count(st.session_state.user_email)
                                
                                progress_text.text("Finalizing...")
                                progress_bar.progress(100)
                                
                                time.sleep(0.5)  # Brief pause to show completion
                                
                                st.success("Text processed successfully!")
                                st.rerun()
                            else:
                                st.error("Could not parse the text. Please check the format.")
            else:
                st.warning("Please paste some data first")
    
    elif input_method == "Web Scraping":
        st.markdown("**Enter URL to scrape data**")
        st.caption("Works best with pages containing tables or structured lists")
        
        # Check tier for web scraping limits
        if user['tier'] == 'free':
            st.info("Free tier: Limited to 3 URL scrapes per month")
        
        url_input = st.text_input(
            "Website URL:",
            placeholder="https://example.com/data-page",
            label_visibility="collapsed"
        )
        
        # Advanced options expander
        with st.expander("Advanced Options"):
            use_js = st.checkbox(
                "Use JavaScript rendering", 
                help="Enable for websites that load data dynamically with JavaScript",
                value=False
            )
            timeout = st.slider("Timeout (seconds)", 10, 60, 30)
        
        col1, col2, col3 = st.columns([1, 1, 2])
        with col1:
            scrape_btn = st.button("Scrape URL", type="primary", use_container_width=True)
        
        if scrape_btn:
            if url_input:
                with st.spinner("Scraping website..."):
                    # Show progress
                    progress_bar = st.progress(0)
                    
                    try:
                        # Step 1: Making request
                        progress_text = st.empty()
                        progress_text.text("Connecting to website...")
                        progress_bar.progress(20)
                        
                        # Step 2: Scraping
                        progress_text.text("Extracting data...")
                        progress_bar.progress(50)
                        
                        # Use enhanced scraping function
                        from utils.scraping import scrape_url
                        df_raw = scrape_url(url_input, timeout=timeout, use_selenium=use_js)
                        
                        progress_bar.progress(80)
                        
                        if df_raw is not None:
                            # Clean column names before storing
                            import pandas as pd
                            
                            # Fill NaN column names
                            df_raw.columns = [f'Column_{i}' if pd.isna(col) else str(col) for i, col in enumerate(df_raw.columns)]
                            
                            # Handle duplicate column names
                            cols = pd.Series(df_raw.columns)
                            for dup in cols[cols.duplicated()].unique():
                                cols[cols == dup] = [f'{dup}_{i}' if i != 0 else dup for i in range(sum(cols == dup))]
                            
                            df_raw.columns = cols
                            
                            st.session_state.df = df_raw
                            # Increment conversion count
                            increment_conversion_count(st.session_state.user_email)
                            
                            progress_text.text("Processing data...")
                            progress_bar.progress(100)
                            
                            st.success("Data scraped successfully!")
                            st.rerun()
                        else:
                            progress_bar.progress(0)
                            st.error("Could not extract data from this URL. Try enabling JavaScript rendering.")
                            
                    except Exception as e:
                        progress_bar.progress(0)
                        st.error(f"Scraping failed: {str(e)}")
            else:
                st.warning("Please enter a URL")
    
    elif input_method == "Upload File":
        st.markdown("**Upload your data file**")
        st.caption("Supported formats: CSV, Excel (.xlsx, .xls), TXT, PDF, DOCX")
        
        uploaded_file = st.file_uploader(
            "Choose file:",
            type=['csv', 'xlsx', 'xls', 'txt', 'pdf', 'docx', 'doc'],
            label_visibility="collapsed"
        )
        
        if uploaded_file:
            # Create unique file identifier
            file_id = f"{uploaded_file.name}_{uploaded_file.size}"
            
            # Check if this is a new file or already processed
            if st.session_state.last_uploaded_file != file_id:
                # New file - process it
                file_ext = uploaded_file.name.split('.')[-1].lower()
                
                st.info(f"Uploaded: {uploaded_file.name} ({file_ext.upper()}, {uploaded_file.size / 1024:.1f} KB)")
                
                with st.spinner(f"Reading {file_ext.upper()} file..."):
                    try:
                        # Import the file parser
                        from utils.file_parser import parse_uploaded_file
                        
                        df_raw = parse_uploaded_file(uploaded_file)
                        
                        if df_raw is not None and len(df_raw) > 0:
                            # Clean column names before storing
                            import pandas as pd
                            
                            # Fill NaN column names
                            df_raw.columns = [f'Column_{i}' if pd.isna(col) else str(col) for i, col in enumerate(df_raw.columns)]
                            
                            # Handle duplicate column names
                            cols = pd.Series(df_raw.columns)
                            for dup in cols[cols.duplicated()].unique():
                                cols[cols == dup] = [f'{dup}_{i}' if i != 0 else dup for i in range(sum(cols == dup))]
                            
                            df_raw.columns = cols
                            
                            st.session_state.df = df_raw
                            st.session_state.last_uploaded_file = file_id
                            st.session_state.file_processed = True
                            
                            # Increment conversion count
                            increment_conversion_count(st.session_state.user_email)
                            
                            # Show preview
                            with st.expander("Data Preview", expanded=True):
                                # Clean column names for display
                                df_display = df_raw.copy()
                                
                                # 1. Fill NaN column names (already done but keep for safety)
                                df_display.columns = [f'Column_{i}' if pd.isna(col) else str(col) for i, col in enumerate(df_display.columns)]
                                
                                # 2. Handle duplicate column names (already done but keep for safety)
                                cols_display = pd.Series(df_display.columns)
                                for dup in cols_display[cols_display.duplicated()].unique():
                                    cols_display[cols_display == dup] = [f'{dup}_{i}' if i != 0 else dup for i in range(sum(cols_display == dup))]
                                
                                df_display.columns = cols_display
                                
                                st.dataframe(df_display.head(10), use_container_width=True)
                                st.caption(f"**Total:** {len(df_raw):,} rows × {len(df_raw.columns)} columns")
                                
                                # Show warning if there were issues
                                original_cols = df_raw.columns.tolist()
                                if any(pd.isna(col) for col in original_cols) or len(original_cols) != len(set(original_cols)):
                                    st.warning("Found duplicate or empty column names. These have been renamed for display.")
                            
                            st.success(f"{file_ext.upper()} file processed successfully!")
                            
                            # Auto-advance hint
                            st.info("Click on the Detect tab to continue")
                            
                        else:
                            st.error(f"Could not extract data from {file_ext.upper()} file")
                            st.info("""
                            **Troubleshooting tips:**
                            - For PDFs: Ensure the document contains actual tables (not scanned images)
                            - For Word docs: Data should be in table format
                            - For Excel: Check if file is password-protected
                            """)
                            
                    except Exception as e:
                        st.error(f"Error reading file: {str(e)}")
                        
                        # Show detailed error for debugging
                        with st.expander("Technical Details"):
                            st.code(str(e))
                            st.caption("If this error persists, try saving your data in CSV format.")
            
            else:
                # File already processed - just show preview
                if st.session_state.df is not None:
                    st.success(f"File already loaded: {uploaded_file.name}")
                    
                    with st.expander("Current Data Preview", expanded=False):
                        # Clean column names for display
                        df_display = st.session_state.df.copy()
                        
                        # 1. Fill NaN column names
                        df_display.columns = [f'Column_{i}' if pd.isna(col) else str(col) for i, col in enumerate(df_display.columns)]
                        
                        # 2. Handle duplicate column names
                        cols_display = pd.Series(df_display.columns)
                        for dup in cols_display[cols_display.duplicated()].unique():
                            cols_display[cols_display == dup] = [f'{dup}_{i}' if i != 0 else dup for i in range(sum(cols_display == dup))]
                        
                        df_display.columns = cols_display
                        
                        st.dataframe(df_display.head(10), use_container_width=True)
                        st.caption(f"**Total:** {len(st.session_state.df):,} rows × {len(st.session_state.df.columns)} columns")
                    
                    st.info("Click on the Detect tab to continue, or upload a different file to start over")
                    
                    # Option to reset
                    if st.button("Upload Different File", type="secondary"):
                        st.session_state.df = None
                        st.session_state.last_uploaded_file = None
                        st.session_state.file_processed = False
                        st.session_state.data_cleaned = False
                        st.session_state.structure_detected = False
                        st.rerun()
    
    # Show examples
    with st.expander("View Examples & Tips"):
        # Time Series Example
        st.markdown('<h4 style="font-size: 1.4rem; font-weight: 600;">Time Series Example:</h4>', unsafe_allow_html=True)
        st.code("Date, Sales, Revenue\n2024-01-01, 1500, 45000\n2024-01-02, 2300, 67000\n2024-01-03, 1800, 52000", language="text")
        
        # Panel Data Example
        st.markdown('<h4 style="font-size: 1.4rem; font-weight: 600;">Panel Data Example:</h4>', unsafe_allow_html=True)
        st.code("Company, Year, Revenue, Profit\nApple, 2022, 394328, 99803\nApple, 2023, 383285, 96995\nGoogle, 2022, 282836, 59972\nGoogle, 2023, 307394, 73795", language="text")
        
        # Tips
        st.markdown('<h4 style="font-size: 1.4rem; font-weight: 600;">Tips:</h4>', unsafe_allow_html=True)
        st.markdown("""
        • **Data can be messy** - the app will clean it automatically  
        • **Multiple delimiters** supported (comma, tab, space, pipe)  
        • **Web scraping** works best with HTML tables  
        • **Dates** can be in any common format  
        • **Large datasets** are automatically optimized for performance
        """)

# TAB 2: DETECT
with tab2:
    if st.session_state.df is not None:
        st.markdown('<h2 class="subheader">Step 2: Data Structure Detection</h2>', unsafe_allow_html=True)
        
        # Only clean data if not already cleaned
        if not st.session_state.data_cleaned:
            # Clean the data with error handling
            try:
                with st.spinner("Cleaning data..."):
                    df_clean = clean_dataframe(st.session_state.df)
                
                # Verify cleaning didn't produce empty result
                if df_clean is None or len(df_clean) == 0:
                    st.error("Data cleaning resulted in empty dataset")
                    st.info("Using original data instead...")
                    df_clean = st.session_state.df
                else:
                    st.session_state.data_cleaned = True
                    
            except Exception as e:
                st.error(f"Error during data cleaning: {str(e)}")
                st.info("Continuing with original data...")
                df_clean = st.session_state.df
                
                # Show error details in expander
                with st.expander("Error Details"):
                    st.code(str(e))
            
            # Save cleaned data
            st.session_state.df = df_clean
        else:
            # Use already cleaned data
            df_clean = st.session_state.df
        
        # Data quality assessment - only run once
        if not st.session_state.structure_detected:
            try:
                from utils.validation import validate_dataframe, get_data_quality_score
                
                with st.spinner("Analyzing data quality..."):
                    quality_score = get_data_quality_score(df_clean)
                    validation_result = validate_dataframe(df_clean)
                    
                    # Cache results
                    st.session_state.quality_score = quality_score
                    st.session_state.validation_result = validation_result
                    
            except Exception as e:
                st.warning(f"Could not assess data quality: {str(e)}")
                # Provide default values
                quality_score = 50
                validation_result = {
                    'row_count': len(df_clean),
                    'column_count': len(df_clean.columns),
                    'missing_percentage': 0,
                    'duplicate_rows': 0,
                    'issues': [],
                    'warnings': []
                }
                st.session_state.quality_score = quality_score
                st.session_state.validation_result = validation_result
        else:
            # Use cached results
            quality_score = st.session_state.get('quality_score', 50)
            validation_result = st.session_state.get('validation_result', {
                'row_count': len(df_clean),
                'column_count': len(df_clean.columns),
                'missing_percentage': 0,
                'duplicate_rows': 0,
                'issues': [],
                'warnings': []
            })
        
        # Display quality metrics
        st.markdown('<h3 style="font-size: 1.6rem; font-weight: 600;">Data Quality Assessment</h3>', unsafe_allow_html=True)
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            # Quality score
            if quality_score >= 80:
                status = "Excellent"
            elif quality_score >= 60:
                status = "Good"
            else:
                status = "Needs Improvement"
            
            st.metric("Quality Score", f"{quality_score:.0f}/100")
            st.caption(status)
        
        with col2:
            st.metric("Rows", f"{validation_result['row_count']:,}")
        
        with col3:
            st.metric("Columns", validation_result['column_count'])
        
        with col4:
            missing_pct = validation_result['missing_percentage']
            st.metric("Missing Data", f"{missing_pct:.1f}%")
        
        # Show issues and warnings
        if validation_result.get("issues"):
            with st.expander("Issues Found", expanded=True):
                for issue in validation_result["issues"]:
                    st.error(f"• {issue}")
        
        if validation_result.get("warnings"):
            with st.expander("Warnings", expanded=False):
                for warning in validation_result["warnings"]:
                    st.warning(f"• {warning}")
        
        st.markdown("---")
        
        # Structure detection - only run once
        if not st.session_state.structure_detected:
            st.markdown('<h3 style="font-size: 1.6rem; font-weight: 600;">Structure Detection</h3>', unsafe_allow_html=True)
            
            try:
                with st.spinner("Detecting data structure..."):
                    structure, date_col, entity_col = detect_data_structure(df_clean)
                    st.session_state.data_structure = (structure, date_col, entity_col)
                    st.session_state.structure_detected = True
            except Exception as e:
                st.warning(f"Could not detect data structure: {str(e)}")
                structure = "General Data"
                date_col = None
                entity_col = None
                st.session_state.data_structure = (structure, date_col, entity_col)
                st.session_state.structure_detected = True
        else:
            st.markdown('<h3 style="font-size: 1.6rem; font-weight: 600;">Structure Detection</h3>', unsafe_allow_html=True)
        
        # Get structure from session state
        structure, date_col, entity_col = st.session_state.data_structure
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Detected Structure", structure)
        
        with col2:
            if structure == "Time Series":
                st.info("Single entity over time")
            elif structure == "Panel Data":
                st.info("Multiple entities over time")
            elif structure == "Cross-Sectional":
                st.info("Single point in time")
            else:
                st.info("General data format")
        
        # Key columns detected
        if date_col or entity_col:
            st.markdown('<h3 style="font-size: 1.6rem; font-weight: 600;">Key Columns Detected</h3>', unsafe_allow_html=True)
            cols = st.columns(2)
            
            if date_col:
                with cols[0]:
                    st.success(f"**Date/Time Column:** `{date_col}`")
            
            if entity_col:
                with cols[1]:
                    st.success(f"**Entity Column:** `{entity_col}`")
        
        # Data preview
        st.markdown('<h3 style="font-size: 1.6rem; font-weight: 600;">Cleaned Data Preview</h3>', unsafe_allow_html=True)
        
        try:
            # Add pagination for large datasets
            if len(df_clean) > 100:
                st.info(f"Showing first 100 of {len(df_clean):,} rows")
                st.dataframe(df_clean.head(100), use_container_width=True, height=300)
            else:
                st.dataframe(df_clean, use_container_width=True, height=300)
        except Exception as e:
            st.error(f"Could not display data preview: {str(e)}")
        
        # Column information
        with st.expander("Detailed Column Information"):
            try:
                col_info = []
                for col in df_clean.columns:
                    col_info.append({
                        "Column Name": col,
                        "Data Type": str(df_clean[col].dtype),
                        "Non-Null Values": df_clean[col].notna().sum(),
                        "Null Values": df_clean[col].isna().sum(),
                        "Unique Values": df_clean[col].nunique()
                    })
                st.dataframe(col_info, use_container_width=True)
            except Exception as e:
                st.error(f"Could not generate column information: {str(e)}")
        
        # Quick actions
        st.markdown("---")
        st.markdown('<h3 style="font-size: 1.6rem; font-weight: 600;">Quick Actions</h3>', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("Fix Missing Values", use_container_width=True):
                st.info("Missing value imputation feature coming soon!")
        
        with col2:
            if st.button("Remove Duplicates", use_container_width=True):
                try:
                    dup_count = validation_result.get('duplicate_rows', 0)
                    if dup_count > 0:
                        df_clean = df_clean.drop_duplicates()
                        st.session_state.df = df_clean
                        st.success(f"Removed {dup_count} duplicate rows")
                        st.rerun()
                    else:
                        st.info("No duplicate rows found")
                except Exception as e:
                    st.error(f"Could not remove duplicates: {str(e)}")
        
    else:
        st.info("Please input data in the Input tab first")

# TAB 3: ORGANIZE
with tab3:
    # SAFETY CHECK: Ensure data structure is properly initialized
    if st.session_state.df is None:
        st.warning("No data loaded. Please input data in the Input tab first.")
        st.stop()
    
    if st.session_state.data_structure is None:
        # Initialize with default values
        st.session_state.data_structure = ("General Data", None, None)
    
    # Now safely unpack
    structure, date_col, entity_col = st.session_state.data_structure
        
        # SAFETY CHECK: Ensure columns exist before organizing
        if structure == "Time Series":
            if date_col and date_col in df.columns:
                df_organized = organize_time_series(df, date_col)
            else:
                st.warning(f"Date column '{date_col}' not found in data. Using general organization.")
                df_organized = df.copy()
                
        elif structure == "Panel Data":
            if date_col and entity_col:
                df_organized = organize_panel_data(df, date_col, entity_col)
            else:
                st.warning("Missing date or entity column for panel data. Using general organization.")
                df_organized = df.copy()
                
        elif structure == "Cross-Sectional":
            df_organized = organize_cross_sectional(df)
        else:
            df_organized = df.copy()
        
        st.markdown('<h3 style="font-size: 1.6rem; font-weight: 600;">Select Columns to Keep</h3>', unsafe_allow_html=True)
        cols_to_keep = st.multiselect(
            "Columns:",
            df_organized.columns.tolist(),
            default=df_organized.columns.tolist(),
            label_visibility="collapsed"
        )
        
        if cols_to_keep:
            df_organized = df_organized[cols_to_keep]
        
        st.markdown('<h3 style="font-size: 1.6rem; font-weight: 600;">Organized Data</h3>', unsafe_allow_html=True)
        st.dataframe(df_organized, use_container_width=True, height=400)
        
        with st.expander("Summary Statistics"):
            if len(df_organized.select_dtypes(include=['number']).columns) > 0:
                st.dataframe(df_organized.describe(), use_container_width=True)
            else:
                st.info("No numeric columns for statistics")
        
        st.session_state.df_organized = df_organized
        
    else:
        st.info("Please detect data structure in the Detect tab first")

# TAB 4: EXPORT
with tab4:
    if st.session_state.df_organized is not None:
        st.markdown('<h2 class="subheader">Step 4: Export Your Data</h2>', unsafe_allow_html=True)
        
        df_export = st.session_state.df_organized
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Rows to Export", f"{len(df_export):,}")
        with col2:
            st.metric("Columns to Export", len(df_export.columns))
        with col3:
            completeness = ((df_export.notna().sum().sum()) / (len(df_export) * len(df_export.columns)) * 100)
            st.metric("Data Completeness", f"{completeness:.1f}%")
        
        st.markdown("---")
        
        st.markdown('<h3 style="font-size: 1.6rem; font-weight: 600;">Download Options</h3>', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown('<h4 style="font-size: 1.4rem; font-weight: 600;">CSV Format</h4>', unsafe_allow_html=True)
            st.caption("Universal format, works everywhere")
            csv_data = export_to_csv(df_export)
            st.download_button(
                label="Download CSV",
                data=csv_data,
                file_name="organized_data.csv",
                mime="text/csv",
                type="primary",
                use_container_width=True
            )
        
        with col2:
            st.markdown('<h4 style="font-size: 1.4rem; font-weight: 600;">Excel Format</h4>', unsafe_allow_html=True)
            if user['tier'] == 'free':
                st.caption("Upgrade to Pro for Excel export")
                if st.button("Upgrade to Pro", use_container_width=True):
                    st.session_state.show_pricing = True
                    st.rerun()
            else:
                st.caption("With formatting and styling")
                try:
                    excel_data = export_to_excel(df_export)
                    st.download_button(
                        label="Download Excel",
                        data=excel_data,
                        file_name="organized_data.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        type="primary",
                        use_container_width=True
                    )
                except Exception as e:
                    st.error(f"Excel export error: {str(e)}")
        
        with st.expander("Final Preview"):
            st.dataframe(df_export, use_container_width=True)
        
        st.markdown("---")
        if st.button("Start New Conversion", type="secondary", use_container_width=True):
            st.session_state.df = None
            st.session_state.data_structure = None
            st.session_state.df_organized = None
            st.rerun()
        
    else:
        st.info("Please organize your data in the Organize tab first")

# Footer
st.markdown("---")
st.markdown("""
    <div style='text-align: center; color: gray; font-size: 1.1rem; padding: 20px 0;'>
        <p>Smart Data Organizer v2.1 | Built with Streamlit | Admin Mode Enabled</p>
    </div>
""", unsafe_allow_html=True)