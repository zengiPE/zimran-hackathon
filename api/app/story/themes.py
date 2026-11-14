"""Case themes: characters, setting, incident and clue style.

The engine (api/engine) decides *what is true*; a theme only supplies names and flavor.
Every theme has exactly 5 suspects, 5 rooms, 5 time slots and 5 items so the engine can
build a 5x5 Einstein-style grid (it may use the first N of each list for smaller cases).

The product UI is in English (US audience), so all player-facing strings are English.
Tone rule from the spec: the hook is about friends, not murder - incidents are mishaps.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Suspect:
    name: str  # unique within the theme; the solver works with these strings
    role: str  # one line shown on the suspect card
    trait: str  # flavor for the narrator, never used as evidence


@dataclass(frozen=True)
class ClueFormat:
    """An in-world document a clue can be written as."""

    key: str
    label: str  # shown above the clue, e.g. "Text message"
    # Used when the LLM is unavailable or its text fails validation.
    # Placeholders: {statement} (the canonical fact sentence), {witness}.
    template: str


@dataclass(frozen=True)
class Theme:
    id: str
    title: str
    tagline: str  # one line for the Create screen
    setting: str  # 2-3 sentences of public backstory everyone reads on day 1
    # Public hook. Placeholders: {room}, {time}. The culprit is whoever was in that room then.
    incident: str
    suspects: tuple[Suspect, ...]
    rooms: tuple[str, ...]
    times: tuple[str, ...]  # ordered, earliest first: the engine relies on this order
    items: tuple[str, ...]
    # People who are NOT suspects; they sign clues ("Text from Rosa, the caretaker").
    witnesses: tuple[str, ...]
    formats: tuple[ClueFormat, ...]
    voice: str  # style guide for the narrator prompt
    tags: tuple[str, ...] = field(default=())
    # Rooms that take "on" instead of "in" ("on the Porch"); used by at_room().
    on_rooms: frozenset[str] = field(default=frozenset())

    def at_room(self, room: str) -> str:
        """Grammatical location for engine statements: 'in the Kitchen', 'on the Porch'."""
        return f"{'on' if room in self.on_rooms else 'in'} the {room}"

    def intro(self, room: str, time: str) -> str:
        return f"{self.setting}\n\n{self.incident.format(room=room, time=time)}"

    @property
    def suspect_names(self) -> tuple[str, ...]:
        return tuple(s.name for s in self.suspects)


LAKE_HOUSE = Theme(
    id="lake-house",
    title="The Lake House Weekend",
    tagline="Five old friends, one rented cabin, and a very expensive accident.",
    setting=(
        "Five college friends rented a cabin on Lake Wendell for their first reunion in "
        "years. Saturday night was supposed to be easy: grill, cards, too much rosé. "
        "By Sunday morning nobody would admit to anything."
    ),
    incident=(
        "The owner's prized 1970s record player was found smashed in the {room}. "
        "The downstairs clock stopped when it fell: {time}. Whoever was in the {room} "
        "at {time} broke it."
    ),
    suspects=(
        Suspect("Maya", "The planner who booked the cabin", "keeps a color-coded itinerary"),
        Suspect("Jordan", "The ex-roommate who never grew up", "challenges everyone to bets"),
        Suspect("Priya", "The doctor on call all weekend", "always checking her phone"),
        Suspect("Leo", "The guy who brought his guitar", "plays the same three songs"),
        Suspect("Sam", "The newcomer, someone's plus-one", "too polite to say no to anything"),
    ),
    rooms=("Kitchen", "Boathouse", "Sunroom", "Loft", "Porch"),
    times=("7:00 PM", "7:30 PM", "8:00 PM", "8:30 PM", "9:00 PM"),
    items=("a flashlight", "a bottle of rosé", "a fishing rod", "a deck of cards", "a guitar"),
    witnesses=("Rosa, the caretaker", "Mr. Dunn from the next cabin", "the pizza delivery guy"),
    formats=(
        ClueFormat("text", "Text message", "Text from {witness}: \"{statement}\""),
        ClueFormat("guestbook", "Guestbook entry", "Scribbled in the cabin guestbook: {statement}"),
        ClueFormat("receipt", "Receipt note", "Handwritten on the back of a gas-station receipt: {statement}"),
        ClueFormat("overheard", "Overheard on the dock", "{witness} remembers: \"{statement}\""),
        ClueFormat("photo", "Photo caption", "Caption on a blurry group-chat photo: {statement}"),
    ),
    voice=(
        "Warm, teasing, nostalgic. Inside jokes between old friends, summer-night details "
        "(crickets, wet towels, citronella). Light comedy, never dark or violent."
    ),
    tags=("cozy", "friends"),
    on_rooms=frozenset({"Porch"}),
)

OFFICE_PARTY = Theme(
    id="office-party",
    title="The Office Holiday Party",
    tagline="Open bar, Secret Santa, and one gingerbread disaster.",
    setting=(
        "Brightline Logistics threw its holiday party on the 12th floor. HR spent three "
        "weeks on a four-foot gingerbread replica of headquarters. It did not survive the night."
    ),
    incident=(
        "The gingerbread headquarters was found crushed in the {room}. The security camera "
        "glitched, but its timestamp froze at {time}. Whoever was in the {room} at {time} did it."
    ),
    suspects=(
        Suspect("Dana", "Head of HR, built the gingerbread", "runs on spreadsheets and cocoa"),
        Suspect("Marcus", "Sales lead, loudest laugh on the floor", "never misses an open bar"),
        Suspect("Ellie", "The intern everyone likes", "volunteers for everything"),
        Suspect("Raj", "IT guy, quietly runs the building", "knows where every camera points"),
        Suspect("Tom", "The VP who 'pops by'", "gives speeches nobody asked for"),
    ),
    rooms=("Break Room", "Conference Room", "Rooftop", "Copy Room", "Lobby"),
    times=("6:00 PM", "6:30 PM", "7:00 PM", "7:30 PM", "8:00 PM"),
    items=("a karaoke mic", "a Secret Santa gift", "a stapler", "a cup of eggnog", "a reindeer sweater"),
    witnesses=("Gloria at the front desk", "the night cleaner", "the caterer"),
    formats=(
        ClueFormat("slack", "Slack message", "#random, from {witness}: \"{statement}\""),
        ClueFormat("badge", "Badge-reader log", "Badge-reader log, annotated by security: {statement}"),
        ClueFormat("expense", "Expense report note", "Note attached to an expense report: {statement}"),
        ClueFormat("overheard", "Overheard at the coffee machine", "{witness} swears: \"{statement}\""),
        ClueFormat("calendar", "Calendar invite", "Calendar invite description, edited at midnight: {statement}"),
    ),
    voice=(
        "Dry workplace comedy: passive-aggressive emails, corporate jargon, holiday cheer "
        "forced by HR. Affectionate, never mean, never dark or violent."
    ),
    tags=("comedy", "work"),
    on_rooms=frozenset({"Rooftop"}),
)

THEMES: dict[str, Theme] = {t.id: t for t in (LAKE_HOUSE, OFFICE_PARTY)}


def get_theme(theme_id: str) -> Theme:
    try:
        return THEMES[theme_id]
    except KeyError:
        raise ValueError(f"unknown theme {theme_id!r}; expected one of {sorted(THEMES)}") from None
