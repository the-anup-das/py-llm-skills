class SkillSDKError(Exception):
    """Base exception for the Skill SDK."""
    pass

class SkillError(SkillSDKError):
    """Base exception for skill-related errors."""
    pass

class InvalidSkillError(SkillError):
    """Raised when a skill definition is invalid (e.g. missing metadata)."""
    pass

class SecurityError(SkillSDKError):
    """Raised when a security violation is detected (e.g. path traversal)."""
    pass

class LLMError(SkillSDKError):
    """Base exception for LLM-related errors."""
    pass
