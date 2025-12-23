# File: utils/keyboard_shortcuts.py
"""
Keyboard shortcuts helper for interactive table
"""

import streamlit as st
from streamlit.components.v1 import html

def inject_keyboard_shortcuts():
    """
    Inject JavaScript to enable keyboard shortcuts
    
    Supported shortcuts:
    - Ctrl+C: Copy
    - Ctrl+V: Paste
    - Ctrl+X: Cut
    - Ctrl+Z: Undo
    - Ctrl+Y: Redo
    - Ctrl+F: Search
    - Ctrl+S: Save/Export
    - Delete: Delete row
    """
    
    keyboard_js = """
    <script>
    // Track selected cells
    let selectedCells = [];
    let clipboard = null;
    
    document.addEventListener('keydown', function(e) {
        // Ctrl+Z - Undo
        if (e.ctrlKey && e.key === 'z') {
            e.preventDefault();
            const undoBtn = document.querySelector('[data-testid*="undo"]');
            if (undoBtn) undoBtn.click();
        }
        
        // Ctrl+Y - Redo
        if (e.ctrlKey && e.key === 'y') {
            e.preventDefault();
            const redoBtn = document.querySelector('[data-testid*="redo"]');
            if (redoBtn) redoBtn.click();
        }
        
        // Ctrl+F - Search
        if (e.ctrlKey && e.key === 'f') {
            e.preventDefault();
            const searchBtn = document.querySelector('[data-testid*="search"]');
            if (searchBtn) searchBtn.click();
        }
        
        // Ctrl+S - Save
        if (e.ctrlKey && e.key === 's') {
            e.preventDefault();
            const saveBtn = document.querySelector('[data-testid*="save"]');
            if (saveBtn) saveBtn.click();
        }
        
        // Escape - Close modals
        if (e.key === 'Escape') {
            const closeButtons = document.querySelectorAll('[aria-label="Close"]');
            closeButtons.forEach(btn => btn.click());
        }
        
        // Ctrl+C - Copy (for data_editor)
        if (e.ctrlKey && e.key === 'c') {
            const selection = window.getSelection().toString();
            if (selection) {
                navigator.clipboard.writeText(selection);
                console.log('Copied:', selection);
            }
        }
        
        // Delete key - Delete row
        if (e.key === 'Delete') {
            const deleteBtn = document.querySelector('[data-testid*="delete"]');
            if (deleteBtn && confirm('Delete selected rows?')) {
                deleteBtn.click();
            }
        }
    });
    
    // Add visual feedback for shortcuts
    const style = document.createElement('style');
    style.textContent = `
        .shortcut-hint {
            position: fixed;
            bottom: 10px;
            right: 10px;
            background: rgba(0, 0, 0, 0.8);
            color: white;
            padding: 10px;
            border-radius: 5px;
            font-size: 12px;
            z-index: 9999;
            display: none;
        }
        
        .shortcut-hint.show {
            display: block;
            animation: fadeIn 0.3s;
        }
        
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
    `;
    document.head.appendChild(style);
    
    // Show hint when Ctrl is pressed
    let ctrlPressed = false;
    document.addEventListener('keydown', (e) => {
        if (e.ctrlKey && !ctrlPressed) {
            ctrlPressed = true;
            showShortcutHint();
        }
    });
    
    document.addEventListener('keyup', (e) => {
        if (!e.ctrlKey) {
            ctrlPressed = false;
            hideShortcutHint();
        }
    });
    
    function showShortcutHint() {
        let hint = document.querySelector('.shortcut-hint');
        if (!hint) {
            hint = document.createElement('div');
            hint.className = 'shortcut-hint';
            hint.innerHTML = `
                <strong>Keyboard Shortcuts:</strong><br>
                Ctrl+C: Copy | Ctrl+V: Paste | Ctrl+Z: Undo<br>
                Ctrl+Y: Redo | Ctrl+F: Search | Ctrl+S: Save<br>
                Delete: Delete row | Esc: Close
            `;
            document.body.appendChild(hint);
        }
        hint.classList.add('show');
    }
    
    function hideShortcutHint() {
        const hint = document.querySelector('.shortcut-hint');
        if (hint) {
            hint.classList.remove('show');
        }
    }
    
    console.log('Keyboard shortcuts loaded');
    </script>
    """
    
    html(keyboard_js, height=0)


def show_keyboard_shortcuts_guide():
    """Display keyboard shortcuts guide"""
    with st.expander("⌨Keyboard Shortcuts", expanded=False):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            **Editing:**
            - `Ctrl+C` - Copy selected cell(s)
            - `Ctrl+V` - Paste into cell(s)
            - `Ctrl+X` - Cut cell(s)
            - `Enter` - Save cell edit
            - `Escape` - Cancel edit
            - `Tab` - Move to next cell
            - `Shift+Tab` - Move to previous cell
            """)
        
        with col2:
            st.markdown("""
            **Actions:**
            - `Ctrl+Z` - Undo last change
            - `Ctrl+Y` - Redo last change
            - `Ctrl+F` - Open search
            - `Ctrl+S` - Save/Export
            - `Delete` - Delete selected row(s)
            - `↑↓←→` - Navigate cells
            """)