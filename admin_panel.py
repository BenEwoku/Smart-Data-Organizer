"""
Admin Panel for Smart Data Organizer
Only accessible to admin users
"""

import streamlit as st
import pandas as pd
from datetime import datetime
import json
import traceback

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
            st.write("Raw users data for debugging:", users)
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

def show_user_management(df_users):
    """Manage users - view, edit, delete"""
    
    st.subheader("User Management")
    
    # Check if df_users is valid
    if df_users is None or len(df_users) == 0:
        st.warning("No user data available")
        return  # Exit early if no data
    
    # Search and filter
    col1, col2, col3 = st.columns(3)
    
    with col1:
        search_email = st.text_input("Search by email", placeholder="user@example.com")
    
    with col2:
        # Check if 'tier' column exists
        if 'tier' in df_users.columns:
            filter_tier = st.selectbox("Filter by tier", ["All", "free", "pro"])
        else:
            filter_tier = "All"
            st.info("No tier data available")
    
    with col3:
        # Check available columns
        available_columns = df_users.columns.tolist()
        sort_options = ["Email" if 'email' in available_columns else "Index"]
        
        if 'tier' in available_columns:
            sort_options.append("Tier")
        if 'conversions_used' in available_columns:
            sort_options.append("Conversions")
        if 'created_at' in available_columns:
            sort_options.append("Created")
        
        sort_by = st.selectbox("Sort by", sort_options)
    
    # Apply filters - with safety checks
    filtered_df = df_users.copy()
    
    if search_email and 'email' in filtered_df.columns:
        filtered_df = filtered_df[filtered_df['email'].str.contains(search_email, case=False, na=False)]
    
    if filter_tier != "All" and 'tier' in filtered_df.columns:
        filtered_df = filtered_df[filtered_df['tier'] == filter_tier]
    
    # Sort with safety checks
    if sort_by == "Email" and 'email' in filtered_df.columns:
        filtered_df = filtered_df.sort_values('email')
    elif sort_by == "Tier" and 'tier' in filtered_df.columns:
        filtered_df = filtered_df.sort_values('tier')
    elif sort_by == "Conversions" and 'conversions_used' in filtered_df.columns:
        filtered_df = filtered_df.sort_values('conversions_used', ascending=False)
    elif sort_by == "Created" and 'created_at' in filtered_df.columns:
        filtered_df = filtered_df.sort_values('created_at', ascending=False)
    
    # Display user table - only if we have data
    if len(filtered_df) > 0:
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
    else:
        st.info("No users match your filters")
    
    # User actions - only if we have users
    if len(filtered_df) > 0:
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
                    st.info(user_data.get('tier', 'free').upper())
                
                with col2:
                    new_tier = st.selectbox(
                        "Change tier:",
                        ["free", "pro"],
                        key=f"tier_{selected_email}"
                    )
                    
                    if st.button("Update Tier", key=f"update_tier_{selected_email}"):
                        from utils.auth import update_user
                        if update_user(selected_email, {'tier': new_tier}):
                            st.success(f"Updated {selected_email} to {new_tier} tier")
                            st.rerun()
                
                with col3:
                    st.write("Conversions:")
                    st.metric("Used", user_data.get('conversions_used', 0))
                    
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
    else:
        st.info("No users available for actions")

def show_analytics_dashboard(users):
    """Analytics and reporting"""
    
    st.subheader("Analytics Dashboard")
    
    # Convert to DataFrame for analysis
    df = pd.DataFrame(users)
    
    # Filter to only free/pro tiers (in case old data exists)
    df['tier'] = df['tier'].apply(lambda x: 'free' if str(x).lower() not in ['free', 'pro'] else str(x).lower())
    
    # Tier distribution
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Tier Distribution")
        tier_counts = df['tier'].value_counts()
        
        # Only show free and pro
        tier_counts = tier_counts[tier_counts.index.isin(['free', 'pro'])]
        st.bar_chart(tier_counts)
        
        # Show percentages
        total_users = len(df)
        if total_users > 0:
            free_count = len(df[df['tier'] == 'free'])
            pro_count = len(df[df['tier'] == 'pro'])
            
            st.caption(f"Free: {free_count} ({free_count/total_users*100:.1f}%)")
            st.caption(f"Pro: {pro_count} ({pro_count/total_users*100:.1f}%)")
    
    with col2:
        st.markdown("### Conversion Usage")
        # Top users by conversions
        top_users = df.nlargest(10, 'conversions_used')[['email', 'tier', 'conversions_used']]
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
    
    # ============ FIXED: Initialize before using ============
    st.markdown("---")
    st.markdown("### Upgrade Code Management")
    
    try:
        # CRITICAL: Initialize upgrade codes FIRST
        if 'upgrade_codes' not in st.session_state:
            st.session_state.upgrade_codes = {}
        
        # Now it's safe to import and use
        from utils.payment import show_code_management
        show_code_management()
        
    except Exception as e:
        st.error(f"Upgrade code system error: {str(e)}")
        
        # Show what the error is
        import traceback
        with st.expander("Error Details"):
            st.code(traceback.format_exc())
        
        st.info("Initializing upgrade codes system...")
        
        # Try to initialize manually
        if 'upgrade_codes' not in st.session_state:
            st.session_state.upgrade_codes = {}
            st.success("Upgrade codes initialized. Please try again.")

    st.markdown("---")
    st.markdown("### PayPal Management")

    try:
        from utils.paypal_integration import show_paypal_admin_panel
        show_paypal_admin_panel()
    except Exception as e:
        st.warning(f"PayPal admin not available: {str(e)}")
    
    # Add manual code generation
    st.markdown("#### Generate Manual Code")
    
    col_gen1, col_gen2 = st.columns([2, 1])
    
    with col_gen1:
        # Get all users for selection
        from utils.auth import get_all_users
        users = get_all_users()
        
        if users:
            user_options = [f"{u['email']} ({u.get('name', 'No name')})" for u in users]
            selected_user = st.selectbox("Select user for code:", user_options)
            
            if selected_user:
                user_email = selected_user.split(" (")[0]
                
                with col_gen2:
                    if st.button("Generate Code", use_container_width=True, type="primary"):
                        try:
                            # Initialize if needed
                            if 'upgrade_codes' not in st.session_state:
                                st.session_state.upgrade_codes = {}
                            
                            from utils.payment import generate_upgrade_code
                            code = generate_upgrade_code(user_email)
                            st.success(f"Generated code: **{code}**")
                            st.info(f"For user: {user_email}")
                            st.caption("This code expires in 24 hours")
                        except Exception as gen_error:
                            st.error(f"Error generating code: {str(gen_error)}")
        else:
            st.info("No users found")

def show_system_settings():
    """System configuration - MINIMAL WORKING VERSION"""
    
    st.subheader("System Settings")
    
    # App configuration form
    st.markdown("### Application Settings")
    
    with st.form("system_settings"):
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
        
        # Save button
        if st.form_submit_button("Save Settings", type="primary"):
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
            st.session_state.system_settings = settings
            st.success("Settings saved!")
    
    # Pricing configuration - SEPARATE FORM
    st.markdown("---")
    st.markdown("### Tier Configuration")
    
    with st.form("pricing_settings"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Free Tier")
            free_conversions_limit = st.number_input(
                "Conversions limit:",
                min_value=1,
                max_value=1000,
                value=50,
                key="free_conv_limit"
            )
            
            free_scrapes_limit = st.number_input(
                "Web scrapes limit:",
                min_value=0,
                max_value=50,
                value=3,
                key="free_scrape_limit"
            )
            
            free_features = st.multiselect(
                "Free tier features:",
                ["CSV Export", "Basic Cleaning", "Email Support", "Data Detection", "Missing Value Imputation"],
                default=["CSV Export", "Basic Cleaning", "Data Detection", "Missing Value Imputation"],
                key="free_feat"
            )
        
        with col2:
            st.markdown("#### Pro Tier")
            pro_price = st.number_input(
                "Monthly price ($):",
                min_value=0.0,
                max_value=100.0,
                value=5.00,
                step=0.01,
                key="pro_price_input"
            )
            
            pro_conversions = st.selectbox(
                "Conversions limit:",
                ["Unlimited", "Custom"],
                key="pro_conv_type"
            )
            
            if pro_conversions == "Custom":
                custom_limit = st.number_input(
                    "Custom limit:",
                    min_value=100,
                    max_value=10000,
                    value=1000,
                    key="custom_limit_input"
                )
            else:
                custom_limit = 1000
            
            pro_features = st.multiselect(
                "Pro tier features:",
                ["Unlimited Conversions", "Excel Export", "Priority Support", "Advanced Organization", 
                 "Web Scraping", "Email Analysis", "AI Assistance", "All Future Features"],
                default=["Unlimited Conversions", "Excel Export", "Priority Support", 
                         "Advanced Organization", "Web Scraping", "Email Analysis", "All Future Features"],
                key="pro_feat"
            )
        
        # Billing options
        st.markdown("---")
        st.markdown("#### Billing Options")
        
        col_b1, col_b2 = st.columns(2)
        
        with col_b1:
            billing_cycle = st.selectbox(
                "Default billing cycle:",
                ["Monthly", "Annual (Save 20%)"],
                key="billing_cycle_select"
            )
        
        with col_b2:
            enable_trial = st.toggle("Enable free trial", value=True, key="trial_toggle")
            if enable_trial:
                trial_days = st.number_input("Trial days:", min_value=1, max_value=30, value=7, key="trial_days_input")
            else:
                trial_days = 0
        
        if st.form_submit_button("Update Tier Configuration", type="primary"):
            tier_config = {
                'free': {
                    'conversions_limit': free_conversions_limit,
                    'scrapes_limit': free_scrapes_limit,
                    'features': free_features,
                    'price': 0.00
                },
                'pro': {
                    'price': pro_price,
                    'conversions': 'unlimited' if pro_conversions == "Unlimited" else custom_limit,
                    'features': pro_features,
                    'billing_cycle': billing_cycle,
                    'trial_enabled': enable_trial,
                    'trial_days': trial_days
                }
            }
            
            st.session_state.tier_configuration = tier_config
            
            if 'system_settings' not in st.session_state:
                st.session_state.system_settings = {}
            
            st.session_state.system_settings['free_conversions'] = free_conversions_limit
            st.session_state.system_settings['free_scrapes'] = free_scrapes_limit
            
            st.success("Tier configuration saved!")
    
    # Show current config if it exists
    if 'tier_configuration' in st.session_state:
        st.markdown("---")
        st.markdown("### Current Configuration")
        
        config = st.session_state.tier_configuration
        
        col_sum1, col_sum2 = st.columns(2)
        
        with col_sum1:
            st.markdown("**Free Tier:**")
            if 'free' in config:
                st.text(f"Conversions: {config['free'].get('conversions_limit', 50)}")
                st.text(f"Web scrapes: {config['free'].get('scrapes_limit', 3)}")
        
        with col_sum2:
            st.markdown("**Pro Tier:**")
            if 'pro' in config:
                st.text(f"Price: ${config['pro'].get('price', 5.00)}/month")
                conversions = config['pro'].get('conversions', 'unlimited')
                st.text(f"Conversions: {conversions}")

def show_development_tools():
    """Development and testing tools - COMPLETELY FIXED VERSION"""
    
    st.subheader("Development Tools")
    
    # Wrap everything in try-except for debugging
    try:
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### Testing Tools")
            
            # Test data generation
            if st.button("Generate Test Dataset", use_container_width=True):
                try:
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
                except Exception as e:
                    st.error(f"Error generating test data: {str(e)}")
                    st.code(traceback.format_exc())
            
            # Clear all data
            if st.button("Clear All App Data", use_container_width=True, type="secondary"):
                try:
                    st.session_state.df = None
                    st.session_state.data_structure = None
                    st.session_state.df_organized = None
                    st.success("All app data cleared!")
                except Exception as e:
                    st.error(f"Error clearing data: {str(e)}")
        
        with col2:
            st.markdown("### Debug Tools")
            
            # View session state
            if st.button("View Session State", use_container_width=True):
                try:
                    st.write("### Current Session State")
                    for key in st.session_state.keys():
                        if key not in ['users_db', 'password']:  # Skip sensitive data
                            st.write(f"**{key}:**", st.session_state[key])
                except Exception as e:
                    st.error(f"Error viewing session: {str(e)}")
            
            # Reset app state
            if st.button("Reset App State", use_container_width=True):
                try:
                    # Keep only essential state
                    keep_keys = ['users_db', 'logged_in', 'user_email', 'user_data', 'is_admin']
                    for key in list(st.session_state.keys()):
                        if key not in keep_keys:
                            del st.session_state[key]
                    
                    st.success("App state reset!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error resetting state: {str(e)}")
                    st.code(traceback.format_exc())
        
        # Cache Management - COMPLETELY REWRITTEN
        st.markdown("---")
        st.markdown("### Cache Management")
        
        cache_col1, cache_col2 = st.columns(2)
        
        with cache_col1:
            if st.button("Clear ALL Caches", use_container_width=True, type="primary"):
                try:
                    st.cache_data.clear()
                    st.cache_resource.clear()
                    if 'user_cache' in st.session_state:
                        st.session_state.user_cache = {}
                    st.success("All caches cleared!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error clearing caches: {str(e)}")
                    st.code(traceback.format_exc())
        
        with cache_col2:
            # User-specific cache clearing - FIXED with proper error handling
            try:
                from utils.auth import get_all_users, clear_user_cache
                
                users = get_all_users()
                
                if users and len(users) > 0:
                    user_emails = [u['email'] for u in users]
                    
                    selected_email = st.selectbox(
                        "Clear cache for user:",
                        user_emails,
                        key="cache_user_select"
                    )
                    
                    if st.button("Clear User Cache", use_container_width=True):
                        try:
                            success = clear_user_cache(selected_email)
                            if success:
                                st.success(f"Cache cleared for {selected_email}")
                                st.rerun()
                            else:
                                st.error("Failed to clear cache")
                        except Exception as clear_error:
                            st.error(f"Error clearing user cache: {str(clear_error)}")
                            st.code(traceback.format_exc())
                else:
                    st.info("No users found")
                    
            except Exception as e:
                st.error(f"Cache management error: {str(e)}")
                st.code(traceback.format_exc())
                st.caption("Try clearing all caches instead")
        
        # Database operations
        st.markdown("---")
        st.markdown("### Database Operations")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("Export Database", use_container_width=True):
                try:
                    from utils.auth import load_users
                    
                    users = load_users()
                    # Remove passwords for security
                    for email_key in users:
                        if 'password' in users[email_key]:
                            users[email_key]['password'] = '***HIDDEN***'
                    
                    db_json = json.dumps(users, indent=2, default=str)
                    st.download_button(
                        label="Download Database JSON",
                        data=db_json,
                        file_name="users_database.json",
                        mime="application/json"
                    )
                except Exception as e:
                    st.error(f"Error exporting database: {str(e)}")
                    st.code(traceback.format_exc())
        
        with col2:
            if st.button("Import Database", use_container_width=True):
                st.warning("Database import feature coming soon!")
        
        # System info
        st.markdown("---")
        with st.expander("System Information"):
            try:
                import sys
                import platform
                
                st.write("**Python Version:**", sys.version.split()[0])
                st.write("**Platform:**", platform.platform())
                st.write("**Streamlit Version:**", st.__version__)
                
                try:
                    import pandas as pd
                    st.write("**Pandas Version:**", pd.__version__)
                except:
                    st.write("**Pandas:** Not available")
                    
            except Exception as e:
                st.error(f"Error getting system info: {str(e)}")
                st.code(traceback.format_exc())
    
    except Exception as main_error:
        st.error(f"CRITICAL ERROR in Development Tools: {str(main_error)}")
        st.code(traceback.format_exc())
        st.warning("Please report this error to the administrator")
        
        # Show which line caused the error
        import sys
        exc_type, exc_value, exc_traceback = sys.exc_info()
        if exc_traceback:
            st.write("**Error Location:**")
            import traceback as tb
            for line in tb.format_tb(exc_traceback):
                st.code(line)