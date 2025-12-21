"""
User authentication and session management
Uses Google Sheets as persistent database
"""

import streamlit as st
import hashlib
from datetime import datetime
import gsheets_db
import time

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

def initialize_demo_accounts():
    """Initialize database with demo accounts"""
    demo_users = [
        {
            "email": "demo@example.com",
            "password": "demo123",
            "name": "Demo User",
            "tier": "free"
        },
        {
            "email": "admin@smartdata.com",
            "password": "admin123",
            "name": "Admin User",
            "tier": "pro"
        }
    ]
    
    # Add your email as admin too
    try:
        admin_email = st.secrets["admin"]["admin_email"]
        demo_users.append({
            "email": admin_email,
            "password": "admin123",
            "name": "Admin",
            "tier": "pro"
        })
    except:
        pass
    
    added = 0
    for user in demo_users:
        # Check if user exists
        existing = gsheets_db.get_user_from_sheet(user["email"])
        
        if not existing:
            # Add user
            success = gsheets_db.add_user_to_sheet(
                email=user["email"],
                password_hash=hash_password(user["password"]),
                name=user["name"],
                tier=user["tier"]
            )
            if success:
                added += 1
    
    return added

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

def get_admin_list():
    """Get list of all admin emails from Google Sheets"""
    try:
        all_users = get_all_users()
        admin_emails = []
        
        for user in all_users:
            is_admin_flag = user.get('is_admin', False)
            
            # Handle string "TRUE"/"FALSE"
            if isinstance(is_admin_flag, str):
                if is_admin_flag.upper() == 'TRUE':
                    admin_emails.append(user['email'])
            # Handle boolean True/False
            elif is_admin_flag:
                admin_emails.append(user['email'])
        
        # Always include default admins
        default_admins = ['admin@smartdata.com']
        try:
            default_admins.append(st.secrets["admin"]["admin_email"])
        except:
            pass
        
        all_admins = list(set(admin_emails + default_admins))
        return all_admins
    except Exception as e:
        print(f"Error getting admin list: {str(e)}")
        return ['admin@smartdata.com', st.secrets.get("admin", {}).get("admin_email", 'admin@example.com')]

# REPLACE the existing is_admin() function with this:
def is_admin(user_email):
    """Check if user is admin - Now checks both default list and user data"""
    # Check default admin list first
    default_admins = ['admin@smartdata.com']
    try:
        default_admins.append(st.secrets["admin"]["admin_email"])
    except:
        pass
    
    if user_email in default_admins:
        return True
    
    # Check user data for admin flag
    user = gsheets_db.get_user_from_sheet(user_email)
    
    if user:
        # Handle different is_admin formats
        is_admin_flag = user.get('is_admin', False)
        
        # Convert string "TRUE"/"FALSE" to boolean
        if isinstance(is_admin_flag, str):
            return is_admin_flag.lower() == 'true'
        
        # Convert integer 1/0 to boolean
        if isinstance(is_admin_flag, int):
            return bool(is_admin_flag)
        
        # Already boolean
        return bool(is_admin_flag)
    
    return False

def promote_to_admin(email):
    """Promote a user to admin status"""
    if not is_logged_in():
        return False, "Not logged in"
    
    current_user_email = st.session_state.get('user_email')
    if not is_admin(current_user_email):
        return False, "Only admins can promote users"
    
    user = gsheets_db.get_user_from_sheet(email)
    if not user:
        return False, "User not found"
    
    # Update with boolean TRUE (not string)
    success = gsheets_db.update_user_in_sheet(email, {'is_admin': True})
    
    if success:
        # Update current session if it's the logged-in user
        if st.session_state.get('user_email') == email:
            st.session_state.is_admin = True
            st.session_state.user_data['is_admin'] = True
        
        # Clear cache to reflect changes immediately
        if 'user_cache' in st.session_state:
            if email in st.session_state.user_cache:
                st.session_state.user_cache[email]['is_admin'] = True
        
        return True, f"{email} is now an admin"
    else:
        return False, "Failed to update user"

def demote_from_admin(email):
    """Remove admin status from a user"""
    if not is_logged_in():
        return False, "Not logged in"
    
    current_user_email = st.session_state.get('user_email')
    if not is_admin(current_user_email):
        return False, "Only admins can demote users"
    
    # Prevent demoting default admins
    default_admins = ['admin@smartdata.com']
    try:
        default_admins.append(st.secrets["admin"]["admin_email"])
    except:
        pass
    
    if email in default_admins:
        return False, "Cannot demote default admin accounts"
    
    # Prevent self-demotion if you're the only admin
    all_admins = get_admin_list()
    if email == current_user_email and len(all_admins) <= 1:
        return False, "Cannot demote yourself - you're the only admin"
    
    # Update with boolean FALSE (not string)
    success = gsheets_db.update_user_in_sheet(email, {'is_admin': False})
    
    if success:
        # Update current session if it's the logged-in user
        if st.session_state.get('user_email') == email:
            st.session_state.is_admin = False
            st.session_state.user_data['is_admin'] = False
        
        # Clear cache to reflect changes immediately
        if 'user_cache' in st.session_state:
            if email in st.session_state.user_cache:
                st.session_state.user_cache[email]['is_admin'] = False
        
        return True, f"{email} is no longer an admin"
    else:
        return False, "Failed to update user"

def get_all_users():
    """Get all users (admin only) - Now from Google Sheets"""
    # Try to get from Google Sheets first
    sheet_users = gsheets_db.get_all_users_from_sheet()
    if sheet_users:
        # Fix is_admin values from strings to booleans
        for user in sheet_users:
            is_admin_flag = user.get('is_admin', False)
            if isinstance(is_admin_flag, str):
                # Convert string "TRUE"/"FALSE" to boolean
                user['is_admin'] = is_admin_flag.upper() == 'TRUE'
        
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
            'last_login': user_data.get('last_login', 'Never'),
            'is_admin': user_data.get('is_admin', False)  # Add is_admin
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
    
    # Check sheets connection ONCE per session (not on every rerun)
    if 'sheets_check_done' not in st.session_state:
        st.session_state.sheets_check_done = False
        st.session_state.sheets_connected = False
    
    # Only check if not already checked
    if not st.session_state.sheets_check_done:
        with st.spinner("Checking database connection..."):
            st.session_state.sheets_connected = gsheets_db.sheet_exists()
            st.session_state.sheets_check_done = True
    
    sheets_connected = st.session_state.sheets_connected
    
    if not sheets_connected:
        st.warning("""
        **⚠️ DATABASE NOT INITIALIZED**
        
        The Google Sheet database needs to be set up with demo accounts.
        """)
        
        # Add initialization button
        if st.button("🔧 Initialize Database (Click Once)", type="primary", use_container_width=True):
            with st.spinner("Creating database and demo accounts..."):
                # Create the sheet
                worksheet = gsheets_db.get_or_create_sheet()
                
                if worksheet:
                    # Add demo accounts
                    added = initialize_demo_accounts()
                    
                    if added > 0:
                        st.success(f"""
                        ✅ **Database Initialized Successfully!**
                        
                        {added} demo accounts created.
                        
                        **You can now login with:**
                        - Email: demo@example.com
                        - Password: demo123
                        
                        **OR**
                        
                        - Email: admin@smartdata.com  
                        - Password: admin123
                        
                        Please refresh the page or click Login below.
                        """)
                        st.balloons()
                        
                        # Update the check flag
                        st.session_state.sheets_connected = True
                        st.session_state.sheets_check_done = True
                    else:
                        st.info("Database already has accounts. You can login below.")
                else:
                    st.error("Failed to create database. Please check your Google Sheets configuration.")
        
        st.markdown("---")
    
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
                    with st.spinner("Logging in..."):
                        success, message = verify_login(email, password)
                        if success:
                            login_user(email)
                            st.success(message)
                            if sheets_connected:
                                st.info("✅ Connected to persistent database")
                            # Small delay before rerun to show success message
                            time.sleep(0.5)
                            st.rerun()
                        else:
                            st.error(message)
                else:
                    st.warning("Please enter email and password")
        
        # Demo credentials hint
        with st.expander("📝 Demo Credentials"):
            st.info("""
            **Demo Account:**
            - Email: demo@example.com
            - Password: demo123
            
            **Admin Account:**
            - Email: admin@smartdata.com
            - Password: admin123
            
            If you don't see these accounts, click "Initialize Database" above.
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
                    with st.spinner("Creating account..."):
                        success, message = save_user(email, password, name)
                        if success:
                            if sheets_connected:
                                st.success(f"{message} ✅ Saved to database")
                            else:
                                st.success(f"{message} (Local session only)")
                            st.info("You can now login with your credentials")
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
                st.sidebar.caption("✅ Persistent account")
        
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