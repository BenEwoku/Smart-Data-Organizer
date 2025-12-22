"""
Smart Data Organizer - Phase 2 with Authentication & Payments
Entry Point: streamlit run app.py
"""

import streamlit as st
from utils.scraping import scrape_url
from utils.parser import parse_text_to_dataframe
from utils.detection import detect_data_structure
from utils.detection import detect_spam_emails
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

import mailbox
import email
from email.header import decode_header
import re
from datetime import datetime
from io import BytesIO  # <-- ADD THIS LINE



def parse_mbox_file(mbox_file):
    """
    Parse MBOX file and extract email data into structured DataFrame
    
    Returns:
        pd.DataFrame with columns:
        Email_ID, From, From_Domain, To, To_Domain, 
        Date, Subject, Body_Preview, Thread_ID, 
        Response_Time, Priority_Score
    """
    emails = []
    
    try:
        # Read MBOX file
        # Handle both file path and file object
        if hasattr(mbox_file, 'read'):
            # It's a file object (uploaded file)
            # Save to temp file first
            import tempfile
            with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.mbox') as tmp_file:
                tmp_file.write(mbox_file.read())
                tmp_path = tmp_file.name
            
            mbox = mailbox.mbox(tmp_path)
        else:
            # It's a file path
            mbox = mailbox.mbox(mbox_file)
        
        st.info(f"Found {len(mbox)} emails to process...")
        
        for i, message in enumerate(mbox):
            try:
                # Extract basic headers
                from_header = str(message.get('From', ''))
                to_header = str(message.get('To', ''))
                subject = str(message.get('Subject', ''))
                date_str = str(message.get('Date', ''))
                
                # Decode subject if encoded
                if subject:
                    try:
                        decoded_subject = decode_header(subject)[0]
                        if decoded_subject[1]:
                            subject = decoded_subject[0].decode(decoded_subject[1], errors='ignore')
                        else:
                            subject = str(decoded_subject[0])
                    except:
                        subject = str(subject)
                
                # Extract email addresses and domains
                from_email, from_domain = extract_email_and_domain(from_header)
                to_email, to_domain = extract_email_and_domain(to_header)
                
                # Parse date
                email_date = parse_email_date(date_str)
                
                # Extract body preview
                body_preview = extract_email_body_preview(message)
                
                # Generate Email_ID
                message_id = message.get('Message-ID', f'msg_{i}_{datetime.now().timestamp()}')
                email_id = str(message_id).strip('<>')
                
                # Calculate thread ID (based on subject)
                thread_id = generate_thread_id(subject)
                
                # Calculate priority score
                priority_score = calculate_priority_score(subject, from_domain, body_preview)
                # Calculate spam score
                spam_score = calculate_spam_score(subject, from_domain, body_preview, from_email)
                
                emails.append({
                    'Email_ID': email_id,
                    'From': from_email,
                    'From_Domain': from_domain,
                    'To': to_email,
                    'To_Domain': to_domain,
                    'Date': email_date,
                    'Subject': subject[:200] if subject else '',  # Limit subject length
                    'Body_Preview': body_preview[:300] if body_preview else '',  # Limit preview
                    'Thread_ID': thread_id,
                    'Response_Time': None,  # Will be calculated later
                    'Priority_Score': priority_score,
                    'Spam_Score': spam_score,  # NEW: Spam score
                    'Is_Spam': spam_score >= 70  # NEW: Spam flag (70+ = spam)
                })
                
                # Progress update every 100 emails
                if i % 100 == 0 and i > 0:
                    st.caption(f"Processed {i} emails...")
                
            except Exception as e:
                # Skip problematic emails but continue processing
                st.caption(f"Skipped email {i}: {str(e)[:50]}...")
                continue
        
        # Clean up temp file if created
        if 'tmp_path' in locals():
            import os
            os.unlink(tmp_path)
        
        # Create DataFrame - FIX: Avoid categorical dtype
        df = pd.DataFrame(emails)
        
        # FIX: Convert any categorical columns to string
        for col in df.columns:
            if pd.api.types.is_categorical_dtype(df[col]):
                df[col] = df[col].astype(str)
        
        # Calculate response times after all emails are loaded
        if len(df) > 0 and 'Thread_ID' in df.columns and 'Date' in df.columns:
            df = calculate_response_times(df)

        # ========== CRITICAL: PREVENT CATEGORICAL DATA ==========
        if len(df) > 0:
            # Force ALL string columns to plain string dtype
            for col in df.columns:
                if df[col].dtype.name == 'category':
                    df[col] = df[col].astype(str)
                elif df[col].dtype == 'object':
                    # Already string/object, ensure it's not categorical
                    try:
                        # Convert to string and back to object
                        df[col] = df[col].astype(str)
                    except:
                        pass
            
            # Convert numeric columns safely
            numeric_cols = ['Priority_Score', 'Response_Time_Hours']
            for col in numeric_cols:
                if col in df.columns:
                    try:
                        df[col] = pd.to_numeric(df[col], errors='coerce')
                    except:
                        pass
        # ========== END CATEGORICAL FIX ==========

        return df
        
    except Exception as e:
        raise Exception(f"Error parsing MBOX file: {str(e)}")

def calculate_spam_score(subject, domain, body, sender_email):
    """Calculate spam score for an email"""
    score = 0
    
    if subject:
        subject_lower = subject.lower()
        
        # Spam keywords in subject
        spam_keywords = [
            'free', 'winner', 'prize', 'congratulations', 'lottery',
            'urgent', 'asap', '!!!', '$$$', 'click here',
            'limited time', 'special offer', 'risk-free',
            'guaranteed', 'act now', 'buy now', 'order now'
        ]
        
        for keyword in spam_keywords:
            if keyword in subject_lower:
                score += 10
        
        # All caps subject
        if subject.isupper():
            score += 15
        
        # Excessive punctuation
        if subject.count('!') > 2:
            score += 5
        if subject.count('?') > 3:
            score += 3
    
    # Suspicious domains
    suspicious_domains = [
        'promo.', 'offer.', 'discount.', 'deal.', 'sale.',
        'newsletter.', 'marketing.', 'advertising.', 'bulk.'
    ]
    
    if domain:
        domain_lower = domain.lower()
        for suspicious in suspicious_domains:
            if suspicious in domain_lower:
                score += 10
    
    # Generic sender addresses
    generic_senders = [
        'noreply@', 'no-reply@', 'newsletter@',
        'notification@', 'info@', 'service@'
    ]
    
    if sender_email:
        sender_lower = sender_email.lower()
        for generic in generic_senders:
            if generic in sender_lower:
                score += 8
    
    # Body content analysis
    if body:
        body_lower = body.lower()
        
        # Spam phrases in body
        spam_phrases = [
            'unsubscribe', 'opt-out', 'click to remove',
            'money back', 'risk free', 'no obligation',
            'this is not spam', 'legal disclaimer'
        ]
        
        for phrase in spam_phrases:
            if phrase in body_lower:
                score += 5
        
        # Generic greetings
        generic_greetings = ['dear friend', 'dear sir', 'dear madam']
        for greeting in generic_greetings:
            if greeting in body_lower[:100]:
                score += 3
    
    # Cap score at 100
    return min(score, 100)

def extract_email_and_domain(header):
    """Extract email address and domain from header - always return strings"""
    if not header:
        return '', ''
    
    # Convert to string if not already
    header = str(header)
    
    # Try to find email pattern
    email_pattern = r'[\w\.-]+@[\w\.-]+\.\w+'
    matches = re.findall(email_pattern, header)
    
    if matches:
        email_addr = str(matches[0])
        domain = str(email_addr.split('@')[-1]) if '@' in email_addr else ''
        return email_addr, domain
    else:
        # If no email pattern, return the header as string
        return str(header), ''

def parse_email_date(date_str):
    """Parse email date string to datetime"""
    try:
        # Try multiple date formats
        date_formats = [
            '%a, %d %b %Y %H:%M:%S %z',
            '%d %b %Y %H:%M:%S %z',
            '%a, %d %b %Y %H:%M:%S %Z',
            '%Y-%m-%d %H:%M:%S'
        ]
        
        for fmt in date_formats:
            try:
                return datetime.strptime(date_str, fmt)
            except:
                continue
        
        # If all fail, return current date
        return datetime.now()
    except:
        return datetime.now()

def extract_email_body_preview(message):
    """Extract plain text body preview from email"""
    body = ""
    
    if message.is_multipart():
        # Walk through multipart messages
        for part in message.walk():
            content_type = part.get_content_type()
            content_disposition = str(part.get("Content-Disposition"))
            
            # Skip attachments
            if "attachment" in content_disposition:
                continue
            
            # Get plain text body
            if content_type == "text/plain":
                try:
                    payload = part.get_payload(decode=True)
                    if payload:
                        charset = part.get_content_charset() or 'utf-8'
                        body += payload.decode(charset, errors='ignore')
                except:
                    pass
    else:
        # Single part message
        try:
            payload = message.get_payload(decode=True)
            if payload:
                charset = message.get_content_charset() or 'utf-8'
                body = payload.decode(charset, errors='ignore')
        except:
            pass
    
    # Clean and preview
    body = re.sub(r'\s+', ' ', body)  # Replace multiple whitespace
    body = body.strip()
    
    return body

def generate_thread_id(subject):
    """Generate thread ID based on subject (remove Re:, Fwd:, etc.)"""
    if not subject:
        return "no_subject"
    
    # Clean subject for thread matching
    clean_subject = re.sub(r'^(Re:|Fwd:|FW:|RE:|fwd:)\s*', '', subject, flags=re.IGNORECASE)
    clean_subject = clean_subject.strip().lower()
    
    # Create hash for thread ID
    import hashlib
    return hashlib.md5(clean_subject.encode()).hexdigest()[:10]

def calculate_priority_score(subject, domain, body):
    """Calculate priority score based on content"""
    score = 50  # Base score
    
    # Subject-based scoring
    if subject:
        subject_lower = subject.lower()
        urgent_keywords = ['urgent', 'asap', 'important', 'critical', 'emergency']
        for keyword in urgent_keywords:
            if keyword in subject_lower:
                score += 20
        
        # Reduce score for promotional emails
        promo_keywords = ['newsletter', 'promotion', 'sale', 'discount', 'unsubscribe']
        for keyword in promo_keywords:
            if keyword in subject_lower:
                score -= 15
    
    # Domain-based scoring
    if domain:
        # Higher priority for internal/corporate domains
        internal_domains = ['company.com', 'corp.com', 'internal.com']
        if any(internal in domain for internal in internal_domains):
            score += 10
    
    # Normalize score
    return max(0, min(100, score))

def calculate_response_times(df):
    """Calculate response times between emails in same thread - SAFE VERSION"""
    if df.empty or 'Thread_ID' not in df.columns or 'Date' not in df.columns:
        return df
    
    # Create a copy and ensure ALL string columns are plain strings
    df = df.copy()
    
    # Convert ALL potential categorical columns to string FIRST
    string_columns = ['Thread_ID', 'From', 'To', 'Subject', 'Email_ID', 'From_Domain', 'To_Domain']
    for col in string_columns:
        if col in df.columns:
            # Force to string, no categorical
            df[col] = df[col].astype(str)
    
    # Also ensure Date is datetime
    if 'Date' in df.columns:
        try:
            df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        except:
            pass
    
    # Initialize response time column
    df['Response_Time_Hours'] = None
    
    try:
        # Get unique thread IDs as plain strings
        thread_ids = df['Thread_ID'].unique().tolist()
        
        # Process each thread
        for thread_id in thread_ids:
            if not thread_id or pd.isna(thread_id):
                continue
            
            # Get emails in this thread
            thread_mask = df['Thread_ID'] == thread_id
            thread_emails = df[thread_mask].copy()
            
            if len(thread_emails) > 1:
                # Sort by date
                thread_emails = thread_emails.sort_values('Date')
                
                # Calculate time differences
                dates = thread_emails['Date'].tolist()
                
                for i in range(1, len(dates)):
                    if pd.notna(dates[i]) and pd.notna(dates[i-1]):
                        try:
                            time_diff = (dates[i] - dates[i-1]).total_seconds() / 3600  # Hours
                            
                            # Update the response time in original DataFrame
                            email_index = thread_emails.index[i]
                            df.at[email_index, 'Response_Time_Hours'] = time_diff
                        except:
                            pass
        
        return df
        
    except Exception as e:
        # If anything fails, just return df with None response times
        st.warning(f"Could not calculate response times: {str(e)[:100]}")
        return df

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

# === ADD USER REFRESH BUTTON HERE ===
if st.sidebar.button("Refresh My Account Data", use_container_width=True, type="secondary"):
    from utils.auth import refresh_current_user_session
    refresh_current_user_session()
    st.sidebar.success("Account data refreshed!")
    st.rerun()

# Debug tier info
with st.sidebar.expander("Tier Status", expanded=False):
    st.write(f"**Tier:** {user['tier'].upper()}")
    st.write(f"**Conversions Used:** {user.get('conversions_used', 0)}")
    
    from utils.auth import get_conversion_limit, get_conversions_remaining
    limit = get_conversion_limit(user['tier'])
    remaining = get_conversions_remaining(user)
    
    st.write(f"**Limit:** {limit if limit != float('inf') else 'Unlimited'}")
    st.write(f"**Remaining:** {remaining}")
    
    # Check if it's recognizing Pro tier correctly
    if user['tier'] == 'pro':
        st.success("✓ Pro tier recognized")
    else:
        st.warning(f"Current tier: {user['tier']}")

# Navigation with admin protection
st.sidebar.markdown("---")
st.sidebar.header("Navigation")

# Show admin option ONLY if user is admin
if is_admin(st.session_state.user_email):
    page_options = ["Home", "Admin Panel", "Pricing", "Billing"]
    st.sidebar.markdown('<div style="background-color: #ff4b4b; color: white; padding: 2px 8px; border-radius: 12px; font-size: 0.8rem; font-weight: bold; display: inline-block; margin-bottom: 10px;">ADMIN</div>', unsafe_allow_html=True)
else:
    page_options = ["Home", "Pricing", "Billing"]

page = st.sidebar.radio("Go to:", page_options, label_visibility="collapsed")

# Handle pages with security check
# In app.py, replace the Admin Panel section with:

if page == "Admin Panel":
    # SECURITY CHECK
    if not is_admin(st.session_state.user_email):
        st.error("Access Denied: Admin privileges required")
        st.stop()
    
    # Use SIMPLE admin panel
    try:
        from admin_panel import show_admin_panel
        show_admin_panel()
    except Exception as e:
        # Fallback to ultra-simple
        st.markdown("# Admin Panel")
        st.error(f"Error: {type(e).__name__}")
        
        if st.button("Clear Cache & Retry"):
            import streamlit as st
            st.cache_data.clear()
            st.rerun()
    
    st.stop()

# Main Home Page
# Main Home Page
st.markdown('<h1 class="main-header">Smart Data Organizer</h1>', unsafe_allow_html=True)
st.markdown('<p class="main-subtitle">Transform messy data into clean, organized tables with intelligent structure detection</p>', unsafe_allow_html=True)
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
    # Change from 3 options to 4 options
    input_method = st.radio(
        "Input Method:",
        ["Paste Text", "Web Scraping", "Upload File", "Email Export"],  # Added Email Export
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


    elif input_method == "Email Export":
        st.markdown("**Upload Email Export File**")
        st.caption("Supported formats: MBOX (Gmail/Apple Mail), EML, CSV email exports")
        
        uploaded_email_file = st.file_uploader(
            "Choose email file:",
            type=['mbox', 'eml', 'csv', 'txt'],
            label_visibility="collapsed"
        )
        
        if uploaded_email_file:
            # Determine file type
            file_name = uploaded_email_file.name.lower()
            
            st.info(f"Uploaded: {uploaded_email_file.name} ({uploaded_email_file.size / 1024:.1f} KB)")
            
            with st.spinner("Parsing email data..."):
                try:
                    if file_name.endswith('.mbox'):
                        # Save uploaded file temporarily
                        import tempfile
                        with tempfile.NamedTemporaryFile(delete=False, suffix='.mbox') as tmp_file:
                            tmp_file.write(uploaded_email_file.getvalue())
                            tmp_path = tmp_file.name
                        
                        # Parse MBOX file
                        df_raw = parse_mbox_file(tmp_path)
                        
                        # Clean up temp file
                        import os
                        os.unlink(tmp_path)
                        
                    elif file_name.endswith('.eml'):
                        # Parse single EML file
                        from email import parser
                        msg_parser = parser.BytesParser()
                        message = msg_parser.parsebytes(uploaded_email_file.getvalue())
                        
                        # Convert single email to DataFrame
                        from_email, from_domain = extract_email_and_domain(str(message.get('From', '')))
                        to_email, to_domain = extract_email_and_domain(str(message.get('To', '')))
                        
                        df_raw = pd.DataFrame([{
                            'Email_ID': str(message.get('Message-ID', 'single_email')).strip('<>'),
                            'From': from_email,
                            'From_Domain': from_domain,
                            'To': to_email,
                            'To_Domain': to_domain,
                            'Date': parse_email_date(str(message.get('Date', ''))),
                            'Subject': str(message.get('Subject', '')),
                            'Body_Preview': extract_email_body_preview(message),
                            'Thread_ID': 'single',
                            'Response_Time': None,
                            'Priority_Score': calculate_priority_score(
                                str(message.get('Subject', '')), 
                                from_domain, 
                                extract_email_body_preview(message)
                            )
                        }])
                        
                    elif file_name.endswith('.csv'):
                        # Parse CSV email export
                        df_raw = pd.read_csv(uploaded_email_file)
                        
                        # Try to standardize column names
                        column_mapping = {
                            'from': 'From',
                            'to': 'To', 
                            'subject': 'Subject',
                            'date': 'Date',
                            'body': 'Body_Preview',
                            'sender': 'From',
                            'recipient': 'To'
                        }
                        
                        df_raw.columns = [column_mapping.get(col.lower(), col) for col in df_raw.columns]
                        
                    else:
                        st.error("Unsupported file format")
                        df_raw = None
                    
                    if df_raw is not None and len(df_raw) > 0:
                        # Clean column names
                        df_raw.columns = [f'Column_{i}' if pd.isna(col) else str(col) for i, col in enumerate(df_raw.columns)]
                        
                        # Handle duplicate column names
                        cols = pd.Series(df_raw.columns)
                        for dup in cols[cols.duplicated()].unique():
                            cols[cols == dup] = [f'{dup}_{i}' if i != 0 else dup for i in range(sum(cols == dup))]
                        df_raw.columns = cols
                        
                        st.session_state.df = df_raw
                        # Increment conversion count
                        increment_conversion_count(st.session_state.user_email)
                        
                        # Show email-specific metrics
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Emails", f"{len(df_raw):,}")
                        with col2:
                            unique_senders = df_raw['From'].nunique() if 'From' in df_raw.columns else 0
                            st.metric("Unique Senders", unique_senders)
                        with col3:
                            if 'Date' in df_raw.columns:
                                try:
                                    date_range = f"{df_raw['Date'].min().date()} to {df_raw['Date'].max().date()}"
                                    st.metric("Date Range", date_range)
                                except:
                                    st.metric("Date Column", "Found")
                        
                        # Show preview
                        with st.expander("Email Data Preview", expanded=True):
                            st.dataframe(df_raw.head(10), use_container_width=True)
                            st.caption(f"**Total:** {len(df_raw):,} emails × {len(df_raw.columns)} columns")
                        
                        st.success("Email data loaded successfully!")
                        
                        # Auto-advance hint
                        st.info("Click on the **Detect** tab to continue with email analysis")
                        
                    else:
                        st.error("Could not extract email data from file")
                        
                except Exception as e:
                    st.error(f"Error parsing email file: {str(e)}")
                    with st.expander("Technical Details"):
                        st.code(str(e))
        
        # Instructions for users
        with st.expander("How to Export Emails from Your Email Client", expanded=True):
            st.markdown("""
            ### **From Gmail:**
            1. Go to [Google Takeout](https://takeout.google.com)
            2. Select only **"Mail"**
            3. Choose **MBOX format**
            4. Download and upload the .mbox file here
            
            ### **From Outlook:**
            1. Open Outlook desktop app
            2. File → Open & Export → Import/Export
            3. Export to a file → **Comma Separated Values**
            4. Select folder and save as CSV
            
            ### **From Apple Mail/Thunderbird:**
            1. Right-click the mailbox/folder
            2. Select **"Export"** or **"Save As"**
            3. Choose **MBOX format**
            
            ### **Privacy Note:**
            Only upload emails you have permission to analyze
            Remove sensitive information before uploading
            """)
    
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
                    # Use the safe detection function
                    structure, date_col, entity_col = detect_data_structure(df_clean)
                    
                    # VALIDATE the result
                    if structure is None:
                        st.error("Detection returned None structure. Using defaults.")
                        structure, date_col, entity_col = ("General Data", None, None)
                    
                    # Store in session state
                    st.session_state.data_structure = (structure, date_col, entity_col)
                    st.session_state.structure_detected = True
                    
                    # Show success
                    st.success(f"✓ Detected: {structure}")
                    if date_col:
                        st.info(f"Date column: {date_col}")
                    if entity_col:
                        st.info(f"Entity column: {entity_col}")
                        
            except Exception as e:
                st.error(f"Could not detect data structure: {str(e)}")
                # Set safe defaults
                structure, date_col, entity_col = ("General Data", None, None)
                st.session_state.data_structure = (structure, date_col, entity_col)
                st.session_state.structure_detected = True
        else:
            st.markdown('<h3 style="font-size: 1.6rem; font-weight: 600;">Structure Detection</h3>', unsafe_allow_html=True)

        # ========== SAFE STRUCTURE UNPACKING ==========
        # ALWAYS validate before unpacking
        if st.session_state.data_structure is None:
            st.warning("Structure data is None. Setting defaults.")
            st.session_state.data_structure = ("General Data", None, None)

        try:
            structure, date_col, entity_col = st.session_state.data_structure
            
            # Additional validation
            if not isinstance(structure, str):
                st.error(f"Invalid structure type: {type(structure)}. Using General Data.")
                structure = "General Data"
                st.session_state.data_structure = (structure, date_col, entity_col)
                
        except (ValueError, TypeError) as e:
            st.error(f"Error unpacking structure: {str(e)}. Resetting to defaults.")
            structure, date_col, entity_col = ("General Data", None, None)
            st.session_state.data_structure = (structure, date_col, entity_col)
        # ========== END SAFE UNPACKING ==========
        
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
            elif structure == "Email Data":
                st.info("Email correspondence data")
            else:
                st.info("General data format")
        
        # ========== KEY COLUMNS DETECTED - ENHANCED FOR EMAIL DATA ==========
        if date_col or entity_col:
            st.markdown('<h3 style="font-size: 1.6rem; font-weight: 600;">Key Columns Detected</h3>', unsafe_allow_html=True)
            
            if structure == "Email Data":
                # Email-specific column display
                cols = st.columns(3)
                
                if date_col:
                    with cols[0]:
                        st.success(f"**Date Column:** `{date_col}`")
                        # Show date range
                        try:
                            if 'Date' in df_clean.columns:
                                min_date = df_clean['Date'].min().strftime('%Y-%m-%d')
                                max_date = df_clean['Date'].max().strftime('%Y-%m-%d')
                                st.caption(f"Range: {min_date} to {max_date}")
                        except:
                            pass
                
                if entity_col:
                    with cols[1]:
                        if entity_col == 'From':
                            st.success(f"**Sender Column:** `{entity_col}`")
                        elif entity_col == 'To':
                            st.success(f"**Recipient Column:** `{entity_col}`")
                        else:
                            st.success(f"**Entity Column:** `{entity_col}`")
                
                # Show other email columns
                with cols[2]:
                    email_cols_found = []
                    for col in ['From', 'To', 'Subject', 'Body', 'Message', 'Body_Preview']:
                        if col in df_clean.columns:
                            email_cols_found.append(col)
                    
                    if email_cols_found:
                        st.info(f"**Email columns:** {', '.join(email_cols_found[:3])}")
                        if len(email_cols_found) > 3:
                            st.caption(f"+ {len(email_cols_found) - 3} more")
            else:
                # Original display for non-email data
                cols = st.columns(2)
                
                if date_col:
                    with cols[0]:
                        st.success(f"**Date/Time Column:** `{date_col}`")
                
                if entity_col:
                    with cols[1]:
                        st.success(f"**Entity Column:** `{entity_col}`")
        
        # ========== EMAIL-SPECIFIC INSIGHTS ==========
        if structure == "Email Data":
            st.markdown('<h3 style="font-size: 1.6rem; font-weight: 600;">Email Data Insights</h3>', unsafe_allow_html=True)
            
            # Email-specific metrics
            from utils.detection import detect_email_threads
            thread_info = detect_email_threads(df_clean)
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                if 'From' in df_clean.columns:
                    unique_senders = df_clean['From'].nunique()
                    st.metric("Unique Senders", unique_senders)
            
            with col2:
                if 'To' in df_clean.columns:
                    unique_recipients = df_clean['To'].nunique()
                    st.metric("Unique Recipients", unique_recipients)
            
            with col3:
                if 'Date' in df_clean.columns:
                    try:
                        days_span = (df_clean['Date'].max() - df_clean['Date'].min()).days
                        emails_per_day = len(df_clean) / max(1, days_span)
                        st.metric("Emails/Day", f"{emails_per_day:.1f}")
                    except:
                        date_count = df_clean['Date'].notna().sum()
                        st.metric("Emails with Date", date_count)
            
            with col4:
                if thread_info['has_threads']:
                    avg_thread = thread_info['avg_thread_size']
                    st.metric("Avg Thread Size", f"{avg_thread:.1f}")
                else:
                    st.metric("Conversation Threads", "Individual")
            
            # Additional email analysis
            with st.expander("Detailed Email Analysis", expanded=False):
                # Sender analysis
                if 'From' in df_clean.columns:
                    st.markdown("**Top 10 Senders:**")
                    top_senders = df_clean['From'].value_counts().head(10)
                    
                    if len(top_senders) > 0:
                        sender_df = top_senders.reset_index()
                        sender_df.columns = ['Sender', 'Email Count']
                        sender_df['Percentage'] = (sender_df['Email Count'] / len(df_clean) * 100).round(1)
                        
                        st.dataframe(sender_df, use_container_width=True, height=250)
                        
                        # Visualize top senders
                        if len(top_senders) > 1:
                            st.bar_chart(top_senders.head(5))
                    else:
                        st.info("No sender data available")
                
                # Time analysis
                if 'Date' in df_clean.columns and pd.api.types.is_datetime64_any_dtype(df_clean['Date']):
                    st.markdown("**Email Distribution by Hour of Day:**")
                    try:
                        df_clean['Hour'] = df_clean['Date'].dt.hour
                        hour_counts = df_clean['Hour'].value_counts().sort_index()
                        st.bar_chart(hour_counts)
                    except:
                        pass
                
                # Thread analysis
                if thread_info['has_threads'] and 'Subject' in df_clean.columns:
                    st.markdown("**Conversation Thread Analysis:**")
                    col_a, col_b = st.columns(2)
                    
                    with col_a:
                        st.metric("Total Threads", thread_info['thread_count'])
                    
                    with col_b:
                        st.metric("Total Emails", thread_info['total_emails'])
                    
                    # Show longest threads
                    if 'Subject' in df_clean.columns:
                        # Group by cleaned subject
                        clean_subjects = df_clean['Subject'].astype(str).str.lower()
                        clean_subjects = clean_subjects.str.replace(r'^(re:|fwd:|fw:|re\[\d+\]:|fwd\[\d+\]:)\s*', '', regex=True)
                        
                        thread_sizes = clean_subjects.value_counts()
                        largest_threads = thread_sizes.head(5)
                        
                        if len(largest_threads) > 0:
                            st.markdown("**Largest Conversations:**")
                            for subject, count in largest_threads.items():
                                subject_display = subject[:50] + "..." if len(subject) > 50 else subject
                                st.write(f"• {subject_display}: {count} emails")
            
            # Email data quality check
            st.markdown("### Email Data Quality")
            
            quality_col1, quality_col2, quality_col3 = st.columns(3)
            
            with quality_col1:
                # Check for missing sender/recipient
                missing_from = df_clean['From'].isna().sum() if 'From' in df_clean.columns else 0
                missing_to = df_clean['To'].isna().sum() if 'To' in df_clean.columns else 0
                missing_contacts = missing_from + missing_to
                
                if missing_contacts > 0:
                    st.warning(f"Missing sender/recipient: {missing_contacts}")
                else:
                    st.success("✓ All emails have sender/recipient")
            
            with quality_col2:
                # Check for missing subjects
                missing_subject = df_clean['Subject'].isna().sum() if 'Subject' in df_clean.columns else 0
                
                if missing_subject > 0:
                    st.warning(f"Missing subjects: {missing_subject}")
                else:
                    st.success("✓ All emails have subjects")
            
            with quality_col3:
                # Check for missing dates
                missing_date = df_clean['Date'].isna().sum() if 'Date' in df_clean.columns else 0
                
                if missing_date > 0:
                    st.warning(f"Missing dates: {missing_date}")
                else:
                    st.success("✓ All emails have dates")
            
            st.markdown("---")
        # ========== END EMAIL INSIGHTS ==========

        # ========== SPAM DETECTION ANALYSIS ==========
        if structure == "Email Data":
            st.markdown('<h3 style="font-size: 1.6rem; font-weight: 600;">Spam Detection Analysis</h3>', unsafe_allow_html=True)
            
            from utils.detection import detect_spam_emails
            
            with st.spinner("Analyzing for spam emails..."):
                spam_results = detect_spam_emails(df_clean)
            
            if spam_results and 'spam_count' in spam_results:
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Total Emails", len(df_clean))
                
                with col2:
                    st.metric("Spam Emails", spam_results['spam_count'])
                
                with col3:
                    st.metric("Ham Emails", spam_results['ham_count'])
                
                with col4:
                    spam_pct = spam_results['spam_percentage']
                    if spam_pct > 20:
                        st.metric("Spam %", f"{spam_pct:.1f}%", delta="High", delta_color="inverse")
                    elif spam_pct > 5:
                        st.metric("Spam %", f"{spam_pct:.1f}%", delta="Moderate", delta_color="off")
                    else:
                        st.metric("Spam %", f"{spam_pct:.1f}%", delta="Low", delta_color="normal")
                
                # Show top spam emails
                if spam_results['spam_count'] > 0:
                    with st.expander(f"View Detected Spam Emails ({spam_results['spam_count']} found)", expanded=False):
                        # Let user adjust spam threshold
                        threshold = st.slider(
                            "Adjust spam sensitivity (higher = stricter):",
                            min_value=50,
                            max_value=90,
                            value=spam_results.get('spam_threshold', 70),
                            step=5
                        )
                        
                        if threshold != spam_results.get('spam_threshold', 70):
                            # Re-run with new threshold
                            spam_results = detect_spam_emails(df_clean, threshold)
                        
                        # Show spam emails table
                        if spam_results['spam_emails']:
                            spam_df = pd.DataFrame(spam_results['spam_emails'])
                            st.dataframe(
                                spam_df[['subject', 'from', 'spam_score', 'date']],
                                use_container_width=True,
                                column_config={
                                    "subject": "Subject",
                                    "from": "Sender",
                                    "spam_score": st.column_config.NumberColumn(
                                        "Spam Score",
                                        help="0-100, higher = more likely spam",
                                        format="%d"
                                    ),
                                    "date": "Date"
                                }
                            )
                            
                            # Actions for spam emails
                            st.markdown("**Actions:**")
                            col_a, col_b = st.columns(2)
                            
                            with col_a:
                                if st.button("Filter Out Spam", type="primary"):
                                    # Filter out spam emails
                                    spam_indices = [email['index'] for email in spam_results['spam_emails']]
                                    df_clean_filtered = df_clean.drop(index=spam_indices)
                                    st.session_state.df = df_clean_filtered
                                    st.success(f"Removed {len(spam_indices)} spam emails")
                                    st.rerun()
                            
                            with col_b:
                                if st.button("Download Spam List", type="secondary"):
                                    # Create CSV of spam emails
                                    spam_list = pd.DataFrame(spam_results['spam_emails'])
                                    csv = spam_list.to_csv(index=False)
                                    st.download_button(
                                        label="Download CSV",
                                        data=csv,
                                        file_name="spam_emails.csv",
                                        mime="text/csv"
                                    )
                            
                            # Visualize spam distribution
                            st.markdown("**Spam Score Distribution:**")
                            
                            if 'spam_scores' in spam_results and spam_results['spam_scores']:
                                # Create histogram
                                scores_df = pd.DataFrame({'spam_score': spam_results['spam_scores']})
                                st.bar_chart(scores_df['spam_score'].value_counts().sort_index())
                                
                                # Show score statistics
                                st.markdown("**Score Statistics:**")
                                col_stats1, col_stats2, col_stats3 = st.columns(3)
                                with col_stats1:
                                    st.metric("Avg Score", f"{scores_df['spam_score'].mean():.1f}")
                                with col_stats2:
                                    st.metric("Median Score", f"{scores_df['spam_score'].median():.1f}")
                                with col_stats3:
                                    st.metric("Max Score", f"{scores_df['spam_score'].max():.1f}")
                else:
                    st.success("✅ No spam detected in your email collection!")
                    
                    # Show spam prevention tips
                    with st.expander("Spam Prevention Tips", expanded=False):
                        st.markdown("""
                        **To keep your inbox clean:**
                        
                        1. **Use filters** - Set up rules to automatically move suspected spam
                        2. **Don't click unsubscribe** on obvious spam (confirms your email is active)
                        3. **Use disposable emails** for website signups
                        4. **Report spam** to your email provider
                        5. **Avoid posting your email** publicly on forums/social media
                        
                        **Common spam indicators:**
                        - Generic greetings ("Dear friend")
                        - Urgent language ("Act now!")
                        - Too good to be true offers
                        - Poor grammar/spelling
                        - Suspicious sender addresses
                        """)
        # ========== END SPAM DETECTION ==========
        
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

        # EMAIL-SPECIFIC: Adjust layout based on data type
        if structure == "Email Data":
            col1, col2, col3, col4 = st.columns(4)  # 4 columns for email data
        else:
            col1, col2 = st.columns(2)  # 2 columns for other data

        with col1:
            # Get missing value statistics
            missing_count = df_clean.isna().sum().sum() if df_clean is not None else 0
            missing_pct = validation_result.get('missing_percentage', 0) if 'validation_result' in locals() else 0
            
            # EMAIL-SPECIFIC: Different button label for email data
            if structure == "Email Data":
                button_label = f"Fix Email Issues ({missing_count:,})"
            else:
                button_label = f"Fix Missing Values ({missing_count:,})"
            
            if missing_count > 0:
                if st.button(button_label, use_container_width=True, type="primary"):
                    st.success(f"Found {missing_count:,} missing values ({missing_pct:.1f}%)")
                    
                    if structure == "Email Data":
                        st.info("""
                        **Email Data Cleaning is available!**
                        
                        Please navigate to the **"Impute" tab (Tab 5)** to:
                        • Fix missing sender/recipient information
                        • Clean email addresses and domains
                        • Handle missing dates in email threads
                        • Clean and standardize subject lines
                        
                        **Click on "Impute" in the tab bar above**
                        """)
                    else:
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
                    
                    # Show quick preview
                    if df_clean is not None:
                        missing_cols = df_clean.columns[df_clean.isna().any()].tolist()
                        if missing_cols:
                            st.write("**Columns with missing values:**")
                            for col in missing_cols[:5]:
                                missing_in_col = df_clean[col].isna().sum()
                                st.write(f"• `{col}`: {missing_in_col} missing ({missing_in_col/len(df_clean)*100:.1f}%)")
                            
                            if len(missing_cols) > 5:
                                st.caption(f"... and {len(missing_cols) - 5} more columns")
            else:
                if structure == "Email Data":
                    if st.button("Email Data Clean", use_container_width=True, disabled=False):
                        st.success("Great! No missing values in your email data.")
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
        
        # ADD EMAIL-SPECIFIC ACTION BUTTONS
        if structure == "Email Data":
            with col3:
                if st.button("Analyze Email Threads", use_container_width=True):
                    from utils.detection import detect_email_threads
                    thread_info = detect_email_threads(df_clean)
                    
                    with st.expander("Email Thread Analysis", expanded=True):
                        st.write(f"**Total Emails:** {len(df_clean)}")
                        st.write(f"**Conversation Threads:** {thread_info['thread_count']}")
                        st.write(f"**Average Thread Size:** {thread_info['avg_thread_size']:.1f} emails")
                        
                        if thread_info['has_threads']:
                            st.success("✓ Conversations detected")
                            st.info("Go to **Tab 3: Organize** to group emails by threads and analyze response times")
                        else:
                            st.info("Mostly individual emails - no long conversations detected")
            
            with col4:
                if st.button("Sender Analysis", use_container_width=True):
                    if 'From' in df_clean.columns:
                        top_senders = df_clean['From'].value_counts().head(10)
                        
                        with st.expander("Top Senders Analysis", expanded=True):
                            for i, (sender, count) in enumerate(top_senders.items(), 1):
                                percentage = (count / len(df_clean)) * 100
                                st.write(f"{i}. **{sender}**: {count} emails ({percentage:.1f}%)")
                        
                        st.info("Go to **Tab 3: Organize** to group emails by sender for deeper analysis")
                    else:
                        st.warning("No 'From' column found for sender analysis")
        
    else:
        st.info("Please input data in the Input tab first")

# TAB 3: ORGANIZE
with tab3:
    # SAFETY CHECK 1: Ensure data is loaded
    if st.session_state.df is None or st.session_state.df.empty:
        st.warning("No data loaded. Please input data in the Input tab first.")
        st.stop()
    
    # Get the DataFrame
    df = st.session_state.df
    
    # SAFETY CHECK 2: Ensure data structure exists AND is valid
    if st.session_state.data_structure is None:
        # Run detection now
        st.warning("Data structure not detected. Running detection...")
        try:
            from utils.detection import detect_data_structure
            structure, date_col, entity_col = detect_data_structure(df)
            st.session_state.data_structure = (structure, date_col, entity_col)
            st.success(f"Detected: {structure}")
        except Exception as e:
            st.error(f"Detection failed: {str(e)}")
            # Set safe defaults
            st.session_state.data_structure = ("General Data", None, None)
    
    # Now safely unpack with validation
    try:
        structure, date_col, entity_col = st.session_state.data_structure
        # Validate the unpacked values
        if structure is None or not isinstance(structure, str):
            raise ValueError("Invalid structure value")
    except (ValueError, TypeError) as e:
        st.error(f"Invalid data structure: {str(e)}")
        # Reset to defaults
        st.session_state.data_structure = ("General Data", None, None)
        structure, date_col, entity_col = ("General Data", None, None)
    
    st.markdown('<h2 class="subheader">Step 3: Organize & Refine Data</h2>', unsafe_allow_html=True)

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
        
    elif structure == "Email Data":  # NEW: Email-specific organization
        from utils.organization import organize_email_data
        df_organized = organize_email_data(df)
        
    else:
        # Fallback: Check if data looks like email data
        from utils.detection import detect_email_data
        is_email, confidence, email_cols = detect_email_data(df)
        
        if is_email and confidence >= 50:
            st.info("Email data detected. Using email-specific organization.")
            from utils.organization import organize_email_data
            df_organized = organize_email_data(df)
        else:
            df_organized = df.copy()
    
    # ========== EMAIL SPAM FILTERING OPTIONS ==========
    if structure == "Email Data":
        st.markdown('<h3 style="font-size: 1.6rem; font-weight: 600;">📧 Email Organization Options</h3>', unsafe_allow_html=True)
        
        # Check if we need to calculate spam scores
        if 'Spam_Score' not in df_organized.columns:
            st.info("Calculating spam scores for your emails...")
            
            # Import spam detection function
            try:
                from utils.detection import detect_spam_emails
                
                # Calculate spam scores
                spam_results = detect_spam_emails(df_organized)
                
                if spam_results and 'spam_scores' in spam_results:
                    # Add spam scores to DataFrame
                    df_organized['Spam_Score'] = spam_results['spam_scores']
                    df_organized['Is_Spam'] = df_organized['Spam_Score'] >= 70
                    
                    spam_count = len(df_organized[df_organized['Is_Spam']])
                    st.success(f"✅ Spam analysis complete: {spam_count} likely spam emails detected")
                else:
                    # Fallback: Calculate simple spam score
                    from utils.detection import calculate_spam_score
                    df_organized['Spam_Score'] = df_organized.apply(
                        lambda row: calculate_spam_score(
                            row.get('Subject', ''),
                            row.get('From_Domain', ''),
                            row.get('Body_Preview', ''),
                            row.get('From', '')
                        ) if 'Subject' in df_organized.columns else 0,
                        axis=1
                    )
                    df_organized['Is_Spam'] = df_organized['Spam_Score'] >= 70
                    
            except Exception as e:
                st.warning(f"Could not calculate spam scores: {str(e)}")
                # Add default scores
                df_organized['Spam_Score'] = 0
                df_organized['Is_Spam'] = False
        
        # Show spam statistics if we have scores
        if 'Spam_Score' in df_organized.columns:
            spam_count = len(df_organized[df_organized['Spam_Score'] >= 70])
            total_emails = len(df_organized)
            spam_percentage = (spam_count / total_emails * 100) if total_emails > 0 else 0
            avg_score = df_organized['Spam_Score'].mean()
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Emails", total_emails)
            with col2:
                st.metric("Likely Spam", spam_count)
            with col3:
                st.metric("Spam %", f"{spam_percentage:.1f}%")
            with col4:
                st.metric("Avg Score", f"{avg_score:.1f}")
            
            # Email organization controls
            st.markdown("#### Organization Options")
            
            col_org1, col_org2 = st.columns(2)
            
            with col_org1:
                # Sort options
                sort_option = st.selectbox(
                    "Sort emails by:",
                    ["Date (Newest First)", "Date (Oldest First)", "Spam Score (High to Low)", 
                     "Sender (A-Z)", "Subject (A-Z)", "Priority Score (High to Low)"]
                )
                
                # Apply sorting
                if sort_option == "Date (Newest First)" and 'Date' in df_organized.columns:
                    df_organized = df_organized.sort_values('Date', ascending=False)
                elif sort_option == "Date (Oldest First)" and 'Date' in df_organized.columns:
                    df_organized = df_organized.sort_values('Date', ascending=True)
                elif sort_option == "Spam Score (High to Low)" and 'Spam_Score' in df_organized.columns:
                    df_organized = df_organized.sort_values('Spam_Score', ascending=False)
                elif sort_option == "Sender (A-Z)" and 'From' in df_organized.columns:
                    df_organized = df_organized.sort_values('From', ascending=True)
                elif sort_option == "Subject (A-Z)" and 'Subject' in df_organized.columns:
                    df_organized = df_organized.sort_values('Subject', ascending=True)
                elif sort_option == "Priority Score (High to Low)" and 'Priority_Score' in df_organized.columns:
                    df_organized = df_organized.sort_values('Priority_Score', ascending=False)
            
            with col_org2:
                # Filter options
                filter_option = st.selectbox(
                    "Filter emails:",
                    ["Show All", "Show Only Spam", "Exclude Spam", "Show High Priority", "Show Recent (Last 30 days)"]
                )
                
                # Apply filtering
                if filter_option == "Show Only Spam" and 'Is_Spam' in df_organized.columns:
                    before_count = len(df_organized)
                    df_organized = df_organized[df_organized['Is_Spam']]
                    after_count = len(df_organized)
                    st.info(f"Showing {after_count} spam emails")
                elif filter_option == "Exclude Spam" and 'Is_Spam' in df_organized.columns:
                    before_count = len(df_organized)
                    df_organized = df_organized[~df_organized['Is_Spam']]
                    after_count = len(df_organized)
                    st.success(f"Excluded {before_count - after_count} spam emails")
                elif filter_option == "Show High Priority" and 'Priority_Score' in df_organized.columns:
                    df_organized = df_organized[df_organized['Priority_Score'] >= 70]
                    st.info(f"Showing {len(df_organized)} high priority emails")
                elif filter_option == "Show Recent (Last 30 days)" and 'Date' in df_organized.columns:
                    try:
                        cutoff_date = pd.Timestamp.now() - pd.Timedelta(days=30)
                        df_organized = df_organized[df_organized['Date'] >= cutoff_date]
                        st.info(f"Showing {len(df_organized)} emails from last 30 days")
                    except:
                        pass
            
            st.markdown("---")
    # ========== END EMAIL SPAM FILTERING ==========
    
    st.markdown('<h3 style="font-size: 1.6rem; font-weight: 600;">Select Columns to Keep</h3>', unsafe_allow_html=True)
    cols_to_keep = st.multiselect(
        "Columns:",
        df_organized.columns.tolist(),
        default=df_organized.columns.tolist(),
        label_visibility="collapsed"
    )
    
    if cols_to_keep:
        df_organized = df_organized[cols_to_keep]
    
    st.markdown('<h3 style="font-size: 1.6rem; font-weight: 600;">Organized Data Preview</h3>', unsafe_allow_html=True)
    
    # Show data preview with spam highlights if applicable
    if structure == "Email Data" and 'Spam_Score' in df_organized.columns:
        # Create a styled dataframe that highlights spam
        display_df = df_organized.copy()
        
        # Add color coding for spam
        def highlight_spam(row):
            if row['Spam_Score'] >= 70:
                return ['background-color: #ffcccc'] * len(row)
            elif row['Spam_Score'] >= 50:
                return ['background-color: #fff3cd'] * len(row)
            else:
                return [''] * len(row)
        
        # Show styled dataframe
        st.dataframe(
            display_df.style.apply(highlight_spam, axis=1),
            use_container_width=True,
            height=400
        )
        
        # Legend for spam highlighting
        col_legend1, col_legend2, col_legend3 = st.columns(3)
        with col_legend1:
            st.markdown('<div style="background-color: #ffcccc; padding: 5px; border-radius: 3px;">Likely spam (≥70)</div>', unsafe_allow_html=True)
        with col_legend2:
            st.markdown('<div style="background-color: #fff3cd; padding: 5px; border-radius: 3px;">Suspicious (50-69)</div>', unsafe_allow_html=True)
        with col_legend3:
            st.markdown('<div style="background-color: #d4edda; padding: 5px; border-radius: 3px;">Clean (<50)</div>', unsafe_allow_html=True)
    else:
        # Regular dataframe display for non-email data
        st.dataframe(df_organized, use_container_width=True, height=400)
    
    with st.expander("Summary Statistics"):
        if len(df_organized.select_dtypes(include=['number']).columns) > 0:
            st.dataframe(df_organized.describe(), use_container_width=True)
        else:
            st.info("No numeric columns for statistics")
    
    # Store the organized data
    st.session_state.df_organized = df_organized
    
    # Action buttons
    st.markdown("---")
    col_action1, col_action2, col_action3 = st.columns(3)
    
    with col_action1:
        if st.button("Apply Organization", type="primary", use_container_width=True):
            st.success("Data organization applied!")
            st.rerun()
    
    with col_action2:
        if st.button("Reset Filters", type="secondary", use_container_width=True):
            # Reset to original organized data
            if structure == "Email Data":
                # Re-organize without filters
                from utils.organization import organize_email_data
                df_organized = organize_email_data(df)
                st.session_state.df_organized = df_organized
            st.info("Filters reset to original organization")
            st.rerun()
    
    with col_action3:
        if st.button("Go to Export", type="secondary", use_container_width=True):
            st.info("Proceeding to Export tab...")
            st.markdown("Please click on the **Export** tab above to save your organized data")

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
                
                # Status indicator
                status = st.empty()
                
                try:
                    with st.spinner("Preparing Excel file..."):
                        buffer = BytesIO()
                        
                        # Prepare data for Excel
                        df_for_excel = df_export.copy()
                        
                        # Handle timezone-aware datetimes
                        for col in df_for_excel.columns:
                            if pd.api.types.is_datetime64_any_dtype(df_for_excel[col]):
                                try:
                                    df_for_excel[col] = df_for_excel[col].dt.tz_localize(None)
                                except:
                                    pass
                        
                        # Export
                        df_for_excel.to_excel(buffer, index=False, engine='openpyxl')
                        excel_data = buffer.getvalue()
                    
                    # Clear the spinner
                    status.empty()
                    
                    if excel_data:
                        # Show download button with success indicator
                        col_a, col_b = st.columns([3, 1])
                        with col_a:
                            st.download_button(
                                label="Download Excel File",
                                data=excel_data,
                                file_name="organized_data.xlsx",
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                type="primary",
                                use_container_width=True
                            )
                        with col_b:
                            file_size_mb = len(excel_data) / (1024 * 1024)
                            st.metric("Size", f"{file_size_mb:.1f} MB")
                    else:
                        st.error("Could not generate Excel file")
                        
                except Exception:
                    st.error("Excel export failed")
                    st.info("Please use the CSV export instead")
        
        # ========== ADD SPAM STATISTICS HERE (for email data) ==========
        # Get structure from session state
        if 'data_structure' in st.session_state and st.session_state.data_structure:
            try:
                structure, _, _ = st.session_state.data_structure
                
                if structure == "Email Data" and 'Spam_Score' in df_export.columns:
                    st.markdown("---")
                    st.markdown("### 📧 Email Spam Statistics")
                    
                    # Calculate spam statistics
                    spam_count = len(df_export[df_export['Spam_Score'] >= 70])
                    total_emails = len(df_export)
                    spam_percentage = (spam_count / total_emails * 100) if total_emails > 0 else 0
                    avg_score = df_export['Spam_Score'].mean()
                    highest_score = df_export['Spam_Score'].max()
                    
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Total Emails", total_emails)
                    with col2:
                        st.metric("Likely Spam", spam_count, 
                                 delta=f"{spam_percentage:.1f}%", 
                                 delta_color="inverse" if spam_percentage > 20 else "off")
                    with col3:
                        st.metric("Avg Spam Score", f"{avg_score:.1f}")
                    with col4:
                        st.metric("Highest Score", f"{highest_score:.1f}")
                    
                    # Additional spam insights
                    with st.expander("Detailed Spam Analysis", expanded=False):
                        # Distribution by spam score ranges
                        st.markdown("**Spam Score Distribution:**")
                        
                        # Create score ranges
                        score_ranges = {
                            "Clean (0-29)": (0, 29),
                            "Low Risk (30-49)": (30, 49),
                            "Suspicious (50-69)": (50, 69),
                            "Likely Spam (70-89)": (70, 89),
                            "High Risk (90-100)": (90, 100)
                        }
                        
                        distribution_data = []
                        for label, (low, high) in score_ranges.items():
                            count = len(df_export[(df_export['Spam_Score'] >= low) & (df_export['Spam_Score'] <= high)])
                            percentage = (count / total_emails * 100) if total_emails > 0 else 0
                            distribution_data.append({
                                "Score Range": label,
                                "Emails": count,
                                "Percentage": f"{percentage:.1f}%"
                            })
                        
                        distribution_df = pd.DataFrame(distribution_data)
                        st.dataframe(distribution_df, use_container_width=True)
                        
                        # Top spam senders
                        if 'From' in df_export.columns and spam_count > 0:
                            st.markdown("**Top Spam Senders:**")
                            spam_senders = df_export[df_export['Spam_Score'] >= 70]['From'].value_counts().head(10)
                            
                            if len(spam_senders) > 0:
                                sender_df = spam_senders.reset_index()
                                sender_df.columns = ['Sender', 'Spam Emails']
                                st.dataframe(sender_df, use_container_width=True)
                        
                        # Export spam-only data
                        if spam_count > 0:
                            st.markdown("**Export Spam Data:**")
                            col_a, col_b = st.columns(2)
                            
                            with col_a:
                                # Export spam emails as CSV
                                spam_df = df_export[df_export['Spam_Score'] >= 70]
                                spam_csv = spam_df.to_csv(index=False)
                                st.download_button(
                                    label="Download Spam Emails (CSV)",
                                    data=spam_csv,
                                    file_name="spam_emails.csv",
                                    mime="text/csv",
                                    type="secondary",
                                    use_container_width=True
                                )
                            
                            with col_b:
                                # Export clean emails
                                clean_df = df_export[df_export['Spam_Score'] < 70]
                                clean_csv = clean_df.to_csv(index=False)
                                st.download_button(
                                    label="Download Clean Emails (CSV)",
                                    data=clean_csv,
                                    file_name="clean_emails.csv",
                                    mime="text/csv",
                                    type="secondary",
                                    use_container_width=True
                                )
            except:
                pass  # Silently skip if structure can't be determined
        # ========== END SPAM STATISTICS ==========
        
        with st.expander("Final Preview"):
            st.dataframe(df_export, use_container_width=True)
        
        st.markdown("---")
        
        # ADD BACK THE CONVERSION TRACKING BUTTONS
        st.markdown("### Next Steps")
        
        col_reset1, col_reset2, col_reset3 = st.columns(3)
        
        with col_reset1:
            if st.button("📥 Save & Start New", type="primary", use_container_width=True):
                # Increment conversion count since user completed this conversion
                increment_conversion_count(st.session_state.user_email)
                
                # Reset for new conversion
                st.session_state.df = None
                st.session_state.data_structure = None
                st.session_state.df_organized = None
                st.session_state.file_processed = False
                st.session_state.data_cleaned = False
                st.session_state.structure_detected = False
                st.session_state.last_uploaded_file = None
                
                st.success("Conversion completed! Starting new conversion...")
                st.rerun()
        
        with col_reset2:
            if st.button("🔄 Reset Current", type="secondary", use_container_width=True):
                # Reset current data without counting as new conversion
                st.session_state.df_organized = None
                st.info("Data reset. You can reorganize without starting over.")
                st.rerun()
        
        with col_reset3:
            if st.button("🏠 Return to Start", type="secondary", use_container_width=True):
                # Go back to Tab 1 without resetting
                st.info("Returning to Input tab...")
                # Note: In Streamlit, we can't directly switch tabs programmatically
                # But we can suggest user to click on Tab 1
                st.markdown("Please click on the **Input** tab above to add new data")
        
        # Show conversion count info
        from utils.auth import get_conversions_remaining
        remaining = get_conversions_remaining(user)
        limit = user.get('conversion_limit', 3) if user['tier'] == 'free' else 'Unlimited'
        
        st.markdown("---")
        st.info(f"**Conversions this month:** {user.get('conversions_used', 0)} used, {remaining} remaining (Limit: {limit})")
        
    else:
        st.info("Please organize your data in the Organize tab first")

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