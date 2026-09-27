"""
Content moderation pipeline:

    Rule-based keyword filter  +  AI moderation provider  +  User reports  +  Admin review

Nothing is auto-deleted purely on an AI/keyword score: matches are flagged
(`is_flagged=True`) and surfaced to moderators, who make the final removal
decision. This mirrors the spec's explicit requirement that high-risk
content stay human-reviewable rather than being silently auto-deleted.
"""
from app.ai import get_ai_provider
from app.security.sanitize import contains_flagged_keywords, contains_personal_info


def evaluate_text(text: str) -> dict:
    provider = get_ai_provider()
    ai_result = provider.moderate_content(text)

    reasons = list(ai_result.get("categories", []))
    if contains_flagged_keywords(text) and "abusive_language" not in reasons:
        reasons.append("abusive_language")
    if contains_personal_info(text) and "personal_information" not in reasons:
        reasons.append("personal_information")

    return {
        "flagged": bool(ai_result.get("flagged")) or bool(reasons),
        "categories": reasons,
    }
