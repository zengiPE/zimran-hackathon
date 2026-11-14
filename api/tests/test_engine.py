"""Property tests for the case engine.

Every generated case is re-verified from scratch (fresh masks, no generator state):
the culprit is unique, nobody can solve alone, everybody is needed, the answer only
appears on the last day, and every clue is true in the hidden world.
"""

import itertools
import json
import os

import pytest

from app.engine import analyze, explain, generate_case
from app.engine.facts import Fact
from app.engine.solver import world_space

SEEDS = int(os.environ.get("ENGINE_SEEDS", "300"))
SIZES = [(3, 5), (4, 3), (4, 5), (5, 4), (6, 3)]


def reverify(case: dict) -> dict:
    w = world_space(len(case["suspects"]))
    grid = [[None] * case["days"] for _ in range(case["players"])]
    for c in case["clues"]:
        grid[c["player"]][c["day"] - 1] = Fact.from_dict(c["fact"])
    truth_index = w.world_index(case["solution"]["truth"])
    return analyze(w, case["crime_room"], case["solution"]["culprit"], truth_index, grid)


@pytest.mark.parametrize("seed", range(SEEDS))
def test_case_guarantees(seed: int) -> None:
    players, days = SIZES[seed % len(SIZES)]
    case = generate_case(seed, players, days)
    report = reverify(case)
    assert report["ok"], report
    assert len(case["clues"]) == players * days
    assert {(c["player"], c["day"]) for c in case["clues"]} == set(
        itertools.product(range(players), range(1, days + 1)))


def test_deterministic_by_seed() -> None:
    a = json.dumps(generate_case(42, 4, 3), sort_keys=True)
    b = json.dumps(generate_case(42, 4, 3), sort_keys=True)
    assert a == b


def test_small_cast_for_demo() -> None:
    case = generate_case(3, 4, 3, suspects=4)
    assert reverify(case)["ok"]


def test_truth_matches_culprit() -> None:
    case = generate_case(5, 4, 3)
    truth = case["solution"]["truth"]
    assert truth["room"][case["solution"]["culprit"]] == case["crime_room"]


def test_explain_chain_ends_on_culprit() -> None:
    case = generate_case(11, 4, 3)
    chain = explain(case)
    assert len(chain) == len(case["clues"])
    assert chain[-1]["remaining"] == [case["solution"]["culprit"]]
    eliminated = [s for step in chain for s in step["eliminated"]]
    assert sorted(eliminated + chain[-1]["remaining"]) == list(range(len(case["suspects"])))


def test_solver_counts_worlds() -> None:
    w = world_space(5)
    assert w.size == 120**3
    assert len(w.culprits(w.all(), crime_room=0)) == 5


@pytest.mark.parametrize("kwargs", [
    {"players": 2, "days": 3}, {"players": 4, "days": 9}, {"players": 6, "days": 4, "suspects": 4},
])
def test_rejects_bad_sizes(kwargs: dict) -> None:
    with pytest.raises(ValueError):
        generate_case(1, **kwargs)
