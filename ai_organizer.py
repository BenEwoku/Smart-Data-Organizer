"""
🤖 AI Organizer Tab - Complete Tab 6 Implementation
"""
import streamlit as st
import pandas as pd
from utils.ai_orchestrator import AIOrchestrator
from io import BytesIO

def show_ai_organizer_tab():
    """Main AI Organizer Tab"""
    
    # ==================== HEADER ====================
    st.markdown("""
    <div style="
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2.5rem;
        border-radius: 15px;
        margin-bottom: 2rem;
        color: white;
        text-align: center;
    ">
        <h1 style="color: white; margin: 0; font-size: 2.8rem;">🤖 AI Data Organizer</h1>
        <p style="color: rgba(255, 255, 255, 0.95); font-size: 1.2rem; margin: 0.8rem 0 0 0;">
        Transform ANY text into organized data • 100% Free • No API Keys Required
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Feature Cards
    st.markdown("### AI Features")
    
    feature_cols = st.columns(4)
    
    with feature_cols[0]:
        st.markdown("""
        <div style="
            background: white;
            padding: 1.5rem;
            border-radius: 10px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
            text-align: center;
            border-top: 4px solid #667eea;
        ">
            <div style="font-size: 2.5rem; margin-bottom: 0.5rem;">📊</div>
            <h4 style="margin: 0;">Data Extraction</h4>
            <p style="color: #666; font-size: 0.9rem; margin: 0.5rem 0 0 0;">
            Extract tables from any text
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    with feature_cols[1]:
        st.markdown("""
        <div style="
            background: white;
            padding: 1.5rem;
            border-radius: 10px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
            text-align: center;
            border-top: 4px solid #764ba2;
        ">
            <div style="font-size: 2.5rem; margin-bottom: 0.5rem;">📝</div>
            <h4 style="margin: 0;">Summarization</h4>
            <p style="color: #666; font-size: 0.9rem; margin: 0.5rem 0 0 0;">
            Generate concise summaries
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    with feature_cols[2]:
        st.markdown("""
        <div style="
            background: white;
            padding: 1.5rem;
            border-radius: 10px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
            text-align: center;
            border-top: 4px solid #4CAF50;
        ">
            <div style="font-size: 2.5rem; margin-bottom: 0.5rem;">🌍</div>
            <h4 style="margin: 0;">Translation</h4>
            <p style="color: #666; font-size: 0.9rem; margin: 0.5rem 0 0 0;">
            Translate text to English
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    with feature_cols[3]:
        st.markdown("""
        <div style="
            background: white;
            padding: 1.5rem;
            border-radius: 10px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
            text-align: center;
            border-top: 4px solid #FF9800;
        ">
            <div style="font-size: 2.5rem; margin-bottom: 0.5rem;">🔍</div>
            <h4 style="margin: 0;">Insights</h4>
            <p style="color: #666; font-size: 0.9rem; margin: 0.5rem 0 0 0;">
            Generate data insights
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    # ==================== INITIALIZE AI ====================
    if 'ai_orchestrator' not in st.session_state:
        st.session_state.ai_orchestrator = AIOrchestrator()
    
    # ==================== INPUT SECTION ====================
    st.markdown("### `Input Your Data")
    
    input_method = st.radio(
        "Choose input method:",
        ["Paste Text", "Upload File", "Web URL"],
        horizontal=True,
        label_visibility="collapsed"
    )
    
    raw_text = ""
    
    if input_method == "Paste Text":
        # Load example if available
        if 'ai_example_text' in st.session_state:
            raw_text = st.session_state.ai_example_text
        
        raw_text = st.text_area(
            "Paste your text here:",
            value=raw_text,
            height=250,
            placeholder="""Examples of what you can paste:

INVOICE #1001
Date: 2024-01-15
Customer: Acme Corp
Total: $125.00

OR

Name, Email, Phone
John, john@email.com, 555-1234
Sarah, sarah@email.com, 555-5678

OR any unstructured text from PDFs, emails, documents...""",
            label_visibility="collapsed"
        )
    
    elif input_method == "Upload File":
        uploaded_file = st.file_uploader(
            "Upload a file:",
            type=['txt', 'pdf', 'doc', 'docx', 'csv'],
            help="Text will be extracted automatically"
        )
        
        if uploaded_file:
            with st.spinner("Extracting text..."):
                raw_text = extract_text_from_file(uploaded_file)
                st.success(f"Extracted {len(raw_text)} characters")
    
    elif input_method == "Web URL":
        url = st.text_input("Enter URL:")
        if url:
            with st.spinner("Fetching content..."):
                try:
                    import requests
                    from bs4 import BeautifulSoup
                    response = requests.get(url, timeout=10)
                    soup = BeautifulSoup(response.content, 'html.parser')
                    raw_text = soup.get_text()
                    st.success(f"Fetched {len(raw_text)} characters")
                except:
                    st.error("Could not fetch URL")
    
    # ==================== AI FEATURES SELECTION ====================
    st.markdown("### Select AI Features")
    
    feature_options = {
        "Extract Data": "extract",
        "Summarize": "summarize", 
        "Translate": "translate",
        "Clean Data": "clean",
        "Generate Insights": "insights"
    }
    
    selected_features = []
    cols = st.columns(5)
    
    for idx, (display_name, feature_key) in enumerate(feature_options.items()):
        with cols[idx % 5]:
            if st.checkbox(display_name, value=(feature_key in ["extract", "summarize"])):
                selected_features.append(feature_key)
    
    # ==================== QUICK EXAMPLES ====================
    st.markdown("### Quick Examples")
    
    example_cols = st.columns(3)
    
    with example_cols[0]:
        if st.button("Invoice Example", width='stretch'):
            st.session_state.ai_example_text = """INVOICE #: INV-2024-001
Date: January 15, 2024
Customer: Acme Corporation
Contact: sales@acme.com | +1-555-123-4567

ITEMS:
1. Widget Pro - 2 units @ $49.99 = $99.98
2. Premium Support - 1 year @ $199.00 = $199.00

SUBTOTAL: $298.98
TAX (8%): $23.92
TOTAL: $322.90

Payment Terms: Net 30
Due Date: February 14, 2024"""
            st.rerun()
    
    with example_cols[1]:
        if st.button("Contact List", width='stretch'):
            st.session_state.ai_example_text = """Name, Email, Phone, Department
John Smith, john@company.com, 555-0101, Sales
Sarah Johnson, sarah@company.com, 555-0102, Marketing
Mike Brown, mike@company.com, 555-0103, Engineering
Lisa Wang, lisa@company.com, 555-0104, HR
David Lee, david@company.com, 555-0105, Finance"""
            st.rerun()
    
    with example_cols[2]:
        if st.button("Product Inventory", width='stretch'):
            st.session_state.ai_example_text = """Product ID | Product Name | Category | Price | Stock
PROD-001 | Laptop Pro | Electronics | $1,299.00 | 45
PROD-002 | Wireless Mouse | Accessories | $49.99 | 120
PROD-003 | Monitor 27" | Electronics | $349.99 | 28
PROD-004 | Keyboard RGB | Accessories | $89.99 | 75
PROD-005 | USB-C Hub | Accessories | $29.99 | 200"""
            st.rerun()
    
    # ==================== PROCESS BUTTON ====================
    if raw_text and len(raw_text) > 10 and selected_features:
        st.markdown("---")
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("PROCESS WITH AI", type="primary", width='stretch', use_container_width=True):
                with st.spinner("AI is processing your data..."):
                    # Process with AI
                    results = st.session_state.ai_orchestrator.process(raw_text, selected_features)
                    
                    # Store results
                    st.session_state.ai_results = results
                    
                    # Show success
                    st.success("AI processing complete!")
    
    # ==================== DISPLAY RESULTS ====================
    if 'ai_results' in st.session_state:
        results = st.session_state.ai_results
        
        st.markdown("---")
        st.markdown("## AI Processing Results")
        
        # Stats Cards
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            success_count = sum(1 for r in results["features"].values() if r.get("success"))
            total_count = len(results["features"])
            st.metric("Features", f"{success_count}/{total_count}")
        
        with col2:
            if results.get("dataframe") is not None:
                st.metric("Rows", len(results["dataframe"]))
            else:
                st.metric("Rows", "N/A")
        
        with col3:
            if results.get("dataframe") is not None:
                st.metric("Columns", len(results["dataframe"].columns))
            else:
                st.metric("Columns", "N/A")
        
        with col4:
            providers = set()
            for r in results["features"].values():
                if r.get("success"):
                    providers.add(r.get("provider", "Unknown"))
            st.metric("Providers", len(providers))
        
        # Display Extracted Data
        if results.get("dataframe") is not None:
            st.markdown("### Extracted Data")
            
            df = results["dataframe"]
            st.dataframe(df, width='stretch', height=350)
            
            # Feature Results
            st.markdown("### ✨ AI Analysis Results")
            
            for feature_name, feature_result in results["features"].items():
                icon = get_feature_icon(feature_name)
                with st.expander(f"{icon} {feature_name.title()}", expanded=True):
                    if feature_result.get("success"):
                        st.success("Success")
                        
                        if feature_name == "extract":
                            st.info(f"Extracted {len(df)} rows")
                        
                        elif feature_name == "summarize":
                            content = feature_result.get("content", "")
                            st.write(content)
                        
                        elif feature_name == "translate":
                            content = feature_result.get("content", "")
                            st.write(content)
                        
                        elif feature_name == "insights":
                            content = feature_result.get("content", "")
                            st.write(content)
                        
                        # Show provider info
                        provider = feature_result.get("provider", "Unknown")
                        processing_time = feature_result.get("processing_time", 0)
                        st.caption(f"Provider: {provider} | Time: {processing_time:.2f}s")
                    
                    else:
                        st.error(f"Failed: {feature_result.get('error', 'Unknown error')}")
            
            # Export Section
            st.markdown("---")
            st.markdown("### Export Options")
            
            export_cols = st.columns(5)
            
            with export_cols[0]:
                csv_data = results["export_formats"].get("csv", "")
                if csv_data:
                    st.download_button(
                        label="CSV",
                        data=csv_data,
                        file_name="ai_data.csv",
                        mime="text/csv",
                        width='stretch'
                    )
            
            with export_cols[1]:
                excel_data = results["export_formats"].get("excel")
                if excel_data:
                    st.download_button(
                        label="Excel",
                        data=excel_data,
                        file_name="ai_data.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        width='stretch'
                    )
            
            with export_cols[2]:
                json_data = results["export_formats"].get("json", "")
                if json_data:
                    st.download_button(
                        label="JSON",
                        data=json_data,
                        file_name="ai_data.json",
                        mime="application/json",
                        width='stretch'
                    )
            
            with export_cols[3]:
                # Generate Markdown Report
                if st.button("Generate Report", width='stretch'):
                    report = generate_ai_report(results)
                    st.download_button(
                        label="Download Report",
                        data=report,
                        file_name="ai_report.md",
                        mime="text/markdown",
                        width='stretch'
                    )
            
            with export_cols[4]:
                # Send to main app
                if st.button("Use in App", width='stretch'):
                    st.session_state.df = df
                    st.success("Data loaded! Switch to 'Detect' tab.")
        
        else:
            st.info("No structured data extracted. Try different text or features.")

def extract_text_from_file(uploaded_file):
    """Extract text from uploaded file"""
    import io
    
    if uploaded_file.name.endswith('.pdf'):
        import PyPDF2
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(uploaded_file.getvalue()))
        return "".join([page.extract_text() for page in pdf_reader.pages])
    
    elif uploaded_file.name.endswith(('.doc', '.docx')):
        import docx
        doc = docx.Document(io.BytesIO(uploaded_file.getvalue()))
        return "\n".join([para.text for para in doc.paragraphs])
    
    else:
        return uploaded_file.getvalue().decode('utf-8')

def get_feature_icon(feature_name: str) -> str:
    """Get icon for feature"""
    icons = {
        "extract": "📊",
        "summarize": "📝",
        "translate": "🌍",
        "clean": "🧹",
        "insights": "🔍"
    }
    return icons.get(feature_name, "✨")

def generate_ai_report(results: Dict) -> str:
    """Generate markdown report from AI results"""
    report = f"""# AI Data Analysis Report
Generated: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}

## Overview
- Original text length: {len(results.get('original_text', ''))} characters
- Features processed: {len(results.get('features', {}))}
- Successful features: {sum(1 for r in results.get('features', {}).values() if r.get('success'))}

## 🔧 Features Executed
"""
    
    for feature_name, feature_result in results.get("features", {}).items():
        status = "Success" if feature_result.get("success") else "Failed"
        provider = feature_result.get("provider", "N/A")
        time_taken = feature_result.get("processing_time", 0)
        
        report += f"- **{feature_name.title()}**: {status} (Provider: {provider}, Time: {time_taken:.2f}s)\n"
    
    if results.get("dataframe") is not None:
        df = results["dataframe"]
        report += f"""
## Extracted Data
- Rows: {len(df)}
- Columns: {len(df.columns)}
- Total cells: {len(df) * len(df.columns)}

### Column Summary
"""
        for col in df.columns:
            non_null = df[col].notna().sum()
            unique = df[col].nunique()
            dtype = str(df[col].dtype)
            report += f"- **{col}**: {non_null} non-null, {unique} unique values ({dtype})\n"
    
    report += "\n---\n*Generated by Smart Data Organizer AI*"
    return report