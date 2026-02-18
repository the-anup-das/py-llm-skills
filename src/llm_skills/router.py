import json
import logging
from typing import List

from .core import Skill, SkillRegistry
from .llm.base import LLMClient

logger = logging.getLogger(__name__)

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
            "Respond ONLY with a JSON list of skill names, e.g. [\"weather\", \"stock-price\"].\n"
            "If no skill is relevant, respond with [].\n\n"
            "Available Skills:\n"
            f"{skill_list_text}"
        )
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": query}
        ]
        
        try:
            # We expect the LLM client to return a dict (e.g. OpenAI format) or specific structure
            # Ideally clients should return a standardized response object, but for MVP we assume raw dict
            response = self.llm_client.chat_completion(messages)
            
            # Extract content - assumes OpenAI structure for now
            # TODO: Abstraction layer for response parsing in LLMClient
            content = ""
            if isinstance(response, dict):
                choices = response.get("choices", [])
                if choices:
                    content = choices[0].get("message", {}).get("content", "")
            else:
                # Handle SDK response object
                content = response.choices[0].message.content

            # Parse JSON
            try:
                # Clean up markdown code blocks if present
                clean_content = content.replace("```json", "").replace("```", "").strip()
                selected_names = json.loads(clean_content)
                
                if not isinstance(selected_names, list):
                    return []
                
                selected_skills = []
                for name in selected_names:
                    skill = registry.get_skill(name)
                    if skill:
                        selected_skills.append(skill)
                        
                return selected_skills
                
            except json.JSONDecodeError:
                logger.error(f"Router failed to parse LLM response: {content}")
                return []
                
        except Exception as e:
            # Fallback or re-raise
            logger.error(f"Router error: {e}")
            return []
