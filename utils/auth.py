"""
User authentication and session management
Uses Google Sheets as persistent database
"""

import streamlit as st
import hashlib
from datetime import datetime
import gsheets_db

# Admin emails - Now from secrets
try:
    # Try to get admin email from secrets
    ADMIN_EMAILS = ['admin@smartdata.com', st.secrets["admin"]["admin_email"]]
except:
    # Fallback for development
    ADMIN_EMAILS = ['admin@smartdata.com', 'admin@example.com']

def hash_password(password):
    """Hash password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def load_users():
    """Load users from session state (for backward compatibility)"""
    if 'users_db' not in st.session_state:
        # Initialize empty for backward compatibility
        st.session_state.users_db = {}
    return st.session_state.users_db

def save_user(email, password, name):
    """Register a new user - Now saves to Google Sheets"""
    
    # Check if user already exists in Google Sheets
    existing_user = gsheets_db.get_user_from_sheet(email)
    if existing_user:
        return False, "Email already registered"
    
    # Add to Google Sheets
    success = gsheets_db.add_user_to_sheet(
        email=email,
        password_hash=hash_password(password),
        name=name,
        tier='free'
    )
    
    if success:
        # Also add to session state for current session
        users = load_users()
        users[email] = {
            'password': hash_password(password),
            'name': name,
            'tier': 'free',
            'created_at': datetime.now().isoformat(),
            'conversions_used': 0,
            'last_reset': datetime.now().isoformat(),
            'last_login': datetime.now().isoformat()
        }
        st.session_state.users_db = users
        
        return True, "Registration successful!"
    else:
        return False, "Registration failed. Please try again."

def verify_login(email, password):
    """Verify user login credentials - Now checks Google Sheets"""
    # First check Google Sheets
    user = gsheets_db.get_user_from_sheet(email)
    
    if user:
        # User exists in Google Sheets
        if user['password'] == hash_password(password):
            # Update last login in Google Sheets
            gsheets_db.update_last_login(email)
            
            # Also update session state
            users = load_users()
            users[email] = user
            users[email]['last_login'] = datetime.now().isoformat()
            st.session_state.users_db = users
            
            return True, "Login successful"
        else:
            return False, "Incorrect password"
    
    # Fallback to session state for backward compatibility
    users = load_users()
    if email in users:
        if users[email]['password'] == hash_password(password):
            users[email]['last_login'] = datetime.now().isoformat()
            st.session_state.users_db = users
            return True, "Login successful (local session)"
        else:
            return False, "Incorrect password"
    
    return False, "Email not found"

def login_user(email):
    """Set user session as logged in"""
    # Try to get user from Google Sheets first
    user = gsheets_db.get_user_from_sheet(email)
    
    if user:
        # User exists in Google Sheets
        st.session_state.logged_in = True
        st.session_state.user_email = email
        st.session_state.user_data = user
        st.session_state.is_admin = is_admin(email)
        return True
    else:
        # Fallback to session state
        users = load_users()
        if email in users:
            st.session_state.logged_in = True
            st.session_state.user_email = email
            st.session_state.user_data = users[email]
            st.session_state.is_admin = is_admin(email)
            return True
    
    return False

def logout_user():
    """Log out current user"""
    st.session_state.logged_in = False
    st.session_state.user_email = None
    st.session_state.user_data = None
    st.session_state.is_admin = False

def is_logged_in():
    """Check if user is logged in"""
    return st.session_state.get('logged_in', False)

def get_current_user():
    """Get current user data"""
    if is_logged_in():
        return st.session_state.get('user_data')
    return None

def is_admin(user_email):
    """Check if user is admin"""
    return user_email in ADMIN_EMAILS

def get_all_users():
    """Get all users (admin only) - Now from Google Sheets"""
    # Try to get from Google Sheets first
    sheet_users = gsheets_db.get_all_users_from_sheet()
    if sheet_users:
        return sheet_users
    
    # Fallback to session state
    users = load_users()
    user_list = []
    for email, user_data in users.items():
        user_list.append({
            'email': email,
            'name': user_data['name'],
            'tier': user_data['tier'],
            'conversions_used': user_data.get('conversions_used', 0),
            'created_at': user_data['created_at'],
            'last_login': user_data.get('last_login', 'Never')
        })
    
    return user_list

def update_user_tier(email, new_tier):
    """Update user's subscription tier - Now updates Google Sheets"""
    # Update in Google Sheets
    success = gsheets_db.update_user_in_sheet(email, {'tier': new_tier})
    
    if success:
        # Also update session state
        users = load_users()
        if email in users:
            users[email]['tier'] = new_tier
            st.session_state.users_db = users
            
            # Update current session if it's the logged-in user
            if st.session_state.get('user_email') == email:
                st.session_state.user_data['tier'] = new_tier
        
        return True
    
    return False

def update_user(email, updates):
    """Update user data (admin only) - Now updates Google Sheets"""
    # Update in Google Sheets
    success = gsheets_db.update_user_in_sheet(email, updates)
    
    if success:
        # Also update session state
        users = load_users()
        if email in users:
            users[email].update(updates)
            st.session_state.users_db = users
            
            # Update current session if it's the logged-in user
            if st.session_state.get('user_email') == email:
                st.session_state.user_data.update(updates)
        
        return True
    
    return False

def delete_user(email):
    """Delete user (admin only) - Now deletes from Google Sheets"""
    if email in ADMIN_EMAILS:  # Don't delete admins
        return False
    
    # Delete from Google Sheets
    success = gsheets_db.delete_user_from_sheet(email)
    
    if success:
        # Also delete from session state
        users = load_users()
        if email in users:
            del users[email]
            st.session_state.users_db = users
        
        return True
    
    return False

def reset_user_conversions(email):
    """Reset user's conversion count (admin only) - Now updates Google Sheets"""
    updates = {
        'conversions_used': 0,
        'last_reset': datetime.now().isoformat()
    }
    
    return update_user(email, updates)

def increment_conversion_count(email):
    """Increment user's conversion count - Now updates Google Sheets"""
    # Update in Google Sheets
    success = gsheets_db.increment_conversions_in_sheet(email)
    
    if success:
        # Also update session state
        users = load_users()
        if email in users:
            users[email]['conversions_used'] += 1
            st.session_state.users_db = users
            
            # Update current session
            if st.session_state.get('user_email') == email:
                st.session_state.user_data['conversions_used'] += 1
        
        return True
    
    return False

def get_conversion_limit(tier):
    """Get conversion limit based on tier"""
    limits = {
        'free': 50,  # Increased for development
        'pro': float('inf'),
        'analyst': float('inf'),
        'business': float('inf')
    }
    return limits.get(tier, 50)

def can_convert(user_data):
    """Check if user can perform a conversion"""
    tier = user_data.get('tier', 'free')
    used = user_data.get('conversions_used', 0)
    limit = get_conversion_limit(tier)
    
    return used < limit

def get_conversions_remaining(user_data):
    """Get number of conversions remaining"""
    tier = user_data.get('tier', 'free')
    used = user_data.get('conversions_used', 0)
    limit = get_conversion_limit(tier)
    
    if limit == float('inf'):
        return "Unlimited"
    
    return max(0, limit - used)

def show_login_page():
    """Display login/signup page"""
    # Check if Google Sheets is connected
    sheets_connected = gsheets_db.sheet_exists()
    
    if not sheets_connected:
        st.warning("""
        **⚠️ DEVELOPMENT MODE**
        
        User accounts are stored in temporary session storage.
        
        **Accounts will be lost when:**
        - You refresh the page
        - Session expires (24 hours)
        - App restarts
        
        For persistent accounts, ensure Google Sheets is properly configured.
        """)
    
    st.markdown("## Welcome to Smart Data Organizer")
    
    tab1, tab2 = st.tabs(["Login", "Sign Up"])
    
    with tab1:
        st.subheader("Login to Your Account")
        
        with st.form("login_form"):
            email = st.text_input("Email", placeholder="your@email.com")
            password = st.text_input("Password", type="password")
            submit = st.form_submit_button("Login", type="primary", use_container_width=True)
            
            if submit:
                if email and password:
                    success, message = verify_login(email, password)
                    if success:
                        login_user(email)
                        st.success(message)
                        if sheets_connected:
                            st.info("Connected to persistent database")
                        st.rerun()
                    else:
                        st.error(message)
                else:
                    st.warning("Please enter email and password")
        
        # Demo credentials hint
        with st.expander("Try Demo Account"):
            st.info("""
            **Demo Credentials:**
            - Email: demo@example.com
            - Password: demo123
            
            **Admin Credentials:**
            - Email: admin@smartdata.com
            - Password: admin123
            
            **Note:** These accounts are pre-loaded in the database.
            """)
    
    with tab2:
        st.subheader("Create New Account")
        
        with st.form("signup_form"):
            name = st.text_input("Full Name", placeholder="John Doe")
            email = st.text_input("Email", placeholder="your@email.com")
            password = st.text_input("Password", type="password")
            password_confirm = st.text_input("Confirm Password", type="password")
            
            agree = st.checkbox("I agree to the Terms of Service")
            
            submit = st.form_submit_button("Create Account", type="primary", use_container_width=True)
            
            if submit:
                if not all([name, email, password, password_confirm]):
                    st.warning("Please fill all fields")
                elif password != password_confirm:
                    st.error("Passwords don't match")
                elif len(password) < 6:
                    st.error("Password must be at least 6 characters")
                elif not agree:
                    st.warning("Please agree to Terms of Service")
                else:
                    success, message = save_user(email, password, name)
                    if success:
                        if sheets_connected:
                            st.success(f"{message} (Saved to database)")
                        else:
                            st.success(f"{message} (Local session only)")
                    else:
                        st.error(message)

def show_user_sidebar():
    """Display user info in sidebar"""
    if is_logged_in():
        user = get_current_user()
        
        st.sidebar.markdown("---")
        st.sidebar.markdown(f"### {user['name']}")
        st.sidebar.caption(st.session_state.user_email)
        
        # Check if data is from Google Sheets
        sheets_connected = gsheets_db.sheet_exists()
        if sheets_connected and st.session_state.user_email:
            sheet_user = gsheets_db.get_user_from_sheet(st.session_state.user_email)
            if sheet_user:
                st.sidebar.caption("✓ Persistent account")
        
        # Tier badge
        tier = user['tier'].upper()
        st.sidebar.markdown(f"**Plan:** {tier}")
        
        # Usage stats
        remaining = get_conversions_remaining(user)
        if remaining == "Unlimited":
            st.sidebar.success("Unlimited conversions")
        else:
            used = user['conversions_used']
            limit = get_conversion_limit(user['tier'])
            st.sidebar.info(f"{remaining}/{limit} conversions left")
            
            # Progress bar
            progress = min(used / limit, 1.0)
            st.sidebar.progress(progress)
        
        # Logout button
        if st.sidebar.button("Logout", use_container_width=True):
            logout_user()
            st.rerun()

def migrate_session_to_sheets():
    """Migrate session users to Google Sheets (one-time operation)"""
    if not gsheets_db.sheet_exists():
        return False
    
    users = load_users()
    migrated = 0
    
    for email, user_data in users.items():
        # Check if user already exists in sheets
        existing = gsheets_db.get_user_from_sheet(email)
        if not existing:
            # Add to sheets
            success = gsheets_db.add_user_to_sheet(
                email=email,
                password_hash=user_data['password'],
                name=user_data['name'],
                tier=user_data['tier']
            )
            if success:
                migrated += 1
    
    return migrated