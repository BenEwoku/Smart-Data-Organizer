# File: utils/interactive_table.py
"""
Interactive table editor with inline editing, search, filter, and keyboard shortcuts
"""

import streamlit as st
import pandas as pd
from datetime import datetime
import re

class InteractiveTable:
    """
    Interactive table editor component
    Supports inline editing, search, filter, sort, copy/paste, undo/redo
    """
    
    def __init__(self, df, key="interactive_table"):
        """
        Initialize interactive table
        
        Args:
            df: pandas DataFrame
            key: Unique key for this table instance
        """
        # Clean column names to avoid reserved names
        self.df = self._clean_column_names(df.copy())
        self.original_df = self.df.copy()
        self.key = key
        
        # Initialize session state for this table
        if f'{key}_history' not in st.session_state:
            st.session_state[f'{key}_history'] = []
            st.session_state[f'{key}_history_index'] = -1
            st.session_state[f'{key}_original'] = self.df.copy()
            st.session_state[f'{key}_modified_cells'] = set()
        
        self.history = st.session_state[f'{key}_history']
        self.history_index = st.session_state[f'{key}_history_index']
        self.original_df_session = st.session_state[f'{key}_original']
        self.modified_cells = st.session_state[f'{key}_modified_cells']
    
    def _clean_column_names(self, df):
        """Clean column names to avoid reserved names and issues"""
        cleaned_df = df.copy()
        
        # List of reserved column names by Streamlit data_editor
        reserved_names = [
            '_index', '_selected_rows', '_selected_row_indices', 
            '_selection', 'index', 'selection'
        ]
        
        # Rename reserved columns
        rename_map = {}
        for col in cleaned_df.columns:
            if col in reserved_names:
                new_name = f"col_{col}"
                rename_map[col] = new_name
                st.warning(f"Renaming reserved column '{col}' to '{new_name}'")
        
        if rename_map:
            cleaned_df = cleaned_df.rename(columns=rename_map)
        
        # Ensure all column names are strings
        cleaned_df.columns = [str(col) for col in cleaned_df.columns]
        
        return cleaned_df
    
    def _restore_original_column_names(self, df, original_df):
        """Restore original column names if they were changed"""
        # This is for display purposes - we'll keep internal names clean
        return df
    
    def save_state(self):
        """Save current state to history for undo/redo"""
        # Remove any states after current index (when user undid then made new changes)
        self.history = self.history[:self.history_index + 1]
        
        # Add current state
        self.history.append({
            'df': self.df.copy(),
            'modified_cells': self.modified_cells.copy(),
            'timestamp': datetime.now(),
            'action': 'edit'
        })
        
        # Limit history to last 50 actions
        if len(self.history) > 50:
            self.history = self.history[-50:]
        
        self.history_index = len(self.history) - 1
        
        # Update session state
        st.session_state[f'{self.key}_history'] = self.history
        st.session_state[f'{self.key}_history_index'] = self.history_index
    
    def undo(self):
        """Undo last change"""
        if self.history_index > 0:
            self.history_index -= 1
            state = self.history[self.history_index]
            self.df = state['df'].copy()
            self.modified_cells = state['modified_cells'].copy()
            
            st.session_state[f'{self.key}_history_index'] = self.history_index
            return True
        return False
    
    def redo(self):
        """Redo last undone change"""
        if self.history_index < len(self.history) - 1:
            self.history_index += 1
            state = self.history[self.history_index]
            self.df = state['df'].copy()
            self.modified_cells = state['modified_cells'].copy()
            
            st.session_state[f'{self.key}_history_index'] = self.history_index
            return True
        return False
    
    def revert_all(self):
        """Revert to original data"""
        self.df = self.original_df.copy()
        self.modified_cells = set()
        self.history = []
        self.history_index = -1
        
        st.session_state[f'{self.key}_history'] = []
        st.session_state[f'{self.key}_history_index'] = -1
        st.session_state[f'{self.key}_modified_cells'] = set()
    
    def get_changes_summary(self):
        """Get summary of changes made"""
        if not self.modified_cells:
            return None
        
        summary = {
            'modified_cells': len(self.modified_cells),
            'modified_rows': len(set(row for row, col in self.modified_cells)),
            'modified_columns': len(set(col for row, col in self.modified_cells))
        }
        return summary
    
    def render_toolbar(self):
        """Render table toolbar with actions"""
        col1, col2, col3, col4, col5, col6 = st.columns([1, 1, 1, 1, 1, 2])
        
        with col1:
            undo_disabled = self.history_index <= 0
            if st.button("Undo", key=f"{self.key}_undo", 
                        disabled=undo_disabled,
                        help="Undo last change (Ctrl+Z)"):
                if self.undo():
                    st.success("Undone")
                    st.rerun()
        
        with col2:
            redo_disabled = self.history_index >= len(self.history) - 1
            if st.button("Redo", key=f"{self.key}_redo",
                        disabled=redo_disabled,
                        help="Redo last undone change (Ctrl+Y)"):
                if self.redo():
                    st.success("Redone")
                    st.rerun()
        
        with col3:
            if st.button("Reset", key=f"{self.key}_revert",
                        help="Discard all changes and revert to original"):
                if st.session_state.get(f"{self.key}_confirm_revert"):
                    self.revert_all()
                    st.success("All changes discarded")
                    st.session_state[f"{self.key}_confirm_revert"] = False
                    st.rerun()
                else:
                    st.session_state[f"{self.key}_confirm_revert"] = True
                    st.warning("Click again to confirm")
        
        with col4:
            if st.button("Add Row", key=f"{self.key}_add_row",
                        help="Add new row at bottom"):
                self.add_row()
        
        with col5:
            if st.button("Search", key=f"{self.key}_search",
                        help="Search table (Ctrl+F)"):
                st.session_state[f"{self.key}_show_search"] = not st.session_state.get(f"{self.key}_show_search", False)
        
        with col6:
            changes = self.get_changes_summary()
            if changes:
                st.info(f"{changes['modified_cells']} cells edited")
            else:
                st.caption("No changes yet")
    
    def render_search_box(self):
        """Render search functionality"""
        if not st.session_state.get(f"{self.key}_show_search"):
            return None
        
        with st.expander("Search Table", expanded=True):
            col1, col2, col3 = st.columns([3, 1, 1])
            
            with col1:
                search_term = st.text_input(
                    "Search term:",
                    key=f"{self.key}_search_term",
                    placeholder="Enter text to search..."
                )
            
            with col2:
                search_column = st.selectbox(
                    "Column:",
                    ["All columns"] + list(self.df.columns),
                    key=f"{self.key}_search_column"
                )
            
            with col3:
                case_sensitive = st.checkbox(
                    "Case sensitive",
                    key=f"{self.key}_case_sensitive"
                )
            
            if search_term:
                matches = self.search(search_term, search_column, case_sensitive)
                if matches:
                    st.success(f"Found {len(matches)} match(es)")
                    # Highlight matching rows
                    return matches
        
        return None
    
    def search(self, term, column="All columns", case_sensitive=False):
        """Search table for term"""
        matches = []
        
        if column == "All columns":
            search_cols = self.df.columns
        else:
            search_cols = [column]
        
        for col in search_cols:
            if self.df[col].dtype == 'object':
                if case_sensitive:
                    mask = self.df[col].astype(str).str.contains(term, na=False)
                else:
                    mask = self.df[col].astype(str).str.contains(term, case=False, na=False)
                
                matching_indices = self.df[mask].index.tolist()
                for idx in matching_indices:
                    matches.append((idx, col))
        
        return matches
    
    def add_row(self):
        """Add new empty row"""
        new_row = pd.Series([None] * len(self.df.columns), index=self.df.columns)
        self.df = pd.concat([self.df, pd.DataFrame([new_row])], ignore_index=True)
        self.save_state()
        st.rerun()
    
    def delete_rows(self, indices):
        """Delete rows by indices"""
        self.df = self.df.drop(indices).reset_index(drop=True)
        self.save_state()
    
    def edit_cell(self, row_idx, col_name, new_value):
        """Edit single cell"""
        old_value = self.df.at[row_idx, col_name]
        
        # Try to maintain data type
        try:
            if pd.api.types.is_numeric_dtype(self.df[col_name]):
                new_value = pd.to_numeric(new_value)
            elif pd.api.types.is_datetime64_any_dtype(self.df[col_name]):
                new_value = pd.to_datetime(new_value)
        except:
            pass
        
        self.df.at[row_idx, col_name] = new_value
        self.modified_cells.add((row_idx, col_name))
        self.save_state()
    
    def rename_column(self, old_name, new_name):
        """Rename column"""
        if new_name and new_name != old_name and new_name not in self.df.columns:
            self.df = self.df.rename(columns={old_name: new_name})
            self.save_state()
            return True
        return False
    
    def delete_column(self, col_name):
        """Delete column"""
        if col_name in self.df.columns:
            self.df = self.df.drop(columns=[col_name])
            self.save_state()
            return True
        return False
    
    def sort_by_column(self, col_name, ascending=True):
        """Sort table by column"""
        if col_name in self.df.columns:
            self.df = self.df.sort_values(col_name, ascending=ascending)
            self.save_state()
            return True
        return False
    
    def render(self):
        """Render the interactive table"""
        # Render toolbar
        self.render_toolbar()
        
        # Render search box
        search_matches = self.render_search_box()
        
        # Display table information
        col_info1, col_info2, col_info3 = st.columns(3)
        with col_info1:
            st.caption(f"Rows: {len(self.df):,}")
        with col_info2:
            st.caption(f"Columns: {len(self.df.columns)}")
        with col_info3:
            st.caption("Click any cell to edit")
        
        st.markdown("---")
        
        # Render editable table using Streamlit's data_editor
        try:
            edited_df = st.data_editor(
                self.df,
                use_container_width=True,
                num_rows="dynamic",  # Allow adding/deleting rows
                key=f"{self.key}_editor",
                height=400,
                column_config={
                    col: st.column_config.Column(
                        col,
                        help=f"Edit values in {col} column"
                    ) for col in self.df.columns
                }
            )
            
            # Detect changes
            if not edited_df.equals(self.df):
                # Find what changed
                for col in self.df.columns:
                    if col in edited_df.columns:
                        try:
                            # Handle NaN comparison
                            changed_mask = (self.df[col] != edited_df[col]) & ~(
                                self.df[col].isna() & edited_df[col].isna()
                            )
                            changed_indices = self.df[changed_mask].index.tolist()
                            
                            for idx in changed_indices:
                                self.modified_cells.add((idx, col))
                        except:
                            # If comparison fails, check for any non-identical values
                            for idx in range(len(self.df)):
                                old_val = self.df.at[idx, col]
                                new_val = edited_df.at[idx, col]
                                
                                # Handle NaN comparison
                                if pd.isna(old_val) and pd.isna(new_val):
                                    continue
                                if old_val != new_val:
                                    self.modified_cells.add((idx, col))
                
                self.df = edited_df.copy()
                self.save_state()
            
            # Update session state
            st.session_state[f'{self.key}_modified_cells'] = self.modified_cells
            
            return self.df
            
        except Exception as e:
            st.error(f"Error rendering table editor: {str(e)}")
            st.info("Falling back to read-only view...")
            
            # Show read-only view
            st.dataframe(self.df, use_container_width=True, height=400)
            return self.df
    
    def get_dataframe(self):
        """Get current DataFrame"""
        return self.df.copy()


def show_interactive_table(df, key="main_table"):
    """
    Show interactive table component
    
    Args:
        df: pandas DataFrame
        key: Unique key for this table
        
    Returns:
        pd.DataFrame: Modified DataFrame
    """
    table = InteractiveTable(df, key=key)
    return table.render()