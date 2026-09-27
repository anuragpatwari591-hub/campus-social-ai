from functools import lru_cache

from app.config import get_settings
from app.ai.base import AIProvider
from app.ai.mock_provider import MockAIProvider

settings = get_settings()


@lru_cache
def get_ai_provider() -> AIProvider:
    if settings.AI_PROVIDER == "openai" and settings.AI_API_KEY:
        from app.ai.openai_provider import OpenAIProvider
        return OpenAIProvider()
    # Default: works offline, no API key required.
    return MockAIProvider()
