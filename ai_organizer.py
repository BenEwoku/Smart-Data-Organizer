"""
AI Organizer Tab
"""
import streamlit as st
import pandas as pd
from typing import Dict, List, Any
from utils.ai_orchestrator import AIOrchestrator

def show_ai_organizer_tab():
    """Main AI Organizer Tab"""
    
    st.markdown('<h2 class="subheader">AI Data Organizer</h2>', unsafe_allow_html=True)
    
    st.markdown("""
    **Transform text into organized data using AI**
    
    This tool uses AI to extract structured data from any text, 
    whether it's invoices, contact lists, tables, or unstructured content.
    """)
    
    # Initialize AI
    if 'ai_orchestrator' not in st.session_state:
        st.session_state.ai_orchestrator = AIOrchestrator()
    
    # Input Section
    st.markdown("### Input Data")
    
    raw_text = st.text_area(
        "Paste your text here:",
        height=200,
        placeholder="""Paste any text with data to organize. Examples:

Product ID | Product Name | Price | Stock
PROD-001 | Laptop Pro | $1,299.00 | 45
PROD-002 | Wireless Mouse | $49.99 | 120

OR

Name, Email, Phone
John, john@email.com, 555-1234
Sarah, sarah@email.com, 555-5678""",
        label_visibility="collapsed"
    )
    
    # Feature Selection
    st.markdown("### Select Features")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        extract_data = st.checkbox("Extract Data", value=True)
    
    with col2:
        summarize = st.checkbox("Summarize")
    
    with col3:
        insights = st.checkbox("Insights")
    
    selected_features = []
    if extract_data:
        selected_features.append("extract")
    if summarize:
        selected_features.append("summarize")
    if insights:
        selected_features.append("insights")
    
    # Process Button
    if raw_text and len(raw_text) > 10 and selected_features:
        if st.button("Process with AI", type="primary", width='stretch'):
            with st.spinner("Processing..."):
                # Process with AI
                results = st.session_state.ai_orchestrator.process(raw_text, selected_features)
                
                # Store results
                st.session_state.ai_results = results
                
                st.success("Processing complete!")
    
    # Display Results
    if 'ai_results' in st.session_state:
        results = st.session_state.ai_results
        
        st.markdown("---")
        st.markdown("## Results")
        
        # Show extracted data if available
        if results.get("dataframe") is not None and not results["dataframe"].empty:
            df = results["dataframe"]
            
            st.markdown("### Extracted Data")
            st.dataframe(df, width='stretch', height=300)
            
            # Show basic info
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Rows", len(df))
            with col2:
                st.metric("Columns", len(df.columns))
            with col3:
                st.metric("Extraction Method", results["features"]["extract"].get("provider", "local"))
            
            # Export options
            st.markdown("### Export")
            col1, col2 = st.columns(2)
            
            with col1:
                csv = df.to_csv(index=False)
                st.download_button(
                    "Download CSV",
                    csv,
                    "extracted_data.csv",
                    "text/csv",
                    width='stretch'
                )
            
            with col2:
                if st.button("Use in Main App", width='stretch'):
                    st.session_state.df = df
                    st.success("Data loaded! Switch to 'Detect' tab.")
        
        # Show other feature results
        for feature_name in ["summarize", "insights"]:
            if feature_name in results["features"]:
                feature_result = results["features"][feature_name]
                
                if feature_result.get("success"):
                    st.markdown(f"### {feature_name.title()}")
                    
                    content = feature_result.get("content", "")
                    if content:
                        st.write(content)
        
        # If extraction failed, show error
        if "extract" in results["features"] and not results["features"]["extract"].get("success"):
            st.warning("Could not extract structured data. The text might not contain table-like data.")
    
    # Examples
    with st.expander("Examples", expanded=False):
        example_cols = st.columns(2)
        
        with example_cols[0]:
            if st.button("Load Example 1", width='stretch'):
                st.session_state.example_text = """Product ID, Product Name, Category, Price, Stock
PROD-001, Laptop Pro, Electronics, $1299.00, 45
PROD-002, Wireless Mouse, Accessories, $49.99, 120
PROD-003, Monitor 27", Electronics, $349.99, 28"""
        
        with example_cols[1]:
            if st.button("Load Example 2", width='stretch'):
                st.session_state.example_text = """Name: John Smith
Email: john@company.com
Phone: 555-0101
Department: Sales

Name: Sarah Johnson  
Email: sarah@company.com
Phone: 555-0102
Department: Marketing"""
    
    # Load example if set
    if 'example_text' in st.session_state:
        raw_text = st.session_state.example_text