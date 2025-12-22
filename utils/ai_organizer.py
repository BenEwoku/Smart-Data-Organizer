"""
Intelligent Data Organizer - Local AI
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Any, Optional
import re
from collections import Counter
from scipy import stats

class IntelligentDataOrganizer:
    """Organize data intelligently using local AI"""
    
    def __init__(self):
        self.domain_knowledge = self._load_domain_knowledge()
        self.data_rules = self._load_data_rules()
    
    def _load_domain_knowledge(self) -> Dict:
        """Load domain-specific knowledge"""
        return {
            'finance': {
                'key_columns': ['date', 'amount', 'description', 'category', 'balance'],
                'patterns': ['$', 'USD', 'transaction', 'debit', 'credit'],
                'suggested_formats': {
                    'date': 'YYYY-MM-DD',
                    'amount': 'decimal(10,2)',
                    'category': 'categorical'
                }
            },
            'inventory': {
                'key_columns': ['item', 'sku', 'quantity', 'price', 'location'],
                'patterns': ['qty', 'stock', 'warehouse', 'inventory'],
                'suggested_formats': {
                    'sku': 'string',
                    'quantity': 'integer',
                    'price': 'decimal(10,2)'
                }
            },
            'contacts': {
                'key_columns': ['name', 'email', 'phone', 'address', 'company'],
                'patterns': ['@', 'email', 'phone', 'street', 'avenue'],
                'suggested_formats': {
                    'email': 'email',
                    'phone': 'phone',
                    'name': 'string'
                }
            },
            'sales': {
                'key_columns': ['date', 'customer', 'product', 'quantity', 'revenue'],
                'patterns': ['sale', 'order', 'purchase', 'customer', 'product'],
                'suggested_formats': {
                    'date': 'YYYY-MM-DD',
                    'revenue': 'decimal(10,2)',
                    'quantity': 'integer'
                }
            }
        }
    
    def organize_dataframe(self, df: pd.DataFrame, context: str = None) -> Dict[str, Any]:
        """Intelligently organize a DataFrame"""
        
        analysis = {
            'original_shape': df.shape,
            'column_analysis': {},
            'suggestions': [],
            'transformations': [],
            'quality_metrics': {},
            'organized_df': df.copy()
        }
        
        # Analyze each column
        for col in df.columns:
            col_analysis = self._analyze_column(df[col], col)
            analysis['column_analysis'][col] = col_analysis
            
            # Generate suggestions
            col_suggestions = self._suggest_column_improvements(col, df[col], col_analysis)
            analysis['suggestions'].extend(col_suggestions)
        
        # Detect domain
        domain = self._detect_domain(df, context)
        analysis['detected_domain'] = domain
        
        # Quality metrics
        analysis['quality_metrics'] = self._calculate_quality_metrics(df)
        
        # Apply automatic improvements
        if analysis['suggestions']:
            df_improved = self._apply_improvements(df, analysis['suggestions'])
            analysis['organized_df'] = df_improved
        
        # Generate summary
        analysis['summary'] = self._generate_summary(analysis)
        
        return analysis
    
    def _analyze_column(self, series: pd.Series, col_name: str) -> Dict[str, Any]:
        """Analyze a single column"""
        
        # Basic statistics
        non_null = series.dropna()
        total_count = len(series)
        non_null_count = len(non_null)
        
        analysis = {
            'name': col_name,
            'original_dtype': str(series.dtype),
            'total_values': total_count,
            'non_null_values': non_null_count,
            'null_percentage': (total_count - non_null_count) / total_count * 100,
            'unique_values': series.nunique(),
            'inferred_type': self._infer_type(series),
            'sample_values': non_null.head(5).tolist() if not non_null.empty else [],
        }
        
        # Type-specific analysis
        inferred_type = analysis['inferred_type']
        if inferred_type == 'numeric':
            analysis.update(self._analyze_numeric(series))
        elif inferred_type == 'datetime':
            analysis.update(self._analyze_datetime(series))
        elif inferred_type == 'categorical':
            analysis.update(self._analyze_categorical(series))
        
        # Pattern detection
        analysis['patterns'] = self._detect_column_patterns(series, col_name)
        
        return analysis
    
    def _infer_type(self, series: pd.Series) -> str:
        """Infer the true data type"""
        if series.empty:
            return 'unknown'
        
        # Try numeric
        try:
            numeric = pd.to_numeric(series, errors='coerce')
            if numeric.notna().sum() > len(series) * 0.9:
                return 'numeric'
        except:
            pass
        
        # Try datetime
        try:
            datetime_series = pd.to_datetime(series, errors='coerce')
            if datetime_series.notna().sum() > len(series) * 0.7:
                return 'datetime'
        except:
            pass
        
        # Check for categorical
        unique_ratio = series.nunique() / len(series)
        if unique_ratio < 0.3 and series.nunique() < 100:
            return 'categorical'
        
        # Check for boolean
        if series.dropna().isin([True, False, 'true', 'false', 'yes', 'no', '1', '0']).all():
            return 'boolean'
        
        return 'text'
    
    def _detect_column_patterns(self, series: pd.Series, col_name: str) -> List[str]:
        """Detect patterns in column data"""
        patterns = []
        col_lower = col_name.lower()
        sample = series.dropna().head(20).astype(str)
        
        # Column name patterns
        if any(word in col_lower for word in ['date', 'time', 'created', 'updated']):
            patterns.append('likely_date')
        if any(word in col_lower for word in ['email', 'mail']):
            patterns.append('likely_email')
        if any(word in col_lower for word in ['phone', 'tel', 'mobile']):
            patterns.append('likely_phone')
        if any(word in col_lower for word in ['amount', 'price', 'cost', 'total']):
            patterns.append('likely_currency')
        if any(word in col_lower for word in ['name', 'first', 'last', 'full']):
            patterns.append('likely_name')
        
        # Data content patterns
        if not sample.empty:
            # Check for email patterns
            if sample.str.contains('@').any():
                patterns.append('contains_emails')
            
            # Check for URL patterns
            if sample.str.contains('http').any():
                patterns.append('contains_urls')
            
            # Check for phone patterns
            phone_pattern = r'\b\d{3}[-.]\d{3}[-.]\d{4}\b'
            if sample.str.contains(phone_pattern).any():
                patterns.append('contains_phones')
            
            # Check for consistent formatting
            if len(set(sample.str.len())) == 1:
                patterns.append('fixed_length')
        
        return patterns
    
    def _suggest_column_improvements(self, col_name: str, series: pd.Series, analysis: Dict) -> List[Dict]:
        """Suggest improvements for a column"""
        suggestions = []
        
        # 1. Rename suggestions
        better_name = self._suggest_better_name(col_name, series, analysis)
        if better_name and better_name != col_name:
            suggestions.append({
                'type': 'rename',
                'column': col_name,
                'suggestion': better_name,
                'reason': f'"{better_name}" better describes the content',
                'priority': 'high'
            })
        
        # 2. Data type conversion
        current_type = analysis['inferred_type']
        if current_type == 'text' and 'likely_date' in analysis.get('patterns', []):
            suggestions.append({
                'type': 'convert',
                'column': col_name,
                'suggestion': 'Convert to datetime',
                'reason': 'Text appears to contain dates',
                'priority': 'medium'
            })
        
        # 3. Handle missing values
        if analysis['null_percentage'] > 20:
            fill_method = self._suggest_fill_method(series, analysis)
            suggestions.append({
                'type': 'fill_missing',
                'column': col_name,
                'suggestion': f'Fill missing values using {fill_method}',
                'reason': f'{analysis["null_percentage"]:.1f}% of values are missing',
                'priority': 'high'
            })
        
        # 4. Standardize format
        if 'contains_emails' in analysis.get('patterns', []):
            suggestions.append({
                'type': 'standardize',
                'column': col_name,
                'suggestion': 'Convert to lowercase and trim',
                'reason': 'Email addresses should be standardized',
                'priority': 'low'
            })
        
        return suggestions
    
    def _suggest_better_name(self, current_name: str, series: pd.Series, analysis: Dict) -> Optional[str]:
        """Suggest a better column name"""
        current_lower = current_name.lower()
        
        # Check patterns for clues
        patterns = analysis.get('patterns', [])
        inferred_type = analysis.get('inferred_type')
        
        if 'likely_date' in patterns or inferred_type == 'datetime':
            return 'date'
        elif 'likely_email' in patterns:
            return 'email'
        elif 'likely_phone' in patterns:
            return 'phone'
        elif 'likely_currency' in patterns or inferred_type == 'numeric':
            # Check if it's a price, amount, or quantity
            sample = series.dropna().head(5).astype(str)
            if sample.str.contains(r'^\$').any():
                return 'price'
            elif 'total' in current_lower or 'amount' in current_lower:
                return 'amount'
            elif 'qty' in current_lower or 'quantity' in current_lower:
                return 'quantity'
            else:
                return 'value'
        elif 'likely_name' in patterns:
            if 'first' in current_lower:
                return 'first_name'
            elif 'last' in current_lower:
                return 'last_name'
            else:
                return 'name'
        
        return None
    
    def _apply_improvements(self, df: pd.DataFrame, suggestions: List[Dict]) -> pd.DataFrame:
        """Apply suggested improvements to DataFrame"""
        df_improved = df.copy()
        
        for suggestion in suggestions:
            if suggestion['type'] == 'rename':
                old_name = suggestion['column']
                new_name = suggestion['suggestion']
                if old_name in df_improved.columns:
                    df_improved = df_improved.rename(columns={old_name: new_name})
        
        return df_improved