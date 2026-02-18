from typing import Dict, Any, List
from .core import Skill

class Patterns:
    """
    Helper class for specific usage patterns.
    """
    
    @staticmethod
    def file_based_prompt(skills: List[Skill]) -> str:
        """
        Returns a system prompt segment containing instructions for all skills.
        Pattern 1: File-based (Context Injection).
        """
        prompt = "You have access to the following skills:\n\n"
        for skill in skills:
            prompt += f"### Skill: {skill.name}\n"
            prompt += f"Description: {skill.description}\n"
            prompt += f"Instructions:\n{skill.instructions}\n\n"
        return prompt

    @staticmethod
    def tool_definitions(skills: List[Skill]) -> List[Dict[str, Any]]:
        """
        Returns a list of tool definitions for API function calling.
        Pattern 2: Tool-based.
        """
        return [skill.to_tool_definition() for skill in skills]
