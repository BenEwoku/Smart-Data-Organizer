"""
100% Free AI Engine using Hugging Face Inference API (with Local Fallback)
"""
import requests
import json
import re
import time
from typing import Dict, Any, Optional
import pandas as pd

class FreeAIEngine:
    """Free AI engine using Hugging Face with local fallback"""
    
    def __init__(self):
        # Try to get token from secrets
        try:
            import streamlit as st
            self.hf_token = st.secrets.get("HF_TOKEN", None)
        except:
            self.hf_token = None
        
        # Fallback models (free tier - prioritize smaller models)
        self.models = [
            "facebook/mbart-large-50-many-to-many-mmt",  # Best for translation (Chinese→English)
            "google/flan-t5-small",                      # Good for extraction/summarization
            "t5-small",                                  # Lightweight
            "sshleifer/distilbart-cnn-12-6"              # Summarization
        ]
        
        self.current_model = 0
    
    def analyze_text(self, text: str, task: str = "extract") -> Dict[str, Any]:
        """Process text with AI"""
        
        start_time = time.time()
        
        try:
            prompt = self._generate_prompt(text[:2000], task)  # Limit input
            
            # First, try Hugging Face if token is available
            if self.hf_token:
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
            
            # If no token or all models failed, use local processing
            return self._local_fallback_processing(text, task, start_time)
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "provider": "local_fallback",
                "processing_time": time.time() - start_time
            }
    
    def _call_huggingface(self, model: str, prompt: str) -> Dict:
        """Call Hugging Face API with better error handling"""
        try:
            # Remove any extra spaces from the model name
            model = model.strip()
            
            headers = {"Authorization": f"Bearer {self.hf_token}"} if self.hf_token else {}
            
            response = requests.post(
                f"https://api-inference.huggingface.co/models/{model}",
                headers=headers,
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
            
            elif response.status_code == 401:
                return {"success": False, "error": "Authentication failed. Check your HF token."}
            
            else:
                return {"success": False, "error": f"HTTP {response.status_code}: {response.text}"}
                
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
            
            "translate": f"""Translate this text to English. If the text is already in English, return it as is.

Text:
{text}

Translation in English:""",
            
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
    
    def _local_fallback_processing(self, text: str, task: str, start_time: float) -> Dict:
        """Fallback processing when Hugging Face fails"""
        
        if task == "extract":
            # Simple regex-based table extraction
            df = self._simple_table_extraction(text)
            if df is not None:
                return {
                    "success": True,
                    "provider": "local_fallback",
                    "model": "regex_extractor",
                    "processing_time": time.time() - start_time,
                    "content": "Extracted data using local processing",
                    "dataframe": df,
                    "data": df.to_dict("records")
                }
        
        elif task == "summarize":
            # Simple summarization - first 3 sentences
            sentences = re.split(r'[.!?]+', text)
            summary = " ".join(sentences[:3]) + "..." if len(sentences) > 3 else text
            return {
                "success": True,
                "provider": "local_fallback",
                "model": "simple_summarizer",
                "processing_time": time.time() - start_time,
                "content": summary,
                "data": {"text": summary}
            }
        
        elif task == "translate":
            # Return original text as translation (no actual translation)
            # You can add a placeholder or use langdetect here
            return {
                "success": True,
                "provider": "local_fallback",
                "model": "passthrough",
                "processing_time": time.time() - start_time,
                "content": f"[TRANSLATION NOT AVAILABLE LOCALLY]\n\nOriginal text:\n{text}",
                "data": {"text": f"[TRANSLATION NOT AVAILABLE LOCALLY]\n\nOriginal text:\n{text}"}
            }
        
        elif task == "insights":
            # Generate simple insights
            word_count = len(text.split())
            char_count = len(text)
            line_count = text.count('\n') + 1
            
            insights = f"Text Analysis:\n- Word count: {word_count}\n- Character count: {char_count}\n- Line count: {line_count}"
            return {
                "success": True,
                "provider": "local_fallback",
                "model": "basic_analyzer",
                "processing_time": time.time() - start_time,
                "content": insights,
                "data": {"text": insights}
            }
        
        return {
            "success": False,
            "error": "Local fallback not implemented for this task",
            "provider": "local_fallback",
            "processing_time": time.time() - start_time
        }
    
    def _simple_table_extraction(self, text: str) -> Optional[pd.DataFrame]:
        """Simple regex-based table extraction"""
        try:
            # Look for comma-separated values
            lines = text.split('\n')
            rows = []
            
            # Find header row (first line with commas or pipes)
            header_row = None
            for i, line in enumerate(lines):
                if ',' in line or '|' in line:
                    header_row = i
                    break
            
            if header_row is None:
                return None
            
            # Extract headers
            header_line = lines[header_row]
            if ',' in header_line:
                headers = [h.strip() for h in header_line.split(',')]
            elif '|' in header_line:
                headers = [h.strip() for h in header_line.split('|') if h.strip()]
            else:
                return None
            
            # Extract data rows
            for line in lines[header_row + 1:]:
                if ',' in line:
                    row = [r.strip() for r in line.split(',')]
                    if len(row) == len(headers):
                        rows.append(row)
                elif '|' in line:
                    row = [r.strip() for r in line.split('|') if r.strip()]
                    if len(row) == len(headers):
                        rows.append(row)
            
            if rows:
                return pd.DataFrame(rows, columns=headers)
            
        except:
            pass
        
        return None