"""Unit tests for geometry matching and chain matching (match.py)."""
from match import revit_to_safi, dist, pair_distance, match, build_chains, chain_distance, match_chains


def elem(id, category, start, end):
    return {"id": id, "category": category, "start": start, "end": end}


def test_revit_to_safi_rotation():
    assert revit_to_safi(1, 2, 3) == (2, -1, 3)


def test_dist_basic():
    assert dist((0, 0, 0), (3, 4, 0)) == 5.0


def test_pair_distance_picks_flipped_when_smaller():
    a = elem("a", "Beam", (0, 0, 0), (10, 0, 0))
    b = elem("b", "Beam", (10, 0, 0), (0, 0, 0))  # start/end reversed relative to a
    assert pair_distance(a, b) == 0.0


def test_match_simple_pair():
    revit = [elem("r1", "Beam", (0, 0, 0), (10, 0, 0))]
    safi = [elem("s1", "Beam", (0, 0, 0), (10, 0, 0))]
    matched, ru, su = match(revit, safi)
    assert matched == [("r1", "s1", 0.0)]
    assert ru == [] and su == []


def test_match_category_filter_blocks_match():
    revit = [elem("r1", "Column", (0, 0, 0), (10, 0, 0))]
    safi = [elem("s1", "Beam", (0, 0, 0), (10, 0, 0))]
    matched, ru, su = match(revit, safi)
    assert matched == []
    assert ru == ["r1"] and su == ["s1"]


def test_match_beyond_tolerance_stays_unmatched():
    revit = [elem("r1", "Beam", (0, 0, 0), (10, 0, 0))]
    safi = [elem("s1", "Beam", (20, 20, 20), (30, 20, 20))]
    matched, ru, su = match(revit, safi, tolerance_m=0.5)
    assert matched == []
    assert ru == ["r1"] and su == ["s1"]


def test_match_mutual_best_tiebreak():
    # both revit elements are only candidates for the one safi element,
    # but only the closer one should win the mutual-best check
    revit = [
        elem("close", "Beam", (0.01, 0, 0), (10, 0, 0)),
        elem("far", "Beam", (0.3, 0, 0), (10, 0, 0)),
    ]
    safi = [elem("s1", "Beam", (0, 0, 0), (10, 0, 0))]
    matched, ru, su = match(revit, safi, tolerance_m=0.5)
    matched_ids = [m[0] for m in matched]
    assert matched_ids == ["close"]
    assert ru == ["far"]


def test_build_chains_groups_touching_elements():
    els = [
        elem("a", "Beam", (0, 0, 0), (5, 0, 0)),
        elem("b", "Beam", (5, 0, 0), (10, 0, 0)),
    ]
    chains = build_chains(els)
    assert len(chains) == 1
    assert set(chains[0]["ids"]) == {"a", "b"}


def test_build_chains_keeps_separate_when_not_touching():
    els = [
        elem("a", "Beam", (0, 0, 0), (5, 0, 0)),
        elem("c", "Beam", (100, 100, 100), (105, 100, 100)),
    ]
    chains = build_chains(els)
    assert len(chains) == 2


def test_build_chains_different_category_not_grouped():
    els = [
        elem("a", "Beam", (0, 0, 0), (5, 0, 0)),
        elem("d", "Column", (0, 0, 0), (5, 0, 0)),  # same coords, different category
    ]
    chains = build_chains(els)
    assert len(chains) == 2


def test_build_chains_three_element_run_has_two_outer_points():
    els = [
        elem("a", "Beam", (0, 0, 0), (5, 0, 0)),
        elem("b", "Beam", (5, 0, 0), (10, 0, 0)),
        elem("c", "Beam", (10, 0, 0), (15, 0, 0)),
    ]
    chains = build_chains(els)
    assert len(chains) == 1
    outer = set(chains[0]["outer_points"])
    assert outer == {(0.0, 0.0, 0.0), (15.0, 0.0, 0.0)}


def test_build_chains_three_way_junction_has_three_outer_points():
    els = [
        elem("a", "Beam", (0, 0, 0), (5, 0, 0)),
        elem("b", "Beam", (5, 0, 0), (10, 0, 0)),
        elem("d", "Beam", (5, 0, 0), (5, 5, 0)),  # branches off the shared joint
    ]
    chains = build_chains(els)
    assert len(chains) == 1
    assert len(chains[0]["outer_points"]) == 3


def test_chain_distance_none_when_outer_points_not_exactly_two():
    simple = {"outer_points": [(0, 0, 0), (10, 0, 0)]}
    junction = {"outer_points": [(0, 0, 0), (10, 0, 0), (5, 5, 0)]}
    assert chain_distance(simple, junction) is None


def test_match_chains_handles_1_to_n_split():
    revit = [elem("r1", "Beam", (0, 0, 0), (10, 0, 0))]
    safi = [
        elem("s1", "Beam", (0, 0, 0), (6, 0, 0)),
        elem("s2", "Beam", (6, 0, 0), (10, 0, 0)),
    ]
    chain_matches = match_chains(revit, safi)
    assert len(chain_matches) == 1
    revit_ids, safi_ids, offset = chain_matches[0]
    assert revit_ids == ["r1"]
    assert set(safi_ids) == {"s1", "s2"}
    assert offset == 0.0


def test_match_chains_skips_both_single_element_chains():
    # match() already tried and failed on these - match_chains must not re-match them
    revit = [elem("r1", "Beam", (0, 0, 0), (10, 0, 0))]
    safi = [elem("s1", "Beam", (0, 0, 0), (10, 0, 0))]
    assert match_chains(revit, safi) == []
