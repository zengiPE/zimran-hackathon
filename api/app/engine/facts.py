"""Atomic facts (clues): how each one constrains the worlds and how it reads."""

from __future__ import annotations

from dataclasses import asdict, dataclass

import numpy as np

from app.engine.solver import WorldSpace

# Lower weight = picked earlier when building a case, so weak clues dominate
# and every player ends up holding something the group needs.
KIND_WEIGHT = {
    "not": 1.0,
    "unlink": 1.0,
    "either": 1.2,
    "before": 1.3,
    "before_link": 1.3,
    "after_link": 1.3,
    "link": 2.5,
    "is": 3.0,
}

SUBJECT = {"room": "the person in the {}", "time": "the person who arrived at {}",
           "item": "the person with the {}"}
PRED = {"room": "was in the {}", "time": "arrived at {}", "item": "had the {}"}
NEG = {"room": "was not in the {}", "time": "did not arrive at {}", "item": "did not have the {}"}
EITHER = {"room": "was in either the {} or the {}", "time": "arrived at either {} or {}",
          "item": "had either the {} or the {}"}


@dataclass(frozen=True)
class Fact:
    kind: str
    a: str = ""  # attribute: room | time | item
    s: int = -1  # suspect
    v: int = -1  # value of attribute a
    v2: int = -1  # second value (either) or value of a2 (link/unlink)
    a2: str = ""  # second attribute (link/unlink)
    s2: int = -1  # second suspect (before, before_link, after_link)

    def to_dict(self) -> dict:
        return {k: val for k, val in asdict(self).items() if val not in ("", -1)}

    @classmethod
    def from_dict(cls, d: dict) -> Fact:
        return cls(**d)

    def mask(self, w: WorldSpace) -> np.ndarray:
        V, O = w.values, w.owner
        k = self.kind
        if k == "is":
            return V[self.a][self.s] == self.v
        if k == "not":
            return V[self.a][self.s] != self.v
        if k == "either":
            col = V[self.a][self.s]
            return (col == self.v) | (col == self.v2)
        if k == "link":
            return O[self.a][self.v] == O[self.a2][self.v2]
        if k == "unlink":
            return O[self.a][self.v] != O[self.a2][self.v2]
        if k == "before":
            return V["time"][self.s] < V["time"][self.s2]
        if k in ("before_link", "after_link"):
            t_owner = w.time_of_owner(self.a, self.v)
            t_other = V["time"][self.s2]
            return t_owner < t_other if k == "before_link" else t_owner > t_other
        raise ValueError(f"unknown fact kind {k}")

    def text(self, names: list[str], labels: dict[str, list[str]]) -> str:
        """Plain English sentence. The narrative layer rewrites it; this stays the source of truth."""
        k = self.kind

        def lab(a: str, v: int) -> str:
            return labels[a][v]

        if k == "is":
            out = f"{names[self.s]} {PRED[self.a].format(lab(self.a, self.v))}"
        elif k == "not":
            out = f"{names[self.s]} {NEG[self.a].format(lab(self.a, self.v))}"
        elif k == "either":
            out = f"{names[self.s]} " + EITHER[self.a].format(
                lab(self.a, self.v), lab(self.a, self.v2))
        elif k == "link":
            out = f"{SUBJECT[self.a].format(lab(self.a, self.v))} " + PRED[self.a2].format(
                lab(self.a2, self.v2))
        elif k == "unlink":
            out = f"{SUBJECT[self.a].format(lab(self.a, self.v))} " + NEG[self.a2].format(
                lab(self.a2, self.v2))
        elif k == "before":
            out = f"{names[self.s]} arrived before {names[self.s2]}"
        elif k == "before_link":
            out = f"{SUBJECT[self.a].format(lab(self.a, self.v))} arrived before {names[self.s2]}"
        elif k == "after_link":
            out = f"{SUBJECT[self.a].format(lab(self.a, self.v))} arrived after {names[self.s2]}"
        else:
            raise ValueError(f"unknown fact kind {k}")
        return out[0].upper() + out[1:] + "."


def true_facts(truth: dict[str, list[int]], n: int) -> list[Fact]:
    """Every atomic fact that holds in the true world."""
    owner = {a: {v: s for s, v in enumerate(vals)} for a, vals in truth.items()}
    t = truth["time"]
    facts: list[Fact] = []
    for a in ("room", "time", "item"):
        for s in range(n):
            tv = truth[a][s]
            facts.append(Fact("is", a=a, s=s, v=tv))
            for v in range(n):
                if v != tv:
                    facts.append(Fact("not", a=a, s=s, v=v))
                    lo, hi = sorted((tv, v))
                    facts.append(Fact("either", a=a, s=s, v=lo, v2=hi))
    for a, a2 in (("room", "item"), ("item", "room"), ("room", "time"), ("item", "time")):
        for v in range(n):
            holder = owner[a][v]
            for v2 in range(n):
                kind = "link" if truth[a2][holder] == v2 else "unlink"
                facts.append(Fact(kind, a=a, v=v, a2=a2, v2=v2))
    for s in range(n):
        for s2 in range(n):
            if s != s2 and t[s] < t[s2]:
                facts.append(Fact("before", s=s, s2=s2))
    for a in ("room", "item"):
        for v in range(n):
            holder = owner[a][v]
            for s2 in range(n):
                if s2 == holder:
                    continue
                kind = "before_link" if t[holder] < t[s2] else "after_link"
                facts.append(Fact(kind, a=a, v=v, s2=s2))
    return facts
