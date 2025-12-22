"""
Free AI Engine with Local Fallback
"""
import requests
import pandas as pd
import json
import re
import time
from typing import Dict, List, Any, Optional
from datetime import datetime

class FreeAIEngine:
    """AI engine with free APIs and local fallback"""
    
    def __init__(self):
        # Simple endpoints (these might work without keys)
        self.endpoints = [
            {
                "name": "deepseek",
                "url": "https://api.deepseek.com/v1/chat/completions",
                "headers": {"Content-Type": "application/json"},
                "model": "deepseek-chat",
            },
            {
                "name": "fireworks",
                "url": "https://api.fireworks.ai/inference/v1/chat/completions",
                "headers": {"Content-Type": "application/json"},
                "model": "accounts/fireworks/models/llama-v2-7b-chat",
            }
        ]
    
    def analyze_text(self, text: str, task: str = "extract") -> Dict[str, Any]:
        """
        Try free APIs first, then use local extraction
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
        
        # Try free API first
        api_result = self._try_free_api(text, task)
        
        if api_result.get("success"):
            # API succeeded
            results.update({
                "success": True,
                "provider": api_result.get("provider"),
                "content": api_result.get("content"),
                "data": self._process_api_response(api_result.get("content"), task)
            })
        else:
            # API failed, use local extraction
            results.update({
                "success": True,
                "provider": "local",
                "content": "Using local pattern matching",
                "data": self._extract_locally(text, task)
            })
        
        results["processing_time"] = time.time() - start_time
        return results
    
    def _try_free_api(self, text: str, task: str) -> Dict[str, Any]:
        """Try free APIs (limited attempts)"""
        prompt = self._generate_prompt(text, task)
        
        for endpoint in self.endpoints:
            try:
                payload = {
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.1,
                    "max_tokens": 1000
                }
                
                if endpoint.get("model"):
                    payload["model"] = endpoint["model"]
                
                response = requests.post(
                    endpoint["url"],
                    headers=endpoint["headers"],
                    json=payload,
                    timeout=10
                )
                
                if response.status_code == 200:
                    data = response.json()
                    content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                    return {"success": True, "provider": endpoint["name"], "content": content}
            
            except:
                continue
        
        return {"success": False, "error": "All APIs failed"}
    
    def _generate_prompt(self, text: str, task: str) -> str:
        """Generate prompt for API"""
        text_sample = text[:1000]
        
        prompts = {
            "extract": f"Extract structured data from: {text_sample} Return as JSON with headers and rows.",
            "summarize": f"Summarize: {text_sample}",
            "translate": f"Translate to English: {text_sample}",
            "insights": f"Analyze and provide insights: {text_sample}"
        }
        
        return prompts.get(task, prompts["extract"])
    
    def _process_api_response(self, content: str, task: str) -> Dict[str, Any]:
        """Process API response"""
        if task == "extract":
            df = self._parse_json_to_dataframe(content)
            if df is not None:
                return {"dataframe": df, "data": df.to_dict("records")}
        
        return {"content": content}
    
    def _parse_json_to_dataframe(self, content: str) -> Optional[pd.DataFrame]:
        """Try to parse JSON in API response"""
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
    
    def _extract_locally(self, text: str, task: str) -> Dict[str, Any]:
        """
        Local extraction using pattern matching
        Works when APIs fail
        """
        if task == "extract":
            df = self._extract_table_locally(text)
            if df is not None:
                return {"dataframe": df, "data": df.to_dict("records")}
            else:
                return {"dataframe": None, "error": "Could not extract data"}
        
        elif task == "summarize":
            return {"content": self._summarize_locally(text)}
        
        elif task == "translate":
            return {"content": text}  # No translation locally
        
        elif task == "insights":
            return {"content": self._generate_insights_locally(text)}
        
        return {"content": "Task completed locally"}
    
    def _extract_table_locally(self, text: str) -> Optional[pd.DataFrame]:
        """
        Extract table from text using pattern matching
        This works for most common formats
        """
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        
        if not lines:
            return None
        
        # Try different separators
        separators = ['|', '\t', ',', '  ']
        
        for sep in separators:
            # Check if separator is used consistently
            data = []
            max_cols = 0
            
            for line in lines:
                parts = [part.strip() for part in line.split(sep) if part.strip()]
                if parts:
                    data.append(parts)
                    max_cols = max(max_cols, len(parts))
            
            # Need at least 2 rows and consistent columns
            if len(data) >= 2 and all(len(row) == max_cols for row in data):
                # Check if first row looks like headers
                if all(not part.replace('.', '').replace('$', '').isdigit() for part in data[0]):
                    headers = data[0]
                    rows = data[1:]
                else:
                    headers = [f'Column_{i+1}' for i in range(max_cols)]
                    rows = data
                
                return pd.DataFrame(rows, columns=headers)
        
        # If no table found, return as single column
        return pd.DataFrame({'Content': lines})
    
    def _summarize_locally(self, text: str) -> str:
        """Simple local summarization"""
        sentences = text.split('.')
        if len(sentences) <= 3:
            return text
        
        # Take first, middle, and last sentences
        summary_sentences = []
        if sentences:
            summary_sentences.append(sentences[0].strip())
        if len(sentences) > 2:
            summary_sentences.append(sentences[len(sentences)//2].strip())
        if len(sentences) > 1:
            summary_sentences.append(sentences[-1].strip())
        
        return ". ".join(summary_sentences) + "."
    
    def _generate_insights_locally(self, text: str) -> str:
        """Generate simple insights locally"""
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        
        insights = []
        insights.append(f"Text has {len(lines)} lines")
        insights.append(f"Total characters: {len(text)}")
        
        # Count common patterns
        patterns = {
            'dates': r'\d{4}[-/]\d{2}[-/]\d{2}',
            'emails': r'[\w\.-]+@[\w\.-]+\.\w+',
            'currency': r'\$\d+(?:\.\d{2})?',
            'numbers': r'\b\d+\b'
        }
        
        for name, pattern in patterns.items():
            matches = re.findall(pattern, text)
            if matches:
                insights.append(f"Found {len(matches)} {name}")
        
        return "\n".join([f"• {insight}" for insight in insights])