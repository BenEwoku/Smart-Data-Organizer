"""
Google Sheets Database for Smart Data Organizer
Persistent database solution for Streamlit Cloud
"""

import gspread
from google.oauth2.service_account import Credentials
import streamlit as st
from datetime import datetime
import pandas as pd
import hashlib

# Initialize once per session
@st.cache_resource
def get_gsheets_client():
    """Initialize Google Sheets client with caching"""
    try:
        # Get credentials from Streamlit secrets
        creds_info = {
            "type": st.secrets["gsheets"]["type"],
            "project_id": st.secrets["gsheets"]["project_id"],
            "private_key_id": st.secrets["gsheets"]["private_key_id"],
            # Fix: Replace literal \n with actual newlines
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
        st.error("Please check your Streamlit Cloud secrets configuration.")
        return None
    except Exception as e:
        st.error(f"Google Sheets connection failed: {str(e)}")
        return None

def get_or_create_sheet(sheet_name="SmartDataOrganizer_Users"):
    """Get or create Google Sheet"""
    client = get_gsheets_client()
    if not client:
        return None
    
    try:
        # Try to open existing sheet
        spreadsheet = client.open(sheet_name)
    except gspread.SpreadsheetNotFound:
        # Create new spreadsheet
        spreadsheet = client.create(sheet_name)
        
        # Share with service account for access
        spreadsheet.share(st.secrets["gsheets"]["client_email"], perm_type='user', role='writer')
        
        # Get the first worksheet
        worksheet = spreadsheet.sheet1
        
        # Add headers
        worksheet.update('A1:H1', [[
            'email', 'password_hash', 'name', 'tier', 
            'conversions_used', 'created_at', 'last_login', 'last_reset'
        ]])
        
        # Format headers
        worksheet.format('A1:H1', {
            'backgroundColor': {'red': 0.2, 'green': 0.2, 'blue': 0.2},
            'horizontalAlignment': 'CENTER',
            'textFormat': {'foregroundColor': {'red': 1.0, 'green': 1.0, 'blue': 1.0}, 'bold': True}
        })
    
    return spreadsheet.sheet1

def sheet_exists():
    """Check if the sheet exists"""
    try:
        client = get_gsheets_client()
        if not client:
            return False
        
        client.open("SmartDataOrganizer_Users")
        return True
    except:
        return False

def add_user_to_sheet(email, password_hash, name, tier='free'):
    """Add user to Google Sheet"""
    worksheet = get_or_create_sheet()
    if not worksheet:
        return False
    
    now = datetime.now().isoformat()
    
    try:
        worksheet.append_row([
            email,
            password_hash,
            name,
            tier,
            0,  # conversions_used
            now,  # created_at
            now,  # last_login
            now   # last_reset
        ])
        return True
    except Exception as e:
        print(f"Error adding user to sheet: {str(e)}")
        return False

def get_user_from_sheet(email):
    """Get user from Google Sheet by email"""
    if not sheet_exists():
        return None
    
    worksheet = get_or_create_sheet()
    if not worksheet:
        return None
    
    try:
        # Get all records
        records = worksheet.get_all_records()
        
        # Find user by email
        for record in records:
            if record['email'] == email:
                return {
                    'email': record['email'],
                    'password': record['password_hash'],
                    'name': record['name'],
                    'tier': record['tier'],
                    'conversions_used': int(record['conversions_used']) if record['conversions_used'] else 0,
                    'created_at': record['created_at'],
                    'last_login': record['last_login'],
                    'last_reset': record['last_reset']
                }
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
        # Get all records
        records = worksheet.get_all_records()
        
        # Find user row
        for i, record in enumerate(records, start=2):  # Start at row 2 (skip header)
            if record['email'] == email:
                # Update fields
                for key, value in updates.items():
                    if key in record:
                        # Find column index
                        col_idx = list(record.keys()).index(key) + 1  # +1 for 1-indexed
                        worksheet.update_cell(i, col_idx, value)
                return True
    except Exception as e:
        print(f"Error updating user in sheet: {str(e)}")
    
    return False

def get_all_users_from_sheet():
    """Get all users from Google Sheet"""
    if not sheet_exists():
        return []
    
    worksheet = get_or_create_sheet()
    if not worksheet:
        return []
    
    try:
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

def increment_conversions_in_sheet(email):
    """Increment user's conversion count"""
    if not sheet_exists():
        return False
    
    worksheet = get_or_create_sheet()
    if not worksheet:
        return False
    
    try:
        # Get all records
        records = worksheet.get_all_records()
        
        # Find user row
        for i, record in enumerate(records, start=2):  # Start at row 2 (skip header)
            if record['email'] == email:
                current = int(record['conversions_used']) if record['conversions_used'] else 0
                worksheet.update_cell(i, 5, current + 1)  # Column 5 is conversions_used
                return True
    except Exception as e:
        print(f"Error incrementing conversions: {str(e)}")
    
    return False

def update_last_login(email):
    """Update user's last login time"""
    if not sheet_exists():
        return False
    
    return update_user_in_sheet(email, {
        'last_login': datetime.now().isoformat()
    })

def delete_user_from_sheet(email):
    """Delete user from Google Sheet"""
    if not sheet_exists():
        return False
    
    worksheet = get_or_create_sheet()
    if not worksheet:
        return False
    
    try:
        # Get all records
        records = worksheet.get_all_records()
        
        # Find user row
        for i, record in enumerate(records, start=2):  # Start at row 2 (skip header)
            if record['email'] == email:
                # Delete the row
                worksheet.delete_rows(i)
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
        # Get all records
        records = worksheet.get_all_records()
        
        # Reset each user's conversions
        for i, record in enumerate(records, start=2):
            worksheet.update_cell(i, 5, 0)  # Column 5 is conversions_used
            worksheet.update_cell(i, 8, datetime.now().isoformat())  # Column 8 is last_reset
        
        return True
    except Exception as e:
        print(f"Error resetting conversions: {str(e)}")
        return False