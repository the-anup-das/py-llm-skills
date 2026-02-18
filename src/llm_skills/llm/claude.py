from typing import List, Dict, Any
from ..core import Skill
from ..exceptions import LLMError

class AnthropicSkillManager:
    """
    Helper for managing skills with the Anthropic API (Beta).
    """
    def __init__(self, client):
        self.client = client

    def upload_skill(self, skill: Skill) -> str:
        """
        Uploads a skill to Anthropic API and returns the skill_id.
        """
        try:
            # We assume the client has beta headers enabled for 'skills-2025-10-02'
            # Note: The client logic should handle beta headers globally or per request
            
            # Prepare files for upload
            # skill.to_anthropic_files() returns list of (filename, file_object or content, mime_type)
            # The Anthropic SDK 'files' param expects tuples similar to Requests.
            
            # IMPORTANT: The official SDK might expect actual file objects or tuples.
            # Let's assume tuples are supported as per our plan.
            
            # For simplicity in this MVP, we create the skill via the API
            # Since 'skill.to_anthropic_files()' returns content strings, we might need to wrap inBytesIO
            # if the SDK expects file-like objects. However, creating a dict/struct is often easier.
            
            # Re-reading the plan: we use client.beta.skills.create
            
            # TODO: Handle file content properly. For now, we assume simple text.
            
            # The official SDK usage:
            # client.beta.skills.create(display_title, files=[...])
            
            # We need to construct the files list correctly.
            files_payload = []
            skill_files = skill.to_anthropic_files() # list of (name, content, type)
            
            for fname, fcontent, ftype in skill_files:
                # The SDK usually takes (filename, file_content)
                files_payload.append((fname, fcontent))
                
            response = self.client.beta.skills.create(
                display_title=skill.name,
                description=skill.description,
                files=files_payload,
                betas=["skills-2025-10-02"] 
            )
            return response.id
            
        except Exception as e:
            raise LLMError(f"Failed to upload skill to Anthropic: {e}")

    def format_container_param(self, skill_ids: List[str]) -> Dict[str, Any]:
        """
        Formats the 'container' parameter for message creation.
        """
        skills = []
        for skill_id in skill_ids:
            skills.append({
                "type": "anthropic",
                "skill_id": skill_id,
                "version": "latest"
            })
            
        return {"skills": skills}
