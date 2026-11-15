"""Unit tests for generic bar/column shape rules (Layer 2). No browser."""

from core.components.chart import (
    ChartCategory,
    align_categories,
    category_count,
    reading_state,
    series_is_descending,
)


def test_descending_ties_pass_and_count_is_categories():
    categories = (
        ChartCategory("A", (5, 1)),
        ChartCategory("B", (5, 4)),
        ChartCategory("C", (2, 0)),
    )
    assert series_is_descending(categories, 0) is True
    assert category_count(categories) == 3


def test_descending_fails_when_a_later_value_is_larger():
    categories = (
        ChartCategory("A", (5,)),
        ChartCategory("B", (9,)),
    )
    assert series_is_descending(categories, 0) is False
    assert category_count(categories) == 2


def test_single_zero_category_passes():
    categories = (ChartCategory("A", (0,)),)
    assert series_is_descending(categories, 0) is True
    assert category_count(categories) == 1


def test_none_series_cell_fails_descending_and_stays_absent():
    categories = align_categories(
        ("A", "B"),
        ("left", "right"),
        ((4, None), (1, 2)),
    )
    assert categories[0].values == (4, None)
    assert categories[0].values[1] is None
    assert series_is_descending(categories, 1) is False


def test_two_series_keep_legend_order_and_count_categories_not_bars():
    categories = align_categories(
        ("A", "B"),
        ("left", "right"),
        ((5, 1), (2, 0)),
    )
    assert category_count(categories) == 2
    assert categories[0].values == (5, 1)
    assert categories[1].values == (2, 0)


def test_empty_chart_is_not_a_sorted_zero():
    assert category_count(()) == 0
    assert series_is_descending((), 0) is False
    assert reading_state((), 0) == "empty"
