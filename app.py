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
if 'df' not in st.session_state:
    st.session_state.df = None
if 'data_structure' not in st.session_state:
    st.session_state.data_structure = None
if 'df_organized' not in st.session_state:
    st.session_state.df_organized = None
if 'show_pricing' not in st.session_state:
    st.session_state.show_pricing = False

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
    if st.sidebar.button("🚀 Load Demo Data", use_container_width=True, type="secondary"):
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
            with st.expander("🔍 Live Preview", expanded=False):
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
                                st.info(f"ℹ️ {warning}")
                    
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
        st.caption("Supported formats: CSV, Excel (.xlsx, .xls), TXT")
        
        uploaded_file = st.file_uploader(
            "Choose file:",
            type=['csv', 'xlsx', 'xls', 'txt'],
            label_visibility="collapsed"
        )
        
        if uploaded_file:
            with st.spinner("Reading file..."):
                try:
                    import pandas as pd
                    if uploaded_file.name.endswith('.csv') or uploaded_file.name.endswith('.txt'):
                        df_raw = pd.read_csv(uploaded_file)
                    elif uploaded_file.name.endswith(('.xlsx', '.xls')):
                        df_raw = pd.read_excel(uploaded_file)
                    
                    if df_raw is not None:
                        st.session_state.df = df_raw
                        # Increment conversion count
                        increment_conversion_count(st.session_state.user_email)
                        st.success("✓ File uploaded successfully!")
                        st.rerun()
                except Exception as e:
                    st.error(f"❌ Error reading file: {str(e)}")
    
    # Show examples
    with st.expander("View Examples & Tips"):
        # Time Series Example
        st.markdown('<h4 style="font-size: 1.4rem; font-weight: 600;">Time Series Example:</h4>', unsafe_allow_html=True)
        st.code("Date, Sales, Revenue\n2024-01-01, 1500, 45000\n2024-01-02, 2300, 67000\n2024-01-03, 1800, 52000", language="text")
        
        # Panel Data Example
        st.markdown('<h4 style="font-size: 1.4rem; font-weight: 600; margin-top: 1.5rem;">Panel Data Example:</h4>', unsafe_allow_html=True)
        st.code("Company, Year, Revenue, Profit\nApple, 2022, 394328, 99803\nApple, 2023, 383285, 96995\nGoogle, 2022, 282836, 59972\nGoogle, 2023, 307394, 73795", language="text")
        
        # Tips
        st.markdown('<h4 style="font-size: 1.4rem; font-weight: 600; margin-top: 1.5rem;">Tips:</h4>', unsafe_allow_html=True)
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
        
        # Clean the data
        with st.spinner("Cleaning data..."):
            df_clean = clean_dataframe(st.session_state.df)
        
        # Data quality assessment
        from utils.validation import validate_dataframe, get_data_quality_score
        
        with st.spinner("Analyzing data quality..."):
            quality_score = get_data_quality_score(df_clean)
            validation_result = validate_dataframe(df_clean)
        
        # Display quality metrics
        st.markdown('<h3 style="font-size: 1.6rem; font-weight: 600;">Data Quality Assessment</h3>', unsafe_allow_html=True)
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            # Quality score
            if quality_score >= 80:
                color = "green"
                status = "Excellent"
            elif quality_score >= 60:
                color = "orange"
                status = "Good"
            else:
                color = "red"
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
        if validation_result["issues"]:
            with st.expander("Issues Found", expanded=True):
                for issue in validation_result["issues"]:
                    st.error(f"{issue}")
        
        if validation_result["warnings"]:
            with st.expander("Warnings", expanded=False):
                for warning in validation_result["warnings"]:
                    st.warning(f"{warning}")
        
        st.markdown("---")
        
        # Structure detection
        st.markdown('<h3 style="font-size: 1.6rem; font-weight: 600;">Structure Detection</h3>', unsafe_allow_html=True)
        with st.spinner("Detecting data structure..."):
            structure, date_col, entity_col = detect_data_structure(df_clean)
            st.session_state.data_structure = (structure, date_col, entity_col)
        
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
        
        # Add pagination for large datasets
        if len(df_clean) > 100:
            st.info(f"Showing first 100 of {len(df_clean):,} rows")
            st.dataframe(df_clean.head(100), use_container_width=True, height=300)
        else:
            st.dataframe(df_clean, use_container_width=True, height=300)
        
        # Column information
        with st.expander("Detailed Column Information"):
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
        
        # Save cleaned data
        st.session_state.df = df_clean
        
        # Quick actions
        st.markdown("---")
        st.markdown('<h3 style="font-size: 1.6rem; font-weight: 600;">Quick Actions</h3>', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("Fix Missing Values", use_container_width=True):
                st.info("Missing value imputation feature coming soon!")
        
        with col2:
            if st.button("Remove Duplicates", use_container_width=True):
                if validation_result['duplicate_rows'] > 0:
                    df_clean = df_clean.drop_duplicates()
                    st.session_state.df = df_clean
                    st.success(f"Removed {validation_result['duplicate_rows']} duplicate rows")
                    st.rerun()
                else:
                    st.info("No duplicate rows found")
        
    else:
        st.info("Please input data in the Input tab first")

# TAB 3: ORGANIZE
with tab3:
    if st.session_state.df is not None and st.session_state.data_structure is not None:
        st.markdown('<h2 class="subheader">Step 3: Organize & Refine Data</h2>', unsafe_allow_html=True)
        
        df = st.session_state.df
        structure, date_col, entity_col = st.session_state.data_structure
        
        if structure == "Time Series" and date_col:
            df_organized = organize_time_series(df, date_col)
        elif structure == "Panel Data" and date_col and entity_col:
            df_organized = organize_panel_data(df, date_col, entity_col)
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