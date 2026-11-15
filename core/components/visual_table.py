"""Generic Power BI Show-as-a-table reader (Layer 2).

Right-clicks a caller-supplied visual, reads the grid as header-to-cell text,
and returns to the canvas. Titles, measure names, and total-row tokens are
opaque caller data. Hover and drill-down stay on the domain page.
"""

from __future__ import annotations

import re
import time
from collections.abc import Mapping, Sequence

from playwright.sync_api import Error, FrameLocator, Locator, Page, expect
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

from config.settings import settings
from core.components.virtual_grid import collect_virtualized_rows

_SHOW_TABLE = ("הצג כטבלה", "Show as a table")
_BACK_TO_REPORT = ("חזרה לדוח", "Back to report")
_SCROLL_DOWN = ("גלול למטה", "Scroll down")
_BIDI_MARKS = ("\u200f", "\u200e", "\u202a", "\u202b", "\u202c")
_PURE_NUMBER = re.compile(r"-?\d[\d.,\u00a0\u202f ]*%?")
_PERCENT_ONLY = re.compile(r"-?\d[\d.,\s]*%")
_TRAILING_COUNT = re.compile(
    r"\s+-?\d[\d,.]*\s*(?:\(\s*\d+(?:[.,]\d+)?\s*%\s*\))?$"
)
_PAREN_PERCENT = re.compile(
    r"(-?\d[\d,.]*)\s*\(\s*\d+(?:[.,]\d+)?\s*%\s*\)\s*$"
)
_ROW_CELLS_JS = """el => {
    const nodes = el.querySelectorAll(
        '[role="rowheader"], [role="gridcell"], [role="cell"]'
    );
    return Array.from(nodes).map(node => (node.textContent || '').trim());
}"""
_SHARES_HOST_JS = """(button, grid) => {
    if (!button || !grid) return false;
    const rootish = (node) => !node
        || node === node.ownerDocument.body
        || node === node.ownerDocument.documentElement;
    const chain = (node) => {
        const nodes = [];
        let current = node;
        while (current && !rootish(current)) {
            nodes.push(current);
            current = current.parentElement;
        }
        return nodes;
    };
    const hosts = new Set(chain(button));
    for (const node of chain(grid)) {
        if (hosts.has(node)) return true;
    }
    return button.contains(grid) || grid.contains(button);
}"""


def _cell_tuple_key(row: Mapping[str, str]) -> str:
    """Identity for one Show-as-a-table row: the full cell tuple, in dict order."""
    return "\x1f".join(str(value) for value in row.values())


def _clean(raw: str) -> str:
    """Trim one cell and drop the bidi marks Power BI inserts."""
    text = raw or ""
    for mark in _BIDI_MARKS:
        text = text.replace(mark, "")
    return text.strip()


def _dedupe_doubled(text: str) -> str:
    """Collapse a label Power BI painted twice in one text node."""
    if len(text) >= 4 and len(text) % 2 == 0:
        half = len(text) // 2
        if text[:half] == text[half:]:
            return text[:half]
    return text


def _is_pure_number(text: str) -> bool:
    """True when the whole string is one numeric token, optionally with %."""
    return _PURE_NUMBER.fullmatch(text) is not None


def _is_percent_only(text: str) -> bool:
    """True when the cell is only a percent, such as ``50%``."""
    return _PERCENT_ONLY.fullmatch(text) is not None


def _pure_int(text: str) -> int | None:
    """Parse a cell that is only an integer. ``0`` is a value. Percents are not."""
    cleaned = (
        _clean(text)
        .replace(",", "")
        .replace("\u00a0", "")
        .replace("\u202f", "")
        .replace(" ", "")
    )
    if re.fullmatch(r"-?\d+", cleaned):
        return int(cleaned)
    return None


def _paren_percent_int(text: str) -> int | None:
    """Leading integer of a trailing ``N (P%)`` suffix, when the cell has one."""
    match = _PAREN_PERCENT.search(text)
    if match is None:
        return None
    return _pure_int(match.group(1))


def _category_label(cells: Sequence[str]) -> str:
    """First non-numeric cell, with a trailing count or percent stripped."""
    for cell in cells:
        if not cell or _is_pure_number(cell) or _is_percent_only(cell):
            continue
        name = _dedupe_doubled(_TRAILING_COUNT.sub("", cell).strip())
        if name and not _is_pure_number(name) and not _is_percent_only(name):
            return name
    return ""


def _measure(cells: Sequence[str]) -> int | None:
    """First integer cell, else the count inside a trailing ``N (P%)`` cell."""
    for cell in cells:
        number = _pure_int(cell)
        if number is not None:
            return number
    for cell in cells:
        number = _paren_percent_int(cell)
        if number is not None:
            return number
    return None


def _skipped(cells: Sequence[str], skip_labels: Sequence[str]) -> bool:
    """True when any cell equals or starts with a caller-supplied token."""
    for cell in cells:
        for token in skip_labels:
            if token and (cell == token or cell.startswith(token)):
                return True
    return False


def rows_to_label_values(
    rows: Sequence[Mapping[str, str]],
    *,
    skip_labels: Sequence[str] = (),
) -> dict[str, int]:
    """Map Show-as-a-table rows to label → integer. The first label wins.

    ``skip_labels`` is caller data. This function does not choose a measure
    column and does not know which report it is reading.
    """
    found: dict[str, int] = {}
    for row in rows:
        cells = [_clean(str(value)) for value in row.values()]
        if _skipped(cells, skip_labels):
            continue
        label = _category_label(cells)
        value = _measure(cells)
        if not label or value is None or label in found:
            continue
        found[label] = value
    return found


class VisualTable:
    """Composed by a caller with the report iframe. The visual locator is opaque."""

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

    def read_rows(
        self,
        container: Locator,
        *,
        name: str = "visual",
    ) -> list[dict[str, str]]:
        """Right-click ``container``, read the grid, and return to the canvas.

        ``name`` is opaque text for error messages. Rows are header → cell
        strings. Integers are not parsed here.
        """
        opened = False
        rows: list[dict[str, str]] | None = None
        error: Exception | None = None
        try:
            container.click(button="right", force=True, timeout=self._timeout)
            self._click_show_as_table(name)
            opened = True
            self._wait_for_back_button(name)
            table = self._visible_table(name)
            self._expect_data_cell(table)
            rows = self._collect_rows(table)
        except Exception as exc:
            error = exc
            if not opened:
                self._dismiss_menu()
        finally:
            if opened:
                try:
                    self._leave_table(name)
                except Exception as leave_exc:
                    if error is None:
                        error = leave_exc
        if error is not None:
            raise error
        return rows or []

    def _roots(self) -> tuple[FrameLocator | Page, Page]:
        """Report iframe first, then the outer page. Menus mount in either."""
        return (self._frame, self._page)

    def _click_show_as_table(self, name: str) -> None:
        """Click the bilingual menu item. A short wait leaves time for both labels."""
        deadline = time.monotonic() + self._timeout / 1000
        while time.monotonic() < deadline:
            for root in self._roots():
                for label in _SHOW_TABLE:
                    remaining_ms = int((deadline - time.monotonic()) * 1000)
                    if remaining_ms <= 0:
                        break
                    for item in (
                        root.get_by_role("menuitem", name=label, exact=True),
                        root.get_by_text(label, exact=True),
                    ):
                        visible = item.filter(visible=True)
                        try:
                            visible.first.wait_for(
                                state="visible", timeout=min(400, remaining_ms)
                            )
                        except PlaywrightTimeoutError:
                            continue
                        visible.first.click()
                        return
        raise AssertionError(f"{name!r} has no show-as-table menu item")

    def _visible_table(self, name: str) -> Locator:
        """Visible grid that already has a data cell.

        One grid is returned as-is, which is the chart path. When several
        grids have a data cell, the grid that shares a host with Back to
        report wins, then the one with the most column headers. The document
        body is not that host. A header strip with no data cell is not a
        candidate. Power BI mounts those cells after Scroll down is clicked.
        """
        deadline = time.monotonic() + self._timeout / 1000
        while time.monotonic() < deadline:
            candidates = self._data_grids()
            if len(candidates) == 1:
                return candidates[0]
            if len(candidates) > 1:
                return self._expanded_grid(candidates, name)
            self._click_scroll_down()
        raise AssertionError(f"{name!r} has no accessible table")

    def _data_grids(self) -> list[Locator]:
        """Visible grids and tables that already show a data cell.

        The first DOM cell may be hidden. Any visible gridcell, cell, or td
        qualifies. A header-only grid does not.
        """
        found: list[Locator] = []
        data_cell = "[role='gridcell'], [role='cell'], td"
        for root in self._roots():
            for role in ("grid", "table", "treegrid"):
                tables = root.get_by_role(role)
                try:
                    count = tables.count()
                except Error:
                    continue
                for index in range(count):
                    candidate = tables.nth(index)
                    try:
                        if not candidate.is_visible():
                            continue
                        if candidate.locator(data_cell).filter(visible=True).count() > 0:
                            found.append(candidate)
                    except Error:
                        continue
        return found

    def _expanded_grid(self, candidates: list[Locator], name: str) -> Locator:
        """Grid tied to Back to report, or the one with the most headers."""
        button = self._wait_for_back_button(name)
        sharing = [
            candidate
            for candidate in candidates
            if self._shares_host(button, candidate)
        ]
        pool = sharing or candidates
        best = pool[0]
        best_count = -1
        for candidate in pool:
            count = self._header_count(candidate)
            if count > best_count:
                best = candidate
                best_count = count
        return best

    def _shares_host(self, button: Locator, grid: Locator) -> bool:
        """True when the button and the grid sit in the same host, not the body."""
        try:
            handle = grid.element_handle(timeout=500)
        except Error:
            return False
        if handle is None:
            return False
        try:
            return bool(button.evaluate(_SHARES_HOST_JS, handle))
        except Error:
            return False

    def _header_count(self, table: Locator) -> int:
        """How many column headers this grid exposes."""
        try:
            return table.get_by_role("columnheader").count()
        except Error:
            return 0

    def _headers(self, table: Locator) -> list[str]:
        """Column header texts in visual order."""
        try:
            raw = table.get_by_role("columnheader").evaluate_all(
                "nodes => nodes.map(node => (node.textContent || '').trim())"
            )
        except Error:
            return []
        return [_clean(text) for text in raw]

    def _row_cells(self, row: Locator) -> list[str]:
        """Cell texts in DOM order. A row header is the category column."""
        try:
            raw = row.evaluate(_ROW_CELLS_JS)
        except Error:
            return []
        if not isinstance(raw, list):
            return []
        return [_clean(str(text)) for text in raw]

    def _visible_rows(self, table: Locator) -> list[dict[str, str]]:
        """Header-to-cell rows currently painted. Skips hidden rows and the header row."""
        headers = self._headers(table)
        rows = table.get_by_role("row")
        try:
            count = rows.count()
        except Error:
            return []
        visible: list[dict[str, str]] = []
        for index in range(count):
            row = rows.nth(index)
            try:
                if not row.is_visible():
                    continue
            except Error:
                continue
            cells = self._row_cells(row)
            if not cells or (headers and cells == headers):
                continue
            visible.append(self._row_mapping(headers, cells))
        return visible

    def _row_mapping(self, headers: list[str], cells: list[str]) -> dict[str, str]:
        """Header → cell. A repeated header keeps the later cell in the value scan."""
        item: dict[str, str] = {}
        for index, cell in enumerate(cells):
            if headers and index < len(headers) and headers[index]:
                key = headers[index]
            else:
                key = str(index)
            if key in item:
                key = f"{key}\x00{index}"
            item[key] = cell
        return item

    def _expect_data_cell(self, table: Locator) -> None:
        """Wait until the table body has a visible data cell before collecting."""
        cell = table.locator(
            "tr td, tr [role='gridcell'], tr [role='cell'], "
            "[role='row'] td, [role='row'] [role='gridcell'], [role='row'] [role='cell']"
        )
        expect(cell.first).to_be_visible(timeout=self._timeout)

    def _click_scroll_down(self) -> bool:
        """Click every visible Scroll down button so a virtualized body can paint."""
        clicked = False
        for root in self._roots():
            for label in _SCROLL_DOWN:
                buttons = root.get_by_role("button", name=label, exact=True).filter(
                    visible=True
                )
                try:
                    count = buttons.count()
                except Error:
                    continue
                for index in range(count):
                    try:
                        buttons.nth(index).click(timeout=1_000)
                        clicked = True
                    except Error:
                        continue
        if clicked:
            try:
                self._frame.locator("body").evaluate(
                    "() => new Promise((resolve) => requestAnimationFrame(() => requestAnimationFrame(resolve)))"
                )
            except Error:
                return clicked
        return clicked

    def _collect_rows(self, table: Locator) -> list[dict[str, str]]:
        """Scroll from the top and store each visible data row once."""
        return collect_virtualized_rows(
            table,
            self._visible_rows,
            _cell_tuple_key,
            timeout_ms=self._timeout,
        )

    def _wait_for_back_button(self, name: str) -> Locator:
        """Visible Back to report button. Its presence means the data table is open."""
        deadline = time.monotonic() + self._timeout / 1000
        while time.monotonic() < deadline:
            for root in self._roots():
                for label in _BACK_TO_REPORT:
                    remaining_ms = int((deadline - time.monotonic()) * 1000)
                    if remaining_ms <= 0:
                        break
                    candidate = root.get_by_role(
                        "button", name=label, exact=True
                    ).filter(visible=True)
                    try:
                        candidate.first.wait_for(
                            state="visible", timeout=min(500, remaining_ms)
                        )
                    except PlaywrightTimeoutError:
                        continue
                    return candidate.first
        raise AssertionError(f"{name!r} data table has no back button")

    def _leave_table(self, name: str) -> None:
        """Click Back to report and wait until that button is gone."""
        button = self._wait_for_back_button(name)
        button.click()
        expect(button).to_be_hidden(timeout=self._timeout)

    def _dismiss_menu(self) -> None:
        """Close a context menu that never offered Show as a table."""
        try:
            self._page.keyboard.press("Escape")
        except Error:
            return
