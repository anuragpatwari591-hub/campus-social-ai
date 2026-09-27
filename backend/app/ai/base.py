"""
AI provider abstraction.

Every AI feature in the app (text generation, image generation, stickers,
moderation, embeddings for recommendations) goes through this interface
instead of calling a specific vendor SDK directly. That means:

  1. The provider can be swapped (mock -> OpenAI -> Anthropic -> anything
     else) by changing one environment variable, with zero changes to the
     routers or frontend.
  2. API keys live only in backend environment variables (app.config),
     never in frontend JavaScript.
  3. A demo/viva can always run offline via MockAIProvider, with no API key
     and no external network dependency.
"""
from abc import ABC, abstractmethod


class AIProvider(ABC):
    name: str = "base"

    @abstractmethod
    def generate_text(self, prompt: str, style: str = "casual", max_words: int = 60) -> str:
        ...

    @abstractmethod
    def generate_image(self, prompt: str) -> str:
        """Returns a URL (or data URL) for the generated image."""
        ...

    @abstractmethod
    def generate_sticker(self, prompt: str) -> str:
        ...

    @abstractmethod
    def moderate_content(self, text: str) -> dict:
        """Returns {'flagged': bool, 'categories': [...], 'reason': str}."""
        ...

    @abstractmethod
    def generate_embedding(self, text: str) -> list[float]:
        """Returns a small numeric vector used for content-similarity features."""
        ...
