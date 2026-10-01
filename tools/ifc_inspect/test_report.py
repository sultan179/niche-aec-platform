"""Unit tests for report.py's chain-match section check (chain_section_status).

Regression test for a real bug Sultan caught (2026-10-01): a chain match
(SAFI splitting one Revit column into 2 segments) came back status
"matched (chain)" even though the two SAFI segments had different sections
from each other and from Revit - build_report() never ran check_section()
on chain rows at all, only on single-element matches.
"""
from report import chain_section_status


def test_chain_section_status_matches_single_consistent_section():
    status, reason = chain_section_status(["HSS6X6X1/2"], ["HSS6x6x1/2"])
    assert status == "matched (chain)"
    assert reason is None


def test_chain_section_status_flags_inconsistent_safi_segments():
    # the exact real bug: one Revit column (one section), split into 2 SAFI
    # segments with different sections from each other
    status, reason = chain_section_status(["HSS6X6X1/2"], ["HSS6x6x1/2", "W16x26"])
    assert status == "matched (chain) - verify section"
    assert "revit=['HSS6X6X1/2']" in reason
    assert "safi=['HSS6x6x1/2', 'W16x26']" in reason


def test_chain_section_status_flags_real_mismatch_single_vs_single():
    status, reason = chain_section_status(["W16X26"], ["W21X44"])
    assert status == "matched (chain) - verify section"
    assert reason is None  # single vs single - check_section() already explains it, no extra reason needed


def test_chain_section_status_unmapped_when_no_revit_section():
    status, reason = chain_section_status([], ["HSS6x6x1/2"])
    assert status == "matched (chain) - no Revit profile to check"
    assert reason is None


def test_chain_section_status_flags_safi_internal_disagreement_even_without_revit_section():
    # caught in code review (2026-10-01): SAFI's own segments disagreeing is a
    # real finding even when Revit has no profile to compare against - it must
    # not get swallowed as "nothing to check"
    status, reason = chain_section_status([], ["HSS6x6x1/2", "W16x26"])
    assert status == "matched (chain) - verify section"
    assert "revit=['?']" in reason
    assert "safi=['HSS6x6x1/2', 'W16x26']" in reason
