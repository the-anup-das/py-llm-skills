import pytest
from unittest.mock import MagicMock, patch
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../src")))

from py_llm_skills.llm.openai import OpenAIRequestClient, OpenAISDKAdapter
from py_llm_skills.llm.claude import AnthropicSkillManager
from py_llm_skills import Skill

@pytest.fixture
def mock_skill():
    return Skill(
        name="test-skill",
        description="test",
        version="1.0",
        instructions="inst",
        input_schema={},
        path="/tmp"
    )

from pydantic import BaseModel

class MockResponseModel(BaseModel):
    reason: str
    confidence: float

class TestOpenAIClients:
    @patch("py_llm_skills.llm.openai.requests.post")
    def test_request_client(self, mock_post):
        mock_response = MagicMock()
        mock_response.json.return_value = {"id": "123"}
        mock_post.return_value = mock_response

        client = OpenAIRequestClient(api_key="sk-test")
        resp = client.chat_completion(messages=[])
        assert resp["id"] == "123"

    @patch("py_llm_skills.llm.openai.requests.post")
    def test_request_client_structured(self, mock_post):
        mock_response = MagicMock()
        # Mock successful JSON response
        mock_response.json.return_value = {
            "choices": [{
                "message": {
                    "content": '{"reason": "test", "confidence": 0.9}'
                }
            }]
        }
        mock_post.return_value = mock_response

        client = OpenAIRequestClient(api_key="sk-test")
        resp = client.chat_completion_with_structure(messages=[], response_model=MockResponseModel)
        
        assert isinstance(resp, MockResponseModel)
        assert resp.reason == "test"
        assert resp.confidence == 0.9

    @patch("py_llm_skills.llm.openai.requests.post")
    def test_request_client_strict_schema(self, mock_post):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": '{"reason": "strict", "confidence": 1.0}'}}]
        }
        mock_post.return_value = mock_response

        client = OpenAIRequestClient(api_key="sk-test")
        client.chat_completion_with_structure(messages=[], response_model=MockResponseModel)
        
        # Verify the payload sent to requests.post
        args, kwargs = mock_post.call_args
        payload = kwargs["json"]
        
        json_schema = payload["response_format"]["json_schema"]["schema"]
        assert json_schema["additionalProperties"] is False
        assert json_schema["properties"]["reason"]["title"] == "Reason" 

    def test_sdk_adapter(self, mock_skill): # mock_skill added just to use fixture if needed, though not used here
        mock_sdk = MagicMock()
        mock_sdk.chat.completions.create.return_value = "mock_response"
        
        client = OpenAISDKAdapter(mock_sdk)
        resp = client.chat_completion(messages=[])
        assert resp == "mock_response"

    def test_sdk_adapter_structured(self):
        mock_sdk = MagicMock()
        # Mock structured output generic response
        expected_obj = MockResponseModel(reason="sdk", confidence=0.8)
        
        mock_completion = MagicMock()
        mock_completion.choices = [MagicMock()]
        mock_completion.choices[0].message.parsed = expected_obj
        
        mock_sdk.beta.chat.completions.parse.return_value = mock_completion
        
        client = OpenAISDKAdapter(mock_sdk)
        resp = client.chat_completion_with_structure(messages=[], response_model=MockResponseModel)
        
        assert resp == expected_obj
        assert resp.reason == "sdk"
        mock_sdk.beta.chat.completions.parse.assert_called_once()

class TestAnthropicManager:
    def test_upload_skill(self, mock_skill):
        mock_client = MagicMock()
        mock_client.beta.skills.create.return_value.id = "skill_123"
        
        manager = AnthropicSkillManager(mock_client)
        # Mock converting skill to files (returns empty list for this test as we don't have real files)
        with patch.object(Skill, 'to_anthropic_files', return_value=[]):
            skill_id = manager.upload_skill(mock_skill)
            
        assert skill_id == "skill_123"
        mock_client.beta.skills.create.assert_called_once()
