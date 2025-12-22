"""
Simple automatic payment system for Smart Data Organizer
Code-based upgrade system
"""

import streamlit as st
import uuid
import hashlib
from datetime import datetime, timedelta

# Store upgrade codes in session state
if 'upgrade_codes' not in st.session_state:
    st.session_state.upgrade_codes = {}

def show_simple_auto_pricing():
    """Main pricing page for users"""
    
    if not st.session_state.get('logged_in'):
        st.error("Please login to view pricing")
        return
    
    from utils.auth import get_current_user, update_user, refresh_current_user_session
    
    user = get_current_user()
    user_email = st.session_state.user_email
    current_tier = user.get('tier', 'free')
    
    st.markdown("# Upgrade Your Account")
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("## Free Tier")
        st.markdown("""
        **$0/month**
        
        • 50 conversions/month
        • CSV export
        • Basic organization
        • Email support
        """)
        
        if current_tier == 'free':
            st.success("Your Current Plan")
        elif st.button("Switch to Free", use_container_width=True, type="secondary"):
            if update_user(user_email, {'tier': 'free'}):
                refresh_current_user_session()
                st.success("Switched to Free tier!")
                st.rerun()
    
    with col2:
        st.markdown("## Pro Tier")
        st.markdown("""
        **$5.00/month**
        
        • Unlimited conversions
        • Excel export
        • Advanced tools
        • Priority support
        • All features
        """)
        
        if current_tier == 'pro':
            st.success("Your Current Plan")
        else:
            # Generate unique code for this user
            upgrade_code = generate_upgrade_code(user_email)
            
            st.markdown(f"""
            **Your Upgrade Code:**
            ```bash
            {upgrade_code}
            ```
            """)
            
            # Payment methods
            with st.expander("Payment Instructions", expanded=True):
                col_pay1, col_pay2 = st.columns(2)
                
                with col_pay1:
                    st.markdown("**PayPal**")
                    st.code("Send $5.00 USD to:\nbewoku14@outlook.com")
                    st.caption("Note: Include code & your email")
                
                with col_pay2:
                    st.markdown("**Mobile Money (Uganda)**")
                    st.code("Send 18,500 UGX to:\n+256 774 617 788 (MTN)")
                    st.caption("Reference: Your code")
            
            # Code verification
            st.markdown("### Verify Your Payment")
            
            entered_code = st.text_input(
                "Enter your upgrade code:",
                placeholder="Paste code here after payment",
                key="verify_code_input"
            ).strip().upper()
            
            col_verify1, col_verify2 = st.columns([3, 1])
            
            with col_verify1:
                if entered_code:
                    if verify_upgrade_code(entered_code, user_email):
                        st.success("Code is valid!")
                    else:
                        st.error("Invalid or expired code")
            
            with col_verify2:
                if st.button("Upgrade Now", type="primary", use_container_width=True):
                    if verify_upgrade_code(entered_code, user_email):
                        # Upgrade user
                        if update_user(user_email, {'tier': 'pro'}):
                            refresh_current_user_session()
                            
                            # Mark code as used
                            if entered_code in st.session_state.upgrade_codes:
                                st.session_state.upgrade_codes[entered_code]['used'] = True
                            
                            st.success("Successfully upgraded to Pro!")
                            st.balloons()
                            st.rerun()
                    elif entered_code:
                        st.error("Please enter a valid code")
                    else:
                        st.warning("Please enter your code first")
    
    # Usage stats
    st.markdown("---")
    from utils.auth import get_conversions_remaining
    remaining = get_conversions_remaining(user)
    
    col_stat1, col_stat2, col_stat3 = st.columns(3)
    with col_stat1:
        st.metric("Current Tier", current_tier.upper())
    with col_stat2:
        st.metric("Conversions Used", user.get('conversions_used', 0))
    with col_stat3:
        st.metric("Conversions Left", "Unlimited" if remaining == "Unlimited" else str(remaining))

def generate_upgrade_code(user_email):
    """Generate a unique 8-character upgrade code"""
    
    # Create unique identifier
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    unique_string = f"{user_email}:{timestamp}:{uuid.uuid4()}"
    
    # Hash to create code
    hash_object = hashlib.sha256(unique_string.encode())
    hex_digest = hash_object.hexdigest()
    short_code = hex_digest[:8].upper()  # First 8 chars as code
    
    # Store code info
    st.session_state.upgrade_codes[short_code] = {
        'user_email': user_email,
        'created_at': datetime.now().isoformat(),
        'expires_at': (datetime.now() + timedelta(hours=24)).isoformat(),
        'used': False
    }
    
    return short_code

def verify_upgrade_code(code, user_email):
    """Verify if a code is valid for a user"""
    
    if not code or len(code) != 8:
        return False
    
    # Check if code exists
    if code not in st.session_state.upgrade_codes:
        return False
    
    code_info = st.session_state.upgrade_codes[code]
    
    # Check if already used
    if code_info.get('used', False):
        return False
    
    # Check expiration
    expires_at = datetime.fromisoformat(code_info['expires_at'])
    if datetime.now() > expires_at:
        return False
    
    # Check if code belongs to this user
    if code_info.get('user_email') != user_email:
        return False
    
    return True

def show_code_management():
    """Admin view of upgrade codes"""
    
    st.markdown("##### Active Upgrade Codes")
    
    if not st.session_state.upgrade_codes:
        st.info("No active upgrade codes")
        return
    
    # Prepare data for display
    active_codes = []
    expired_codes = []
    
    current_time = datetime.now()
    
    for code, info in st.session_state.upgrade_codes.items():
        expires_at = datetime.fromisoformat(info['expires_at'])
        time_left = expires_at - current_time
        
        code_data = {
            'Code': code,
            'User': info['user_email'],
            'Created': info['created_at'][:19].replace('T', ' '),
            'Expires': expires_at.strftime('%Y-%m-%d %H:%M'),
            'Time Left': f"{int(time_left.total_seconds() / 3600)}h {int((time_left.total_seconds() % 3600) / 60)}m",
            'Status': 'Used' if info.get('used', False) else 'Active' if current_time < expires_at else 'Expired'
        }
        
        if info.get('used', False):
            continue  # Skip used codes
        
        if current_time < expires_at:
            active_codes.append(code_data)
        else:
            expired_codes.append(code_data)
    
    # Show active codes
    if active_codes:
        import pandas as pd
        st.markdown("**Active Codes:**")
        df_active = pd.DataFrame(active_codes)
        st.dataframe(df_active, use_container_width=True, hide_index=True)
    
    # Show expired codes
    if expired_codes:
        with st.expander(f"Expired Codes ({len(expired_codes)})"):
            df_expired = pd.DataFrame(expired_codes)
            st.dataframe(df_expired, use_container_width=True, hide_index=True)
    
    # Action buttons
    col_act1, col_act2, col_act3 = st.columns(3)
    
    with col_act1:
        if st.button("Refresh", use_container_width=True):
            st.rerun()
    
    with col_act2:
        if st.button("Clear Expired", use_container_width=True):
            clear_expired_codes()
            st.success("Cleared expired codes")
            st.rerun()
    
    with col_act3:
        if st.button("Clear All", use_container_width=True, type="secondary"):
            st.session_state.upgrade_codes = {}
            st.success("Cleared all codes")
            st.rerun()

def clear_expired_codes():
    """Remove expired codes"""
    current_time = datetime.now()
    
    codes_to_remove = []
    
    for code, info in st.session_state.upgrade_codes.items():
        expires_at = datetime.fromisoformat(info['expires_at'])
        if current_time > expires_at or info.get('used', False):
            codes_to_remove.append(code)
    
    for code in codes_to_remove:
        del st.session_state.upgrade_codes[code]
    
    return len(codes_to_remove)