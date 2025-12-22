"""
Main AI Orchestrator - Coordinates all local AI components
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Any, Optional
from datetime import datetime
import json

class LocalAIOrchestrator:
    """Orchestrates all local AI components"""
    
    def __init__(self):
        from .ai_patterns import SmartPatternDetector
        from .ai_language import LocalLanguageProcessor
        from .ai_organizer import IntelligentDataOrganizer
        
        self.pattern_detector = SmartPatternDetector()
        self.language_processor = LocalLanguageProcessor()
        self.data_organizer = IntelligentDataOrganizer()
        
    def process_text(self, text: str, options: Dict = None) -> Dict[str, Any]:
        """
        Main processing function for any text input
        """
        if options is None:
            options = {}
        
        start_time = datetime.now()
        
        results = {
            'processing_info': {
                'start_time': start_time.isoformat(),
                'input_length': len(text),
                'options': options
            },
            'language': {},
            'patterns': {},
            'extraction': {},
            'organization': {},
            'export': {},
            'insights': {}
        }
        
        try:
            # Step 1: Language Detection
            lang_code, confidence = self.language_processor.detect_language(text)
            results['language'] = {
                'detected': lang_code,
                'confidence': confidence,
                'method': 'statistical_analysis'
            }
            
            # Step 2: Pattern Analysis
            pattern_analysis = self.pattern_detector.analyze_text(text)
            results['patterns'] = pattern_analysis
            
            # Step 3: Extract to DataFrame
            df = self.pattern_detector.extract_to_dataframe(text)
            results['extraction'] = {
                'success': not df.empty,
                'rows': len(df),
                'columns': len(df.columns),
                'data_preview': df.head(5).to_dict('records') if not df.empty else []
            }
            
            # Step 4: Language-specific processing
            if options.get('translate', False) and lang_code != 'en':
                df = self.language_processor.translate_column_names(df, 'en')
                results['language']['translated_to'] = 'en'
            
            # Step 5: Intelligent Organization
            if not df.empty:
                organization = self.data_organizer.organize_dataframe(df, text[:500])
                results['organization'] = organization
                
                # Get organized DataFrame
                organized_df = organization.get('organized_df', df)
                
                # Step 6: Export formats
                results['export'] = {
                    'csv': organized_df.to_csv(index=False),
                    'excel': self._df_to_excel(organized_df),
                    'json': organized_df.to_json(orient='records', indent=2),
                    'shape': organized_df.shape
                }
                
                # Step 7: Generate insights
                results['insights'] = self._generate_insights(text, organized_df, pattern_analysis)
            
            # Processing complete
            end_time = datetime.now()
            results['processing_info']['end_time'] = end_time.isoformat()
            results['processing_info']['duration_seconds'] = (end_time - start_time).total_seconds()
            results['processing_info']['success'] = True
            
        except Exception as e:
            results['processing_info']['success'] = False
            results['processing_info']['error'] = str(e)
        
        return results
    
    def _df_to_excel(self, df: pd.DataFrame) -> bytes:
        """Convert DataFrame to Excel bytes"""
        from io import BytesIO
        buffer = BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Data')
        return buffer.getvalue()
    
    def _generate_insights(self, text: str, df: pd.DataFrame, pattern_analysis: Dict) -> Dict:
        """Generate insights from processed data"""
        insights = {
            'summary': [],
            'warnings': [],
            'suggestions': [],
            'statistics': {}
        }
        
        if df.empty:
            insights['summary'].append('No structured data could be extracted from the text.')
            return insights
        
        # Basic statistics
        insights['statistics'] = {
            'total_rows': len(df),
            'total_columns': len(df.columns),
            'total_cells': len(df) * len(df.columns),
            'completeness': (df.notna().sum().sum() / (len(df) * len(df.columns))) * 100
        }
        
        # Pattern-based insights
        patterns = pattern_analysis.get('patterns', {})
        if patterns:
            pattern_summary = []
            for pattern_type, data in patterns.items():
                if data['count'] > 0:
                    pattern_summary.append(f"{data['count']} {pattern_type}")
            
            if pattern_summary:
                insights['summary'].append(f"Detected: {', '.join(pattern_summary)}")
        
        # Structure insights
        structure = pattern_analysis.get('structure', {})
        if structure.get('type'):
            insights['summary'].append(f"Structure: {structure['type']} (confidence: {structure['confidence']:.0%})")
        
        # Data quality insights
        null_columns = df.columns[df.isna().any()].tolist()
        if null_columns:
            insights['warnings'].append(f"Missing values found in: {', '.join(null_columns[:3])}")
            if len(null_columns) > 3:
                insights['warnings'][-1] += f" and {len(null_columns) - 3} more columns"
        
        # Column type insights
        type_summary = {}
        for col in df.columns:
            dtype = str(df[col].dtype)
            type_summary[dtype] = type_summary.get(dtype, 0) + 1
        
        if type_summary:
            type_desc = ', '.join([f"{count} {dtype}" for dtype, count in type_summary.items()])
            insights['summary'].append(f"Column types: {type_desc}")
        
        return insights