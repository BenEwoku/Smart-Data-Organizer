"""
100% Free AI Engine using Hugging Face Inference API
"""
import streamlit as st
import requests
import json
import re
import time
from typing import Dict, Any, Optional
import pandas as pd

class FreeAIEngine:
    """Free AI engine using Hugging Face"""
    
    def __init__(self):
        # Try to get token from secrets
        self.hf_token = st.secrets.get("HF_TOKEN", None)
        
        # Fallback models (free tier)
        self.models = [
            "mistralai/Mistral-7B-Instruct-v0.3",  # Fast, good quality
            "meta-llama/Llama-3.2-3B-Instruct",    # Backup
            "google/flan-t5-large"                  # Lightweight fallback
        ]
        
        self.current_model = 0
    
    def analyze_text(self, text: str, task: str = "extract") -> Dict[str, Any]:
        """Process text with AI"""
        
        if not self.hf_token:
            return {
                "success": False,
                "error": "No Hugging Face token configured. Get one free at: https://huggingface.co/settings/tokens",
                "provider": "huggingface"
            }
        
        start_time = time.time()
        
        try:
            prompt = self._generate_prompt(text[:2000], task)  # Limit input
            
            # Try models in order
            for model_name in self.models:
                result = self._call_huggingface(model_name, prompt)
                
                if result["success"]:
                    # Process based on task
                    processed = self._process_response(result["content"], task)
                    
                    return {
                        "success": True,
                        "provider": "huggingface",
                        "model": model_name.split("/")[-1],
                        "processing_time": time.time() - start_time,
                        **processed
                    }
            
            return {
                "success": False,
                "error": "All models failed",
                "provider": "huggingface"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "provider": "huggingface",
                "processing_time": time.time() - start_time
            }
    
    def _call_huggingface(self, model: str, prompt: str) -> Dict:
        """Call Hugging Face API"""
        try:
            response = requests.post(
                f"https://api-inference.huggingface.co/models/{model}",
                headers={"Authorization": f"Bearer {self.hf_token}"},
                json={
                    "inputs": prompt,
                    "parameters": {
                        "max_new_tokens": 500,
                        "temperature": 0.1,
                        "return_full_text": False
                    }
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                
                # Handle different response formats
                if isinstance(result, list) and len(result) > 0:
                    content = result[0].get("generated_text", "")
                elif isinstance(result, dict):
                    content = result.get("generated_text", result.get("output", ""))
                else:
                    content = str(result)
                
                return {"success": True, "content": content}
            
            elif response.status_code == 503:
                # Model loading, wait and retry once
                time.sleep(2)
                return {"success": False, "error": "Model loading"}
            
            else:
                return {"success": False, "error": f"HTTP {response.status_code}"}
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _generate_prompt(self, text: str, task: str) -> str:
        """Generate task-specific prompts"""
        
        prompts = {
            "extract": f"""Extract structured data from this text and output ONLY valid JSON.

Text:
{text}

Output JSON format:
{{"headers": ["column1", "column2"], "rows": [["value1", "value2"]]}}

JSON:""",
            
            "summarize": f"""Summarize this text in 3 concise bullet points:

{text}

Summary:""",
            
            "translate": f"""Translate this text to English:

{text}

Translation:""",
            
            "insights": f"""Analyze this data and provide 3 key insights:

{text}

Insights:"""
        }
        
        return prompts.get(task, prompts["extract"])
    
    def _process_response(self, content: str, task: str) -> Dict:
        """Process AI response"""
        
        if task == "extract":
            df = self._extract_to_dataframe(content)
            return {
                "content": content,
                "dataframe": df,
                "data": df.to_dict("records") if df is not None else []
            }
        
        return {"content": content, "data": {"text": content}}
    
    def _extract_to_dataframe(self, content: str) -> Optional[pd.DataFrame]:
        """Convert JSON response to DataFrame"""
        try:
            # Find JSON in response
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                data = json.loads(json_str)
                
                if "headers" in data and "rows" in data:
                    return pd.DataFrame(data["rows"], columns=data["headers"])
        except:
            pass
        
        return None