# File: utils/auth.py
"""
User authentication and session management
"""

import streamlit as st
import json
import hashlib
from datetime import datetime

# Simple file-based user storage (for MVP)
# In production, use a proper database

def hash_password(password):
    """Hash password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def load_users():
    """Load users from session state (simulated database)"""
    if 'users_db' not in st.session_state:
        # Initialize with default users for testing
        st.session_state.users_db = {
            'demo@example.com': {
                'password': hash_password('demo123'),
                'name': 'Demo User',
                'tier': 'free',
                'created_at': datetime.now().isoformat(),
                'conversions_used': 0,
                'last_reset': datetime.now().isoformat()
            }
        }
    return st.session_state.users_db

def save_user(email, password, name):
    """Register a new user"""
    users = load_users()
    
    if email in users:
        return False, "Email already registered"
    
    users[email] = {
        'password': hash_password(password),
        'name': name,
        'tier': 'free',
        'created_at': datetime.now().isoformat(),
        'conversions_used': 0,
        'last_reset': datetime.now().isoformat()
    }
    
    st.session_state.users_db = users
    return True, "Registration successful"

def verify_login(email, password):
    """Verify user login credentials"""
    users = load_users()
    
    if email not in users:
        return False, "Email not found"
    
    if users[email]['password'] != hash_password(password):
        return False, "Incorrect password"
    
    return True, "Login successful"

def login_user(email):
    """Set user session as logged in"""
    users = load_users()
    st.session_state.logged_in = True
    st.session_state.user_email = email
    st.session_state.user_data = users[email]

def logout_user():
    """Log out current user"""
    st.session_state.logged_in = False
    st.session_state.user_email = None
    st.session_state.user_data = None

def is_logged_in():
    """Check if user is logged in"""
    return st.session_state.get('logged_in', False)

def get_current_user():
    """Get current user data"""
    if is_logged_in():
        return st.session_state.get('user_data')
    return None

def update_user_tier(email, new_tier):
    """Update user's subscription tier"""
    users = load_users()
    if email in users:
        users[email]['tier'] = new_tier
        st.session_state.users_db = users
        
        # Update current session if it's the logged-in user
        if st.session_state.get('user_email') == email:
            st.session_state.user_data['tier'] = new_tier

def increment_conversion_count(email):
    """Increment user's conversion count"""
    users = load_users()
    if email in users:
        users[email]['conversions_used'] += 1
        st.session_state.users_db = users
        
        # Update current session
        if st.session_state.get('user_email') == email:
            st.session_state.user_data['conversions_used'] += 1

def get_conversion_limit(tier):
    """Get conversion limit based on tier"""
    limits = {
        'free': 5,
        'pro': float('inf'),
        'analyst': float('inf'),
        'business': float('inf')
    }
    return limits.get(tier, 5)

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
    st.markdown("## 🔐 Welcome to Smart Data Organizer")
    
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
                        st.rerun()
                    else:
                        st.error(message)
                else:
                    st.warning("Please enter email and password")
        
        # Demo credentials hint
        with st.expander("🎮 Try Demo Account"):
            st.info("""
            **Demo Credentials:**
            - Email: demo@example.com
            - Password: demo123
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
                        st.success(message + " - Please login")
                    else:
                        st.error(message)

def show_user_sidebar():
    """Display user info in sidebar"""
    if is_logged_in():
        user = get_current_user()
        
        st.sidebar.markdown("---")
        st.sidebar.markdown(f"### 👤 {user['name']}")
        st.sidebar.caption(st.session_state.user_email)
        
        # Tier badge
        tier = user['tier'].upper()
        tier_colors = {
            'FREE': '🆓',
            'PRO': '⭐',
            'ANALYST': '💎',
            'BUSINESS': '🏢'
        }
        st.sidebar.markdown(f"**Plan:** {tier_colors.get(tier, '')} {tier}")
        
        # Usage stats
        remaining = get_conversions_remaining(user)
        if remaining == "Unlimited":
            st.sidebar.success("✅ Unlimited conversions")
        else:
            used = user['conversions_used']
            limit = get_conversion_limit(user['tier'])
            st.sidebar.info(f"📊 {remaining}/{limit} conversions left")
            
            # Progress bar
            progress = min(used / limit, 1.0)
            st.sidebar.progress(progress)
        
        # Logout button
        if st.sidebar.button("🚪 Logout", use_container_width=True):
            logout_user()
            st.rerun()