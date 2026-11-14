"""Case themes: the cast, places, times and objects a case is built from.

Placeholder content: person 3 owns the final copy. The engine only needs
at least 5 entries in every list and a crime sentence with a {room} slot.
Times must be listed in chronological order (clues compare them).
"""

THEMES: dict[str, dict] = {
    "lake_house": {
        "title": "The Lake House Weekend",
        "crime": "Someone smashed the anniversary cake in the {room} the night of the party.",
        "suspects": [
            {"name": "Maya", "role": "the host"},
            {"name": "Ben", "role": "Maya's brother"},
            {"name": "Priya", "role": "the college roommate"},
            {"name": "Leo", "role": "the new boyfriend"},
            {"name": "Ruth", "role": "the neighbor"},
            {"name": "Sam", "role": "the caterer"},
        ],
        "rooms": ["kitchen", "boathouse", "porch", "library", "garage", "attic"],
        "times": ["6:00 pm", "6:30 pm", "7:00 pm", "7:30 pm", "8:00 pm", "8:30 pm"],
        "items": ["flashlight", "wine bottle", "canoe paddle", "camera", "spare key", "umbrella"],
    },
    "office_party": {
        "title": "The Office Holiday Party",
        "crime": "The envelope with everyone's bonus checks vanished from the {room}.",
        "suspects": [
            {"name": "Dana", "role": "the manager"},
            {"name": "Omar", "role": "the intern"},
            {"name": "Kim", "role": "HR"},
            {"name": "Theo", "role": "the sales lead"},
            {"name": "Nina", "role": "IT support"},
            {"name": "Raj", "role": "accounting"},
        ],
        "rooms": ["break room", "server room", "lobby", "copy room", "rooftop", "conference room"],
        "times": ["5:00 pm", "5:30 pm", "6:00 pm", "6:30 pm", "7:00 pm", "7:30 pm"],
        "items": ["badge", "stapler", "coffee mug", "laptop", "umbrella", "gift bag"],
    },
}


def theme_list() -> list[dict]:
    return [{"id": key, "title": t["title"]} for key, t in THEMES.items()]
