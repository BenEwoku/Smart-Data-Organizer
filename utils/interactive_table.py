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
    Supports inline editing, search, filter, sort, copy/paste, undo/redo, and column renaming
    """
    
    def __init__(self, df, key="interactive_table"):
        """
        Initialize interactive table
        
        Args:
            df: pandas DataFrame
            key: Unique key for this table instance
        """
        # Clean column names to avoid reserved names
        self.df = self._clean_dataframe(df.copy())
        self.original_df = self.df.copy()
        self.key = key
        
        # Initialize session state for this table - WITH PROPER DEFAULT VALUES
        self._initialize_session_state()
        
        # Now safely access session state
        self.history = st.session_state[f'{key}_history']
        self.history_index = st.session_state[f'{key}_history_index']
        self.original_df_session = st.session_state[f'{key}_original']
        self.modified_cells = st.session_state[f'{key}_modified_cells']
        self.renamed_columns = st.session_state[f'{key}_renamed_columns']
    
    def _initialize_session_state(self):
        """Initialize all session state keys with proper defaults"""
        key = self.key
        
        # Initialize each key individually
        if f'{key}_history' not in st.session_state:
            st.session_state[f'{key}_history'] = []
        
        if f'{key}_history_index' not in st.session_state:
            st.session_state[f'{key}_history_index'] = -1
        
        if f'{key}_original' not in st.session_state:
            st.session_state[f'{key}_original'] = self.df.copy()
        
        if f'{key}_modified_cells' not in st.session_state:
            st.session_state[f'{key}_modified_cells'] = set()
        
        if f'{key}_renamed_columns' not in st.session_state:
            st.session_state[f'{key}_renamed_columns'] = {}
        
        if f'{key}_show_rename' not in st.session_state:
            st.session_state[f'{key}_show_rename'] = False
        
        if f'{key}_show_search' not in st.session_state:
            st.session_state[f'{key}_show_search'] = False
        
        if f'{key}_confirm_revert' not in st.session_state:
            st.session_state[f'{key}_confirm_revert'] = False
    
    def _clean_dataframe(self, df):
        """Clean dataframe to avoid issues"""
        cleaned_df = df.copy()
        
        # Ensure all column names are strings
        cleaned_df.columns = [str(col) for col in cleaned_df.columns]
        
        # List of reserved column names by Streamlit data_editor
        reserved_names = [
            '_index', '_selected_rows', '_selected_row_indices', 
            '_selection', 'index', 'selection'
        ]
        
        # Rename reserved columns
        rename_map = {}
        for col in cleaned_df.columns:
            if col in reserved_names:
                new_name = f"column_{col}"
                rename_map[col] = new_name
        
        if rename_map:
            cleaned_df = cleaned_df.rename(columns=rename_map)
        
        # Reset index to avoid index column issues
        cleaned_df = cleaned_df.reset_index(drop=True)
        
        # Ensure no duplicate column names
        cols = pd.Series(cleaned_df.columns)
        for dup in cols[cols.duplicated()].unique():
            cols[cols == dup] = [f'{dup}_{i}' if i != 0 else dup for i in range(sum(cols == dup))]
        cleaned_df.columns = cols
        
        return cleaned_df
    
    def _safe_compare(self, old_val, new_val):
        """Safely compare two values, handling NaN and different types"""
        try:
            # Handle NaN comparison
            if pd.isna(old_val) and pd.isna(new_val):
                return True
            
            # Handle None comparison
            if old_val is None and new_val is None:
                return True
            
            # Try direct comparison
            return old_val == new_val
        except:
            # If comparison fails, convert to strings
            try:
                return str(old_val) == str(new_val)
            except:
                return False
    
    def save_state(self):
        """Save current state to history for undo/redo"""
        # Remove any states after current index (when user undid then made new changes)
        self.history = self.history[:self.history_index + 1]
        
        # Add current state
        self.history.append({
            'df': self.df.copy(),
            'modified_cells': self.modified_cells.copy(),
            'renamed_columns': self.renamed_columns.copy(),
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
        st.session_state[f'{self.key}_modified_cells'] = self.modified_cells
        st.session_state[f'{self.key}_renamed_columns'] = self.renamed_columns
    
    def undo(self):
        """Undo last change"""
        if self.history_index > 0:
            self.history_index -= 1
            state = self.history[self.history_index]
            self.df = state['df'].copy()
            self.modified_cells = state['modified_cells'].copy()
            self.renamed_columns = state['renamed_columns'].copy()
            
            # Update session state
            st.session_state[f'{self.key}_history_index'] = self.history_index
            st.session_state[f'{self.key}_modified_cells'] = self.modified_cells
            st.session_state[f'{self.key}_renamed_columns'] = self.renamed_columns
            
            return True
        return False
    
    def redo(self):
        """Redo last undone change"""
        if self.history_index < len(self.history) - 1:
            self.history_index += 1
            state = self.history[self.history_index]
            self.df = state['df'].copy()
            self.modified_cells = state['modified_cells'].copy()
            self.renamed_columns = state['renamed_columns'].copy()
            
            # Update session state
            st.session_state[f'{self.key}_history_index'] = self.history_index
            st.session_state[f'{self.key}_modified_cells'] = self.modified_cells
            st.session_state[f'{self.key}_renamed_columns'] = self.renamed_columns
            
            return True
        return False
    
    def revert_all(self):
        """Revert to original data"""
        self.df = self.original_df.copy()
        self.modified_cells = set()
        self.renamed_columns = {}
        self.history = []
        self.history_index = -1
        
        # Clear confirmation state
        st.session_state[f'{self.key}_confirm_revert'] = False
        
        # Update all session state keys
        st.session_state[f'{self.key}_history'] = []
        st.session_state[f'{self.key}_history_index'] = -1
        st.session_state[f'{self.key}_modified_cells'] = set()
        st.session_state[f'{self.key}_renamed_columns'] = {}
    
    def get_changes_summary(self):
        """Get summary of changes made"""
        summary = {
            'modified_cells': len(self.modified_cells),
            'modified_rows': len(set(row for row, col in self.modified_cells)),
            'modified_columns': len(set(col for row, col in self.modified_cells)),
            'renamed_columns': len(self.renamed_columns)
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
            confirm_revert = st.session_state.get(f"{self.key}_confirm_revert", False)
            if st.button("Reset All", key=f"{self.key}_revert",
                        help="Discard all changes and revert to original"):
                if confirm_revert:
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
            show_rename = st.session_state.get(f"{self.key}_show_rename", False)
            if st.button("Rename Columns", key=f"{self.key}_rename_cols",
                        help="Rename table columns"):
                st.session_state[f"{self.key}_show_rename"] = not show_rename
                st.rerun()
        
        with col6:
            changes = self.get_changes_summary()
            if changes['modified_cells'] > 0 or changes['renamed_columns'] > 0:
                changes_text = []
                if changes['modified_cells'] > 0:
                    changes_text.append(f"{changes['modified_cells']} cells edited")
                if changes['renamed_columns'] > 0:
                    changes_text.append(f"{changes['renamed_columns']} columns renamed")
                st.info(", ".join(changes_text))
            else:
                st.caption("No changes yet")
    
    def render_column_rename_section(self):
        """Render column renaming interface"""
        show_rename = st.session_state.get(f"{self.key}_show_rename", False)
        if not show_rename:
            return
        
        st.markdown("---")
        st.markdown("### Rename Columns")
        
        with st.expander("Column Names Editor", expanded=True):
            st.caption("Change column names below. Press Enter to save each change.")
            
            # Display current column names with rename fields
            for i, col in enumerate(self.df.columns):
                col1, col2, col3 = st.columns([2, 4, 1])
                
                with col1:
                    st.text(f"Column {i+1}:")
                
                with col2:
                    new_name = st.text_input(
                        "New name:",
                        value=col,
                        key=f"{self.key}_rename_{col}",
                        label_visibility="collapsed"
                    )
                
                with col3:
                    if new_name and new_name != col:
                        if st.button("Apply", key=f"{self.key}_apply_{col}"):
                            if self.rename_column(col, new_name):
                                st.success(f"Renamed '{col}' to '{new_name}'")
                                st.rerun()
                            else:
                                st.error(f"Cannot rename to '{new_name}' - name already exists")
            
            # Add new column option
            st.markdown("---")
            st.markdown("**Add New Column**")
            
            col_a, col_b = st.columns([3, 1])
            with col_a:
                new_col_name = st.text_input(
                    "New column name:",
                    placeholder="Enter new column name",
                    key=f"{self.key}_new_col"
                )
            
            with col_b:
                if st.button("Add Column", key=f"{self.key}_add_col"):
                    if new_col_name and new_col_name not in self.df.columns:
                        self.add_column(new_col_name)
                        st.success(f"Added column '{new_col_name}'")
                        st.rerun()
                    elif new_col_name in self.df.columns:
                        st.error(f"Column '{new_col_name}' already exists")
            
            # Delete column option
            st.markdown("**Delete Column**")
            col_to_delete = st.selectbox(
                "Select column to delete:",
                [""] + list(self.df.columns),
                key=f"{self.key}_delete_select"
            )
            
            if col_to_delete:
                if st.button("Delete Column", type="secondary", key=f"{self.key}_delete_btn"):
                    if self.delete_column(col_to_delete):
                        st.success(f"Deleted column '{col_to_delete}'")
                        st.rerun()
        
        st.markdown("---")
    
    def render_search_box(self):
        """Render search functionality"""
        show_search = st.session_state.get(f"{self.key}_show_search", False)
        if not show_search:
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
                    return matches
                else:
                    st.info("No matches found")
        
        return None
    
    def search(self, term, column="All columns", case_sensitive=False):
        """Search table for term with safe regex handling"""
        matches = []
        
        if not term:
            return matches
        
        # Escape regex special characters to avoid errors
        try:
            escaped_term = re.escape(term)
        except:
            escaped_term = term
        
        if column == "All columns":
            search_cols = self.df.columns
        else:
            search_cols = [column]
        
        for col in search_cols:
            try:
                # Convert column to string for safe searching
                col_data = self.df[col].astype(str)
                
                if case_sensitive:
                    mask = col_data.str.contains(escaped_term, na=False, regex=True)
                else:
                    mask = col_data.str.contains(escaped_term, case=False, na=False, regex=True)
                
                matching_indices = self.df[mask].index.tolist()
                for idx in matching_indices:
                    matches.append((idx, col))
            except re.error:
                # If regex fails, do simple string search
                col_data = self.df[col].astype(str)
                if case_sensitive:
                    mask = col_data.str.contains(term, na=False, regex=False)
                else:
                    mask = col_data.str.lower().str.contains(term.lower(), na=False, regex=False)
                
                matching_indices = self.df[mask].index.tolist()
                for idx in matching_indices:
                    matches.append((idx, col))
            except Exception:
                # Skip columns that can't be searched
                continue
        
        return matches
    
    def add_row(self):
        """Add new empty row"""
        new_row = pd.Series([None] * len(self.df.columns), index=self.df.columns)
        self.df = pd.concat([self.df, pd.DataFrame([new_row])], ignore_index=True)
        self.save_state()
        st.rerun()
    
    def add_column(self, col_name):
        """Add new column"""
        if col_name and col_name not in self.df.columns:
            self.df[col_name] = None
            self.renamed_columns[col_name] = f"Added: {col_name}"
            self.save_state()
            return True
        return False
    
    def rename_column(self, old_name, new_name):
        """Rename column"""
        if new_name and new_name != old_name and new_name not in self.df.columns:
            # Track the rename in our dictionary
            if old_name not in self.renamed_columns:
                self.renamed_columns[old_name] = new_name
            else:
                # Update the rename chain
                original_name = old_name
                for key, value in self.renamed_columns.items():
                    if value == old_name:
                        original_name = key
                        break
                self.renamed_columns[original_name] = new_name
            
            # Actually rename the column
            self.df = self.df.rename(columns={old_name: new_name})
            self.save_state()
            return True
        return False
    
    def delete_column(self, col_name):
        """Delete column"""
        if col_name in self.df.columns:
            # Remove from renamed columns tracking if present
            if col_name in self.renamed_columns:
                del self.renamed_columns[col_name]
            
            # Actually delete the column
            self.df = self.df.drop(columns=[col_name])
            self.save_state()
            return True
        return False
    
    def render(self):
        """Render the interactive table"""
        # Render toolbar
        self.render_toolbar()
        
        # Render column rename section if active
        self.render_column_rename_section()
        
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
            # Create column configuration
            column_config = {}
            for col in self.df.columns:
                column_config[col] = st.column_config.Column(
                    col,
                    help=f"Edit values in {col} column"
                )
            
            edited_df = st.data_editor(
                self.df,
                use_container_width=True,
                num_rows="dynamic",
                key=f"{self.key}_editor",
                height=400,
                column_config=column_config
            )
            
            # Safely detect changes
            try:
                if not edited_df.equals(self.df):
                    # Find what changed
                    for col in self.df.columns:
                        if col in edited_df.columns:
                            for idx in range(len(self.df)):
                                old_val = self.df.at[idx, col]
                                new_val = edited_df.at[idx, col]
                                
                                if not self._safe_compare(old_val, new_val):
                                    self.modified_cells.add((idx, col))
                    
                    self.df = edited_df.copy()
                    self.save_state()
            except Exception as e:
                # If change detection fails, assume changes were made
                st.warning("Change detection failed, but changes may have been made")
                self.df = edited_df.copy()
                self.save_state()
            
            # Update session state
            st.session_state[f'{self.key}_modified_cells'] = self.modified_cells
            st.session_state[f'{self.key}_renamed_columns'] = self.renamed_columns
            
            return self.df
            
        except Exception as e:
            st.error(f"Error rendering table editor: {type(e).__name__} - {str(e)}")
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
    try:
        table = InteractiveTable(df, key=key)
        return table.render()
    except Exception as e:
        st.error(f"Error creating interactive table: {type(e).__name__} - {str(e)}")
        with st.expander("Error Details"):
            st.code(str(e))
        st.info("Showing read-only view instead...")
        st.dataframe(df, use_container_width=True, height=400)
        return df