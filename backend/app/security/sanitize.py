"""
Input sanitization helpers.

- HTML/script tags are escaped so user text can never execute as HTML/JS in
  another user's browser (stored XSS defense). Content is stored escaped and
  rendered as plain text on the frontend, so no separate "rich text" allowlist
  is required at this project's scope.
- A small keyword-based filter flags obviously abusive content for the
  moderation queue, layered underneath the AI moderation provider.
"""
import html
import re

ABUSE_KEYWORDS = {
    "kill you", "suicide", "self harm", "rape", "terrorist attack",
}

_PHONE_RE = re.compile(r"\b\d{10}\b")
_EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")


def sanitize_text(text: str) -> str:
    """Escape HTML so stored/rendered text can't inject markup or scripts."""
    return html.escape(text.strip())


def contains_flagged_keywords(text: str) -> bool:
    lowered = text.lower()
    return any(keyword in lowered for keyword in ABUSE_KEYWORDS)


def contains_personal_info(text: str) -> bool:
    """Used by moderation to flag posts that leak a phone number/email (privacy risk)."""
    return bool(_PHONE_RE.search(text) or _EMAIL_RE.search(text))
