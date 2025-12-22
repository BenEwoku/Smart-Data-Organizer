"""
Local Language Processing - No APIs needed
"""
import re
import numpy as np
from typing import Dict, List, Tuple, Optional
import json
from collections import defaultdict

class LocalLanguageProcessor:
    """Local language detection and processing"""
    
    def __init__(self):
        self.language_patterns = self._load_language_patterns()
        self.common_terms = self._load_common_terms()
    
    def _load_language_patterns(self) -> Dict:
        """Load language detection patterns"""
        return {
            'en': {  # English
                'common_words': ['the', 'and', 'for', 'are', 'with', 'this', 'that', 'have', 'from'],
                'patterns': [r'\bthe\b', r'\band\b', r'\bfor\b'],
            },
            'es': {  # Spanish
                'common_words': ['el', 'la', 'los', 'las', 'y', 'en', 'de', 'que', 'por'],
                'patterns': [r'\bel\b', r'\bla\b', r'\by\b'],
            },
            'fr': {  # French
                'common_words': ['le', 'la', 'les', 'et', 'en', 'de', 'que', 'pour', 'dans'],
                'patterns': [r'\ble\b', r'\bla\b', r'\bet\b'],
            },
            'de': {  # German
                'common_words': ['der', 'die', 'das', 'und', 'in', 'den', 'von', 'mit', 'sich'],
                'patterns': [r'\bder\b', r'\bdie\b', r'\bund\b'],
            },
        }
    
    def _load_common_terms(self) -> Dict:
        """Load common business terms in multiple languages"""
        return {
            'date': {
                'en': 'date', 'es': 'fecha', 'fr': 'date', 'de': 'datum',
                'it': 'data', 'pt': 'data', 'nl': 'datum', 'ru': 'дата'
            },
            'name': {
                'en': 'name', 'es': 'nombre', 'fr': 'nom', 'de': 'name',
                'it': 'nome', 'pt': 'nome', 'nl': 'naam', 'ru': 'имя'
            },
            'amount': {
                'en': 'amount', 'es': 'cantidad', 'fr': 'montant', 'de': 'betrag',
                'it': 'importo', 'pt': 'quantia', 'nl': 'bedrag', 'ru': 'сумма'
            },
            'total': {
                'en': 'total', 'es': 'total', 'fr': 'total', 'de': 'gesamt',
                'it': 'totale', 'pt': 'total', 'nl': 'totaal', 'ru': 'итого'
            },
            'invoice': {
                'en': 'invoice', 'es': 'factura', 'fr': 'facture', 'de': 'rechnung',
                'it': 'fattura', 'pt': 'fatura', 'nl': 'factuur', 'ru': 'счёт'
            },
        }
    
    def detect_language(self, text: str) -> Tuple[str, float]:
        """
        Detect language using statistical analysis
        Returns: (language_code, confidence)
        """
        words = re.findall(r'\b[a-z]+\b', text.lower())
        if not words:
            return 'en', 0.0
        
        word_counter = Counter(words)
        total_words = len(words)
        
        scores = {}
        for lang_code, lang_data in self.language_patterns.items():
            score = 0
            # Check common words
            for word in lang_data['common_words']:
                if word in word_counter:
                    score += word_counter[word]
            
            # Check patterns
            for pattern in lang_data['patterns']:
                matches = re.findall(pattern, text.lower())
                score += len(matches) * 2
            
            scores[lang_code] = score
        
        # Find best match
        if scores:
            best_lang = max(scores.items(), key=lambda x: x[1])
            confidence = min(best_lang[1] / total_words, 1.0)
            return best_lang[0], confidence
        
        return 'en', 0.0
    
    def translate_column_names(self, df: pd.DataFrame, target_lang: str = 'en') -> pd.DataFrame:
        """Translate column names to target language"""
        df_translated = df.copy()
        
        # Build reverse lookup dictionary
        term_to_lang = {}
        for term, translations in self.common_terms.items():
            for lang, translation in translations.items():
                if lang not in term_to_lang:
                    term_to_lang[lang] = {}
                term_to_lang[lang][translation.lower()] = term
        
        # Translate each column
        new_columns = []
        for col in df.columns:
            col_lower = str(col).lower()
            translated = col
            
            # Try direct translation
            if target_lang in term_to_lang and col_lower in term_to_lang[target_lang]:
                term = term_to_lang[target_lang][col_lower]
                if term in self.common_terms and target_lang in self.common_terms[term]:
                    translated = self.common_terms[term][target_lang]
            else:
                # Try to find similar terms
                for term, translations in self.common_terms.items():
                    for lang, word in translations.items():
                        if word.lower() in col_lower or col_lower in word.lower():
                            if target_lang in translations:
                                translated = translations[target_lang]
                                break
            
            new_columns.append(translated)
        
        df_translated.columns = new_columns
        return df_translated
    
    def extract_entities(self, text: str) -> Dict[str, List[str]]:
        """Extract named entities using pattern matching"""
        entities = {
            'dates': [],
            'emails': [],
            'phones': [],
            'urls': [],
            'amounts': [],
            'names': [],
        }
        
        # Date patterns
        date_patterns = [
            r'\b\d{4}[-/]\d{2}[-/]\d{2}\b',
            r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b',
            r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{1,2},?\s+\d{4}\b',
        ]
        
        # Email patterns
        email_patterns = [r'[\w\.-]+@[\w\.-]+\.\w+']
        
        # Phone patterns
        phone_patterns = [
            r'(\+\d{1,3}[-\.\s]?)?\(?\d{3}\)?[-\.\s]?\d{3}[-\.\s]?\d{4}\b',
            r'\b\d{3}[-.]\d{3}[-.]\d{4}\b',
        ]
        
        # Extract using patterns
        entities['dates'] = re.findall('|'.join(date_patterns), text, re.IGNORECASE)
        entities['emails'] = re.findall('|'.join(email_patterns), text, re.IGNORECASE)
        entities['phones'] = re.findall('|'.join(phone_patterns), text, re.IGNORECASE)
        
        # Currency amounts
        currency_patterns = [
            r'\$\s?\d{1,3}(?:,\d{3})*(?:\.\d{2})?\b',
            r'\b\d+(?:\.\d{2})?\s?(?:USD|EUR|GBP)\b',
        ]
        entities['amounts'] = re.findall('|'.join(currency_patterns), text, re.IGNORECASE)
        
        # Simple name extraction (capitalized words in certain positions)
        name_patterns = [
            r'\b(?:Mr\.?|Mrs\.?|Ms\.?|Dr\.?|Prof\.?)\s+[A-Z][a-z]+\s+[A-Z][a-z]+\b',
            r'\b[A-Z][a-z]+\s+[A-Z][a-z]+\b',  # First Last
        ]
        entities['names'] = re.findall('|'.join(name_patterns), text)
        
        return entities