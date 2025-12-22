"""
Local AI Pattern Detector - No APIs needed
Uses statistical analysis and pattern matching
"""
import re
import pandas as pd
import numpy as np
from collections import Counter, defaultdict
from typing import Dict, List, Tuple, Any, Optional
import json
from datetime import datetime

class SmartPatternDetector:
    """Intelligent pattern detection using local algorithms"""
    
    def __init__(self):
        # Load pattern knowledge base
        self.patterns = self._load_pattern_knowledge()
        self.entity_cache = {}
        
    def _load_pattern_knowledge(self) -> Dict:
        """Load comprehensive pattern knowledge"""
        return {
            'data_types': {
                'date': [
                    r'\b\d{4}[-/]\d{2}[-/]\d{2}\b',
                    r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b',
                    r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{1,2},?\s+\d{4}\b',
                    r'\b(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)\b',
                ],
                'currency': [
                    r'\$\s?\d{1,3}(?:,\d{3})*(?:\.\d{2})?\b',
                    r'\b\d+(?:\.\d{2})?\s?(?:USD|EUR|GBP|JPY|CAD|AUD)\b',
                    r'\b\d+(?:,\d{3})*(?:\.\d{2})?\s?dollars?\b',
                ],
                'email': [
                    r'[\w\.-]+@[\w\.-]+\.\w+',
                    r'[\w\.-]+@[\w\.-]+\.\w+\.\w+',  # For .co.uk etc
                ],
                'phone': [
                    r'(\+\d{1,3}[-\.\s]?)?\(?\d{3}\)?[-\.\s]?\d{3}[-\.\s]?\d{4}\b',
                    r'\b\d{3}[-.]\d{3}[-.]\d{4}\b',
                    r'\b\(\d{3}\)\s?\d{3}[-.]\d{4}\b',
                ],
                'url': [
                    r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+',
                    r'www\.[-\w.]+\.[a-z]{2,}',
                ],
                'number': [
                    r'\b\d+(?:,\d{3})*(?:\.\d+)?\b',
                    r'\b\d*\.\d+\b',
                ],
                'percentage': [
                    r'\b\d+(?:\.\d+)?%\b',
                    r'\b\d+(?:\.\d+)?\s?percent\b',
                ],
                'zip_code': [
                    r'\b\d{5}(?:-\d{4})?\b',
                ],
                'ssn': [
                    r'\b\d{3}[-]?\d{2}[-]?\d{4}\b',
                ],
                'ip_address': [
                    r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b',
                ],
            },
            'business_patterns': {
                'invoice': ['invoice', 'bill', 'receipt', 'statement', 'payment'],
                'customer': ['customer', 'client', 'buyer', 'purchaser'],
                'product': ['product', 'item', 'sku', 'code', 'description'],
                'financial': ['amount', 'total', 'subtotal', 'tax', 'discount'],
                'contact': ['name', 'email', 'phone', 'address', 'contact'],
                'date_related': ['date', 'time', 'due', 'created', 'updated'],
            },
            'separators': {
                'common': ['\t', '  ', '|', ',', ';'],
                'weighted': {
                    '\t': 1.0,    # Strong table indicator
                    '  ': 0.8,    # Fixed-width tables
                    '|': 0.7,     # Pipe-separated
                    ',': 0.5,     # CSV
                    ';': 0.4,     # European CSV
                }
            }
        }
    
    def analyze_text(self, text: str) -> Dict[str, Any]:
        """
        Comprehensive text analysis using local AI
        """
        analysis = {
            'metadata': {
                'length': len(text),
                'lines': text.count('\n') + 1,
                'words': len(text.split()),
                'characters': len(text),
                'timestamp': datetime.now().isoformat(),
            },
            'patterns': {},
            'structure': {},
            'quality': {},
            'suggestions': []
        }
        
        # Detect all patterns
        for pattern_type, regex_list in self.patterns['data_types'].items():
            matches = []
            for regex in regex_list:
                matches.extend(re.findall(regex, text, re.IGNORECASE))
            if matches:
                analysis['patterns'][pattern_type] = {
                    'count': len(matches),
                    'examples': list(set(matches))[:5],
                    'density': len(matches) / max(1, len(text.split()))
                }
        
        # Detect structure
        analysis['structure'] = self._detect_structure(text)
        
        # Calculate quality score
        analysis['quality'] = self._calculate_quality(text, analysis)
        
        # Generate suggestions
        analysis['suggestions'] = self._generate_suggestions(analysis)
        
        return analysis
    
    def _detect_structure(self, text: str) -> Dict[str, Any]:
        """Detect the underlying data structure"""
        lines = [line.rstrip() for line in text.split('\n') if line.strip()]
        
        if not lines:
            return {'type': 'empty', 'confidence': 0}
        
        scores = {
            'tabular': self._score_tabular(lines),
            'key_value': self._score_key_value(lines),
            'list': self._score_list(lines),
            'paragraph': self._score_paragraph(lines),
            'mixed': self._score_mixed(lines),
        }
        
        # Find best match
        best_type = max(scores.items(), key=lambda x: x[1])
        
        structure = {
            'type': best_type[0],
            'confidence': best_type[1],
            'scores': scores,
            'line_count': len(lines),
            'estimated_rows': self._estimate_rows(lines, best_type[0]),
        }
        
        # Add structure-specific details
        if best_type[0] == 'tabular':
            structure.update(self._analyze_tabular(lines))
        elif best_type[0] == 'key_value':
            structure.update(self._analyze_key_value(lines))
        
        return structure
    
    def _score_tabular(self, lines: List[str]) -> float:
        """Score how tabular the data is"""
        if len(lines) < 2:
            return 0.0
        
        # Try different separators
        separator_scores = []
        for sep, weight in self.patterns['separators']['weighted'].items():
            column_counts = []
            for line in lines[:20]:  # Sample first 20 lines
                parts = [p.strip() for p in line.split(sep) if p.strip()]
                if len(parts) >= 2:
                    column_counts.append(len(parts))
            
            if column_counts:
                # Calculate consistency
                if len(set(column_counts)) == 1:
                    consistency = 1.0
                else:
                    mean_cols = np.mean(column_counts)
                    std_cols = np.std(column_counts)
                    consistency = max(0, 1 - (std_cols / mean_cols))
                
                separator_scores.append(consistency * weight)
        
        return max(separator_scores) if separator_scores else 0.0
    
    def _score_key_value(self, lines: List[str]) -> float:
        """Score for key-value pairs"""
        kv_patterns = [
            r'^[A-Za-z][A-Za-z\s]*[:=]\s*.+$',      # key: value
            r'^[A-Za-z\s]+\s+[-–]\s+.+$',           # key - value
            r'^[A-Za-z\s]+\s+\.+\s+.+$',            # key ..... value
            r'^[A-Za-z]+\s*=\s*.+$',                # key=value
        ]
        
        kv_count = 0
        total = min(50, len(lines))
        
        for line in lines[:total]:
            line = line.strip()
            if not line:
                continue
            for pattern in kv_patterns:
                if re.match(pattern, line, re.IGNORECASE):
                    kv_count += 1
                    break
        
        return kv_count / total if total > 0 else 0.0
    
    def _score_list(self, lines: List[str]) -> float:
        """Score for list structure"""
        list_patterns = [
            r'^\s*[\d•\-*+]\s+.+$',          # Numbered or bulleted
            r'^\s*\d+\.\s+.+$',              # 1. Item
            r'^\s*[a-z]\)\s+.+$',            # a) Item
            r'^\s*\[[x\s]\]\s+.+$',          # [ ] or [x] checklist
        ]
        
        list_count = 0
        total = min(50, len(lines))
        
        for line in lines[:total]:
            line = line.strip()
            if not line:
                continue
            for pattern in list_patterns:
                if re.match(pattern, line, re.IGNORECASE):
                    list_count += 1
                    break
        
        return list_count / total if total > 0 else 0.0
    
    def _analyze_tabular(self, lines: List[str]) -> Dict[str, Any]:
        """Detailed analysis of tabular data"""
        # Find best separator
        best_sep = None
        best_score = 0
        column_counts = {}
        
        for sep, weight in self.patterns['separators']['weighted'].items():
            counts = []
            for line in lines[:20]:
                parts = [p.strip() for p in line.split(sep) if p.strip()]
                if len(parts) >= 2:
                    counts.append(len(parts))
            
            if counts:
                consistency = 1 - (np.std(counts) / np.mean(counts)) if np.mean(counts) > 0 else 0
                score = consistency * weight
                if score > best_score:
                    best_score = score
                    best_sep = sep
                    column_counts = counts
        
        # Estimate headers
        headers = []
        if best_sep and lines:
            # Look for header in first few lines
            for i in range(min(3, len(lines))):
                parts = [p.strip() for p in lines[i].split(best_sep) if p.strip()]
                if len(parts) >= 2:
                    # Check if this looks like a header (not too many numbers)
                    num_count = sum(1 for p in parts if re.match(r'^\d', p))
                    if num_count / len(parts) < 0.5:
                        headers = parts
                        header_line = i
                        break
        
        return {
            'separator': best_sep,
            'estimated_columns': int(np.median(column_counts)) if column_counts else 0,
            'headers_found': bool(headers),
            'header_line': header_line if 'header_line' in locals() else None,
            'suggested_headers': headers,
        }
    
    def extract_to_dataframe(self, text: str) -> pd.DataFrame:
        """Extract structured data from text into DataFrame"""
        analysis = self.analyze_text(text)
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        
        if not lines:
            return pd.DataFrame()
        
        structure = analysis['structure']
        
        if structure['type'] == 'tabular' and 'separator' in structure:
            sep = structure['separator']
            
            # Find data start (skip header if found)
            start_idx = structure.get('header_line', 0) + 1 if structure.get('headers_found') else 0
            
            # Extract data
            data = []
            for line in lines[start_idx:]:
                parts = [p.strip() for p in line.split(sep) if p.strip()]
                if parts:
                    data.append(parts)
            
            # Use suggested headers or create generic ones
            if structure.get('suggested_headers'):
                headers = structure['suggested_headers']
                # Ensure header count matches data
                if data and len(data[0]) != len(headers):
                    # Pad or truncate headers
                    if len(data[0]) > len(headers):
                        headers.extend([f'Column_{i}' for i in range(len(headers), len(data[0]))])
                    else:
                        headers = headers[:len(data[0])]
            else:
                # Create generic headers
                max_cols = max(len(row) for row in data) if data else 0
                headers = [f'Column_{i+1}' for i in range(max_cols)]
            
            # Create DataFrame
            df = pd.DataFrame(data, columns=headers)
            
            # Clean and infer types
            df = self._clean_dataframe(df)
            
            return df
        
        elif structure['type'] == 'key_value':
            # Extract key-value pairs
            data = {}
            for line in lines:
                # Try different key-value patterns
                for pattern in [':', '=', '-', '–']:
                    if pattern in line:
                        parts = line.split(pattern, 1)
                        if len(parts) == 2:
                            key = parts[0].strip()
                            value = parts[1].strip()
                            if key not in data:
                                data[key] = []
                            data[key].append(value)
                            break
            
            # Create DataFrame
            if data:
                max_len = max(len(v) for v in data.values())
                for key in data:
                    data[key] = data[key] + [''] * (max_len - len(data[key]))
                df = pd.DataFrame(data)
                return self._clean_dataframe(df)
        
        # Fallback: Create simple DataFrame
        return pd.DataFrame({'Content': lines})
    
    def _clean_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and infer types in DataFrame"""
        df_clean = df.copy()
        
        for col in df_clean.columns:
            # Try to infer and convert types
            df_clean[col] = self._infer_and_convert(df_clean[col])
            
            # Clean strings
            if df_clean[col].dtype == 'object':
                df_clean[col] = df_clean[col].astype(str).str.strip()
        
        return df_clean
    
    def _infer_and_convert(self, series: pd.Series) -> pd.Series:
        """Infer and convert data types"""
        # Skip if too many nulls
        if series.isna().all():
            return series
        
        # Try numeric
        try:
            numeric = pd.to_numeric(series, errors='coerce')
            if numeric.notna().sum() > len(series) * 0.8:  # 80% success rate
                return numeric
        except:
            pass
        
        # Try datetime
        try:
            datetime_series = pd.to_datetime(series, errors='coerce')
            if datetime_series.notna().sum() > len(series) * 0.7:  # 70% success rate
                return datetime_series
        except:
            pass
        
        # Keep as string
        return series.astype(str).str.strip()