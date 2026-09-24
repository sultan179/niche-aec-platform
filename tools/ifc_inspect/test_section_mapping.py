"""Unit tests for section formatting normalization (docs/evidence/safi-integration.md, 2026-09-24)."""
from section_mapping import normalize_section, check_section


def test_normalize_none_and_nan_return_none():
    assert normalize_section(None) is None
    assert normalize_section(float("nan")) is None


def test_normalize_empty_and_whitespace_return_none():
    assert normalize_section("") is None
    assert normalize_section("   ") is None


def test_normalize_already_clean():
    assert normalize_section("W18X40") == "W18X40"


def test_normalize_case():
    assert normalize_section("w18x40") == "W18X40"


def test_normalize_internal_space():
    assert normalize_section("w 18X40") == "W18X40"


def test_normalize_leading_trailing_space():
    assert normalize_section(" W18X40 ") == "W18X40"


def test_normalize_unicode_multiply():
    assert normalize_section("W18×40") == "W18X40"


def test_normalize_stray_hyphen():
    assert normalize_section("HSS-6X6X1/2") == "HSS6X6X1/2"


def test_normalize_preserves_fraction():
    assert normalize_section("HSS6x6x1/2") == "HSS6X6X1/2"


def test_normalize_preserves_decimal():
    assert normalize_section("HSS4X4X0.25") == "HSS4X4X0.25"


def test_check_section_no_revit_profile_is_unmapped():
    assert check_section(float("nan"), "W460x60") == "unmapped"
    assert check_section("", "W460x60") == "unmapped"


def test_check_section_exact_match():
    assert check_section("W18X40", "W18X40") == "match"


def test_check_section_formatting_only_difference_is_a_match():
    assert check_section("W18X40", "w 18x40") == "match"


def test_check_section_different_size_is_mismatch():
    assert check_section("W18X40", "W21X44") == "mismatch"


def test_check_section_different_hss_thickness_is_mismatch():
    assert check_section("HSS6X6X1/2", "HSS6X6X3/8") == "mismatch"
