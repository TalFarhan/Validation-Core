"""Unit tests for generic Gauge scale parsing (Layer 2)."""

import pytest

from core.components.kpi import extract_gauge_scale, extract_kpi_value_text


@pytest.mark.parametrize(
    ("raw", "value", "minimum", "maximum", "state"),
    [
        ("Series 3. ערך מינימלי 0. ערך מקסימלי 1,337.", 3, 0, 1337, "value"),
        ("Minimum value 0. Maximum value 1,337. 3", 3, 0, 1337, "value"),
        ("0 1,337 3", 3, 0, 1337, "value"),
        ("3 / 10", 3, None, 10, "value"),
        ("1,234", 1234, None, None, "value"),
        ("0", 0, None, None, "value"),
        ("", None, None, None, "empty"),
    ],
)
def test_extract_gauge_scale_shapes(raw, value, minimum, maximum, state):
    assert extract_gauge_scale(raw) == {
        "state": state,
        "value": value,
        "minimum": minimum,
        "maximum": maximum,
    }


def test_extract_kpi_value_text_unchanged_for_gauge_and_slash():
    """Scale parsing must not redefine the feature-013 current-value extractor."""
    assert (
        extract_kpi_value_text("Series 3. ערך מינימלי 0. ערך מקסימלי 1,337.")
        == "3"
    )
    assert extract_kpi_value_text("Minimum value 0. Maximum value 1,337. 3") == "3"
    assert extract_kpi_value_text("0 1,337 3") == "3"
    # A slash pair is not a 013 gauge. The longest token stays the right-hand number.
    assert extract_kpi_value_text("3 / 10") == "10"
