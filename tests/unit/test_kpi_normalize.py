"""Unit tests for the generic KPI value normalizer (Layer 2)."""

import pytest

from core.components.kpi import extract_kpi_value_text, normalize_kpi_text


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("1,234", "1234"),
        ("\u200f1,234\u200f", "1234"),
        ("  12 345 ", "12345"),
        ("1\u00a0234", "1234"),
        ("\u202b5,678\u202c", "5678"),
        ("42", "42"),
        ("3.5", "3.5"),
        ("", ""),
    ],
)
def test_normalize_strips_marks_commas_and_whitespace(raw, expected):
    assert normalize_kpi_text(raw) == expected


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        # Plain value (group img aria-label == just the number).
        ("1,234", "1,234"),
        # Group aria-label bundling the Hebrew title with the value.
        ("\u05d0\u05d6\u05d5\u05e8\u05d9 \u05d4\u05ea\u05e8\u05e2\u05d4 1,234", "1,234"),
        # Value preceding an RTL label, wrapped in bidi marks.
        ("\u200f5,678\u200f \u05d0\u05d5\u05db\u05dc\u05d5\u05e1\u05d9\u05d9\u05d4", "5,678"),
        # Non-breaking-space thousands separator inside a labelled string.
        ("Population 1\u00a0234", "1\u00a0234"),
        # Decimal value with a trailing unit word.
        ("avg 3.5 days", "3.5"),
        # No digits at all -> fall back to the cleaned text.
        ("N/A", "N/A"),
        # Labeled Gauge (Hebrew min/max chrome): current value is 3, not the scale max.
        ("distinct_alerted_areas 3. ערך מינימלי 0. ערך מקסימלי 1,337.", "3"),
        # Labeled Gauge (English min/max chrome).
        ("Minimum value 0. Maximum value 1,337. 3", "3"),
        # Compact Gauge (min, max, current): current value is the last token.
        ("0 1,337 3", "3"),
    ],
)
def test_extract_pulls_numeric_token_from_group_label(raw, expected):
    assert extract_kpi_value_text(raw) == expected


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("\u05d0\u05d6\u05d5\u05e8\u05d9 \u05d4\u05ea\u05e8\u05e2\u05d4 1,234", "1234"),
        ("Population 1\u00a0234", "1234"),
        ("avg 3.5 days", "3.5"),
        ("distinct_alerted_areas 3. ערך מינימלי 0. ערך מקסימלי 1,337.", "3"),
        ("Minimum value 0. Maximum value 1,337. 3", "3"),
        ("0 1,337 3", "3"),
    ],
)
def test_extract_then_normalize_is_parseable(raw, expected):
    """The group path feeds extracted text into the existing normalizer."""
    assert normalize_kpi_text(extract_kpi_value_text(raw)) == expected
