# File: utils/organization.py
"""
Data organization utilities for structure-specific formatting
"""

import pandas as pd
import streamlit as st
# Add to existing imports in organization.py
import re
from datetime import datetime, timedelta
from collections import Counter

def organize_time_series(df, date_col):
    """
    Organize time series data
    
    Args:
        df: pandas DataFrame
        date_col: Name of date column
        
    Returns:
        pd.DataFrame: Organized time series data
    """
    df = df.copy()
    
    st.subheader("Time Series Organization")
    
    col1, col2 = st.columns(2)
    
    with col1:
        sort_order = st.selectbox(
            "Sort by date:",
            ["Ascending (oldest first)", "Descending (newest first)"]
        )
    
    with col2:
        date_format = st.selectbox(
            "Date format:",
            ["YYYY-MM-DD", "MM/DD/YYYY", "DD/MM/YYYY", "YYYY-MM-DD HH:MM:SS"]
        )
    
    # Convert to datetime
    try:
        df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
        
        # Sort by date
        ascending = (sort_order == "Ascending (oldest first)")
        df = df.sort_values(date_col, ascending=ascending)
        
        # Format dates
        format_map = {
            "YYYY-MM-DD": '%Y-%m-%d',
            "MM/DD/YYYY": '%m/%d/%Y',
            "DD/MM/YYYY": '%d/%m/%Y',
            "YYYY-MM-DD HH:MM:SS": '%Y-%m-%d %H:%M:%S'
        }
        
        df[date_col] = df[date_col].dt.strftime(format_map[date_format])
        
        # Show date range
        st.info(f"📅 Date range: {df[date_col].iloc[0]} to {df[date_col].iloc[-1]}")
        
    except Exception as e:
        st.warning(f"Could not process dates: {str(e)}")
    
    # Optional: Fill missing dates
    with st.expander("🔧 Advanced Options"):
        fill_gaps = st.checkbox("Fill missing dates")
        
        if fill_gaps:
            st.info("This feature creates continuous timeline (coming in Phase 2)")
    
    return df

def organize_panel_data(df, date_col, entity_col):
    """
    Organize panel/longitudinal data
    
    Args:
        df: pandas DataFrame
        date_col: Name of date column
        entity_col: Name of entity column
        
    Returns:
        pd.DataFrame: Organized panel data
    """
    df = df.copy()
    
    st.subheader("Panel Data Organization")
    
    # SAFETY CHECK 1: Validate date_col exists
    if date_col not in df.columns:
        st.warning(f"Date column '{date_col}' not found. Attempting to find date column...")
        
        # Look for columns with 'date', 'time', 'year', 'month' in name (case-insensitive)
        date_like_cols = [col for col in df.columns if any(
            keyword in str(col).lower() for keyword in ['date', 'time', 'year', 'month', 'day']
        )]
        
        if date_like_cols:
            date_col = date_like_cols[0]
            st.info(f"Using column '{date_col}' as date column.")
        else:
            # Try to find datetime columns
            datetime_cols = [col for col in df.columns if pd.api.types.is_datetime64_any_dtype(df[col])]
            if datetime_cols:
                date_col = datetime_cols[0]
                st.info(f"Using datetime column '{date_col}' as date column.")
            else:
                st.error("No suitable date column found. Panel organization may not work correctly.")
    
    # SAFETY CHECK 2: Validate entity_col exists
    if entity_col not in df.columns:
        st.warning(f"Entity column '{entity_col}' not found. Attempting to find entity column...")
        
        # Strategy 1: Look for column that STARTS WITH the original name
        # (catches 'Anhui Province' -> 'Anhui Province_1')
        possible_cols = [col for col in df.columns if str(col).startswith(str(entity_col))]
        
        if possible_cols:
            entity_col = possible_cols[0]
            st.info(f"Using column '{entity_col}' for entities.")
        else:
            # Strategy 2: Look for columns with entity-like names
            entity_like_cols = [col for col in df.columns if any(
                keyword in str(col).lower() for keyword in ['name', 'id', 'code', 'region', 'country', 'company', 'entity']
            )]
            
            if entity_like_cols:
                entity_col = entity_like_cols[0]
                st.info(f"Using column '{entity_col}' as entity column.")
            else:
                # Strategy 3: Use first non-date string column
                non_date_cols = [col for col in df.columns if col != date_col and pd.api.types.is_string_dtype(df[col])]
                if non_date_cols:
                    entity_col = non_date_cols[0]
                    st.info(f"Using first string column '{entity_col}' as entity column.")
                else:
                    # Last resort: Use first non-date column
                    other_cols = [col for col in df.columns if col != date_col]
                    entity_col = other_cols[0] if other_cols else df.columns[0]
                    st.warning(f"No suitable entity column found. Using '{entity_col}'. Results may be inaccurate.")
    
    # Now safely proceed with organization
    st.info(f"Organizing: Date='{date_col}', Entity='{entity_col}'")
    
    # Convert date column
    try:
        df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
        st.success(f"Converted '{date_col}' to datetime format")
    except Exception as e:
        st.warning(f"Could not convert date column: {str(e)}")
    
    # Sort by entity then date
    try:
        df = df.sort_values([entity_col, date_col])
        st.success(f"Sorted by {entity_col} → {date_col}")
    except Exception as e:
        st.warning(f"Could not sort panel data: {str(e)}")
    
    # Panel statistics - WITH SAFETY CHECK
    col1, col2, col3 = st.columns(3)
    
    with col1:
        try:
            n_entities = df[entity_col].nunique()
            st.metric("Entities", n_entities)
        except:
            st.metric("Entities", "N/A")
    
    with col2:
        try:
            n_periods = df[date_col].nunique() if date_col in df.columns else 0
            st.metric("Time Periods", n_periods)
        except:
            st.metric("Time Periods", "N/A")
    
    with col3:
        try:
            obs_per_entity = len(df) / n_entities if n_entities > 0 else 0
            st.metric("Avg Obs/Entity", f"{obs_per_entity:.1f}")
        except:
            st.metric("Avg Obs/Entity", "N/A")
    
    # Check balance
    try:
        counts = df.groupby(entity_col).size()
        is_balanced = counts.nunique() == 1
        
        if is_balanced:
            st.success("Balanced panel: All entities have same number of observations")
        else:
            min_obs = counts.min()
            max_obs = counts.max()
            st.info(f"Unbalanced panel: Observations range from {min_obs} to {max_obs} per entity")
    except Exception as e:
        st.warning(f"Could not check panel balance: {str(e)}")
    
    # Optional: Pivot to wide format
    with st.expander("Advanced Options"):
        format_choice = st.radio(
            "Data format:",
            ["Long format (current)", "Wide format (pivot)"],
            help="Long: Each row is entity-time observation. Wide: Each entity is a row, time as columns"
        )
        
        if format_choice == "Wide format (pivot)":
            st.info("Pivot to wide format (coming in Phase 2)")
    
    return df

def organize_cross_sectional(df):
    """
    Organize cross-sectional data
    
    Args:
        df: pandas DataFrame
        
    Returns:
        pd.DataFrame: Organized cross-sectional data
    """
    df = df.copy()
    
    st.subheader("📉 Cross-Sectional Organization")
    
    col1, col2 = st.columns(2)
    
    with col1:
        sort_col = st.selectbox(
            "Sort by column:",
            ["None"] + list(df.columns)
        )
    
    with col2:
        if sort_col != "None":
            sort_order = st.radio(
                "Order:",
                ["Ascending", "Descending"],
                horizontal=True
            )
        else:
            sort_order = "Ascending"
    
    # Apply sorting
    if sort_col != "None" and sort_col in df.columns:
        try:
            ascending = (sort_order == "Ascending")
            df = df.sort_values(sort_col, ascending=ascending)
            st.success(f"✓ Sorted by {sort_col} ({sort_order.lower()})")
        except:
            st.warning(f"Could not sort by {sort_col}")
    
    # Optional: Group by categories
    with st.expander("🔧 Advanced Options"):
        categorical_cols = df.select_dtypes(include=['object']).columns.tolist()
        
        if categorical_cols:
            group_by = st.selectbox(
                "Group by category:",
                ["None"] + categorical_cols
            )
            
            if group_by != "None":
                st.info("Grouping and aggregation (coming in Phase 2)")
        else:
            st.info("No categorical columns detected for grouping")
    
    return df

def create_lag_variables(df, columns, lags=[1]):
    """
    Create lagged variables for time series
    
    Args:
        df: pandas DataFrame
        columns: List of columns to lag
        lags: List of lag periods
        
    Returns:
        pd.DataFrame: DataFrame with lag variables
    """
    df = df.copy()
    
    for col in columns:
        if col in df.columns:
            for lag in lags:
                df[f'{col}_lag{lag}'] = df[col].shift(lag)
    
    return df

def resample_time_series(df, date_col, freq='D', agg_func='mean'):
    """
    Resample time series to different frequency
    
    Args:
        df: pandas DataFrame
        date_col: Date column name
        freq: Frequency ('D'=daily, 'W'=weekly, 'M'=monthly, 'Q'=quarterly, 'Y'=yearly)
        agg_func: Aggregation function ('mean', 'sum', 'first', 'last')
        
    Returns:
        pd.DataFrame: Resampled data
    """
    df = df.copy()
    
    try:
        df[date_col] = pd.to_datetime(df[date_col])
        df = df.set_index(date_col)
        
        if agg_func == 'mean':
            df_resampled = df.resample(freq).mean()
        elif agg_func == 'sum':
            df_resampled = df.resample(freq).sum()
        elif agg_func == 'first':
            df_resampled = df.resample(freq).first()
        elif agg_func == 'last':
            df_resampled = df.resample(freq).last()
        
        df_resampled = df_resampled.reset_index()
        return df_resampled
        
    except:
        return df

def organize_email_data(df):
    """
    Organize email data with email-specific analysis
    
    Args:
        df: pandas DataFrame with email data
        
    Returns:
        pd.DataFrame: Organized email data with email-specific metrics
    """
    df_organized = df.copy()
    
    # Check if this is actually email data
    email_columns = ['From', 'To', 'Subject', 'Date']
    has_email_columns = sum(1 for col in email_columns[:3] if col in df_organized.columns) >= 2
    
    if not has_email_columns:
        # Not enough email columns, return as-is
        return df_organized
    
    try:
        # Sort by date if available
        if 'Date' in df_organized.columns:
            try:
                # Convert to datetime if not already
                if not pd.api.types.is_datetime64_any_dtype(df_organized['Date']):
                    df_organized['Date'] = pd.to_datetime(df_organized['Date'], errors='coerce')
                
                # Sort by date (newest first)
                df_organized = df_organized.sort_values('Date', ascending=False)
            except:
                pass
        
        # Add spam detection columns if not already present
        if 'Spam_Score' not in df_organized.columns:
            try:
                from utils.detection import add_spam_columns_to_dataframe
                df_organized = add_spam_columns_to_dataframe(df_organized)
            except:
                # Fallback: add simple spam columns
                df_organized['Spam_Score'] = 0
                df_organized['Is_Spam'] = False
        
        # Ensure Is_Spam column exists
        if 'Is_Spam' not in df_organized.columns and 'Spam_Score' in df_organized.columns:
            df_organized['Is_Spam'] = df_organized['Spam_Score'] >= 70
        
        # Calculate email metrics if columns exist
        if 'Body_Preview' in df_organized.columns:
            # Add email length
            df_organized['Email_Length'] = df_organized['Body_Preview'].astype(str).str.len()
        
        if 'Subject' in df_organized.columns:
            # Add subject length
            df_organized['Subject_Length'] = df_organized['Subject'].astype(str).str.len()
        
        # Add priority if not exists
        if 'Priority_Score' not in df_organized.columns:
            df_organized['Priority_Score'] = 50  # Default medium priority
        
        # Calculate response times if we have thread info and dates
        if 'Thread_ID' in df_organized.columns and 'Date' in df_organized.columns:
            try:
                df_organized = calculate_response_times(df_organized)
            except:
                pass
        
        # Reorder columns for better readability
        preferred_order = [
            'Date', 'From', 'To', 'Subject', 'Body_Preview',
            'Thread_ID', 'Response_Time_Hours', 'Priority_Score',
            'Spam_Score', 'Is_Spam', 'Email_Length', 'Subject_Length'
        ]
        
        # Get existing columns in preferred order, then others
        existing_preferred = [col for col in preferred_order if col in df_organized.columns]
        other_columns = [col for col in df_organized.columns if col not in existing_preferred]
        
        df_organized = df_organized[existing_preferred + other_columns]
        
        return df_organized
        
    except Exception as e:
        print(f"Error organizing email data: {str(e)}")
        return df.copy()

def apply_email_sorting(df, sort_option):
    """Apply email-specific sorting"""
    try:
        if "Date" in df.columns:
            # Ensure Date is datetime
            if not pd.api.types.is_datetime64_any_dtype(df['Date']):
                df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        
        if sort_option == "Date (newest first)":
            if 'Date' in df.columns:
                df = df.sort_values('Date', ascending=False)
                st.success("✓ Sorted by date (newest first)")
        
        elif sort_option == "Date (oldest first)":
            if 'Date' in df.columns:
                df = df.sort_values('Date', ascending=True)
                st.success("✓ Sorted by date (oldest first)")
        
        elif sort_option == "Sender (A-Z)":
            if 'From' in df.columns:
                df = df.sort_values('From', ascending=True)
                st.success("✓ Sorted by sender (A-Z)")
        
        elif sort_option == "Recipient (A-Z)":
            if 'To' in df.columns:
                df = df.sort_values('To', ascending=True)
                st.success("✓ Sorted by recipient (A-Z)")
        
        elif sort_option == "Subject (A-Z)":
            if 'Subject' in df.columns:
                df = df.sort_values('Subject', ascending=True)
                st.success("✓ Sorted by subject (A-Z)")
        
        elif sort_option == "Priority Score":
            if 'Priority_Score' in df.columns:
                df = df.sort_values('Priority_Score', ascending=False)
                st.success("✓ Sorted by priority score (highest first)")
        
        elif sort_option == "Thread Activity":
            # Sort by thread activity (most recent in thread first)
            if all(col in df.columns for col in ['Thread_ID', 'Date']):
                # Get most recent date per thread
                thread_latest = df.groupby('Thread_ID')['Date'].max()
                df['Thread_Latest'] = df['Thread_ID'].map(thread_latest)
                df = df.sort_values(['Thread_Latest', 'Date'], ascending=[False, False])
                df = df.drop('Thread_Latest', axis=1)
                st.success("✓ Sorted by thread activity")
    
    except Exception as e:
        st.warning(f"Could not apply sorting: {str(e)}")
    
    return df

def apply_email_filters(df):
    """Apply email-specific filters"""
    with st.expander("Email Filters", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            # Sender filter
            if 'From' in df.columns:
                unique_senders = df['From'].dropna().unique()
                selected_senders = st.multiselect(
                    "Filter by sender:",
                    options=list(unique_senders)[:50],  # Limit to first 50
                    default=[]
                )
                if selected_senders:
                    df = df[df['From'].isin(selected_senders)]
            
            # Date range filter
            if 'Date' in df.columns and pd.api.types.is_datetime64_any_dtype(df['Date']):
                min_date = df['Date'].min().date()
                max_date = df['Date'].max().date()
                date_range = st.date_input(
                    "Filter by date range:",
                    value=[min_date, max_date],
                    min_value=min_date,
                    max_value=max_date
                )
                if len(date_range) == 2:
                    df = df[(df['Date'].dt.date >= date_range[0]) & 
                           (df['Date'].dt.date <= date_range[1])]
        
        with col2:
            # Subject keyword filter
            if 'Subject' in df.columns:
                keyword = st.text_input("Filter by subject keyword:")
                if keyword:
                    df = df[df['Subject'].str.contains(keyword, case=False, na=False)]
            
            # Priority filter
            if 'Priority_Score' in df.columns:
                min_priority = st.slider("Minimum priority score:", 0, 100, 0)
                df = df[df['Priority_Score'] >= min_priority]
        
        st.caption(f"Filtered to {len(df)} emails")
    
    return df

def apply_email_grouping(df, group_option):
    """Apply email grouping and aggregation"""
    try:
        if group_option == "Sender":
            if 'From' in df.columns:
                st.info("Grouping by sender - showing sender statistics")
                # Add sender counts
                sender_counts = df['From'].value_counts().reset_index()
                sender_counts.columns = ['From', 'Email_Count']
                df = df.merge(sender_counts, on='From', how='left')
        
        elif group_option == "Recipient":
            if 'To' in df.columns:
                st.info("Grouping by recipient - showing recipient statistics")
                recipient_counts = df['To'].value_counts().reset_index()
                recipient_counts.columns = ['To', 'Email_Count']
                df = df.merge(recipient_counts, on='To', how='left')
        
        elif group_option == "Date (day)":
            if 'Date' in df.columns:
                st.info("Grouping by day - showing daily email volume")
                df['Date_Day'] = df['Date'].dt.date
                day_counts = df['Date_Day'].value_counts().reset_index()
                day_counts.columns = ['Date_Day', 'Daily_Count']
                df = df.merge(day_counts, on='Date_Day', how='left')
        
        elif group_option == "Date (week)":
            if 'Date' in df.columns:
                st.info("Grouping by week - showing weekly email volume")
                df['Date_Week'] = df['Date'].dt.to_period('W').apply(lambda r: r.start_time.date())
                week_counts = df['Date_Week'].value_counts().reset_index()
                week_counts.columns = ['Date_Week', 'Weekly_Count']
                df = df.merge(week_counts, on='Date_Week', how='left')
        
        elif group_option == "Date (month)":
            if 'Date' in df.columns:
                st.info("Grouping by month - showing monthly email volume")
                df['Date_Month'] = df['Date'].dt.to_period('M').apply(lambda r: r.start_time.date())
                month_counts = df['Date_Month'].value_counts().reset_index()
                month_counts.columns = ['Date_Month', 'Monthly_Count']
                df = df.merge(month_counts, on='Date_Month', how='left')
        
        elif group_option == "Thread":
            if 'Thread_ID' in df.columns:
                st.info("Grouping by thread - showing thread statistics")
                thread_counts = df['Thread_ID'].value_counts().reset_index()
                thread_counts.columns = ['Thread_ID', 'Thread_Size']
                df = df.merge(thread_counts, on='Thread_ID', how='left')
    
    except Exception as e:
        st.warning(f"Could not apply grouping: {str(e)}")
    
    return df

def add_email_analysis(df, analysis_type):
    """Add email-specific analysis columns"""
    try:
        if analysis_type == "Sentiment Score":
            df = add_sentiment_analysis(df)
            st.success("✓ Added sentiment analysis")
        
        elif analysis_type == "Response Time":
            df = calculate_response_times_advanced(df)
            st.success("✓ Added response time analysis")
        
        elif analysis_type == "Email Length":
            df = calculate_email_length(df)
            st.success("✓ Added email length analysis")
        
        elif analysis_type == "Attachment Count":
            df = estimate_attachment_count(df)
            st.success("✓ Added attachment count estimation")
        
        elif analysis_type == "Urgency Flag":
            df = flag_urgent_emails(df)
            st.success("✓ Added urgency flags")
    
    except Exception as e:
        st.warning(f"Could not add {analysis_type}: {str(e)}")
    
    return df

def add_sentiment_analysis(df):
    """Simple sentiment analysis based on subject and body"""
    try:
        # Simple keyword-based sentiment
        positive_words = ['thanks', 'thank you', 'great', 'good', 'excellent', 'awesome', 'happy']
        negative_words = ['urgent', 'problem', 'issue', 'error', 'failed', 'broken', 'critical']
        
        def calculate_sentiment(text):
            if not isinstance(text, str):
                return 0
            
            text_lower = text.lower()
            positive_count = sum(1 for word in positive_words if word in text_lower)
            negative_count = sum(1 for word in negative_words if word in text_lower)
            
            # Simple sentiment score: positive - negative
            return positive_count - negative_count
        
        # Apply to subject and body
        if 'Subject' in df.columns:
            df['Subject_Sentiment'] = df['Subject'].apply(calculate_sentiment)
        
        if 'Body_Preview' in df.columns:
            df['Body_Sentiment'] = df['Body_Preview'].apply(calculate_sentiment)
        
        # Overall sentiment
        if 'Subject_Sentiment' in df.columns and 'Body_Sentiment' in df.columns:
            df['Overall_Sentiment'] = df['Subject_Sentiment'] + df['Body_Sentiment'] * 0.5
    
    except:
        pass
    
    return df

def calculate_response_times_advanced(df):
    """Calculate response times between emails in threads"""
    try:
        if all(col in df.columns for col in ['Thread_ID', 'Date', 'From']):
            # Sort by thread and date
            df_sorted = df.sort_values(['Thread_ID', 'Date']).copy()
            
            response_times = []
            for thread_id in df_sorted['Thread_ID'].unique():
                thread_emails = df_sorted[df_sorted['Thread_ID'] == thread_id]
                
                if len(thread_emails) > 1:
                    # Calculate response time for each email after first
                    prev_sender = None
                    prev_date = None
                    
                    for idx, row in thread_emails.iterrows():
                        if prev_sender and prev_date and row['From'] != prev_sender:
                            # Different sender - likely a response
                            time_diff = (row['Date'] - prev_date).total_seconds() / 3600  # Hours
                            response_times.append((idx, time_diff))
                        else:
                            response_times.append((idx, None))
                        
                        prev_sender = row['From']
                        prev_date = row['Date']
                else:
                    # Single email in thread
                    response_times.append((thread_emails.index[0], None))
            
            # Create response time series
            response_series = pd.Series(dict(response_times))
            df['Response_Time_Hours'] = df.index.map(response_series)
    
    except:
        pass
    
    return df

def calculate_email_length(df):
    """Calculate email length metrics"""
    try:
        if 'Body_Preview' in df.columns:
            df['Email_Length'] = df['Body_Preview'].apply(
                lambda x: len(str(x)) if pd.notna(x) else 0
            )
            
            # Categorize by length
            def categorize_length(length):
                if length < 100:
                    return 'Very Short'
                elif length < 500:
                    return 'Short'
                elif length < 2000:
                    return 'Medium'
                else:
                    return 'Long'
            
            df['Email_Length_Category'] = df['Email_Length'].apply(categorize_length)
    
    except:
        pass
    
    return df

def estimate_attachment_count(df):
    """Estimate attachment count based on keywords"""
    try:
        if 'Body_Preview' in df.columns:
            attachment_keywords = ['attachment', 'attached', 'enclosed', 'file', 'document', 'pdf', 'doc', 'zip']
            
            def count_attachments(text):
                if not isinstance(text, str):
                    return 0
                
                text_lower = text.lower()
                # Count mentions of attachment keywords
                count = sum(1 for keyword in attachment_keywords if keyword in text_lower)
                return min(count, 5)  # Cap at 5
            
            df['Estimated_Attachments'] = df['Body_Preview'].apply(count_attachments)
    
    except:
        pass
    
    return df

def flag_urgent_emails(df):
    """Flag urgent emails based on content"""
    try:
        urgent_keywords = ['urgent', 'asap', 'immediate', 'emergency', 'critical', 'important']
        urgent_pattern = '|'.join(urgent_keywords)
        
        if 'Subject' in df.columns:
            df['Is_Urgent_Subject'] = df['Subject'].str.contains(
                urgent_pattern, case=False, na=False
            )
        
        if 'Body_Preview' in df.columns:
            df['Is_Urgent_Body'] = df['Body_Preview'].str.contains(
                urgent_pattern, case=False, na=False
            )
        
        # Overall urgency flag
        if 'Is_Urgent_Subject' in df.columns and 'Is_Urgent_Body' in df.columns:
            df['Is_Urgent'] = df['Is_Urgent_Subject'] | df['Is_Urgent_Body']
    
    except:
        pass
    
    return df

def show_email_insights(df):
    """Display email-specific insights"""
    with st.expander("📊 Email Insights", expanded=True):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Top senders
            if 'From' in df.columns:
                top_senders = df['From'].value_counts().head(5)
                st.metric("Top Sender", top_senders.index[0] if len(top_senders) > 0 else "N/A")
                st.caption(f"Sends: {top_senders.iloc[0] if len(top_senders) > 0 else 0} emails")
        
        with col2:
            # Email volume trend
            if 'Date' in df.columns and pd.api.types.is_datetime64_any_dtype(df['Date']):
                emails_per_day = len(df) / max(1, (df['Date'].max() - df['Date'].min()).days)
                st.metric("Avg Emails/Day", f"{emails_per_day:.1f}")
        
        with col3:
            # Thread analysis
            if 'Thread_ID' in df.columns:
                avg_thread_size = df['Thread_ID'].value_counts().mean()
                st.metric("Avg Thread Size", f"{avg_thread_size:.1f}")
        
        # More detailed insights
        if st.checkbox("Show detailed email statistics"):
            st.markdown("---")
            
            # Sender analysis
            if 'From' in df.columns:
                st.markdown("**Top 10 Senders:**")
                sender_stats = df['From'].value_counts().head(10)
                st.dataframe(sender_stats.reset_index().rename(
                    columns={'index': 'Sender', 'From': 'Email Count'}
                ), use_container_width=True, height=200)
            
            # Time analysis
            if 'Date' in df.columns:
                st.markdown("**Email Distribution by Hour:**")
                df['Hour'] = df['Date'].dt.hour
                hour_counts = df['Hour'].value_counts().sort_index()
                st.bar_chart(hour_counts)