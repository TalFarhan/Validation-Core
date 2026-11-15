"""Unit tests for rendered-zero versus empty visual presence (Layer 2)."""

import pytest

from core.components.visual import classify_presence


@pytest.mark.parametrize(
    ("numbers", "mark_count", "expected"),
    [
        ([0], 0, "value"),
        ([0], 2, "value"),
        ([None], 0, "empty"),
        ([], 0, "empty"),
        ([None, None], 3, "value"),
        ([4, None], 2, "value"),
    ],
)
def test_classify_presence(numbers, mark_count, expected):
    assert classify_presence(numbers, mark_count) == expected


def test_none_cell_is_not_rewritten_to_zero():
    numbers = [4, None]
    assert classify_presence(numbers, 2) == "value"
    assert numbers[1] is None
