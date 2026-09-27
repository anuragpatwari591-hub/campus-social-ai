"""
Real AI provider backed by the OpenAI-compatible HTTP API.

Deliberately implemented with plain `httpx` calls (already a dependency for
testing) instead of the full vendor SDK, to keep the dependency surface
small and the request/response shape fully visible for a viva walkthrough.

Falls back to raising a clear error if AI_API_KEY is missing -- the caller
(app.ai.get_ai_provider) only constructs this class when a key is present.
"""
import httpx

from app.ai.base import AIProvider
from app.config import get_settings

settings = get_settings()

STYLE_INSTRUCTIONS = {
    "funny": "Make it witty and humorous.",
    "casual": "Keep it casual and friendly.",
    "professional": "Keep it professional and clear.",
    "genz": "Use Gen-Z internet slang and emojis.",
    "short": "Keep it to one short sentence.",
    "emotional": "Make it warm and emotionally genuine.",
}


class OpenAIProvider(AIProvider):
    name = "openai"

    def __init__(self):
        self._client = httpx.Client(
            base_url="https://api.openai.com/v1",
            headers={"Authorization": f"Bearer {settings.AI_API_KEY}"},
            timeout=30,
        )

    def generate_text(self, prompt: str, style: str = "casual", max_words: int = 60) -> str:
        instruction = STYLE_INSTRUCTIONS.get(style, STYLE_INSTRUCTIONS["casual"])
        resp = self._client.post(
            "/chat/completions",
            json={
                "model": settings.AI_TEXT_MODEL,
                "messages": [
                    {"role": "system", "content": f"You write short campus social-media content. {instruction} Max {max_words} words."},
                    {"role": "user", "content": prompt},
                ],
                "max_tokens": 150,
            },
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"].strip()

    def generate_image(self, prompt: str) -> str:
        resp = self._client.post(
            "/images/generations",
            json={"model": settings.AI_IMAGE_MODEL, "prompt": prompt, "n": 1, "size": "512x512"},
        )
        resp.raise_for_status()
        return resp.json()["data"][0]["url"]

    def generate_sticker(self, prompt: str) -> str:
        return self.generate_image(f"A cute sticker-style illustration, transparent background: {prompt}")

    def moderate_content(self, text: str) -> dict:
        resp = self._client.post("/moderations", json={"input": text})
        resp.raise_for_status()
        result = resp.json()["results"][0]
        flagged_categories = [k for k, v in result["categories"].items() if v]
        return {"flagged": result["flagged"], "categories": flagged_categories, "reason": ""}

    def generate_embedding(self, text: str) -> list[float]:
        resp = self._client.post("/embeddings", json={"model": "text-embedding-3-small", "input": text})
        resp.raise_for_status()
        return resp.json()["data"][0]["embedding"]
