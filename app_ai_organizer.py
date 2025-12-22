"""
AI Organizer Tab for Streamlit App
"""
import streamlit as st
import pandas as pd
from utils.ai_orchestrator import LocalAIOrchestrator
import plotly.express as px

def show_ai_organizer_tab():
    """Main AI Organizer Interface"""
    
    st.markdown("""
    <style>
    .ai-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        color: white;
    }
    .ai-header h1 {
        color: white;
        margin: 0;
        font-size: 2.5rem;
    }
    .ai-header p {
        color: rgba(255, 255, 255, 0.9);
        margin: 0.5rem 0 0 0;
        font-size: 1.1rem;
    }
    .feature-card {
        background: white;
        border-radius: 10px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        border-left: 5px solid #667eea;
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="ai-header">
        <h1>AI Data Organizer</h1>
        <p>Transform ANY unstructured text into clean, organized data • 100% Local • No APIs</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Feature showcase
    with st.expander("✨ What This AI Can Do", expanded=True):
        cols = st.columns(4)
        features = [
            ("Pattern Detection", "Find dates, emails, phones, currencies"),
            ("Language Detection", "Identify text language automatically"),
            ("Structure Analysis", "Detect tables, lists, key-value pairs"),
            ("Smart Organization", "Suggest column names & data types"),
            ("Quality Analysis", "Score data quality & suggest fixes"),
            ("Multiple Export", "CSV, Excel, JSON formats"),
            ("Translation", "Translate column names (basic)"),
            ("Local Processing", "No internet required, 100% private")
        ]
        
        for i, (icon_text, description) in enumerate(features):
            with cols[i % 4]:
                st.markdown(f"""
                <div class="feature-card">
                    <h4>{icon_text}</h4>
                    <p style="font-size: 0.9rem; color: #666;">{description}</p>
                </div>
                """, unsafe_allow_html=True)
    
    # Initialize AI Engine
    if 'ai_engine' not in st.session_state:
        st.session_state.ai_engine = LocalAIOrchestrator()
    
    # Input Section
    st.markdown("### Input Your Data")
    
    input_method = st.radio(
        "Choose input method:",
        ["Paste Text", "Upload File", "Web Content"],
        horizontal=True,
        label_visibility="collapsed"
    )
    
    raw_text = ""
    
    if input_method == "Paste Text":
        # Load example if available
        if 'example_text' in st.session_state:
            raw_text = st.session_state.example_text
        
        raw_text = st.text_area(
            "Paste your unstructured data:",
            value=raw_text,
            height=300,
            placeholder="""Paste ANY unstructured data here. Examples:

• Invoice text: "Invoice #1001 Date: 2024-01-15 Total: $125.00"
• Contact list: "John, john@email.com, 555-1234"
• Tabular data: "Name Age City\nJohn 30 NYC\nSarah 25 London"
• Mixed content from PDFs, emails, documents...
            """,
            help="The AI will automatically detect structure and organize it"
        )
        
        # Quick examples
        st.markdown("**Quick Examples:**")
        example_cols = st.columns(3)
        
        with example_cols[0]:
            if st.button("Invoice", use_container_width=True):
                invoice_text = """INVOICE #INV-2024-001
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
                st.session_state.example_text = invoice_text
                st.rerun()
        
        with example_cols[1]:
            if st.button("Contact List", use_container_width=True):
                contact_text = """Name, Email, Phone, Department, Join Date
John Smith, john@company.com, 555-0101, Sales, 2023-01-15
Sarah Johnson, sarah@company.com, 555-0102, Marketing, 2022-08-22
Mike Brown, mike@company.com, 555-0103, Engineering, 2021-03-10
Lisa Wang, lisa@company.com, 555-0104, HR, 2023-06-30
David Lee, david@company.com, 555-0105, Finance, 2020-11-05"""
                st.session_state.example_text = contact_text
                st.rerun()
        
        with example_cols[2]:
            if st.button("Inventory", use_container_width=True):
                inventory_text = """Product ID | Product Name | Category | Price | Stock | Last Ordered
PROD-001 | Laptop Pro | Electronics | $1,299.00 | 45 | 2024-01-10
PROD-002 | Wireless Mouse | Accessories | $49.99 | 120 | 2024-01-12
PROD-003 | Monitor 27" | Electronics | $349.99 | 28 | 2024-01-08
PROD-004 | Keyboard RGB | Accessories | $89.99 | 75 | 2024-01-11
PROD-005 | USB-C Hub | Accessories | $29.99 | 200 | 2024-01-09"""
                st.session_state.example_text = inventory_text
                st.rerun()
    
    elif input_method == "Upload File":
        uploaded_file = st.file_uploader(
            "Upload text-based file:",
            type=['txt', 'csv', 'pdf', 'doc', 'docx'],
            help="PDF and Word docs will have text extracted"
        )
        
        if uploaded_file:
            with st.spinner(f"Extracting text from {uploaded_file.name}..."):
                raw_text = extract_text_from_file(uploaded_file)
                st.success(f"Extracted {len(raw_text)} characters")
    
    # Processing Options
    with st.expander("Processing Options", expanded=False):
        col1, col2 = st.columns(2)
        with col1:
            auto_translate = st.checkbox("Auto-translate column names", value=True)
            detect_language = st.checkbox("Detect language", value=True)
        with col2:
            infer_types = st.checkbox("Infer data types", value=True)
            suggest_improvements = st.checkbox("Suggest improvements", value=True)
    
    # Process Button
    if raw_text and len(raw_text) > 10:
        col1, col2, col3 = st.columns([1, 1, 3])
        with col1:
            process_btn = st.button("Process with AI", type="primary", use_container_width=True)
        
        if process_btn:
            with st.spinner("AI is analyzing your data..."):
                # Prepare options
                options = {
                    'translate': auto_translate,
                    'detect_language': detect_language,
                    'infer_types': infer_types,
                    'suggest_improvements': suggest_improvements
                }
                
                # Process with AI
                results = st.session_state.ai_engine.process_text(raw_text, options)
                
                # Store results
                st.session_state.ai_results = results
                
                # Show success
                if results['processing_info']['success']:
                    st.success(f"Successfully processed {results['processing_info']['input_length']} characters")
                else:
                    st.error("Processing failed")
    
    # Display Results
    if 'ai_results' in st.session_state:
        results = st.session_state.ai_results
        
        if results['processing_info']['success']:
            # Results Dashboard
            st.markdown("---")
            st.markdown("## AI Analysis Results")
            
            # Summary Cards
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                lang = results['language'].get('detected', 'Unknown')
                conf = results['language'].get('confidence', 0)
                st.metric("Language", lang)
                st.caption(f"Confidence: {conf:.0%}")
            
            with col2:
                structure = results['patterns'].get('structure', {}).get('type', 'Unknown')
                confidence = results['patterns'].get('structure', {}).get('confidence', 0)
                st.metric("Structure", structure)
                st.caption(f"Confidence: {confidence:.0%}")
            
            with col3:
                rows = results['extraction'].get('rows', 0)
                st.metric("Rows", rows)
            
            with col4:
                cols = results['extraction'].get('columns', 0)
                st.metric("Columns", cols)
            
            # Display Extracted Data
            if results['extraction']['success']:
                df = pd.DataFrame(results['extraction']['data_preview'])
                if not df.empty:
                    st.markdown("### Organized Data Preview")
                    
                    # Show data with optional editing
                    edited_df = st.data_editor(
                        df,
                        use_container_width=True,
                        height=400,
                        num_rows="dynamic",
                        column_config={
                            col: st.column_config.TextColumn(col)
                            for col in df.columns
                        }
                    )
                    
                    # AI Suggestions
                    if 'organization' in results and results['organization'].get('suggestions'):
                        st.markdown("### AI Suggestions")
                        
                        suggestions = results['organization']['suggestions']
                        for i, suggestion in enumerate(suggestions[:5]):
                            with st.expander(f"{i+1}. {suggestion['type'].title()}: {suggestion['column']}"):
                                st.write(f"**Suggestion:** {suggestion['suggestion']}")
                                st.write(f"**Reason:** {suggestion['reason']}")
                                st.write(f"**Priority:** {suggestion.get('priority', 'medium').title()}")
                                
                                if suggestion['type'] == 'rename':
                                    st.code(f"df.rename(columns={{'{suggestion['column']}': '{suggestion['suggestion']}'}})")
                    
                    # Export Section
                    st.markdown("---")
                    st.markdown("### Export Organized Data")
                    
                    export_cols = st.columns(4)
                    
                    with export_cols[0]:
                        csv_data = results['export']['csv']
                        st.download_button(
                            label="CSV",
                            data=csv_data,
                            file_name="ai_organized.csv",
                            mime="text/csv",
                            use_container_width=True
                        )
                    
                    with export_cols[1]:
                        excel_data = results['export']['excel']
                        st.download_button(
                            label="Excel",
                            data=excel_data,
                            file_name="ai_organized.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            use_container_width=True
                        )
                    
                    with export_cols[2]:
                        json_data = results['export']['json']
                        st.download_button(
                            label="JSON",
                            data=json_data,
                            file_name="ai_organized.json",
                            mime="application/json",
                            use_container_width=True
                        )
                    
                    with export_cols[3]:
                        if st.button("Send to Pipeline", use_container_width=True):
                            # Convert back to full DataFrame
                            full_df = pd.DataFrame(results['extraction']['data_preview'])
                            st.session_state.df = full_df
                            st.success("Data sent to main pipeline! Switch to 'Detect' tab.")
                    
                    # Insights Section
                    if results['insights']:
                        st.markdown("---")
                        st.markdown("### AI Insights")
                        
                        insights = results['insights']
                        
                        if insights.get('summary'):
                            st.markdown("**Summary:**")
                            for item in insights['summary']:
                                st.write(f"• {item}")
                        
                        if insights.get('warnings'):
                            st.markdown("**Warnings:**")
                            for warning in insights['warnings']:
                                st.warning(f"{warning}")
                        
                        if insights.get('statistics'):
                            stats = insights['statistics']
                            stat_cols = st.columns(4)
                            with stat_cols[0]:
                                st.metric("Total Rows", stats.get('total_rows', 0))
                            with stat_cols[1]:
                                st.metric("Total Columns", stats.get('total_columns', 0))
                            with stat_cols[2]:
                                st.metric("Total Cells", stats.get('total_cells', 0))
                            with stat_cols[3]:
                                completeness = stats.get('completeness', 0)
                                st.metric("Completeness", f"{completeness:.1f}%")
            
            # Raw Analysis (for debugging)
            with st.expander("🔧 Raw Analysis Data", expanded=False):
                st.json(results, expanded=False)

def extract_text_from_file(uploaded_file):
    """Extract text from various file types"""
    import io
    
    if uploaded_file.name.endswith('.pdf'):
        # Use PyPDF2 (already in requirements)
        import PyPDF2
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(uploaded_file.getvalue()))
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text()
        return text
    
    elif uploaded_file.name.endswith(('.doc', '.docx')):
        # Use python-docx (already in requirements)
        import docx
        doc = docx.Document(io.BytesIO(uploaded_file.getvalue()))
        return "\n".join([para.text for para in doc.paragraphs])
    
    elif uploaded_file.name.endswith('.csv'):
        # Read CSV and convert to text representation
        df = pd.read_csv(io.BytesIO(uploaded_file.getvalue()))
        return df.to_string(index=False)
    
    else:
        # Assume text file
        return uploaded_file.getvalue().decode('utf-8')

# Add to your main app.py
# tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["Input", "Detect", "Organize", "Export", "Impute", "🧠 AI"])
# with tab6:
#     from app_ai_organizer import show_ai_organizer_tab
#     show_ai_organizer_tab()