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

# Page configuration
st.set_page_config(
    page_title="Smart Data Organizer",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
    }
    .stDownloadButton button {
        width: 100%;
    }
    .admin-badge {
        background-color: #ff4b4b;
        color: white;
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 0.8rem;
        font-weight: bold;
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
st.markdown('<p class="main-header">Smart Data Organizer</p>', unsafe_allow_html=True)
st.markdown("Transform messy data into clean, organized tables with intelligent structure detection")
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
    st.header("Step 1: Input Your Data")
    
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
                with st.spinner("Processing text..."):
                    df_raw = parse_text_to_dataframe(text_input)
                    if df_raw is not None:
                        st.session_state.df = df_raw
                        # Increment conversion count
                        increment_conversion_count(st.session_state.user_email)
                        st.success("✓ Text processed successfully!")
                        st.rerun()
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
            placeholder="https://example.com/data-page ",
            label_visibility="collapsed"
        )
        
        col1, col2, col3 = st.columns([1, 1, 2])
        with col1:
            scrape_btn = st.button("🌐 Scrape URL", type="primary", use_container_width=True)
        
        if scrape_btn:
            if url_input:
                with st.spinner("Scraping website..."):
                    df_raw = scrape_url(url_input)
                    if df_raw is not None:
                        st.session_state.df = df_raw
                        # Increment conversion count
                        increment_conversion_count(st.session_state.user_email)
                        st.success("✓ Data scraped successfully!")
                        st.rerun()
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
    with st.expander("📖 View Examples & Tips"):
        st.markdown("""
        ### Time Series Example:
        ```
        Date, Sales, Revenue
        2024-01-01, 1500, 45000
        2024-01-02, 2300, 67000
        2024-01-03, 1800, 52000
        ```
        
        ### Panel Data Example:
        ```
        Company, Year, Revenue, Profit
        Apple, 2022, 394328, 99803
        Apple, 2023, 383285, 96995
        Google, 2022, 282836, 59972
        Google, 2023, 307394, 73795
        ```
        
        ### Tips:
        - Data can be messy - the app will clean it automatically
        - Multiple delimiters supported (comma, tab, space, pipe)
        - Web scraping works best with HTML tables
        """)

# TAB 2: DETECT
with tab2:
    if st.session_state.df is not None:
        st.header("Step 2: Data Structure Detection")
        
        df_clean = clean_dataframe(st.session_state.df)
        structure, date_col, entity_col = detect_data_structure(df_clean)
        st.session_state.data_structure = (structure, date_col, entity_col)
        
        # Display detection results
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            structure_icons = {
                "Time Series": "📈",
                "Panel Data": "📊",
                "Cross-Sectional": "📉",
                "General Data": "📋"
            }
            st.metric(f"{structure_icons.get(structure, '📋')} Structure", structure.split()[0])
        
        with col2:
            st.metric("📏 Rows", f"{len(df_clean):,}")
        
        with col3:
            st.metric("Columns", len(df_clean.columns))
        
        with col4:
            missing = df_clean.isna().sum().sum()
            st.metric("Missing", missing)
        
        st.markdown("---")
        
        if date_col or entity_col:
            st.subheader("Key Columns Detected")
            col1, col2 = st.columns(2)
            
            with col1:
                if date_col:
                    st.success(f"**Date Column:** `{date_col}`")
            
            with col2:
                if entity_col:
                    st.success(f"**Entity Column:** `{entity_col}`")
        
        st.subheader("👀 Cleaned Data Preview")
        st.dataframe(df_clean, use_container_width=True, height=300)
        
        with st.expander("Column Information"):
            col_info = []
            for col in df_clean.columns:
                col_info.append({
                    "Column": col,
                    "Type": str(df_clean[col].dtype),
                    "Non-Null": df_clean[col].notna().sum(),
                    "Null": df_clean[col].isna().sum(),
                    "Unique": df_clean[col].nunique()
                })
            st.dataframe(col_info, use_container_width=True)
        
        st.session_state.df = df_clean
        
    else:
        st.info("👈 Please input data in the **Input** tab first")

# TAB 3: ORGANIZE
with tab3:
    if st.session_state.df is not None and st.session_state.data_structure is not None:
        st.header("Step 3: Organize & Refine Data")
        
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
        
        st.subheader("Select Columns to Keep")
        cols_to_keep = st.multiselect(
            "Columns:",
            df_organized.columns.tolist(),
            default=df_organized.columns.tolist(),
            label_visibility="collapsed"
        )
        
        if cols_to_keep:
            df_organized = df_organized[cols_to_keep]
        
        st.subheader("✨ Organized Data")
        st.dataframe(df_organized, use_container_width=True, height=400)
        
        with st.expander("Summary Statistics"):
            if len(df_organized.select_dtypes(include=['number']).columns) > 0:
                st.dataframe(df_organized.describe(), use_container_width=True)
            else:
                st.info("No numeric columns for statistics")
        
        st.session_state.df_organized = df_organized
        
    else:
        st.info("👈 Please detect data structure in the **Detect** tab first")

# TAB 4: EXPORT
with tab4:
    if st.session_state.df_organized is not None:
        st.header("Step 4: Export Your Data")
        
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
        
        st.subheader("Download Options")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### CSV Format")
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
            st.markdown("### Excel Format")
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
                        label="📥 Download Excel",
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
        st.info("Please organize your data in the **Organize** tab first")

# Footer
st.markdown("---")
st.markdown("""
    <div style='text-align: center; color: gray;'>
        <p>Smart Data Organizer v2.1 | Built with Streamlit | Admin Mode Enabled</p>
    </div>
""", unsafe_allow_html=True)