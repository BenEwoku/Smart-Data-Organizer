"""
AI Orchestrator - Coordinates all AI features
"""
import pandas as pd
from typing import Dict, List, Any
from datetime import datetime

class AIOrchestrator:
    """Main AI orchestrator"""
    
    def __init__(self):
        from .free_ai import FreeAIEngine
        self.ai_engine = FreeAIEngine()
        self.history = []
    
    def process(self, text: str, features: List[str]) -> Dict[str, Any]:
        """Process text with selected features"""
        results = {
            "original_text": text[:500] + "..." if len(text) > 500 else text,
            "features": {},
            "dataframe": None,
            "export_formats": {},
            "timestamp": datetime.now().isoformat()
        }
        
        # Execute each feature
        for feature in features:
            feature_result = self.ai_engine.analyze_text(text, feature)
            results["features"][feature] = feature_result
            
            # Store dataframe if extraction was successful
            if feature == "extract" and feature_result.get("success"):
                results["dataframe"] = feature_result.get("dataframe")
        
        # Generate export formats if we have a dataframe
        if results["dataframe"] is not None:
            results["export_formats"] = self._generate_exports(results["dataframe"])
        
        # Add to history
        self.history.append({
            "timestamp": datetime.now(),
            "text_length": len(text),
            "features": features,
            "success_count": sum(1 for r in results["features"].values() if r.get("success"))
        })
        
        return results
    
    def _generate_exports(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Generate export formats"""
        from io import BytesIO
        
        return {
            "csv": df.to_csv(index=False),
            "excel": self._df_to_excel(df),
            "json": df.to_json(orient="records", indent=2)
        }
    
    def _df_to_excel(self, df: pd.DataFrame) -> bytes:
        """Convert DataFrame to Excel bytes"""
        from io import BytesIO
        
        buffer = BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='AI_Data')
        return buffer.getvalue()