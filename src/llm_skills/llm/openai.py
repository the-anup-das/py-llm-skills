import requests
import json
from typing import List, Dict, Any, Optional
from ..exceptions import LLMError

class OpenAIRequestClient:
    """
    Lightweight OpenAI Client using requests.
    """
    def __init__(self, api_key: str, model: str = "gpt-4o"):
        self.api_key = api_key
        self.model = model
        self.api_url = "https://api.openai.com/v1/chat/completions"

    def chat_completion(self, messages: List[Dict[str, str]], tools: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.model,
            "messages": messages,
        }
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"
            
        try:
            response = requests.post(self.api_url, headers=headers, json=payload)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise LLMError(f"OpenAI API Request Failed: {e}")

class OpenAISDKAdapter:
    """
    Adapter for the official OpenAI SDK client.
    Assuming the user has 'openai' installed.
    """
    def __init__(self, client, model: str = "gpt-4o"):
        self.client = client
        self.model = model

    def chat_completion(self, messages: List[Dict[str, str]], tools: Optional[List[Dict[str, Any]]] = None) -> Any:
        try:
            kwargs = {
                "model": self.model,
                "messages": messages,
            }
            if tools:
                kwargs["tools"] = tools
                kwargs["tool_choice"] = "auto"
                
            return self.client.chat.completions.create(**kwargs)
        except Exception as e:
            raise LLMError(f"OpenAI SDK Error: {e}")
