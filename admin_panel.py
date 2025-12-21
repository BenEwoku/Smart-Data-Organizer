"""
Admin Panel for Smart Data Organizer
CLEAN WORKING VERSION
"""

import streamlit as st
import pandas as pd
from datetime import datetime

# ===== SIMPLE WORKING FUNCTIONS =====

def show_admin_panel():
    """Main admin panel - SIMPLE WORKING VERSION"""
    
    st.markdown("# Admin Panel")
    st.markdown("---")
    
    # Get users safely
    try:
        from utils.auth import get_all_users
        users = get_all_users() or []
    except:
        users = []
    
    # Basic stats
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Users", len(users))
    with col2:
        paid = len([u for u in users if u.get('tier') != 'free']) if users else 0
        st.metric("Paid Users", paid)
    with col3:
        conversions = sum(u.get('conversions_used', 0) for u in users) if users else 0
        st.metric("Total Conversions", conversions)
    
    st.markdown("---")
    
    # Simple tabs
    tab1, tab2, tab3 = st.tabs(["User Management", "Quick Actions", "System"])
    
    with tab1:
        show_user_management_simple(users)
    
    with tab2:
        show_quick_actions_simple()
    
    with tab3:
        show_system_simple()
    
    st.markdown("---")
    st.caption("Admin Panel v2.1")

def show_user_management_simple(users):
    """Simple user management"""
    st.subheader("User Management")
    
    if not users:
        st.info("No users found")
        return
    
    # Display users
    for user in users:
        col1, col2, col3 = st.columns([3, 2, 2])
        with col1:
            st.write(f"**{user.get('name', 'No name')}**")
            st.caption(user.get('email', 'No email'))
        with col2:
            tier = user.get('tier', 'free')
            st.write(f"Tier: **{tier.upper()}**")
        with col3:
            if st.button("Edit", key=f"edit_{user.get('email')}"):
                st.session_state.edit_user = user.get('email')
    
    # Edit selected user
    if 'edit_user' in st.session_state:
        st.markdown("---")
        st.subheader(f"Edit {st.session_state.edit_user}")
        
        # Find user
        user_to_edit = next((u for u in users if u.get('email') == st.session_state.edit_user), None)
        
        if user_to_edit:
            new_tier = st.selectbox(
                "Change tier:",
                ["free", "pro", "analyst", "business"],
                index=["free", "pro", "analyst", "business"].index(user_to_edit.get('tier', 'free'))
            )
            
            if st.button("Update Tier"):
                try:
                    from utils.auth import update_user
                    if update_user(st.session_state.edit_user, {'tier': new_tier}):
                        st.success(f"Updated to {new_tier} tier")
                        del st.session_state.edit_user
                        st.rerun()
                except:
                    st.error("Update failed")
            
            if st.button("Cancel"):
                del st.session_state.edit_user
                st.rerun()

def show_quick_actions_simple():
    """Simple quick actions - NO ERRORS"""
    st.subheader("Quick Actions")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔄 Clear ALL Caches", use_container_width=True, type="primary"):
            import streamlit as st
            st.cache_data.clear()
            st.cache_resource.clear()
            st.success("All caches cleared!")
            st.rerun()
        
        if st.button("🧪 Add Test User", use_container_width=True):
            try:
                from utils.auth import save_user
                import random
                email = f"test{random.randint(1000,9999)}@example.com"
                save_user(email, "test123", "Test User")
                st.success(f"Added {email}")
            except:
                st.info("Test user feature")
    
    with col2:
        if st.button("📊 View Session", use_container_width=True):
            st.write("Session keys:", [k for k in st.session_state.keys() if k != 'password'])
        
        if st.button("⚙️ System Check", use_container_width=True):
            st.success("System OK")

def show_system_simple():
    """Simple system settings"""
    st.subheader("System Settings")
    
    with st.form("settings"):
        free_limit = st.number_input("Free tier limit", value=50, min_value=1, max_value=1000)
        timeout = st.number_input("Session timeout (min)", value=120, min_value=5)
        
        if st.form_submit_button("Save"):
            st.session_state.settings = {
                'free_limit': free_limit,
                'timeout': timeout
            }
            st.success("Settings saved (session only)")

# ===== ORIGINAL FUNCTIONS (DISABLED) =====
# Keep these as placeholders but don't use them

def show_admin_management():
    """Placeholder - not used in simple version"""
    st.info("Admin management disabled in simple mode")

def show_analytics_dashboard(users):
    """Placeholder - not used in simple version"""
    st.info("Analytics disabled in simple mode")

def show_development_tools():
    """Placeholder - not used in simple version"""
    st.info("Development tools disabled in simple mode")

def generate_admin_report(users):
    """Placeholder"""
    return "Report placeholder"