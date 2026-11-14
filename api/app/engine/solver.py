"""Exhaustive solver over every possible world of a case.

A world assigns each suspect exactly one room, one arrival time and one item
(three permutations of 0..n-1). With 5 suspects that is 120**3 = 1,728,000
worlds, small enough to enumerate once and evaluate every clue as a vectorized
boolean mask. So the engine never guesses: "the culprit is unique" means every
world consistent with the clues has the same person in the crime room.
"""

from __future__ import annotations

import itertools
from functools import lru_cache

import numpy as np

ATTRS = ("room", "time", "item")


class WorldSpace:
    def __init__(self, n: int) -> None:
        self.n = n
        perms = np.array(list(itertools.permutations(range(n))), dtype=np.int8)  # [k, suspect]
        inverse = np.argsort(perms, axis=1).astype(np.int8)  # [k, value] -> suspect
        self.perms = perms
        self.k = len(perms)
        idx = np.indices((self.k,) * len(ATTRS), dtype=np.int16).reshape(len(ATTRS), -1)
        self.size = idx.shape[1]
        # values[attr][suspect] -> array over worlds of that suspect's value
        self.values = {a: np.ascontiguousarray(perms.T[:, idx[i]]) for i, a in enumerate(ATTRS)}
        # owner[attr][value] -> array over worlds of the suspect holding that value
        self.owner = {a: np.ascontiguousarray(inverse.T[:, idx[i]]) for i, a in enumerate(ATTRS)}
        self._perm_index = {tuple(p): i for i, p in enumerate(perms.tolist())}
        # Worlds are ordered room-permutation first, so each block of k*k worlds
        # shares one room layout. The culprit depends only on that layout.
        self._room_owner = inverse  # [room perm, room] -> suspect
        self._time_of_owner: dict[tuple[str, int], np.ndarray] = {}

    def time_of_owner(self, attr: str, value: int) -> np.ndarray:
        """Arrival time of whoever holds attr=value, per world (cached)."""
        key = (attr, value)
        out = self._time_of_owner.get(key)
        if out is None:
            out = self._time_of_owner[key] = np.choose(self.owner[attr][value], self.values["time"])
        return out

    def world_index(self, truth: dict[str, list[int]]) -> int:
        """Index of the world where suspect s has truth[attr][s] for every attribute."""
        i = 0
        for a in ATTRS:
            i = i * self.k + self._perm_index[tuple(truth[a])]
        return i

    def all(self) -> np.ndarray:
        return np.ones(self.size, dtype=bool)

    def culprits(self, mask: np.ndarray, crime_room: int) -> list[int]:
        """Suspects who are in the crime room in at least one world allowed by mask."""
        layouts = mask.reshape(self.k, -1).any(axis=1)
        return np.unique(self._room_owner[layouts, crime_room]).tolist()


@lru_cache(maxsize=4)
def world_space(n: int) -> WorldSpace:
    return WorldSpace(n)
