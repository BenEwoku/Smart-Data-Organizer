"""
Simple AI Orchestrator
"""
import pandas as pd
from typing import Dict, List, Any
from .free_ai import FreeAIEngine

class AIOrchestrator:
    """Simple AI orchestrator"""
    
    def __init__(self):
        self.ai_engine = FreeAIEngine()
    
    def process(self, text: str, features: List[str]) -> Dict[str, Any]:
        """Process text with selected features"""
        results = {
            "original_text": text[:500] + "..." if len(text) > 500 else text,
            "features": {},
            "dataframe": None
        }
        
        # Execute each feature
        for feature in features:
            feature_result = self.ai_engine.analyze_text(text, feature)
            results["features"][feature] = feature_result
            
            # Store dataframe if extraction was successful
            if feature == "extract" and feature_result.get("success"):
                data = feature_result.get("data", {})
                results["dataframe"] = data.get("dataframe")
        
        return results