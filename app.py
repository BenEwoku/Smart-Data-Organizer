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
    /* Main header styling - MUCH larger and left-aligned */
    .main-header {
        font-size: 6.5rem;
        font-weight: 900;
        color: #1f77b4;
        text-align: left;
        margin-bottom: 0.5rem;
        line-height: 1.1;
        text-shadow: 1px 1px 3px rgba(0, 0, 0, 0.1);
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
    
    /* GOOGLE CHROME-STYLE COFFEE BROWN TABS WITH RED PROGRESS BAR */
    .stTabs [data-baseweb="tab-list"] {
        font-size: 1.3rem !important;
        font-weight: 600 !important;
        background-color: transparent !important;
        padding: 10px 10px 0 10px !important;
        margin-bottom: 0 !important;
        gap: 4px !important;  /* Increased from 2px for slightly more spacing */
        border-bottom: none !important;
    }

    .stTabs [data-baseweb="tab"] {
        background-color: #d7ccc8 !important;  /* Coffee brown */
        color: #5d4037 !important;  /* Dark brown text */
        padding: 12px 28px 10px 28px !important;  /* Slightly wider padding */
        margin: 0 !important;
        border-radius: 12px 12px 0 0 !important;  /* Slightly more rounded */
        border: 1px solid #bcaaa4 !important;
        border-bottom: none !important;
        transition: all 0.2s ease !important;
        font-size: 1.2rem !important;
        position: relative;
        z-index: 1;
        box-shadow: 0 -2px 5px rgba(0, 0, 0, 0.05);
    }

    /* Add small spacing between tabs (instead of overlap) */
    .stTabs [data-baseweb="tab"]:not(:first-child) {
        margin-left: 2px !important;  /* Small space instead of -5px overlap */
    }

    .stTabs [data-baseweb="tab"]:hover {
        background-color: #efebe9 !important;  /* Lighter coffee on hover */
        color: #3e2723 !important;
        transform: translateY(-2px);
        z-index: 10;
        box-shadow: 0 -4px 8px rgba(0, 0, 0, 0.1);
    }

    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        background-color: #f5f1eb !important;  /* Light cream coffee for active */
        color: #3e2723 !important;  /* Very dark brown */
        font-weight: 700 !important;
        border: 2px solid #a1887f !important;
        border-bottom: 2px solid white !important;  /* Connect to content */
        z-index: 100 !important;
        padding: 12px 28px 12px 28px !important;
        box-shadow: 0 -4px 10px rgba(0, 0, 0, 0.08);
        position: relative;
    }

    /* RED PROGRESS BAR FOR ACTIVE TAB (replaces the white one) */
    .stTabs [data-baseweb="tab"][aria-selected="true"]::before {
        content: '';
        position: absolute;
        bottom: -2px;
        left: -2px;
        right: -2px;
        height: 4px;  /* Progress bar height */
        background: linear-gradient(90deg, #ff6b6b 0%, #ff5252 50%, #ff3838 100%) !important;  /* Red gradient */
        border-radius: 0 0 3px 3px;
        z-index: 101;
        animation: pulse-red 2s infinite ease-in-out;  /* Optional animation */
    }

    /* Optional: Add a pulsing animation to the red progress bar */
    @keyframes pulse-red {
        0% { opacity: 0.8; }
        50% { opacity: 1; }
        100% { opacity: 0.8; }
    }

    /* Remove the default blue indicator */
    .stTabs [data-baseweb="tab"][aria-selected="true"]::after {
        display: none !important;
    }

    /* Tab content area */
    .stTabs [data-baseweb="tab-panel"] {
        background-color: white !important;
        padding: 25px !important;
        border-radius: 0 0 8px 8px !important;
        border: 2px solid #a1887f !important;
        border-top: none !important;
        margin-top: -2px !important;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
        position: relative;
        z-index: 50;
    }
    
    /* COFFEE BROWN TABLE HEADERS */
    .dataframe th {
        font-size: 1.1rem !important;
        font-weight: 600 !important;
        background-color: #d7ccc8 !important;  /* Coffee brown */
        color: #3e2723 !important;  /* Dark brown text */
        padding: 12px 15px !important;
        border: 1px solid #bcaaa4 !important;
        text-align: left !important;
    }
    
    /* Coffee brown hover effect for headers */
    .dataframe th:hover {
        background-color: #bcaaa4 !important;
    }
    
    /* Coffee brown for other table elements if needed */
    .stDataFrame th {
        background-color: #d7ccc8 !important;
        color: #3e2723 !important;
    }
    
    /* Table cells styling */
    .dataframe td {
        font-size: 1rem !important;
        padding: 10px 15px !important;
        border: 1px solid #e0e0e0 !important;
    }
    
    /* Zebra striping for rows */
    .dataframe tr:nth-child(even) {
        background-color: #f9f9f9 !important;
    }
    
    .dataframe tr:nth-child(odd) {
        background-color: white !important;
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
    
    /* Button text - make buttons match green theme */
    .stButton > button {
        font-size: 1.1rem !important;
        font-weight: 600 !important;
        background-color: #4caf50 !important;
        color: white !important;
        border: none !important;
        padding: 10px 20px !important;
        border-radius: 5px !important;
        transition: background-color 0.2s ease !important;
    }
    
    .stButton > button:hover {
        background-color: #45a049 !important;
        box-shadow: 0 2px 5px rgba(0, 0, 0, 0.2);
    }
    
    /* Primary buttons - darker green */
    .stButton > button[kind="primary"] {
        background-color: #2e7d32 !important;
    }
    
    .stButton > button[kind="primary"]:hover {
        background-color: #1b5e20 !important;
    }
    
    /* Secondary buttons - light coffee brown */
    .stButton > button[kind="secondary"] {
        background-color: #d7ccc8 !important;
        color: #3e2723 !important;
    }
    
    .stButton > button[kind="secondary"]:hover {
        background-color: #bcaaa4 !important;
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
        background-color: #4caf50 !important;
        color: white !important;
    }
    
    .stDownloadButton button:hover {
        background-color: #45a049 !important;
    }
    
    /* Make the title in browser tab larger */
    .css-10trblm {
        font-size: 1.3rem !important;
    }
    
    /* Tab content area */
    .stTabs [data-baseweb="tab-panel"] {
        background-color: white !important;
        padding: 25px !important;
        border-radius: 0 0 5px 5px !important;
        border: 1px solid #e0e0e0 !important;
        border-top: none !important;
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

def get_method_description(method):
    """Get description for imputation method"""
    descriptions = {
        'mean': 'Average value (good for normal distributions)',
        'median': 'Middle value (robust to outliers)',
        'mode': 'Most frequent value (for categories)',
        'forward_fill': 'Use previous value',
        'backward_fill': 'Use next value',
        'interpolate': 'Estimate between neighboring values',
        'knn': 'K-Nearest Neighbors estimation',
        'constant': 'Fill with specified value',
        'delete': 'Remove rows with missing values',
        'delete_rows': 'Delete rows where this column has missing values',
        'impute_zero': 'Fill missing with 0',
        'impute_unknown': "Fill missing with 'Unknown'",
        'keep': 'Leave missing values as-is'
    }
    return descriptions.get(method, 'Custom method')

# Main content area
tab1, tab2, tab3, tab4, tab5 = st.tabs(["Input", "Detect", "Organize", "Export", "Impute"])

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
            # Get missing value statistics
            missing_count = df_clean.isna().sum().sum() if df_clean is not None else 0
            missing_pct = validation_result.get('missing_percentage', 0) if 'validation_result' in locals() else 0
            
            if missing_count > 0:
                button_label = f"Fix Missing Values ({missing_count:,} found)"
                
                if st.button(button_label, use_container_width=True, type="primary"):
                    st.success(f"Found {missing_count:,} missing values ({missing_pct:.1f}%)")
                    st.info("""
                    **Missing Value Imputation is now available!**
                    
                    Please navigate to the **"Impute" tab (Tab 5)** to:
                    • View all columns with missing values
                    • Choose imputation methods (mean, median, mode, etc.)
                    • Preview changes before applying
                    • Delete rows/columns with missing data
                    
                    **Click on "Impute" in the tab bar above**
                    """)
                    
                    # Visual indicator
                    st.markdown("""
                    <div style="background-color: #e6f3ff; padding: 10px; border-radius: 5px; border-left: 5px solid #1f77b4; margin: 10px 0;">
                    <strong>Look for this tab:</strong> <span style="background-color: #1f77b4; color: white; padding: 2px 8px; border-radius: 3px; font-weight: bold;">Impute</span>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Show quick preview of missing columns
                    if df_clean is not None:
                        missing_cols = df_clean.columns[df_clean.isna().any()].tolist()
                        if missing_cols:
                            st.write("**Columns with missing values:**")
                            for col in missing_cols[:5]:  # Show first 5
                                missing_in_col = df_clean[col].isna().sum()
                                st.write(f"• `{col}`: {missing_in_col} missing ({missing_in_col/len(df_clean)*100:.1f}%)")
                            
                            if len(missing_cols) > 5:
                                st.caption(f"... and {len(missing_cols) - 5} more columns")
            else:
                if st.button("Check Missing Values", use_container_width=True, disabled=False):
                    st.success("Great! No missing values found in your data.")

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
# TAB 3: ORGANIZE
with tab3:
    # SAFETY CHECK 1: Ensure data is loaded
    if st.session_state.df is None:
        st.warning("No data loaded. Please input data in the Input tab first.")
        st.stop()
    
    # SAFETY CHECK 2: Ensure data structure exists (fix for PDF parsing failure)
    if st.session_state.data_structure is None:
        # Initialize with default values when PDF parsing fails
        st.session_state.data_structure = ("General Data", None, None)
        st.info("Data structure not detected. Using general organization mode.")
    
    # Now safely proceed with your original logic
    if st.session_state.df is not None and st.session_state.data_structure is not None:
        st.markdown('<h2 class="subheader">Step 3: Organize & Refine Data</h2>', unsafe_allow_html=True)
        
        df = st.session_state.df
        structure, date_col, entity_col = st.session_state.data_structure
        
        # ADDITIONAL SAFETY CHECK: Verify DataFrame is valid
        if df.empty or len(df) == 0:
            st.warning("DataFrame is empty. Please check your input data.")
            st.stop()
        
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
        # This should not happen with our safety checks, but keep as backup
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

# Add to your tab definitions at the top of main content
#tab1, tab2, tab3, tab4, tab5 = st.tabs(["Input", "Detect", "Organize", "Export", "Impute"])

# TAB 5: IMPUTE
with tab5:
    if st.session_state.df is not None:
        st.markdown('<h2 class="subheader">Step 5: Handle Missing Values</h2>', unsafe_allow_html=True)
        
        df = st.session_state.df
        
        # Detect missing values
        from utils.imputation import detect_missing_values
        missing_stats = detect_missing_values(df)
        
        # Display summary
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Missing", f"{missing_stats['total_missing']:,}")
        with col2:
            st.metric("Missing %", f"{missing_stats['overall_missing_percent']:.1f}%")
        with col3:
            cols_with_missing = sum(1 for count in missing_stats['missing_by_column'].values() if count > 0)
            st.metric("Columns Affected", cols_with_missing)
        with col4:
            if missing_stats['total_missing'] == 0:
                st.metric("Status", "Clean", delta="No missing values")
            elif missing_stats['overall_missing_percent'] < 5:
                st.metric("Status", "Minor", delta=f"{missing_stats['overall_missing_percent']:.1f}%")
            else:
                st.metric("Status", "Needs Fix", delta=f"{missing_stats['overall_missing_percent']:.1f}%")
        
        if missing_stats['total_missing'] > 0:
            st.markdown("---")
            
            # Option 1: Quick Fix (Auto-impute all)
            with st.expander("Quick Fix (Auto-impute all columns)", expanded=True):
                st.markdown("**Automatically apply recommended imputation methods:**")
                
                # Show suggested methods
                suggestions = []
                for col, method in missing_stats['suggested_methods'].items():
                    if missing_stats['missing_by_column'][col] > 0:
                        suggestions.append({
                            'Column': col,
                            'Type': missing_stats['column_types'][col],
                            'Missing': missing_stats['missing_by_column'][col],
                            'Method': method.upper(),
                            'Description': get_method_description(method)
                        })
                
                if suggestions:
                    suggestions_df = pd.DataFrame(suggestions)
                    st.dataframe(suggestions_df, use_container_width=True)
                    
                    if st.button("Apply All Suggested Methods", type="primary", use_container_width=True):
                        from utils.imputation import batch_impute
                        
                        imputation_map = {}
                        for col, method in missing_stats['suggested_methods'].items():
                            if missing_stats['missing_by_column'][col] > 0:
                                imputation_map[col] = method
                        
                        with st.spinner("Applying imputation..."):
                            df_imputed, results = batch_impute(df, imputation_map)
                            st.session_state.df = df_imputed
                            
                            # Show results
                            st.success(f"Imputed {len(results)} columns successfully!")
                            for col, result in results.items():
                                st.info(f"• **{col}**: {result['imputed_count']} values imputed using {result['method']}")
                            
                            st.rerun()
            
            # Option 2: Column-by-column control
            with st.expander("Advanced Column-by-Column Control", expanded=False):
                st.markdown("**Select specific imputation methods for each column:**")
                
                columns_with_missing = [col for col, count in missing_stats['missing_by_column'].items() 
                                       if count > 0]
                
                selected_columns = st.multiselect(
                    "Select columns to impute:",
                    columns_with_missing,
                    default=columns_with_missing[:3] if len(columns_with_missing) > 3 else columns_with_missing
                )
                
                if selected_columns:
                    imputation_map = {}
                    
                    for col in selected_columns:
                        st.markdown(f"### {col}")
                        col1, col2, col3 = st.columns([2, 2, 1])
                        
                        with col1:
                            st.caption(f"**Type:** {missing_stats['column_types'][col]}")
                            st.caption(f"**Missing:** {missing_stats['missing_by_column'][col]} values ({missing_stats['missing_percentage'][col]:.1f}%)")
                        
                        with col2:
                            # Method selection based on column type
                            col_type = missing_stats['column_types'][col]
                            
                            if col_type == 'numeric':
                                methods = ['median', 'mean', 'interpolate', 'knn', 'constant', 'delete', 'forward_fill', 'backward_fill']
                                default_method = missing_stats['suggested_methods'].get(col, 'median')
                            elif col_type == 'categorical':
                                methods = ['mode', 'constant', 'delete', 'forward_fill']
                                default_method = missing_stats['suggested_methods'].get(col, 'mode')
                            elif col_type == 'datetime':
                                methods = ['forward_fill', 'backward_fill', 'interpolate', 'constant', 'delete']
                                default_method = missing_stats['suggested_methods'].get(col, 'forward_fill')
                            else:
                                methods = ['mode', 'constant', 'delete', 'forward_fill']
                                default_method = 'mode'
                            
                            method = st.selectbox(
                                f"Method for {col}:",
                                methods,
                                index=methods.index(default_method) if default_method in methods else 0,
                                key=f"method_{col}"
                            )
                        
                        with col3:
                            # Preview button
                            if st.button("Preview", key=f"preview_{col}"):
                                from utils.imputation import get_imputation_preview
                                preview = get_imputation_preview(df, col, method)
                                
                                with st.expander(f"Preview for {col}", expanded=True):
                                    if preview['original_sample']:
                                        st.write("**Before/After Examples:**")
                                        for orig, imp in zip(preview['original_sample'], preview['imputed_sample']):
                                            st.write(f"Row {orig['index']}: `{orig['value']}` → `{imp['value']}`")
                                    
                                    if preview['stats']:
                                        st.write("**Column Statistics:**")
                                        for stat_name, stat_value in preview['stats'].items():
                                            st.write(f"- {stat_name}: {stat_value}")
                        
                        # Store in imputation map
                        imputation_map[col] = method
                        
                        # Custom value input for constant method
                        if method == 'constant':
                            custom_col1, custom_col2 = st.columns(2)
                            with custom_col1:
                                if col_type == 'numeric':
                                    custom_val = st.number_input(
                                        f"Custom value for {col}:",
                                        value=0.0,
                                        key=f"custom_{col}"
                                    )
                                else:
                                    custom_val = st.text_input(
                                        f"Custom value for {col}:",
                                        value="Missing",
                                        key=f"custom_{col}"
                                    )
                                imputation_map[col] = ('constant', custom_val)
                        
                        st.markdown("---")
                    
                    # Apply button
                    if st.button("Apply Selected Imputations", type="primary", use_container_width=True):
                        from utils.imputation import batch_impute
                        
                        with st.spinner("Applying imputations..."):
                            df_imputed, results = batch_impute(df, imputation_map)
                            st.session_state.df = df_imputed
                            
                            # Show summary
                            st.success("Imputation completed!")
                            total_imputed = sum(r['imputed_count'] for r in results.values())
                            st.info(f"**Total values imputed:** {total_imputed}")
                            
                            for col, result in results.items():
                                st.write(f"• **{col}**: {result['imputed_count']} values → {result['method']}")
                            
                            st.rerun()
                        
            # Option 3: Delete rows/columns with granular control
            with st.expander("Delete Missing Values (Column-Specific)", expanded=False):
                st.markdown("**Choose how to handle missing values for each column:**")
                
                # Get columns with missing values
                missing_cols = [col for col, count in missing_stats['missing_by_column'].items() 
                            if count > 0]
                
                if missing_cols:
                    # Create a multi-select for columns
                    st.markdown("### Select Columns to Clean")
                    selected_columns = st.multiselect(
                        "Choose columns to handle missing values:",
                        missing_cols,
                        default=missing_cols[:3] if len(missing_cols) > 3 else missing_cols,
                        help="Select which columns you want to clean"
                    )
                    
                    if selected_columns:
                        st.markdown("### Choose Action for Each Column")
                        
                        # Dictionary to store actions for each column
                        column_actions = {}
                        
                        for col in selected_columns:
                            st.markdown(f"#### {col}")
                            col_type = missing_stats['column_types'][col]
                            missing_count = missing_stats['missing_by_column'][col]
                            missing_pct = missing_stats['missing_percentage'][col]
                            
                            col1, col2, col3 = st.columns([3, 2, 1])
                            
                            with col1:
                                st.caption(f"**Type:** {col_type}")
                                st.caption(f"**Missing:** {missing_count} values ({missing_pct:.1f}%)")
                            
                            with col2:
                                # Different options based on column type
                                if col_type == 'numeric':
                                    action_options = ["Keep as is", "Impute with median", "Impute with mean", 
                                                    "Impute with zero", "Delete rows", "Fill with custom value"]
                                elif col_type == 'categorical':
                                    action_options = ["Keep as is", "Impute with mode", "Impute with 'Unknown'", 
                                                    "Delete rows", "Fill with custom value"]
                                elif col_type == 'datetime':
                                    action_options = ["Keep as is", "Forward fill", "Backward fill", 
                                                    "Delete rows", "Fill with custom value"]
                                else:
                                    action_options = ["Keep as is", "Impute with mode", "Delete rows", 
                                                    "Fill with custom value"]
                                
                                # Select action
                                action = st.selectbox(
                                    f"Action for {col}:",
                                    action_options,
                                    key=f"action_{col}"
                                )
                            
                            with col3:
                                # Preview button
                                if st.button("🔍 Preview", key=f"preview_action_{col}"):
                                    st.info(f"Preview for {col}: {action}")
                            
                            # Store custom values if needed
                            custom_value = None
                            if "custom value" in action.lower():
                                if col_type == 'numeric':
                                    custom_value = st.number_input(
                                        f"Custom value for {col}:",
                                        value=0.0,
                                        key=f"custom_val_{col}"
                                    )
                                else:
                                    custom_value = st.text_input(
                                        f"Custom value for {col}:",
                                        value="Unknown",
                                        key=f"custom_val_{col}"
                                    )
                            
                            column_actions[col] = {
                                'action': action,
                                'custom_value': custom_value,
                                'type': col_type
                            }
                            
                            st.markdown("---")
                        
                        # Apply all actions button
                        if st.button("Apply All Selected Actions", type="primary", use_container_width=True):
                            df_processed = df.copy()
                            results = []
                            
                            with st.spinner("Applying actions..."):
                                for col, actions in column_actions.items():
                                    action = actions['action']
                                    custom_val = actions['custom_value']
                                    
                                    if action == "Delete rows":
                                        # Delete rows where this column has missing values
                                        before_len = len(df_processed)
                                        df_processed = df_processed.dropna(subset=[col])
                                        after_len = len(df_processed)
                                        deleted = before_len - after_len
                                        results.append(f"**{col}**: Deleted {deleted} rows")
                                        
                                    elif "Impute with median" in action:
                                        df_processed[col] = df_processed[col].fillna(df_processed[col].median())
                                        imputed = df[col].isna().sum() - df_processed[col].isna().sum()
                                        results.append(f"**{col}**: Imputed {imputed} values with median")
                                        
                                    elif "Impute with mean" in action:
                                        df_processed[col] = df_processed[col].fillna(df_processed[col].mean())
                                        imputed = df[col].isna().sum() - df_processed[col].isna().sum()
                                        results.append(f"**{col}**: Imputed {imputed} values with mean")
                                        
                                    elif "Impute with mode" in action:
                                        mode_val = df_processed[col].mode()
                                        fill_val = mode_val[0] if len(mode_val) > 0 else "Unknown"
                                        df_processed[col] = df_processed[col].fillna(fill_val)
                                        imputed = df[col].isna().sum() - df_processed[col].isna().sum()
                                        results.append(f"**{col}**: Imputed {imputed} values with mode")
                                        
                                    elif "Forward fill" in action:
                                        df_processed[col] = df_processed[col].ffill()
                                        imputed = df[col].isna().sum() - df_processed[col].isna().sum()
                                        results.append(f"**{col}**: Forward filled {imputed} values")
                                        
                                    elif "Backward fill" in action:
                                        df_processed[col] = df_processed[col].bfill()
                                        imputed = df[col].isna().sum() - df_processed[col].isna().sum()
                                        results.append(f"**{col}**: Backward filled {imputed} values")
                                        
                                    elif "Impute with zero" in action:
                                        df_processed[col] = df_processed[col].fillna(0)
                                        imputed = df[col].isna().sum() - df_processed[col].isna().sum()
                                        results.append(f"**{col}**: Imputed {imputed} values with zero")
                                        
                                    elif "Impute with 'Unknown'" in action:
                                        df_processed[col] = df_processed[col].fillna("Unknown")
                                        imputed = df[col].isna().sum() - df_processed[col].isna().sum()
                                        results.append(f"**{col}**: Imputed {imputed} values with 'Unknown'")
                                        
                                    elif "Fill with custom value" in action and custom_val is not None:
                                        df_processed[col] = df_processed[col].fillna(custom_val)
                                        imputed = df[col].isna().sum() - df_processed[col].isna().sum()
                                        results.append(f"**{col}**: Imputed {imputed} values with '{custom_val}'")
                                    
                                    # For "Keep as is" - do nothing
                                
                                # Update session state
                                st.session_state.df = df_processed
                                
                                # Show results
                                st.success("Actions applied successfully!")
                                st.markdown("### Results Summary")
                                for result in results:
                                    st.write(f"• {result}")
                                
                                # Show data loss warning if rows were deleted
                                rows_deleted = len(df) - len(df_processed)
                                if rows_deleted > 0:
                                    st.warning(f"⚠️ **Note:** {rows_deleted} rows were deleted ({rows_deleted/len(df)*100:.1f}% of data)")
                                
                                st.rerun()
                else:
                    st.info("No columns have missing values to delete.")
                
                st.markdown("---")
                
                # Bulk deletion options (keep the original as well)
                st.markdown("### Bulk Deletion Options")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    if st.button("Delete Rows with ANY Missing", use_container_width=True):
                        original_len = len(df)
                        df_clean = df.dropna()
                        new_len = len(df_clean)
                        removed = original_len - new_len
                        
                        if removed > 0:
                            st.session_state.df = df_clean
                            st.success(f"Removed {removed} rows ({removed/original_len*100:.1f}% of data)")
                            st.rerun()
                        else:
                            st.info("No rows contained missing values")
                
                with col2:
                    if st.button("Delete Columns with ANY Missing", use_container_width=True):
                        original_cols = len(df.columns)
                        df_clean = df.dropna(axis=1)
                        new_cols = len(df_clean.columns)
                        removed = original_cols - new_cols
                        
                        if removed > 0:
                            st.session_state.df = df_clean
                            st.success(f"Removed {removed} columns")
                            st.rerun()
                        else:
                            st.info("No columns contained missing values")

# Footer
st.markdown("---")
st.markdown("""
    <div style='text-align: center; color: gray; font-size: 1.1rem; padding: 20px 0;'>
        <p>Smart Data Organizer v2.1 | Built with Streamlit | Admin Mode Enabled</p>
    </div>
""", unsafe_allow_html=True)