"""Build a case: hidden truth, a minimal set of clues, and the split by player and day.

Guarantees, checked by analyze() for every case we hand out:
  unique      all clues together leave exactly one possible culprit
  no_solo     no single player's clues identify the culprit
  all_needed  without any one player's clues the culprit is not identified
  last_day    the culprit only becomes identifiable on the final day
  truthful    every clue holds in the hidden true world
"""

from __future__ import annotations

import random

import numpy as np

from app.engine.facts import KIND_WEIGHT, Fact, true_facts
from app.engine.solver import ATTRS, WorldSpace, world_space
from app.engine.themes import THEMES

FILLER_KINDS = ("not", "either", "unlink", "before", "before_link", "after_link")


class GenerationError(RuntimeError):
    pass


class _Masks:
    """Caches clue masks; a mask over 1.7M worlds is computed once per fact."""

    def __init__(self, w: WorldSpace) -> None:
        self.w = w
        self.cache: dict[Fact, np.ndarray] = {}

    def __call__(self, f: Fact) -> np.ndarray:
        m = self.cache.get(f)
        if m is None:
            m = self.cache[f] = f.mask(self.w)
        return m

    def all_of(self, facts: list[Fact]) -> np.ndarray:
        out = self.w.all()
        for f in facts:
            out &= self(f)
        return out


def _core(rng: random.Random, pool: list[Fact], masks: _Masks, crime_room: int) -> list[Fact]:
    """Greedy weak-first selection until the culprit is unique, then drop redundant clues.

    The result is minimal: removing any single clue makes the culprit ambiguous.
    """
    w = masks.w
    ordered = sorted(pool, key=lambda f: rng.random() * KIND_WEIGHT[f.kind])
    cur = w.all()
    cur_count = int(cur.sum())
    chosen: list[Fact] = []
    for f in ordered:
        m = masks(f)
        if len(w.culprits(m, crime_room)) < 2:
            continue  # gives the answer away on its own
        new = cur & m
        new_count = int(new.sum())
        if new_count == cur_count:
            continue  # adds nothing
        chosen.append(f)
        cur, cur_count = new, new_count
        if len(w.culprits(cur, crime_room)) == 1:
            break
    else:
        raise GenerationError("pool cannot pin down the culprit")

    order = list(range(len(chosen)))
    rng.shuffle(order)
    keep = set(range(len(chosen)))
    for i in order:
        rest = [chosen[j] for j in keep if j != i]
        if len(w.culprits(masks.all_of(rest), crime_room)) == 1:
            keep.discard(i)
    return [chosen[j] for j in sorted(keep)]


def analyze(w: WorldSpace, crime_room: int, culprit: int, truth_index: int,
            grid: list[list[Fact]], masks: _Masks | None = None) -> dict:
    """Check the guarantees for a grid[player][day] of facts."""
    masks = masks or _Masks(w)
    players = len(grid)
    days = len(grid[0])
    per_player = [masks.all_of(row) for row in grid]
    everything = w.all()
    for m in per_player:
        everything &= m

    final = w.culprits(everything, crime_room)
    solo = [len(w.culprits(m, crime_room)) for m in per_player]
    without = []
    for p in range(players):
        m = w.all()
        for q in range(players):
            if q != p:
                m &= per_player[q]
        without.append(len(w.culprits(m, crime_room)))
    by_day = []
    cum = w.all()
    for d in range(days):
        for p in range(players):
            cum &= masks(grid[p][d])
        by_day.append(len(w.culprits(cum, crime_room)))
    truthful = all(bool(masks(f)[truth_index]) for row in grid for f in row)

    checks = {
        "unique": final == [culprit],
        "no_solo": min(solo) >= 2,
        "all_needed": min(without) >= 2,
        "last_day": by_day[-1] == 1 and (days < 2 or by_day[-2] >= 2),
        "truthful": truthful,
    }
    return {
        "ok": all(checks.values()),
        "checks": checks,
        "solo_candidates": solo,
        "without_player_candidates": without,
        "candidates_by_day": by_day,
        "worlds_total": w.size,
        "worlds_left": int(everything.sum()),
    }


def _partition(rng: random.Random, core: list[Fact], fillers: list[Fact], players: int,
               days: int) -> list[list[Fact]] | None:
    """Spread core clues so every player holds one and the last day holds one; fill the rest."""
    slots = [(p, d) for p in range(players) for d in range(days)]
    grid: list[list[Fact | None]] = [[None] * days for _ in range(players)]
    core = core[:]
    rng.shuffle(core)
    order = list(range(players))
    rng.shuffle(order)
    for i, p in enumerate(order):
        d = days - 1 if i == 0 else rng.randrange(days)
        grid[p][d] = core[i]
    free = [(p, d) for p, d in slots if grid[p][d] is None]
    rng.shuffle(free)
    for f in core[players:]:
        p, d = free.pop()
        grid[p][d] = f
    if len(fillers) < len(free):
        return None
    for (p, d), f in zip(free, rng.sample(fillers, len(free))):
        grid[p][d] = f
    return grid  # type: ignore[return-value]


def generate_case(seed: int, players: int, days: int, suspects: int = 5,
                  theme: str = "lake_house", max_attempts: int = 60) -> dict:
    if theme not in THEMES:
        raise ValueError(f"unknown theme {theme}")
    if not 3 <= players <= 6:
        raise ValueError("players must be 3..6")
    if not 2 <= days <= 5:
        raise ValueError("days must be 2..5")
    if suspects not in (4, 5):
        raise ValueError("suspects must be 4 or 5")
    if suspects == 4 and players * days > 16:
        raise ValueError("4 suspects support at most 16 clues; use 5")

    rng = random.Random(seed)
    w = world_space(suspects)
    th = THEMES[theme]
    cast = rng.sample(th["suspects"], suspects)
    labels = {
        "room": rng.sample(th["rooms"], suspects),
        "time": sorted(rng.sample(range(len(th["times"])), suspects)),
        "item": rng.sample(th["items"], suspects),
    }
    labels["time"] = [th["times"][i] for i in labels["time"]]
    names = [c["name"] for c in cast]

    for _ in range(max_attempts):
        truth = {a: rng.sample(range(suspects), suspects) for a in ATTRS}
        crime_room = rng.randrange(suspects)
        culprit = truth["room"].index(crime_room)
        truth_index = w.world_index(truth)
        masks = _Masks(w)
        pool = true_facts(truth, suspects)
        try:
            core = _core(rng, pool, masks, crime_room)
        except GenerationError:
            continue
        if not players <= len(core) <= players * days:
            continue
        core_set = set(core)
        fillers = [f for f in pool if f.kind in FILLER_KINDS and f not in core_set]
        fillers = [f for f in fillers if len(w.culprits(masks(f), crime_room)) >= 2]
        for _ in range(25):
            grid = _partition(rng, core, fillers, players, days)
            if grid is None:
                break
            report = analyze(w, crime_room, culprit, truth_index, grid, masks)
            if report["ok"]:
                return _assemble(seed, theme, th, cast, names, labels, truth, crime_room,
                                 culprit, grid, core_set, report)
    raise GenerationError(f"no valid case for seed={seed} players={players} days={days}")


def _assemble(seed, theme, th, cast, names, labels, truth, crime_room, culprit, grid,
              core_set, report) -> dict:
    clues = []
    for d in range(len(grid[0])):
        for p in range(len(grid)):
            f = grid[p][d]
            clues.append({
                "id": f"d{d + 1}p{p}",
                "player": p,
                "day": d + 1,
                "fact": f.to_dict(),
                "text": f.text(names, labels),
                "key": f in core_set,
            })
    return {
        "seed": seed,
        "theme": theme,
        "title": th["title"],
        "intro": th["crime"].format(room=labels["room"][crime_room]),
        "players": len(grid),
        "days": len(grid[0]),
        "suspects": [{"id": i, **c} for i, c in enumerate(cast)],
        "labels": labels,
        "crime_room": crime_room,
        "solution": {"culprit": culprit, "truth": truth},
        "clues": clues,
        "report": report,
    }


def explain(case: dict) -> list[dict]:
    """Reveal chain: in unlock order, which suspects each clue ruled out."""
    w = world_space(len(case["suspects"]))
    crime_room = case["crime_room"]
    cum = w.all()
    alive = set(range(w.n))
    chain = []
    for c in sorted(case["clues"], key=lambda c: (c["day"], c["player"])):
        cum &= Fact.from_dict(c["fact"]).mask(w)
        now = set(w.culprits(cum, crime_room))
        chain.append({
            "clue_id": c["id"],
            "day": c["day"],
            "player": c["player"],
            "text": c["text"],
            "eliminated": sorted(alive - now),
            "remaining": sorted(now),
            "worlds_left": int(cum.sum()),
        })
        alive = now
    return chain
