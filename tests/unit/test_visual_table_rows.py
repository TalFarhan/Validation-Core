"""Unit tests for Show-as-a-table row mapping. No browser."""

from core.components.visual_table import rows_to_label_values


def test_text_cell_and_integer_cell():
    rows = [{"category": "alpha", "count": "12"}]
    assert rows_to_label_values(rows) == {"alpha": 12}


def test_zero_is_a_value():
    rows = [{"name": "alpha", "count": "0"}]
    assert rows_to_label_values(rows) == {"alpha": 0}


def test_thousands_separators_and_bidi_marks_are_stripped():
    rows = [{"name": "unit\u200f", "count": "1,234"}]
    assert rows_to_label_values(rows) == {"unit": 1234}


def test_skip_label_drops_total_rows():
    token = 'סה"כ'
    rows = [
        {"name": "alpha", "count": "4"},
        {"name": token, "count": "9"},
        {"name": f"{token} אחר", "count": "1"},
    ]
    assert rows_to_label_values(rows, skip_labels=(token,)) == {"alpha": 4}


def test_pie_cell_keeps_the_name_and_the_leading_count():
    rows = [{"slice": "name 3 (50.0%)"}]
    assert rows_to_label_values(rows) == {"name": 3}


def test_doubled_power_bi_label_collapses():
    rows = [{"name": "מחוז דןמחוז דן", "count": "2"}]
    assert rows_to_label_values(rows) == {"מחוז דן": 2}


def test_first_value_wins_for_a_repeated_label():
    rows = [
        {"name": "alpha", "count": "1"},
        {"name": "alpha", "count": "9"},
    ]
    assert rows_to_label_values(rows) == {"alpha": 1}


def test_percent_only_cell_is_not_the_count():
    rows = [{"name": "alpha", "share": "50%", "count": "4"}]
    assert rows_to_label_values(rows) == {"alpha": 4}


def test_row_without_an_integer_is_omitted():
    assert rows_to_label_values([{"name": "only"}]) == {}
    assert rows_to_label_values([{"name": "alpha", "share": "50%"}]) == {}


def test_empty_rows_return_an_empty_mapping():
    assert rows_to_label_values([]) == {}
