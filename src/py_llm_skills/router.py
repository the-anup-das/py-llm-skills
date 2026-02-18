import logging
from typing import List
from pydantic import BaseModel, Field

from .core import Skill, SkillRegistry
from .llm.base import LLMClient

logger = logging.getLogger(__name__)

class SkillSelectionResponse(BaseModel):
    selected_skills: List[str] = Field(description="List of skill names selected for the query")

class SkillRouter:
    """
    Intelligent router that selects the best skill(s) for a given query
    using a small/fast LLM.
    """
    def __init__(self, llm_client: LLMClient, model: str = "gpt-4o-mini"):
        self.llm_client = llm_client
        self.model = model

    def select_skill(self, query: str, registry: SkillRegistry) -> List[Skill]:
        """
        Selects relevant skills from the registry based on the query.
        """
        available_skills = registry.list_skills()
        if not available_skills:
            return []

        # Construct a prompt with skill descriptions
        skill_list_text = "\n".join([f"- {s.name}: {s.description}" for s in available_skills])
        
        system_prompt = (
            "You are a skill selection assistant. "
            "Your goal is to select the most appropriate skill(s) from the list below to answer the user's query.\n"
            "Respond with a JSON object containing a list of skill names.\n"
            "If no skill is relevant, return an empty list.\n\n"
            "Available Skills:\n"
            f"{skill_list_text}"
        )
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": query}
        ]
        
        try:
            # Use structured output
            response = self.llm_client.chat_completion_with_structure(messages, SkillSelectionResponse)
            
            selected_skills = []
            for name in response.selected_skills:
                skill = registry.get_skill(name)
                if skill:
                    selected_skills.append(skill)
                    
            return selected_skills
                
        except Exception as e:
            logger.error(f"Router error: {e}")
            return []
