import os
import yaml
from pathlib import Path
from typing import Dict, Any, Union
from .exceptions import SecurityError

def safe_read_file(file_path: Union[str, Path], base_dir: Union[str, Path]) -> str:
    """
    Safely reads a file, preventing path traversal attacks.
    Ensures that file_path is within base_dir.
    """
    base_path = Path(base_dir).resolve()
    target_path = (base_path / file_path).resolve()

    # Check if target_path is within base_path
    if not str(target_path).startswith(str(base_path)):
        # Provide limited info in error message for security
        raise SecurityError(f"Access denied: Path is outside the allowed directory.")
    
    if not target_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
        
    try:
        return target_path.read_text(encoding="utf-8")
    except Exception as e:
        raise IOError(f"Error reading file {file_path}: {e}")

def parse_frontmatter(content: str) -> tuple[Dict[str, Any], str]:
    """
    Parses YAML frontmatter from a string.
    Returns (metadata, remaining_content).
    """
    if not content.startswith("---"):
        return {}, content

    try:
        parts = content.split("---", 2)
        if len(parts) < 3:
            return {}, content
        
        frontmatter = parts[1]
        body = parts[2]
        
        metadata = yaml.safe_load(frontmatter)
        if not isinstance(metadata, dict):
            return {}, content
            
        return metadata, body.strip()
    except yaml.YAMLError as e:
        # If YAML parsing fails, treat it as just content? 
        # Or should we raise InvalidSkillError? 
        # For now, let's return empty meta and full content to be safe/lenient,
        # but structured validation in Skill class will catch missing fields.
        return {}, content
