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

class TestOpenAIClients:
    @patch("py_llm_skills.llm.openai.requests.post")
    def test_request_client(self, mock_post):
        mock_response = MagicMock()
        mock_response.json.return_value = {"id": "123"}
        mock_post.return_value = mock_response

        client = OpenAIRequestClient(api_key="sk-test")
        resp = client.chat_completion(messages=[])
        assert resp["id"] == "123"

    def test_sdk_adapter(self):
        mock_sdk = MagicMock()
        mock_sdk.chat.completions.create.return_value = "mock_response"
        
        client = OpenAISDKAdapter(mock_sdk)
        resp = client.chat_completion(messages=[])
        assert resp == "mock_response"

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
