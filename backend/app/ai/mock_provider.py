"""
Deterministic, offline AI provider used by default (AI_PROVIDER=mock).

It does not call any external API. It uses simple templates and keyword
rules so the whole AI Creation Studio can be demonstrated in a viva without
an internet connection or an API key, while still producing believably
different output per prompt/style.
"""
import hashlib
import random

from app.ai.base import AIProvider
from app.security.sanitize import contains_flagged_keywords, contains_personal_info

STYLE_TEMPLATES = {
    "funny": ["😂 {p} ... campus chaos, as always.", "Plot twist: {p} 💀🔥"],
    "casual": ["{p} — just another day on campus.", "so, {p}. thoughts?"],
    "professional": ["{p}. Sharing this update with the campus community.", "Announcement: {p}."],
    "genz": ["{p} 💀 no cap fr fr", "ok but {p}... that's actually kind of iconic ✨"],
    "short": ["{p}."],
    "emotional": ["Honestly, {p}. It means a lot to share this here. ❤️", "{p}... still processing this one."],
}

HASHTAG_POOL = [
    "#CampusLife", "#StudentLife", "#TeaTime", "#CollegeDiaries", "#StudyBreak",
    "#CampusVibes", "#Trending", "#College", "#Reels", "#Fest",
]


class MockAIProvider(AIProvider):
    name = "mock"

    def generate_text(self, prompt: str, style: str = "casual", max_words: int = 60) -> str:
        rng = random.Random(hashlib.sha256(f"{prompt}{style}".encode()).hexdigest())
        templates = STYLE_TEMPLATES.get(style, STYLE_TEMPLATES["casual"])
        template = rng.choice(templates)
        text = template.format(p=prompt.strip().rstrip("."))
        words = text.split()
        return " ".join(words[:max_words])

    def generate_image(self, prompt: str) -> str:
        # Deterministic placeholder image so the UI has something to render
        # without any external call. A real provider (see openai_provider.py)
        # returns an actual generated-image URL instead.
        seed = hashlib.sha256(prompt.encode()).hexdigest()[:16]
        return f"https://picsum.photos/seed/{seed}/512/512"

    def generate_sticker(self, prompt: str) -> str:
        seed = hashlib.sha256(("sticker:" + prompt).encode()).hexdigest()[:16]
        return f"https://picsum.photos/seed/{seed}/256/256"

    def moderate_content(self, text: str) -> dict:
        flagged = contains_flagged_keywords(text)
        categories = []
        if flagged:
            categories.append("abusive_language")
        if contains_personal_info(text):
            categories.append("personal_information")
            flagged = True
        return {
            "flagged": flagged,
            "categories": categories,
            "reason": "Matched moderation keyword rules (mock provider)." if flagged else "",
        }

    def generate_embedding(self, text: str) -> list[float]:
        digest = hashlib.sha256(text.lower().encode()).digest()
        return [b / 255.0 for b in digest[:16]]

    def suggest_hashtags(self, prompt: str, n: int = 5) -> list[str]:
        rng = random.Random(hashlib.sha256(prompt.encode()).hexdigest())
        return rng.sample(HASHTAG_POOL, k=min(n, len(HASHTAG_POOL)))
