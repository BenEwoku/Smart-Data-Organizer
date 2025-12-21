# File: utils/organization.py
"""
Data organization utilities for structure-specific formatting
"""

import pandas as pd
import streamlit as st

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
    
    st.subheader("⏰ Time Series Organization")
    
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