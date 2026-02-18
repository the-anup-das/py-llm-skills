import requests
import json
from typing import List, Dict, Any, Optional, Type, TypeVar
from pydantic import BaseModel
from ..exceptions import LLMError
from .base import LLMClient

T = TypeVar('T', bound=BaseModel)

class OpenAIRequestClient(LLMClient):
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

    def chat_completion_with_structure(self, messages: List[Dict[str, str]], response_model: Type[T]) -> T:
        """
        Request structured JSON output and validate against Pydantic model.
        Uses OpenAI's 'json_schema' response format for strict adherence.
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # Generate JSON schema from Pydantic model
        schema = response_model.model_json_schema()
        
        # Helper to recursively set additionalProperties: False
        def enforce_strict_schema(s: Dict[str, Any]):
            if s.get("type") == "object":
                s["additionalProperties"] = False
                
            properties = s.get("properties", {})
            for prop_name, prop_schema in properties.items():
                enforce_strict_schema(prop_schema)
                
            if "items" in s:
                enforce_strict_schema(s["items"])
                
            # Also handle definitions/$defs if present
            for def_map in [s.get("$defs", {}), s.get("definitions", {})]:
                for def_name, def_schema in def_map.items():
                    enforce_strict_schema(def_schema)

        enforce_strict_schema(schema)
        
        payload = {
            "model": self.model,
            "messages": messages,
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": response_model.__name__,
                    "strict": True,
                    "schema": schema
                }
            }
        }

        try:
            response = requests.post(self.api_url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
            
            content = data["choices"][0]["message"]["content"]
            try:
                # Parse JSON and validate with Pydantic
                json_data = json.loads(content)
                return response_model.model_validate(json_data)
            except (json.JSONDecodeError, ValueError) as e:
                raise LLMError(f"Failed to parse or validate structured output: {e}")
                
        except requests.exceptions.RequestException as e:
            # Handle API errors (e.g. 400 Bad Request if schema is invalid)
            error_msg = f"OpenAI API Request Failed: {e}"
            if e.response is not None:
                try:
                    error_details = e.response.json()
                    error_msg += f" - {json.dumps(error_details)}"
                except:
                    pass
            raise LLMError(error_msg)


class OpenAISDKAdapter(LLMClient):
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

    def chat_completion_with_structure(self, messages: List[Dict[str, str]], response_model: Type[T]) -> T:
        try:
            completion = self.client.beta.chat.completions.parse(
                model=self.model,
                messages=messages,
                response_format=response_model,
            )
            parsed = completion.choices[0].message.parsed
            if not parsed:
                 raise LLMError("OpenAI SDK returned empty parsed response")
            return parsed
        except Exception as e:
            raise LLMError(f"OpenAI SDK Structured Output Error: {e}")
