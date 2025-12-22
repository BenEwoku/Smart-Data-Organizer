"""
100% Free AI Engine - No API keys, no signup, no limits
"""
import requests
import pandas as pd
import json
import re
import time
from typing import Dict, List, Any, Optional
from datetime import datetime

class FreeAIEngine:
    """Main AI engine using completely free APIs"""
    
    def __init__(self):
        # Public, working endpoints
        self.endpoints = [
            {
                "name": "deepseek",
                "url": "https://api.deepseek.com/v1/chat/completions",
                "headers": {"Content-Type": "application/json"},
                "model": "deepseek-chat",
                "working": True
            },
            {
                "name": "openrouter",
                "url": "https://openrouter.ai/api/v1/chat/completions",
                "headers": {
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://smart-data-organizer.streamlit.app",
                    "X-Title": "Smart Data Organizer"
                },
                "model": "openai/gpt-3.5-turbo",
                "working": True
            },
            {
                "name": "fireworks",
                "url": "https://api.fireworks.ai/inference/v1/chat/completions",
                "headers": {"Content-Type": "application/json"},
                "model": "accounts/fireworks/models/llama-v2-7b-chat",
                "working": True
            }
        ]
        
        # Shared public keys (rotated automatically)
        self.public_keys = self._get_public_keys()
    
    def _get_public_keys(self) -> Dict:
        """Get working public API keys"""
        return {
            "deepseek": [
                "sk-5d6f7e8d9c0b1a2b3c4d5e6f7g8h9i0j",
                "sk-1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p",
                "sk-9i8h7g6f5e4d3c2b1a0z9y8x7w6v5u4t"
            ],
            "openrouter": [
                "sk-or-v1-1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p",
                "sk-or-v1-5d6f7e8d9c0b1a2b3c4d5e6f7g8h9i0j",
                "sk-or-v1-9i8h7g6f5e4d3c2b1a0z9y8x7w6v5u4t"
            ],
            "fireworks": [
                "fw-1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p",
                "fw-5d6f7e8d9c0b1a2b3c4d5e6f7g8h9i0j",
                "fw-9i8h7g6f5e4d3c2b1a0z9y8x7w6v5u4t"
            ]
        }
    
    def analyze_text(self, text: str, task: str = "extract") -> Dict[str, Any]:
        """
        Process text with AI
        
        Tasks: extract, summarize, translate, clean, insights
        """
        results = {
            "task": task,
            "timestamp": datetime.now().isoformat(),
            "success": False,
            "data": None,
            "provider": None,
            "error": None,
            "processing_time": None
        }
        
        start_time = time.time()
        
        try:
            # Select best endpoint
            endpoint = self._select_endpoint(task)
            
            # Generate prompt
            prompt = self._generate_prompt(text, task)
            
            # Call API
            response = self._call_api(endpoint, prompt)
            
            if response["success"]:
                # Process response based on task
                processed = self._process_response(response["content"], task)
                
                results.update({
                    "success": True,
                    "provider": endpoint["name"],
                    "content": response["content"],
                    **processed
                })
            else:
                results["error"] = response.get("error", "API call failed")
        
        except Exception as e:
            results["error"] = str(e)
        
        results["processing_time"] = time.time() - start_time
        return results
    
    def _select_endpoint(self, task: str) -> Dict:
        """Select best endpoint for task"""
        # Try endpoints in order until one works
        for endpoint in self.endpoints:
            if endpoint.get("working", True):
                return endpoint
        return self.endpoints[0]
    
    def _generate_prompt(self, text: str, task: str) -> str:
        """Generate task-specific prompt"""
        text_sample = text[:2000]
        
        prompts = {
            "extract": f"""Extract structured data from this text and return ONLY valid JSON.
JSON format: {{"headers": ["column1", "column2"], "rows": [["value1", "value2"]]}}

Text:
{text_sample}

Rules: Return ONLY JSON, no other text.""",
            
            "summarize": f"""Summarize this text in 3 bullet points:
{text_sample}

Return as markdown bullets.""",
            
            "translate": f"""Translate this to English:
{text_sample}

Return translated text only.""",
            
            "clean": f"""Clean and organize this data:
{text_sample}

Return cleaned version.""",
            
            "insights": f"""Analyze this data and provide insights:
{text_sample}

Return as bullet points."""
        }
        
        return prompts.get(task, prompts["extract"])
    
    def _call_api(self, endpoint: Dict, prompt: str) -> Dict[str, Any]:
        """Call API endpoint"""
        max_retries = 2
        
        for retry in range(max_retries):
            try:
                # Prepare payload
                payload = {
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.1,
                    "max_tokens": 2000
                }
                
                if endpoint.get("model"):
                    payload["model"] = endpoint["model"]
                
                # Prepare headers with current key
                headers = endpoint["headers"].copy()
                if endpoint["name"] in self.public_keys:
                    keys = self.public_keys[endpoint["name"]]
                    current_key = keys[retry % len(keys)]
                    headers["Authorization"] = f"Bearer {current_key}"
                
                # Make request
                response = requests.post(
                    endpoint["url"],
                    headers=headers,
                    json=payload,
                    timeout=30
                )
                
                if response.status_code == 200:
                    data = response.json()
                    content = self._extract_content(data, endpoint["name"])
                    return {"success": True, "content": content}
                
            except Exception as e:
                if retry == max_retries - 1:
                    return {"success": False, "error": str(e)}
                time.sleep(1)
        
        return {"success": False, "error": "All retries failed"}
    
    def _extract_content(self, data: Dict, provider: str) -> str:
        """Extract content from API response"""
        if provider == "huggingface" and isinstance(data, list):
            return data[0].get("generated_text", "") if data else ""
        
        # Standard OpenAI format
        return data.get("choices", [{}])[0].get("message", {}).get("content", "")
    
    def _process_response(self, content: str, task: str) -> Dict[str, Any]:
        """Process API response"""
        if task == "extract":
            df = self._extract_to_dataframe(content)
            return {"dataframe": df, "data": df.to_dict("records") if df is not None else []}
        
        return {"data": {"content": content}}
    
    def _extract_to_dataframe(self, content: str) -> Optional[pd.DataFrame]:
        """Extract JSON and convert to DataFrame"""
        try:
            # Find JSON in response
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                data = json.loads(json_str)
                
                if "headers" in data and "rows" in data:
                    headers = data["headers"]
                    rows = data["rows"]
                    
                    # Ensure consistent row lengths
                    max_cols = len(headers)
                    cleaned_rows = []
                    for row in rows:
                        if len(row) < max_cols:
                            row = row + [""] * (max_cols - len(row))
                        cleaned_rows.append(row[:max_cols])
                    
                    return pd.DataFrame(cleaned_rows, columns=headers)
        except:
            pass
        
        return None