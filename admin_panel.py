"""
Admin Panel for Smart Data Organizer
Only accessible to admin users
"""

import streamlit as st
import pandas as pd
from datetime import datetime
import json

def show_admin_panel():
    """Main admin panel interface"""
    
    st.markdown("# Admin Panel")
    st.markdown("---")
    
    # Admin stats
    from utils.auth import get_all_users
    users = get_all_users()
    df_users = pd.DataFrame(users)
    
    # Summary stats
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Users", len(users))
    
    with col2:
        paid_users = len([u for u in users if u['tier'] != 'free'])
        st.metric("Paid Users", paid_users)
    
    with col3:
        total_conversions = sum(u['conversions_used'] for u in users)
        st.metric("Total Conversions", total_conversions)
    
    with col4:
        today = datetime.now().strftime('%Y-%m-%d')
        new_today = len([u for u in users if u.get('created_at', '').startswith(today)])
        st.metric("New Today", new_today)
    
    st.markdown("---")
    
    # Main admin tabs
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "User Management",
        "Admin Management", 
        "Analytics", 
        "Quick Actions",
        "System Settings",
        "Development Tools"
    ])
    
    with tab1:
        show_user_management(df_users)

    with tab2:
        show_admin_management()  # NEW FUNCTION
    
    with tab3:
        show_analytics_dashboard(users)
    
    with tab4:
        show_quick_actions()
    
    with tab5:
        show_system_settings()
    
    with tab6:
        show_development_tools()

def show_user_management(df_users):
    """Manage users - view, edit, delete"""
    
    st.subheader("User Management")
    
    # Search and filter
    col1, col2, col3 = st.columns(3)
    
    with col1:
        search_email = st.text_input("Search by email", placeholder="user@example.com")
    
    with col2:
        filter_tier = st.selectbox("Filter by tier", ["All", "free", "pro", "analyst", "business"])
    
    with col3:
        sort_by = st.selectbox("Sort by", ["Email", "Tier", "Conversions", "Created"])
    
    # Apply filters
    filtered_df = df_users.copy()
    
    if search_email:
        filtered_df = filtered_df[filtered_df['email'].str.contains(search_email, case=False, na=False)]
    
    if filter_tier != "All":
        filtered_df = filtered_df[filtered_df['tier'] == filter_tier]
    
    # Sort
    if sort_by == "Email":
        filtered_df = filtered_df.sort_values('email')
    elif sort_by == "Tier":
        filtered_df = filtered_df.sort_values('tier')
    elif sort_by == "Conversions":
        filtered_df = filtered_df.sort_values('conversions_used', ascending=False)
    elif sort_by == "Created":
        filtered_df = filtered_df.sort_values('created_at', ascending=False)
    
    # Display user table
    st.dataframe(
        filtered_df,
        use_container_width=True,
        column_config={
            "email": "Email",
            "name": "Name",
            "tier": "Tier",
            "conversions_used": "Conversions Used",
            "created_at": "Created At",
            "last_login": "Last Login"
        },
        height=400
    )
    
    # User actions
    st.subheader("User Actions")
    
    selected_email = st.selectbox(
        "Select user to manage:",
        filtered_df['email'].tolist(),
        key="user_select"
    )
    
    if selected_email:
        from utils.auth import get_all_users
        all_users = get_all_users()
        user_data = next((u for u in all_users if u['email'] == selected_email), None)
        
        if user_data:
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.write("Current Tier:")
                st.info(user_data['tier'].upper())
            
            with col2:
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
            
            with col3:
                st.write("Conversions:")
                st.metric("Used", user_data['conversions_used'])
                
                if st.button("Reset Count", key=f"reset_{selected_email}"):
                    from utils.auth import reset_user_conversions
                    if reset_user_conversions(selected_email):
                        st.success(f"Reset conversions for {selected_email}")
                        st.rerun()
            
            with col4:
                if st.button("Delete User", type="secondary", key=f"delete_{selected_email}"):
                    from utils.auth import delete_user
                    if delete_user(selected_email):
                        st.success(f"Deleted user {selected_email}")
                        st.rerun()

def show_analytics_dashboard(users):
    """Analytics and reporting"""
    
    st.subheader("Analytics Dashboard")
    
    # Convert to DataFrame for analysis
    df = pd.DataFrame(users)
    
    # Tier distribution
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Tier Distribution")
        tier_counts = df['tier'].value_counts()
        st.bar_chart(tier_counts)
    
    with col2:
        st.markdown("### Conversion Usage")
        # Top users by conversions
        top_users = df.nlargest(10, 'conversions_used')[['email', 'conversions_used']]
        st.dataframe(top_users, use_container_width=True, height=300)
    
    # Monthly growth
    st.markdown("### User Growth")
    
    try:
        df['created_month'] = pd.to_datetime(df['created_at']).dt.to_period('M')
        monthly_growth = df.groupby('created_month').size().cumsum()
        st.line_chart(monthly_growth)
    except:
        st.info("Not enough data for growth chart")
    
    # Export data
    st.markdown("---")
    st.subheader("Export Analytics")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Export User Data", use_container_width=True):
            csv = df.to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name="admin_users.csv",
                mime="text/csv"
            )
    
    with col2:
        if st.button("Generate Report", use_container_width=True):
            report = generate_admin_report(users)
            st.download_button(
                label="Download Report",
                data=report,
                file_name="admin_report.txt",
                mime="text/plain"
            )

def generate_admin_report(users):
    """Generate comprehensive admin report"""
    report_lines = []
    
    report_lines.append("=== SMART DATA ORGANIZER ADMIN REPORT ===")
    report_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append(f"Total Users: {len(users)}")
    report_lines.append("")
    
    # Tier breakdown
    report_lines.append("TIER DISTRIBUTION:")
    tiers = {}
    for user in users:
        tier = user['tier']
        tiers[tier] = tiers.get(tier, 0) + 1
    
    for tier, count in tiers.items():
        report_lines.append(f"  {tier.upper()}: {count} users ({count/len(users)*100:.1f}%)")
    
    report_lines.append("")
    
    # Top users
    report_lines.append("TOP 10 USERS BY CONVERSIONS:")
    sorted_users = sorted(users, key=lambda x: x['conversions_used'], reverse=True)
    for i, user in enumerate(sorted_users[:10], 1):
        report_lines.append(f"  {i}. {user['email']}: {user['conversions_used']} conversions")
    
    report_lines.append("")
    
    # Recent activity
    report_lines.append("RECENT USERS (Last 7 days):")
    recent_users = 0
    for user in users:
        try:
            if user.get('last_login'):
                last_login = datetime.fromisoformat(user['last_login'])
                if (datetime.now() - last_login).days <= 7:
                    recent_users += 1
        except:
            pass
    
    report_lines.append(f"  Active users: {recent_users}")
    
    return "\n".join(report_lines)

def show_quick_actions():
    """Quick admin actions"""
    
    st.subheader("Quick Actions")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Development Actions")
        
        if st.button("Add Test Users", use_container_width=True, type="primary"):
            from utils.auth import load_users, save_user
            import random
            
            users = load_users()
            test_domains = ["test.com", "demo.org", "example.net"]
            
            for i in range(5):
                email = f"testuser{i+1}@{random.choice(test_domains)}"
                if email not in users:
                    save_user(email, "password123", f"Test User {i+1}")
            
            st.success("Added 5 test users!")
            st.rerun()
        
        if st.button("Reset All Stats", use_container_width=True):
            from utils.auth import load_users, update_user
            
            users = load_users()
            for email in users:
                if email not in ['admin@smartdata.com', st.session_state.user_email]:
                    update_user(email, {'conversions_used': 0})
            
            st.success("Reset all user conversion counts!")
            st.rerun()
        
        if st.button("Clear All Sessions", use_container_width=True):
            st.warning("This will log out all users except you!")
            if st.checkbox("Confirm clear all sessions"):
                # Save current user data
                current_email = st.session_state.user_email
                current_data = st.session_state.user_data
                
                # Clear session state
                keys_to_keep = ['users_db', 'user_email', 'user_data', 'logged_in', 'is_admin']
                for key in list(st.session_state.keys()):
                    if key not in keys_to_keep:
                        del st.session_state[key]
                
                # Restore admin
                st.session_state.logged_in = True
                st.session_state.user_email = current_email
                st.session_state.user_data = current_data
                st.session_state.is_admin = True
                
                st.success("All other sessions cleared!")
                st.rerun()
    
    with col2:
        st.markdown("### System Actions")
        
        if st.button("System Health Check", use_container_width=True):
            from utils.auth import get_all_users
            
            users = get_all_users()
            conversions = sum(u['conversions_used'] for u in users)
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.success("Database: OK")
            with col2:
                st.success("Auth System: OK")
            with col3:
                st.success("Session: OK")
            
            st.info(f"Total Users: {len(users)}")
            st.info(f"Total Conversions: {conversions}")
            st.info(f"Admin Session: Active")
        
        if st.button("View Raw Data", use_container_width=True):
            from utils.auth import load_users
            
            users = load_users()
            st.json(users, expanded=False)
        
        if st.button("Reset Admin Password", use_container_width=True):
            st.info("Admin password reset (development only)")

def show_system_settings():
    """System configuration"""
    
    st.subheader("System Settings")
    
    # App configuration
    with st.form("system_settings"):
        st.markdown("### Application Settings")
        
        # Free tier limits
        free_conversions = st.number_input(
            "Free tier conversions limit:",
            min_value=1,
            max_value=1000,
            value=50,
            help="Number of conversions allowed for free tier"
        )
        
        # Web scraping limits
        free_scrapes = st.number_input(
            "Free tier web scrapes limit:",
            min_value=1,
            max_value=100,
            value=3,
            help="Number of URL scrapes allowed for free tier"
        )
        
        # Session timeout
        session_timeout = st.number_input(
            "Session timeout (minutes):",
            min_value=5,
            max_value=1440,
            value=120,
            help="User session timeout in minutes"
        )
        
        # Feature toggles
        st.markdown("### Feature Toggles")
        col1, col2 = st.columns(2)
        
        with col1:
            enable_web_scraping = st.toggle("Enable web scraping", value=True)
            enable_file_upload = st.toggle("Enable file upload", value=True)
            enable_excel_export = st.toggle("Enable Excel export for free tier", value=False)
        
        with col2:
            enable_registration = st.toggle("Enable new registrations", value=True)
            enable_demo_mode = st.toggle("Enable demo mode", value=True)
            enable_admin_panel = st.toggle("Enable admin panel", value=True)
        
        # Save settings
        if st.form_submit_button("Save Settings", type="primary"):
            # In production, save to database or config file
            settings = {
                'free_conversions': free_conversions,
                'free_scrapes': free_scrapes,
                'session_timeout': session_timeout,
                'features': {
                    'web_scraping': enable_web_scraping,
                    'file_upload': enable_file_upload,
                    'excel_export_free': enable_excel_export,
                    'registration': enable_registration,
                    'demo_mode': enable_demo_mode,
                    'admin_panel': enable_admin_panel
                }
            }
            
            # Save to session state (in production, save to database)
            st.session_state.system_settings = settings
            st.success("Settings saved! (Note: Changes are session-only in development)")
    
    # Pricing configuration
    st.markdown("---")
    st.markdown("### Pricing Configuration")
    
    with st.form("pricing_settings"):
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            pro_price = st.number_input("Pro price ($)", min_value=0.0, value=19.99, step=0.01)
        
        with col2:
            analyst_price = st.number_input("Analyst price ($)", min_value=0.0, value=39.99, step=0.01)
        
        with col3:
            business_price = st.number_input("Business price ($)", min_value=0.0, value=99.99, step=0.01)
        
        with col4:
            billing_cycle = st.selectbox("Billing cycle", ["Monthly", "Annual"])
        
        if st.form_submit_button("Update Pricing"):
            st.success("Pricing updated! (Note: Changes are session-only in development)")

def show_development_tools():
    """Development and testing tools"""
    
    st.subheader("Development Tools")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Testing Tools")
        
        # Test data generation
        if st.button("Generate Test Dataset", use_container_width=True):
            import pandas as pd
            import numpy as np
            
            # Create sample time series data
            dates = pd.date_range(start='2024-01-01', periods=100, freq='D')
            data = {
                'Date': dates,
                'Sales': np.random.randint(1000, 5000, 100),
                'Revenue': np.random.randint(50000, 200000, 100),
                'Region': np.random.choice(['North', 'South', 'East', 'West'], 100)
            }
            
            df = pd.DataFrame(data)
            st.session_state.df = df
            st.success("Test dataset generated! Switch to Home tab to see it.")
        
        # Clear all data
        if st.button("Clear All App Data", use_container_width=True, type="secondary"):
            st.session_state.df = None
            st.session_state.data_structure = None
            st.session_state.df_organized = None
            st.success("All app data cleared!")
    
    with col2:
        st.markdown("### Debug Tools")
        
        # View session state
        if st.button("View Session State", use_container_width=True):
            st.write("### Current Session State")
            for key in st.session_state.keys():
                if key not in ['users_db', 'password']:  # Skip sensitive data
                    st.write(f"**{key}:**", st.session_state[key])
        
        # Reset app state
        if st.button("Reset App State", use_container_width=True):
            # Keep only essential state
            keep_keys = ['users_db', 'logged_in', 'user_email', 'user_data', 'is_admin']
            for key in list(st.session_state.keys()):
                if key not in keep_keys:
                    del st.session_state[key]
            
            st.success("App state reset!")
            st.rerun()
    
    # Database operations
    st.markdown("---")
    st.markdown("### Database Operations")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Export Database", use_container_width=True):
            from utils.auth import load_users
            import json
            
            users = load_users()
            # Remove passwords for security
            for email in users:
                if 'password' in users[email]:
                    users[email]['password'] = '***HIDDEN***'
            
            db_json = json.dumps(users, indent=2, default=str)
            st.download_button(
                label="Download Database JSON",
                data=db_json,
                file_name="users_database.json",
                mime="application/json"
            )
    
    with col2:
        if st.button("Import Database", use_container_width=True):
            st.warning("Database import feature coming soon!")
    
    # System info
    st.markdown("---")
    with st.expander("System Information"):
        import sys
        import platform
        
        st.write("Python Version:", sys.version.split()[0])
        st.write("Platform:", platform.platform())
        st.write("Streamlit Version:", st.__version__)
        
        try:
            import pandas as pd
            st.write("Pandas Version:", pd.__version__)
        except:
            pass