"""Generic Power BI bar/column reader (Layer 2).

Reads category order, a numeric descending check, the category count, and
legend series. Category labels and series names are opaque caller data.
Tooltips, drilldown, and hover stay on the domain page.
"""

from __future__ import annotations

import re
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal

from playwright.sync_api import FrameLocator, Locator, Page, expect

from config.settings import settings
from core.components.kpi import normalize_kpi_text
from core.components.visual import (
    classify_presence,
    count_data_marks,
    displayed_title_text,
    scope_host,
)

_BIDI_MARKS = ("\u200f", "\u200e", "\u202a", "\u202b", "\u202c")
_COMPACT_NUMBER = re.compile(r"-?\d[\d.,\u00a0\u202f]*\d|-?\d")
_PURE_NUMBER = re.compile(r"-?\d[\d.,\u00a0\u202f ]*%?")
_PERCENT_LABEL = re.compile(r"-?\d[\d.,\s]*\(\s*\d+([.,]\d+)?\s*%\s*\)")
_MARKS = "svg rect, svg path, svg circle, [class*='bar'], [class*='column']"
_LEGEND = "[class*='legend'] text, [class*='Legend'] text, .legend text"
_TICKS = (
    "svg text, .axis text, [class*='tick'] text, "
    "[class*='category'] text, [class*='dataLabel'] text"
)


def _strip_bidi(raw: str) -> str:
    """Remove the invisible RTL/LTR marks Power BI injects around text."""
    text = raw or ""
    for mark in _BIDI_MARKS:
        text = text.replace(mark, "")
    return text


def _parse_token(token: str | None) -> int | float | None:
    """Parse one numeric token. None stays None. 0 is a real number."""
    if token is None:
        return None
    clean = normalize_kpi_text(token)
    if not clean:
        return None
    try:
        number = float(clean)
    except ValueError:
        return None
    if number.is_integer():
        return int(number)
    return number


def _dedupe_doubled(text: str) -> str:
    """Collapse a label Power BI painted twice in one text node."""
    if len(text) >= 4 and len(text) % 2 == 0:
        half = len(text) // 2
        if text[:half] == text[half:]:
            return text[:half]
    return text


def _is_pure_number(text: str) -> bool:
    """True when the whole string is one numeric token, optionally with %."""
    return _PURE_NUMBER.fullmatch(text.strip()) is not None


@dataclass(frozen=True)
class ChartCategory:
    """One axis row. ``values`` follows legend order. None is a missing mark."""

    label: str
    values: tuple[int | float | None, ...]


@dataclass(frozen=True)
class ChartReading:
    """Snapshot of one bar or column visual."""

    title: str
    categories: tuple[ChartCategory, ...]
    series: tuple[str, ...]
    state: Literal["value", "empty"]


def series_is_descending(
    categories: Sequence[ChartCategory],
    series_index: int = 0,
) -> bool:
    """True when one series is non-increasing down the categories.

    Ties pass. A missing cell, an empty category list, or an index past the
    row fails. A single numeric cell passes, including 0. Labels are not compared.
    """
    if not categories or series_index < 0:
        return False
    column: list[int | float] = []
    for category in categories:
        if series_index >= len(category.values):
            return False
        cell = category.values[series_index]
        if cell is None:
            return False
        column.append(cell)
    return all(column[index] >= column[index + 1] for index in range(len(column) - 1))


def category_count(categories: Sequence[ChartCategory]) -> int:
    """Number of category rows, not the number of bars."""
    return len(categories)


def align_categories(
    labels: Sequence[str],
    series: Sequence[str],
    cells: Sequence[Sequence[int | float | None]],
) -> tuple[ChartCategory, ...]:
    """Pad each row to the legend width. A missing cell stays None, not 0."""
    width = len(series) if series else 1
    rows: list[ChartCategory] = []
    for index, label in enumerate(labels):
        raw = list(cells[index]) if index < len(cells) else []
        if series:
            values = tuple(raw[col] if col < len(raw) else None for col in range(width))
        else:
            values = (raw[0] if raw else None,)
        rows.append(ChartCategory(label=label, values=values))
    return tuple(rows)


def reading_state(
    categories: Sequence[ChartCategory],
    mark_count: int = 0,
) -> Literal["value", "empty"]:
    """Presence of a chart. A 0 cell is a value. No cells and no marks is empty."""
    numbers = [value for category in categories for value in category.values]
    return classify_presence(numbers, mark_count)


def parse_mark_label(raw: str) -> tuple[str, str | None, int | float] | None:
    """Split a mark accessible name into category, optional series, and value.

    The last number is the value. One remaining text part is the category.
    Two remaining parts are category then series. Returns None when no number
    is present.
    """
    cleaned = _strip_bidi(raw).strip()
    if not cleaned:
        return None
    compact = [token.strip() for token in _COMPACT_NUMBER.findall(cleaned)]
    if not compact:
        return None
    value = _parse_token(compact[-1])
    if value is None:
        return None
    without_numbers = _COMPACT_NUMBER.sub(" ", cleaned)
    parts = [
        part.strip(" .,-:\t")
        for part in re.split(r"[\n|.]+", without_numbers)
        if part.strip(" .,-:\t")
    ]
    if not parts:
        return ("", None, value)
    if len(parts) == 1:
        return (parts[0], None, value)
    return (parts[0], parts[1], value)


def _assemble(
    points: Sequence[tuple[str, str | None, int | float | None]],
    legend: Sequence[str],
) -> tuple[tuple[ChartCategory, ...], tuple[str, ...]]:
    """Group points into category rows. Series order follows the legend."""
    series: list[str] = []
    for name in legend:
        if name and name not in series:
            series.append(name)
    for _category, series_name, _value in points:
        if series_name and series_name not in series:
            series.append(series_name)

    labels: list[str] = []
    for category, _series_name, _value in points:
        if category and category not in labels:
            labels.append(category)
    if not labels:
        return (), tuple(series)

    if not series:
        buckets: dict[str, int | float | None] = {}
        for category, _series_name, value in points:
            if category:
                buckets[category] = value
        rows = tuple(
            ChartCategory(label=label, values=(buckets[label],)) for label in labels
        )
        return rows, ()

    matrix = {label: [None] * len(series) for label in labels}
    for category, series_name, value in points:
        if not category:
            continue
        column = series.index(series_name) if series_name in series else 0
        matrix[category][column] = value
    rows = tuple(
        ChartCategory(label=label, values=tuple(matrix[label])) for label in labels
    )
    return rows, tuple(series)


class Chart:
    """Composed by a caller with the report iframe. Titles and scopes are opaque."""

    def __init__(
        self,
        page: Page,
        frame: FrameLocator,
        timeout_ms: int | None = None,
    ) -> None:
        self._page = page
        self._frame = frame
        self._timeout = (
            timeout_ms if timeout_ms is not None else settings.DEFAULT_TIMEOUT
        )

    def _container(self, title: str, scope: str | None) -> Locator:
        """Visual that contains the opaque title anchor. Not a report-specific id."""
        host = scope_host(self._frame, scope)
        pattern = re.compile(re.escape(title))
        title_node = host.get_by_text(pattern).first
        for xpath in (
            'xpath=ancestor::*[contains(@class,"visualContainerHost")][1]',
            'xpath=ancestor::*[contains(@class,"visual-container-host")][1]',
            'xpath=ancestor::*[contains(@class,"visualContainer")][1]',
            'xpath=ancestor::*[contains(@class,"visual-container")][1]',
            'xpath=ancestor::*[@role="group"][1]',
        ):
            try:
                node = title_node.locator(xpath)
                if node.count() > 0:
                    return node.first
            except Exception:
                continue
        named = host.get_by_role("group", name=pattern)
        try:
            if named.count() > 0:
                return named.first
        except Exception:
            pass
        return title_node

    def _texts(self, root: Locator, selector: str, limit: int = 60) -> list[str]:
        """Visible text nodes under ``root``, bidi marks removed, blanks dropped."""
        nodes = root.locator(selector)
        found: list[str] = []
        try:
            count = min(nodes.count(), limit)
        except Exception:
            return found
        for index in range(count):
            try:
                text = nodes.nth(index).text_content(timeout=500) or ""
            except Exception:
                continue
            cleaned = _dedupe_doubled(_strip_bidi(text).strip())
            if cleaned:
                found.append(cleaned)
        return found

    def _legend_names(self, container: Locator, title_text: str) -> list[str]:
        """Non-numeric legend entries, excluding the visual title."""
        names: list[str] = []
        for text in self._texts(container, _LEGEND):
            if text == title_text or _is_pure_number(text) or _PERCENT_LABEL.fullmatch(text):
                continue
            if text not in names:
                names.append(text)
        return names

    def _points_from_marks(
        self, container: Locator
    ) -> list[tuple[str, str | None, int | float]]:
        """Prefer each data mark's accessible name."""
        nodes = container.locator(_MARKS)
        points: list[tuple[str, str | None, int | float]] = []
        try:
            total = min(nodes.count(), 80)
        except Exception:
            return points
        for index in range(total):
            node = nodes.nth(index)
            raw = ""
            for attr in ("aria-label", "title"):
                try:
                    value = node.get_attribute(attr, timeout=500)
                except Exception:
                    value = None
                if value:
                    raw = value
                    break
            if not raw:
                continue
            parsed = parse_mark_label(raw)
            if parsed is None or not parsed[0]:
                continue
            points.append(parsed)
        return points

    def _points_from_texts(
        self,
        container: Locator,
        title_text: str,
        legend: Sequence[str],
        mark_count: int,
    ) -> tuple[tuple[ChartCategory, ...], tuple[str, ...]]:
        """Pair category ticks with numeric labels when marks have no names.

        Axis text alone, with no numbers and no data marks, is an empty plot.
        """
        labels: list[str] = []
        numbers: list[int | float] = []
        for text in self._texts(container, _TICKS):
            if text == title_text or text in legend or _PERCENT_LABEL.fullmatch(text):
                continue
            if _is_pure_number(text):
                number = _parse_token(text)
                if number is not None:
                    numbers.append(number)
                continue
            if text not in labels and len(text) <= 80:
                labels.append(text)
        if not labels or (not numbers and mark_count == 0):
            return (), ()
        series = tuple(name for name in legend if name not in labels)
        width = len(series) if series else 1
        rows: list[ChartCategory] = []
        for row_index, label in enumerate(labels):
            cells: list[int | float | None] = []
            for column in range(width):
                offset = row_index * width + column
                cells.append(numbers[offset] if offset < len(numbers) else None)
            rows.append(ChartCategory(label=label, values=tuple(cells)))
        return tuple(rows), series

    def _parse(
        self, container: Locator, title_text: str
    ) -> tuple[tuple[ChartCategory, ...], tuple[str, ...], int]:
        """Categories, legend series, and a data-mark count for presence."""
        legend = self._legend_names(container, title_text)
        points = self._points_from_marks(container)
        mark_count = count_data_marks(container)
        if points:
            categories, series = _assemble(points, legend)
            return categories, series, max(mark_count, len(points))
        categories, series = self._points_from_texts(
            container, title_text, legend, mark_count
        )
        return categories, series, mark_count

    def parse_container(
        self, container: Locator, title: str
    ) -> tuple[tuple[ChartCategory, ...], tuple[str, ...]]:
        """Categories and series for a container the caller already resolved.

        An empty plot stays as parsed. ``read`` is the method that clears it.
        """
        categories, series, _mark_count = self._parse(container, title)
        return categories, series

    def read(self, title: str, scope: str | None = None) -> ChartReading:
        """Read one bar or column visual located by an opaque title anchor."""
        container = self._container(title, scope)
        expect(container).to_be_visible(timeout=self._timeout)
        shown = displayed_title_text(container)
        categories, series, mark_count = self._parse(container, shown)
        state = reading_state(categories, mark_count)
        if state == "empty":
            categories = ()
            series = ()
        return ChartReading(
            title=shown,
            categories=categories,
            series=series,
            state=state,
        )

    def category_count(self, title: str, scope: str | None = None) -> int:
        """How many category rows are rendered. Not the number of bars."""
        return len(self.read(title, scope).categories)

    def is_descending(
        self,
        title: str,
        scope: str | None = None,
        series_index: int = 0,
    ) -> bool:
        """Numeric descending check for one series index. Ties pass."""
        reading = self.read(title, scope)
        return series_is_descending(reading.categories, series_index)

    def displayed_title(self, title: str, scope: str | None = None) -> str:
        """Full title currently shown. May be longer than the lookup anchor."""
        container = self._container(title, scope)
        expect(container).to_be_visible(timeout=self._timeout)
        return displayed_title_text(container)
