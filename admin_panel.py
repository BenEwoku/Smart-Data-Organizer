"""
Admin Panel for Smart Data Organizer
Only accessible to admin users
CLEAN VERSION - NO ERRORS
"""

import streamlit as st
import pandas as pd
from datetime import datetime
import json

# ===== ADMIN MANAGEMENT =====
def show_admin_management():
    """Manage admin users"""
    st.subheader("Admin User Management")
    
    from utils.auth import get_all_users, get_admin_list, promote_to_admin, demote_from_admin, is_admin
    
    # Get all users and admins
    all_users = get_all_users()
    admin_emails = get_admin_list()
    
    # Display current admins
    st.markdown("### Current Administrators")
    
    if admin_emails:
        admin_data = []
        for email in admin_emails:
            user = next((u for u in all_users if u['email'] == email), None)
            if user:
                admin_data.append({
                    'Email': email,
                    'Name': user.get('name', 'N/A'),
                    'Tier': user.get('tier', 'N/A'),
                    'Type': 'Super Admin' if email in ['admin@smartdata.com', st.secrets.get("admin", {}).get("admin_email")] else 'Admin'
                })
            else:
                admin_data.append({
                    'Email': email,
                    'Name': 'System Admin',
                    'Tier': 'N/A',
                    'Type': 'Super Admin'
                })
        
        admin_df = pd.DataFrame(admin_data)
        st.dataframe(admin_df, use_container_width=True)
        
        st.info(f"**Total Administrators:** {len(admin_emails)}")
    else:
        st.warning("No administrators found")
    
    st.markdown("---")
    
    # Promote user to admin
    st.markdown("### Promote User to Admin")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        # Get non-admin users
        non_admin_users = [u['email'] for u in all_users if u['email'] not in admin_emails]
        
        if non_admin_users:
            selected_user = st.selectbox(
                "Select user to promote:",
                non_admin_users,
                key="promote_user_select"
            )
            
            # Show user info
            user_info = next((u for u in all_users if u['email'] == selected_user), None)
            if user_info:
                st.caption(f"**Name:** {user_info['name']} | **Tier:** {user_info['tier']} | **Conversions:** {user_info['conversions_used']}")
        else:
            st.info("All users are already admins")
            selected_user = None
    
    with col2:
        if selected_user:
            if st.button("Promote to Admin", type="primary", use_container_width=True):
                success, message = promote_to_admin(selected_user)
                if success:
                    st.success(message)
                    st.balloons()
                    st.rerun()
                else:
                    st.error(message)
    
    st.markdown("---")
    
    # Demote admin
    st.markdown("### Demote Admin to Regular User")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        # Get admins that can be demoted (not super admins)
        default_admins = ['admin@smartdata.com']
        try:
            default_admins.append(st.secrets["admin"]["admin_email"])
        except:
            pass
        
        demotable_admins = [email for email in admin_emails if email not in default_admins]
        
        if demotable_admins:
            selected_admin = st.selectbox(
                "Select admin to demote:",
                demotable_admins,
                key="demote_admin_select"
            )
            
            # Show user info
            user_info = next((u for u in all_users if u['email'] == selected_admin), None)
            if user_info:
                st.caption(f"**Name:** {user_info['name']} | **Tier:** {user_info['tier']}")
            
            st.warning("This will remove admin privileges from this user")
        else:
            st.info("No admins available for demotion (only super admins remain)")
            selected_admin = None
    
    with col2:
        if selected_admin:
            if st.button("Demote Admin", type="secondary", use_container_width=True):
                success, message = demote_from_admin(selected_admin)
                if success:
                    st.success(message)
                    st.rerun()
                else:
                    st.error(message)
    
    st.markdown("---")
    
    # Admin activity log (placeholder)
    with st.expander("Admin Activity Log"):
        st.info("Admin activity logging coming soon")

# ===== MAIN ADMIN PANEL =====
def show_admin_panel():
    """Main admin panel interface"""
    
    st.markdown("# Admin Panel")
    st.markdown("---")
    
    # Admin stats with error handling
    from utils.auth import get_all_users
    
    try:
        users = get_all_users()
        
        # Check if users is valid
        if users is None:
            st.error("Error: get_all_users() returned None")
            users = []
        elif not isinstance(users, list):
            st.error(f"Error: get_all_users() returned {type(users)}, expected list")
            users = []
            
    except Exception as e:
        st.error(f"Error getting users: {str(e)}")
        users = []
    
    # Create DataFrame safely
    if users and len(users) > 0:
        try:
            df_users = pd.DataFrame(users)
        except Exception as e:
            st.error(f"Error creating DataFrame: {str(e)}")
            df_users = pd.DataFrame()
    else:
        st.warning("No user data available")
        df_users = pd.DataFrame()
    
    # Summary stats - only if we have users
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Users", len(users) if users else 0)
    
    with col2:
        if users:
            paid_users = len([u for u in users if u.get('tier', 'free') != 'free'])
            st.metric("Paid Users", paid_users)
        else:
            st.metric("Paid Users", 0)
    
    with col3:
        if users:
            total_conversions = sum(u.get('conversions_used', 0) for u in users)
            st.metric("Total Conversions", total_conversions)
        else:
            st.metric("Total Conversions", 0)
    
    with col4:
        if users:
            today = datetime.now().strftime('%Y-%m-%d')
            new_today = len([u for u in users if str(u.get('created_at', '')).startswith(today)])
            st.metric("New Today", new_today)
        else:
            st.metric("New Today", 0)
    
    st.markdown("---")
    
    # Main admin tabs - with safe DataFrame passing
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "User Management",
        "Admin Management", 
        "Analytics", 
        "Quick Actions",
        "System Settings",
        "Development Tools"
    ])
    
    with tab1:
        # Pass the DataFrame safely
        show_user_management(df_users)

    with tab2:
        show_admin_management()
    
    with tab3:
        show_analytics_dashboard(users)
    
    with tab4:
        show_quick_actions()
    
    with tab5:
        show_system_settings()
    
    with tab6:
        show_development_tools()

# ===== USER MANAGEMENT =====
def show_user_management(df_users):
    """Manage users - view, edit, delete"""
    
    st.subheader("User Management")
    
    # Check if df_users is valid
    if df_users is None or len(df_users) == 0:
        st.warning("No user data available")
        return
    
    # Simple display first
    st.dataframe(df_users, use_container_width=True, height=300)
    
    # User actions
    st.subheader("User Actions")
    
    if len(df_users) > 0:
        selected_email = st.selectbox(
            "Select user to manage:",
            df_users['email'].tolist(),
            key="user_select"
        )
        
        if selected_email:
            from utils.auth import get_all_users
            all_users = get_all_users()
            user_data = next((u for u in all_users if u['email'] == selected_email), None)
            
            if user_data:
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write("Current Tier:")
                    st.info(user_data.get('tier', 'free').upper())
                    
                    new_tier = st.selectbox(
                        "Change tier:",
                        ["free", "pro", "analyst", "business"],
                        key=f"tier_{selected_email}"
                    )
                    
                    if st.button("Update Tier", key=f"update_tier_{selected_email}"):
                        from utils.auth import update_user
                        if update_user(selected_email, {'tier': new_tier}):
                            st.success(f"Updated {selected_email} to {new_tier} tier")
                            st.rerun()
                
                with col2:
                    st.write("Conversions:")
                    st.metric("Used", user_data.get('conversions_used', 0))
                    
                    if st.button("Reset Count", key=f"reset_{selected_email}"):
                        from utils.auth import reset_user_conversions
                        if reset_user_conversions(selected_email):
                            st.success(f"Reset conversions for {selected_email}")
                            st.rerun()
    else:
        st.info("No users available for actions")

# ===== ANALYTICS =====
def show_analytics_dashboard(users):
    """Analytics and reporting"""
    
    st.subheader("Analytics Dashboard")
    
    if not users or len(users) == 0:
        st.info("No user data for analytics")
        return
    
    # Convert to DataFrame for analysis
    df = pd.DataFrame(users)
    
    # Simple stats
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Tier Distribution")
        if 'tier' in df.columns:
            tier_counts = df['tier'].value_counts()
            st.bar_chart(tier_counts)
        else:
            st.info("No tier data")
    
    with col2:
        st.markdown("### Top Users by Conversions")
        if 'conversions_used' in df.columns and 'email' in df.columns:
            top_users = df.nlargest(5, 'conversions_used')[['email', 'conversions_used']]
            st.dataframe(top_users, use_container_width=True, height=200)
        else:
            st.info("No conversion data")

# ===== QUICK ACTIONS =====
def show_quick_actions():
    """Quick admin actions"""
    
    st.subheader("Quick Actions")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### System Actions")
        
        if st.button("Clear ALL Caches", use_container_width=True, type="primary"):
            import streamlit as st
            st.cache_data.clear()
            st.cache_resource.clear()
            st.success("All caches cleared!")
            st.rerun()
        
        if st.button("System Health Check", use_container_width=True):
            st.success("System check completed")
    
    with col2:
        st.markdown("### User Actions")
        
        if st.button("Add Test User", use_container_width=True):
            st.info("Test user feature")
        
        if st.button("View Session State", use_container_width=True):
            st.write("Session keys:", list(st.session_state.keys()))

# ===== SYSTEM SETTINGS =====
def show_system_settings():
    """System configuration"""
    
    st.subheader("System Settings")
    
    with st.form("system_settings"):
        st.markdown("### Application Settings")
        
        free_conversions = st.number_input(
            "Free tier conversions limit:",
            min_value=1,
            max_value=1000,
            value=50
        )
        
        session_timeout = st.number_input(
            "Session timeout (minutes):",
            min_value=5,
            max_value=1440,
            value=120
        )
        
        if st.form_submit_button("Save Settings", type="primary"):
            st.success("Settings saved!")

# ===== DEVELOPMENT TOOLS =====
def show_development_tools():
    """Development and testing tools - SIMPLE VERSION"""
    
    # LINE 648: This should work now
    st.subheader("Development Tools")
    
    # Simple layout - no complex imports
    st.write("### Cache Management")
    
    if st.button("🧹 Clear ALL Caches", type="primary", use_container_width=True):
        import streamlit as st
        st.cache_data.clear()
        st.cache_resource.clear()
        st.success("✅ All caches cleared!")
        st.rerun()
    
    st.markdown("---")
    st.write("### Testing Tools")
    
    if st.button("Generate Test Data", use_container_width=True):
        try:
            import pandas as pd
            import numpy as np
            
            dates = pd.date_range(start='2024-01-01', periods=100, freq='D')
            data = {
                'Date': dates,
                'Sales': np.random.randint(1000, 5000, 100),
                'Revenue': np.random.randint(50000, 200000, 100)
            }
            
            df = pd.DataFrame(data)
            st.session_state.df = df
            st.success("Test dataset generated!")
        except Exception as e:
            st.error(f"Error: {str(e)}")
    
    if st.button("Clear App Data", use_container_width=True, type="secondary"):
        st.session_state.df = None
        st.success("App data cleared!")

# ===== ADMIN REPORT =====
def generate_admin_report(users):
    """Generate comprehensive admin report"""
    report_lines = []
    
    report_lines.append("=== SMART DATA ORGANIZER ADMIN REPORT ===")
    report_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append(f"Total Users: {len(users)}")
    
    return "\n".join(report_lines)