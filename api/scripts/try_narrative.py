"""Manual check of the narrator prompt against the real model.

Usage (from api/, with ANTHROPIC_API_KEY in api/.env):
    uv run python -m scripts.try_narrative [lake-house|office-party]

Prints each clue with its source: "llm" if Claude's text passed validation, otherwise
"template" plus the reason. One run = one Claude call (a few cents at most).
"""

import logging
import sys

from app.story import ClueFact, get_theme, narrate_case, validate_text


def sample_facts(theme_id: str) -> list[ClueFact]:
    t = get_theme(theme_id)
    s, r, tm, i = t.suspect_names, t.rooms, t.times, t.items
    return [
        ClueFact("f1", f"{s[0]} was not {t.at_room(r[0])}.", (s[0], r[0])),
        ClueFact("f2", f"Whoever had {i[2]} arrived before {s[3]}.", (i[2], s[3])),
        ClueFact("f3", f"{s[1]} had {i[4]}.", (s[1], i[4])),
        ClueFact("f4", f"Either {s[2]} or {s[4]} was {t.at_room(r[4])} at {tm[3]}.", (s[2], s[4], r[4], tm[3])),
        ClueFact("f5", f"Nobody {t.at_room(r[1])} had {i[0]}.", (r[1], i[0])),
    ]


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    theme = get_theme(sys.argv[1] if len(sys.argv) > 1 else "lake-house")
    facts = sample_facts(theme.id)
    clues = narrate_case(theme, facts)
    llm_texts = {c.fact_id: c.text for c in clues if c.source == "llm"}
    for fact, clue in zip(facts, clues):
        print(f"\n[{clue.source}] {clue.format_label}")
        print(f"  {clue.text}")
        print(f"  fact: {clue.statement}")
        if clue.source == "template" and fact.id not in llm_texts:
            print(f"  (template; validator would say: {validate_text(theme, fact, clue.text) or 'ok'})")
    used = sum(c.source == "llm" for c in clues)
    print(f"\n{used}/{len(clues)} clues from Claude, the rest from templates.")


if __name__ == "__main__":
    main()
