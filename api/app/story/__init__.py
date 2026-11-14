"""Story layer (Person 3): themes and clue narration. The engine decides truth; this adds words."""

from app.story.narrative import ClueFact, ClueText, narrate_case, template_clue, validate_text
from app.story.themes import THEMES, Theme, get_theme

__all__ = [
    "THEMES",
    "ClueFact",
    "ClueText",
    "Theme",
    "get_theme",
    "narrate_case",
    "template_clue",
    "validate_text",
]
