"""
Google Sheets Database for Smart Data Organizer
Persistent database solution with caching to avoid rate limits
"""

import gspread
from google.oauth2.service_account import Credentials
import streamlit as st
from datetime import datetime, timedelta
import pandas as pd
import hashlib
import time

# Cache duration in seconds
CACHE_DURATION = 300  # 5 minutes

# Initialize once per session
@st.cache_resource
def get_gsheets_client():
    """Initialize Google Sheets client with caching"""
    try:
        creds_info = {
            "type": st.secrets["gsheets"]["type"],
            "project_id": st.secrets["gsheets"]["project_id"],
            "private_key_id": st.secrets["gsheets"]["private_key_id"],
            "private_key": st.secrets["gsheets"]["private_key"].replace("\\n", "\n"),
            "client_email": st.secrets["gsheets"]["client_email"],
            "client_id": st.secrets["gsheets"]["client_id"],
            "auth_uri": st.secrets["gsheets"]["auth_uri"],
            "token_uri": st.secrets["gsheets"]["token_uri"],
            "auth_provider_x509_cert_url": st.secrets["gsheets"]["auth_provider_x509_cert_url"],
            "client_x509_cert_url": st.secrets["gsheets"]["client_x509_cert_url"],
            "universe_domain": "googleapis.com"
        }
        
        scopes = [
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive'
        ]
        creds = Credentials.from_service_account_info(creds_info, scopes=scopes)
        client = gspread.authorize(creds)
        return client
        
    except KeyError as e:
        st.error(f"Missing secret key: {str(e)}")
        return None
    except Exception as e:
        st.error(f"Google Sheets connection failed: {str(e)}")
        return None

@st.cache_resource(ttl=CACHE_DURATION)
def get_or_create_sheet(sheet_name="SmartDataOrganizer_Users"):
    """Get existing Google Sheet with caching"""
    client = get_gsheets_client()
    if not client:
        return None
    
    try:
        spreadsheet = client.open(sheet_name)
        worksheet = spreadsheet.sheet1
        
        # Verify headers exist
        headers = worksheet.row_values(1)
        expected_headers = ['email', 'password_hash', 'name', 'tier', 
                          'conversions_used', 'created_at', 'last_login', 'last_reset']
        
        if not headers or headers != expected_headers:
            worksheet.update('A1:H1', [expected_headers])
            worksheet.format('A1:H1', {
                'backgroundColor': {'red': 0.2, 'green': 0.2, 'blue': 0.2},
                'horizontalAlignment': 'CENTER',
                'textFormat': {'foregroundColor': {'red': 1.0, 'green': 1.0, 'blue': 1.0}, 'bold': True}
            })
        
        return worksheet
        
    except gspread.SpreadsheetNotFound:
        st.error(f"❌ Google Sheet '{sheet_name}' not found. Please create it manually.")
        return None
    except Exception as e:
        st.error(f"Error accessing sheet: {str(e)}")
        return None

def sheet_exists():
    """Check if the sheet exists - cached version"""
    if 'sheet_exists_cache' not in st.session_state:
        st.session_state.sheet_exists_cache = None
        st.session_state.sheet_exists_time = None
    
    # Check cache
    if st.session_state.sheet_exists_cache is not None:
        if st.session_state.sheet_exists_time:
            elapsed = (datetime.now() - st.session_state.sheet_exists_time).total_seconds()
            if elapsed < CACHE_DURATION:
                return st.session_state.sheet_exists_cache
    
    # Cache miss - check for real
    try:
        client = get_gsheets_client()
        if not client:
            result = False
        else:
            client.open("SmartDataOrganizer_Users")
            result = True
    except:
        result = False
    
    # Update cache
    st.session_state.sheet_exists_cache = result
    st.session_state.sheet_exists_time = datetime.now()
    
    return result

@st.cache_data(ttl=CACHE_DURATION)
def get_all_users_cached():
    """Get all users with caching"""
    worksheet = get_or_create_sheet()
    if not worksheet:
        return []
    
    try:
        time.sleep(0.1)  # Rate limiting
        records = worksheet.get_all_records()
        
        users = []
        for record in records:
            users.append({
                'email': record['email'],
                'name': record['name'],
                'tier': record['tier'],
                'conversions_used': int(record['conversions_used']) if record['conversions_used'] else 0,
                'created_at': record['created_at'],
                'last_login': record['last_login']
            })
        
        return users
    except Exception as e:
        print(f"Error getting all users: {str(e)}")
        return []

def add_user_to_sheet(email, password_hash, name, tier='free'):
    """Add user to Google Sheet"""
    worksheet = get_or_create_sheet()
    if not worksheet:
        return False
    
    now = datetime.now().isoformat()
    
    try:
        time.sleep(0.2)  # Rate limiting
        worksheet.append_row([
            email,
            password_hash,
            name,
            tier,
            0,
            now,
            now,
            now
        ])
        
        # Clear caches
        st.cache_data.clear()
        if 'user_cache' in st.session_state:
            del st.session_state.user_cache
        
        return True
    except Exception as e:
        print(f"Error adding user to sheet: {str(e)}")
        return False

def get_user_from_sheet(email):
    """Get user from Google Sheet with caching"""
    # Check session cache first
    if 'user_cache' not in st.session_state:
        st.session_state.user_cache = {}
        st.session_state.user_cache_time = {}
    
    # Return cached user if fresh
    if email in st.session_state.user_cache:
        cache_time = st.session_state.user_cache_time.get(email)
        if cache_time:
            elapsed = (datetime.now() - cache_time).total_seconds()
            if elapsed < CACHE_DURATION:
                return st.session_state.user_cache[email]
    
    # Cache miss - fetch from sheet
    if not sheet_exists():
        return None
    
    worksheet = get_or_create_sheet()
    if not worksheet:
        return None
    
    try:
        time.sleep(0.1)  # Rate limiting
        records = worksheet.get_all_records()
        
        for record in records:
            if record['email'] == email:
                user_data = {
                    'email': record['email'],
                    'password': record['password_hash'],
                    'name': record['name'],
                    'tier': record['tier'],
                    'conversions_used': int(record['conversions_used']) if record['conversions_used'] else 0,
                    'created_at': record['created_at'],
                    'last_login': record['last_login'],
                    'last_reset': record['last_reset']
                }
                
                # Cache the result
                st.session_state.user_cache[email] = user_data
                st.session_state.user_cache_time[email] = datetime.now()
                
                return user_data
    except Exception as e:
        print(f"Error reading from sheet: {str(e)}")
    
    return None

def update_user_in_sheet(email, updates):
    """Update user data in Google Sheet"""
    if not sheet_exists():
        return False
    
    worksheet = get_or_create_sheet()
    if not worksheet:
        return False
    
    try:
        time.sleep(0.2)  # Rate limiting
        records = worksheet.get_all_records()
        
        for i, record in enumerate(records, start=2):
            if record['email'] == email:
                for key, value in updates.items():
                    if key in record:
                        col_idx = list(record.keys()).index(key) + 1
                        worksheet.update_cell(i, col_idx, value)
                        time.sleep(0.1)  # Rate limiting between updates
                
                # Clear user cache
                if 'user_cache' in st.session_state and email in st.session_state.user_cache:
                    del st.session_state.user_cache[email]
                
                return True
    except Exception as e:
        print(f"Error updating user in sheet: {str(e)}")
    
    return False

def get_all_users_from_sheet():
    """Get all users from Google Sheet - uses cached version"""
    return get_all_users_cached()

def increment_conversions_in_sheet(email):
    """Increment user's conversion count"""
    if not sheet_exists():
        return False
    
    worksheet = get_or_create_sheet()
    if not worksheet:
        return False
    
    try:
        time.sleep(0.2)  # Rate limiting
        records = worksheet.get_all_records()
        
        for i, record in enumerate(records, start=2):
            if record['email'] == email:
                current = int(record['conversions_used']) if record['conversions_used'] else 0
                worksheet.update_cell(i, 5, current + 1)
                
                # Clear user cache
                if 'user_cache' in st.session_state and email in st.session_state.user_cache:
                    del st.session_state.user_cache[email]
                
                return True
    except Exception as e:
        print(f"Error incrementing conversions: {str(e)}")
    
    return False

def update_last_login(email):
    """Update user's last login time - DISABLED to reduce API calls"""
    # Skip this to reduce API calls during login
    # It's not critical information
    return True

def delete_user_from_sheet(email):
    """Delete user from Google Sheet"""
    if not sheet_exists():
        return False
    
    worksheet = get_or_create_sheet()
    if not worksheet:
        return False
    
    try:
        time.sleep(0.2)  # Rate limiting
        records = worksheet.get_all_records()
        
        for i, record in enumerate(records, start=2):
            if record['email'] == email:
                worksheet.delete_rows(i)
                
                # Clear caches
                st.cache_data.clear()
                if 'user_cache' in st.session_state and email in st.session_state.user_cache:
                    del st.session_state.user_cache[email]
                
                return True
    except Exception as e:
        print(f"Error deleting user: {str(e)}")
    
    return False

def reset_all_conversions_in_sheet():
    """Reset all users' conversion counts"""
    if not sheet_exists():
        return False
    
    worksheet = get_or_create_sheet()
    if not worksheet:
        return False
    
    try:
        time.sleep(0.2)  # Rate limiting
        records = worksheet.get_all_records()
        
        for i, record in enumerate(records, start=2):
            worksheet.update_cell(i, 5, 0)
            time.sleep(0.1)
            worksheet.update_cell(i, 8, datetime.now().isoformat())
            time.sleep(0.1)
        
        # Clear caches
        st.cache_data.clear()
        if 'user_cache' in st.session_state:
            st.session_state.user_cache = {}
        
        return True
    except Exception as e:
        print(f"Error resetting conversions: {str(e)}")
        return False