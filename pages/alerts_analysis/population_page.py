"""Second page of the Alerts Analysis report: population and distribution.

Opens the same catalog product as page 1, then selects this page. Titles and
slicer labels stay here. Portal login and the iframe wait stay on ReportShell.
"""

from __future__ import annotations

import re
import time
from typing import Literal

from playwright.sync_api import (
    Error,
    Locator,
    Page,
    TimeoutError as PlaywrightTimeoutError,
    expect,
)

from core.components.chart import Chart
from core.components.kpi import KPI
from pages.alerts_analysis.page import AlertsAnalysisPage

DayNightMode = Literal["off", "day", "night"]
CardRole = Literal["total", "warned", "unprotected"]
AggregationMode = Literal["sum", "average"]

# A decimal point with digits on both sides. Thousands separators are not fractional.
_FRACTIONAL_NUMBER = re.compile(r"\d+\.\d+")
_ALERT_COUNT = re.compile(r"התרעות\s*([0-9,]+)")
_BARE_INTEGER = re.compile(r"^(?:\d{1,3}(?:[,\u00a0\u202f ]\d{3})+|\d+)$")
_SVG_MARKS = "svg rect, svg path, svg circle"
_DISTRICT_MARKS = "svg rect, svg path, svg circle, [class*='bar'], [class*='column']"
_HOUR_TOKEN = re.compile(r"(?<!\d)(\d{1,2}):(\d{2})(?!\d)")
# One row's index and cells. Header rows return null. Callers apply their own key rules.
_ROW_CELLS_JS = """row => {
    if (row.querySelector('[role="columnheader"]')) return null;
    return {
        rowIndex: row.getAttribute('aria-rowindex') || '',
        cells: [...row.querySelectorAll(
            '[role="rowheader"], [role="gridcell"], [role="cell"]'
        )].map(cell => ({
            role: cell.getAttribute('role') || '',
            text: (cell.textContent || '').trim()
        }))
    };
}"""


def _integer_from_mark_label(raw: str) -> int | None:
    """Alert count from one SVG aria-label.

    A label that names the series contributes the integer after that word.
    A label that is only an integer stays a bar. Average and fractional labels
    are omitted.
    """
    text = (raw or "").strip()
    if not text or "ממוצע" in text or _FRACTIONAL_NUMBER.search(text):
        return None
    match = _ALERT_COUNT.search(text)
    if match:
        digits = match.group(1).replace(",", "")
        return int(digits) if digits.isdigit() else None
    if _BARE_INTEGER.fullmatch(text):
        digits = re.sub(r"[,\u00a0\u202f ]", "", text)
        return int(digits) if digits.isdigit() else None
    return None


def _plain_cell(raw: str) -> str:
    """Cell text with a doubled Power BI label collapsed to one copy."""
    text = (raw or "").strip()
    if len(text) >= 2 and len(text) % 2 == 0 and text[: len(text) // 2] == text[len(text) // 2 :]:
        return text[: len(text) // 2]
    return text


def _table_integer(raw: str) -> int | None:
    """Integer from one table cell. Thousands separators and spaces are removed."""
    digits = re.sub(r"[,\u00a0\u202f ]", "", raw or "")
    if digits.isdigit():
        return int(digits)
    return None


def _first_whole_number(values) -> int | None:
    """First integer cell. Booleans and fractional averages are omitted."""
    for cell in values:
        if isinstance(cell, bool) or not isinstance(cell, (int, float)):
            continue
        if isinstance(cell, float) and not cell.is_integer():
            continue
        return int(cell)
    return None


def _hour_bucket(raw: str) -> tuple[str, int] | None:
    """Hour token and alert count from one SVG label.

    The clock token is removed before the count is parsed, so 00:00 is not
    stored as the value 0. Average and fractional labels are omitted.
    """
    text = (raw or "").strip()
    if not text or "ממוצע" in text or _FRACTIONAL_NUMBER.search(text):
        return None
    found = _HOUR_TOKEN.search(text)
    if not found:
        return None
    remainder = (text[: found.start()] + " " + text[found.end() :]).strip()
    value = _integer_from_mark_label(remainder)
    if value is None:
        return None
    hour = f"{int(found.group(1)):02d}:{found.group(2)}"
    return hour, value


def _district_tooltip_pair(raw: str) -> tuple[str, int] | None:
    """District name and integer from one tooltip. Average text is omitted."""
    name = None
    value = None
    for line in (raw or "").splitlines():
        text = _plain_cell(line.strip())
        if not text or "ממוצע" in text:
            continue
        number = _table_integer(text)
        if number is not None and value is None:
            value = number
        elif number is None and name is None:
            name = text
    if name is None or value is None:
        return None
    return name, value


class AlertsPopulationPage(AlertsAnalysisPage):
    """Population and distribution page. Scope for every metric is PAGE_TITLE."""

    # Accessible name of this report page. Metric and chart scope only.
    PAGE_TITLE = "ניתוח התרעות"
    # Screen 2 distance filter. Ready locator only, not a metric scope.
    _SCREEN2_READY_ANCHOR = "מרחק מהגבול"
    DATES_CHART = "התרעות לפי תאריך"
    # Visual title of the 24-hour distribution. It also draws an average line.
    HOUR_CHART = "גרף התרעות וגם ממוצע לפי שעה"
    # Accessible name uses English "and"/"by" when the canvas title is Hebrew.
    _HOUR_CHART_GROUP = re.compile(
        r"גרף התרעות\s+(?:וגם|and)\s+ממוצע\s+(?:לפי|by)\s+שעה"
    )
    # Live title. The shorter phrase "אוכלוסייה לפי יישוב" is not on the page.
    SETTLEMENT_CHART = "אוכלוסייה מותרעת לפי יישוב"
    WARNED_SERIES = "מותרעת"
    UNWARNED_SERIES = "לא מותרעת"

    TOTAL_CARD = 'סה"כ אוכלוסייה'
    WARNED_CARD = "אוכלוסייה מותרעת"
    UNPROTECTED_CARD = "אוכלוסייה לא ממוגנת"

    DAY_TOGGLE = "שעות היום"
    NIGHT_TOGGLE = "שעות הלילה"
    SUM_MODE = "סכום"
    AVERAGE_MODE = "ממוצע ליום"
    # Page-rail control that leaves the first page and opens this one.
    _PAGE_NAV_LABEL = "ניווט בין עמודים"
    _PAGE_NAV_LABEL_EN = "Page navigation"
    # District visual title is "התרעות לפי " plus the active hierarchy name.
    _HIERARCHY_LEVEL_NAMES = {
        "mahoz": "מחוז",
        "nafa": "נפה",
        "rashut": "רשות",
        "yeshuv": "יישוב",
    }
    _DATE_LABEL_EN = {
        "תאריך התחלה": "Start date",
        "תאריך סיום": "End date",
    }

    _CARD_TITLES = {
        "total": TOTAL_CARD,
        "warned": WARNED_CARD,
        "unprotected": UNPROTECTED_CARD,
    }

    def __init__(self, page: Page):
        super().__init__(page)
        # Larger budget so slow Power BI rendering does not raise LoadTimeoutError.
        self.timeout = 120_000
        page.set_default_navigation_timeout(self.timeout)
        page.set_default_timeout(self.timeout)
        # Base level until set_hierarchy_level records a drill-down.
        self._active_hierarchy_level = "mahoz"
        self._resolved_district_title = None
        self._kpi = KPI(page=page, frame=self.dashboard, timeout_ms=self.timeout)
        self._chart = Chart(page=page, frame=self.dashboard, timeout_ms=self.timeout)

    @staticmethod
    def district_chart_title_for(level: str) -> str:
        """District visual title at one hierarchy level, without a page instance."""
        name = AlertsPopulationPage._HIERARCHY_LEVEL_NAMES[level]
        return "התרעות לפי " + name

    def district_chart_title(self, level: str | None = None) -> str:
        """Live district visual title for the active (or given) hierarchy level."""
        if (
            level is None
            and self._active_hierarchy_level == "yeshuv"
            and self._resolved_district_title
        ):
            return self._resolved_district_title
        return self.district_chart_title_for(level or self._active_hierarchy_level)

    def before_report_ready_check(self) -> None:
        """Click the Screen 2 tab inside the page navigator.

        The click targets that tab, not the rail container. The hook returns
        when מרחק מהגבול is visible. Three clicks are not success. One call
        retries for about eight seconds so short probes stay short.
        """
        if self._screen2_anchor_visible():
            return
        # Short probes and reload timing also call this hook. Do not spend
        # the full ready timeout inside one call.
        deadline = time.monotonic() + 8
        while time.monotonic() < deadline:
            self._dismiss_overlay()
            target = self._screen2_nav_target()
            if target is not None:
                try:
                    # A short click timeout keeps a missing node from using
                    # the page's 120s budget.
                    target.click(force=True, timeout=2_000)
                except Error:
                    pass
            self.page.wait_for_timeout(400)
            if self._screen2_anchor_visible():
                return

    def _screen2_anchor_visible(self) -> bool:
        """True when the Screen 2 distance filter is already showing."""
        try:
            return self._report_ready_locator().is_visible(timeout=500)
        except Error:
            return False

    def _screen2_nav_target(self) -> Locator | None:
        """Screen 2 tab inside the page navigator, else the rail control.

        The tab name is also the report header, so the search stays inside
        the page-navigation visual.
        """
        frame = self._report_frame()
        he = self._PAGE_NAV_LABEL
        en = self._PAGE_NAV_LABEL_EN
        rail = (
            frame.get_by_role("navigation", name=he)
            .or_(frame.get_by_role("group", name=he))
            .or_(frame.get_by_label(he, exact=False))
            .or_(frame.get_by_role("navigation", name=en))
            .or_(frame.get_by_role("group", name=en))
            .or_(frame.get_by_label(en, exact=False))
        ).filter(visible=True)
        try:
            if rail.count() > 0:
                inner = self._screen2_tab_in(rail.first)
                if inner is not None:
                    return inner
        except Error:
            pass
        fallback = (
            frame.get_by_role("link", name=he)
            .or_(frame.get_by_role("button", name=he))
            .or_(frame.get_by_label(he, exact=False))
            .or_(frame.get_by_role("link", name=en))
            .or_(frame.get_by_role("button", name=en))
            .or_(frame.get_by_label(en, exact=False))
        ).filter(visible=True)
        try:
            if fallback.count() == 0:
                return None
        except Error:
            return None
        return fallback.first

    def _screen2_tab_in(self, rail: Locator) -> Locator | None:
        """Exact Screen 2 page control inside one navigation visual."""
        title = self.PAGE_TITLE
        inner = (
            rail.get_by_role("button", name=title, exact=True)
            .or_(rail.get_by_role("tab", name=title, exact=True))
            .or_(rail.get_by_role("link", name=title, exact=True))
            .or_(rail.get_by_role("option", name=title, exact=True))
            .or_(rail.get_by_text(title, exact=True))
        ).filter(visible=True)
        try:
            if inner.count() == 0:
                return None
        except Error:
            return None
        return inner.first

    def _report_ready_locator(self) -> Locator:
        # Screen 2 distance filter. The shared title phrase is also on Screen 1.
        return (
            self._report_frame()
            .get_by_text(self._SCREEN2_READY_ANCHOR)
            .filter(visible=True)
            .first
        )

    def clear_filters(self) -> None:
        """Clear every slicer, then wait until the total card stops changing."""
        self._dismiss_overlay()
        expect(self._iframe_phrase_locator(self.TOTAL_CARD)).to_be_visible(
            timeout=self.timeout
        )
        self._slicer.clear_all()
        previous = None
        deadline = time.monotonic() + self.timeout / 1000
        while time.monotonic() < deadline:
            current = self.read_card("total")
            if previous is not None and current == previous:
                return
            previous = current
            self.page.wait_for_timeout(400)

    def set_between_dates(self, start: str, end: str) -> None:
        """Fill the start and end date fields. Values use the page's date format."""
        self._fill_input("תאריך התחלה", start)
        self._fill_input("תאריך סיום", end)

    def set_date_range(self, start_date: str, end_date: str) -> None:
        """Commit a start and end date, then wait until filtered data is showing."""
        self.set_between_dates(start_date, end_date)
        warned = self._iframe_phrase_locator(self.WARNED_CARD)
        expect(warned).to_be_visible(timeout=self.timeout)

        def _warned_is_calculated() -> bool:
            # The all-time total can already be stable while this card is still 0.
            # Blank text raises ValueError and counts as not ready.
            try:
                current = self.read_card("warned")
            except (ValueError, AssertionError):
                return False
            return current not in (0, 0.0)

        # This Playwright build has no expect.poll. Retry the same condition
        # on a 400 ms interval until self.timeout, then fail the expect.
        deadline = time.monotonic() + self.timeout / 1000
        while time.monotonic() < deadline:
            try:
                expect(warned).to_be_visible(timeout=400)
            except AssertionError:
                self.page.wait_for_timeout(400)
                continue
            if _warned_is_calculated():
                return
            self.page.wait_for_timeout(400)
        expect(warned).to_be_visible(timeout=1000)
        raise AssertionError(
            "Warned population card stayed blank or 0 after the date range"
        )

    def set_day_night(self, mode: DayNightMode) -> None:
        """Leave both hour toggles off, or press exactly one of them."""
        self._dismiss_overlay()
        if mode == "off":
            for label in (self.DAY_TOGGLE, self.NIGHT_TOGGLE):
                if self._is_pressed(label):
                    self._toggle(label).click()
            return
        target = self.DAY_TOGGLE if mode == "day" else self.NIGHT_TOGGLE
        other = self.NIGHT_TOGGLE if mode == "day" else self.DAY_TOGGLE
        if self._is_pressed(other):
            self._toggle(other).click()
        if not self._is_pressed(target):
            self._toggle(target).click()

    # def set_value_range(self, low: int, high: int) -> None:
    #     """Set the numeric range inputs. The clear test uses 0 and 349."""
    #     self._fill_exact("התחל", str(low))
    #     self._fill_exact("סיום", str(high))

    def set_value_range(self, low: int, high: int) -> None:
        """Set the numeric range inputs. The clear test uses 0 and 349."""
        self._fill_exact(re.compile(r"התחל|Start"), str(low))
        self._fill_exact(re.compile(r"סיום|End"), str(high))

    def set_district_aggregation(self, mode: AggregationMode) -> None:
        """Select Sum or the per-day average on the district chart."""
        label = self.SUM_MODE if mode == "sum" else self.AVERAGE_MODE
        self._dismiss_overlay()
        container = None
        try:
            container = self._visual_container(self.district_chart_title())
        except AssertionError:
            container = None
        if container is not None:
            scoped = container.get_by_role("button", name=label, exact=True)
            try:
                if scoped.count() == 1:
                    scoped.click()
                    return
            except Error:
                pass
        self._report_frame().get_by_role("button", name=label, exact=True).first.click()

    def _hierarchy_control(self, label: str) -> Locator:
        """Exact Hebrew label of a custom hierarchy tab in the report iframe."""
        return self._report_frame().get_by_text(label, exact=True)

    def set_hierarchy_level(self, level: str) -> bool:
        """Select נפה, רשות, or יישוב on the district chart.

        Returns false when the level is unknown or the chart title does not update.
        """
        if level not in ("nafa", "rashut", "yeshuv"):
            return False
        label = self._HIERARCHY_LEVEL_NAMES[level]
        # The settlement tab is drawn as ישוב. The other two tabs match the map.
        tab_label = "ישוב" if level == "yeshuv" else label
        control = self._hierarchy_control(tab_label)
        self._dismiss_overlay()
        # Custom tabs sit above the district chart. Click the label and let Playwright wait.
        tab = control.first
        tab.click()
        if not self._wait_for_level_selection(tab):
            return False
        # The visual retitles on drill-down; wait for that title, not מחוז.
        # The settlement title may use either ישוב or יישוב.
        phrase = self._iframe_phrase_locator(self.district_chart_title_for(level))
        if level == "yeshuv":
            phrase = phrase.or_(self._iframe_phrase_locator("התרעות לפי ישוב"))
        try:
            expect(phrase.first).to_be_visible(timeout=self.timeout)
        except (AssertionError, Error):
            return False
        self._active_hierarchy_level = level
        self._remember_district_title(level)
        return True

    def _remember_district_title(self, level: str) -> None:
        """Store the district title spelling that is actually on the chart.

        The settlement tab and its title use ישוב. The level map still says יישוב.
        """
        if level == "yeshuv":
            self._resolved_district_title = "התרעות לפי ישוב"
            return
        self._resolved_district_title = self.district_chart_title_for(level)

    def _wait_for_level_selection(self, control: Locator) -> bool:
        """Wait until the clicked level control reports selected.

        A control with neither aria-pressed nor aria-selected has nothing
        further to wait on here. The caller still checks the district title.
        """
        try:
            pressed = control.get_attribute("aria-pressed")
            selected = control.get_attribute("aria-selected")
        except Error:
            return True
        attribute = None
        if pressed is not None:
            attribute = "aria-pressed"
        elif selected is not None:
            attribute = "aria-selected"
        if attribute is None:
            return True
        try:
            expect(control).to_have_attribute(attribute, "true", timeout=self.timeout)
        except AssertionError:
            return False
        return True

    def read_card(self, role: CardRole) -> int | float:
        """Read one population card inside this page's title scope."""
        title = self._CARD_TITLES[role]
        return self._kpi.number(title, scope=self.PAGE_TITLE)

    def chart_total(self, title: str, series_index: int = 0) -> int | float:
        """Sum one chart.

        The dates total scrolls the menu table and keeps each visible row once.
        The hour total uses SVG mark labels. The district total uses visible
        rows in that chart. Non-numeric cells on the settlement chart are
        skipped, not stored as 0.
        """
        if title == self.DATES_CHART:
            return self._dates_table_total()
        if title == self.HOUR_CHART:
            return self._svg_mark_total(title)
        if title == self.district_chart_title():
            return self._district_visible_total()
        categories, _series = self._rows_for_total(title)
        total = 0
        included = 0
        for category in categories:
            if series_index >= len(category.values):
                continue
            cell = category.values[series_index]
            if isinstance(cell, bool) or not isinstance(cell, (int, float)):
                continue
            total += cell
            included += 1
        if included == 0:
            raise AssertionError(f"Chart {title!r} has no numeric values")
        if isinstance(total, float) and total.is_integer():
            return int(total)
        return total

    def read_chart_categories(self, title: str):
        """Category rows inside one chart container, not the whole page group."""
        container = self._visual_container(title)
        return self._chart.parse_container(container, title)

    def read_district_labels(self) -> dict[str, int]:
        """District name to alerts count.

        Visible rows are merged while the chart scrolls. Mark labels are next.
        A tooltip hover runs only when both of those reads are empty.
        """
        title = self.district_chart_title()
        try:
            container = self._visual_container(title)
        except AssertionError:
            return {}
        labels = self._scrolled_district_rows(container)
        if labels:
            return labels
        labels = self._labeled_mark_values(
            title,
            {title, self.SUM_MODE, self.AVERAGE_MODE},
        )
        if labels:
            return labels
        labels = self._tooltip_name_counts(container)
        if labels:
            return labels
        labels = self._visual_table_map(title, "התרעות")
        if labels:
            return labels
        return self._listbox_name_counts(container, "התרעות")

    def _scrolled_district_rows(self, container: Locator) -> dict[str, int]:
        """Merge district rows that appear while the visual scrolls."""
        labels: dict[str, int] = {}
        labels.update(self._visible_district_rows(container))
        for _ in range(12):
            if not self._scroll_visual(container):
                break
            self.page.wait_for_timeout(200)
            labels.update(self._visible_district_rows(container))
        return labels

    def _visible_district_rows(self, container: Locator) -> dict[str, int]:
        """District name to alerts count for the rows on screen now."""
        column = self._header_index(container, "התרעות")
        rows = container.get_by_role("row")
        labels: dict[str, int] = {}
        try:
            count = rows.count()
        except Error:
            return labels
        for index in range(count):
            row = rows.nth(index)
            try:
                if not row.is_visible():
                    continue
            except Error:
                continue
            label, value = self._visible_district_label(row, column)
            if label is None or value is None:
                continue
            labels[label] = value
        return labels

    def _scroll_visual(self, container: Locator) -> bool:
        """Move a scrollable descendant of this visual down one step."""
        try:
            moved = container.evaluate(
                """el => {
                    const nodes = [el, ...el.querySelectorAll('*')];
                    let best = null;
                    let room = 0;
                    for (const node of nodes) {
                        const extra = node.scrollHeight - node.clientHeight;
                        if (extra > room && node.clientHeight > 20) {
                            best = node;
                            room = extra;
                        }
                    }
                    if (!best) return false;
                    const before = best.scrollTop;
                    const step = Math.max(best.clientHeight - 24, 40);
                    best.scrollTop = Math.min(before + step, best.scrollHeight);
                    return best.scrollTop !== before;
                }"""
            )
        except Error:
            return False
        return bool(moved)

    def _tooltip_text(self) -> str:
        """Text of the visible tooltip in the report frame, if one is open."""
        frame = self._report_frame()
        for selector in ("[role='tooltip']", "[class*='tooltip']"):
            node = frame.locator(selector).filter(visible=True)
            try:
                if node.count() > 0:
                    return node.first.inner_text(timeout=500) or ""
            except Error:
                continue
        return ""

    def _hover_mark_values(self, container: Locator, parse) -> dict[str, int]:
        """Hover visible marks and keep the pairs ``parse`` returns.

        Hidden marks are skipped. The walk stops at 40 marks. The overlay
        closes after the last mark, including when no pair was stored.
        """
        marks = container.locator(_SVG_MARKS)
        found: dict[str, int] = {}
        try:
            count = min(marks.count(), 40)
        except Error:
            return found
        for index in range(count):
            mark = marks.nth(index)
            try:
                if not mark.is_visible():
                    continue
                mark.hover(timeout=1000)
            except Error:
                continue
            parsed = parse(self._tooltip_text())
            if parsed is None:
                continue
            name, value = parsed
            found[name] = value
        self._dismiss_overlay()
        return found

    def _tooltip_name_counts(self, container: Locator) -> dict[str, int]:
        """Name and integer from each visible bar tooltip."""
        return self._hover_mark_values(container, _district_tooltip_pair)

    def _hour_tooltip_buckets(self, container: Locator) -> dict[str, int]:
        """Hour sum from bar tooltips. Average and fractional text are omitted."""
        return self._hover_mark_values(container, _hour_bucket)

    def _labeled_mark_values(self, title: str, ignored: set[str]) -> dict[str, int]:
        """Pair category lines with bare integer mark labels, in draw order."""
        container = self._visual_container(title)
        try:
            raw_text = container.inner_text(timeout=self.timeout) or ""
        except Error:
            return {}
        names: list[str] = []
        for line in raw_text.splitlines():
            text = _plain_cell(line.strip())
            if not text or text in ignored:
                continue
            if _table_integer(text) is not None:
                continue
            names.append(text)
        values: list[int] = []
        for raw in self._aria_labels(container, _SVG_MARKS):
            value = _integer_from_mark_label(raw)
            if value is None:
                continue
            values.append(value)
        if not names or len(values) < len(names):
            return {}
        return {name: values[index] for index, name in enumerate(names)}

    def read_settlement_warned(self) -> dict[str, int]:
        """Warned population by settlement, in the order the chart draws them.

        Mark labels on this chart are bare integers. Category names are the
        non-numeric lines. Axis ticks stay out of the name list.
        """
        return self._labeled_mark_values(
            self.SETTLEMENT_CHART,
            {self.SETTLEMENT_CHART, self.WARNED_SERIES, self.UNWARNED_SERIES},
        )

    def read_date_counts(self) -> dict[str, int]:
        """Date header to alerts count from the dates chart table.

        The table is closed before this method returns, including when the
        column cannot be read.
        """
        self._dismiss_overlay()
        opened = False
        try:
            container = self._visual_container(self.DATES_CHART)
            container.click(button="right")
            self._click_show_as_table(self.DATES_CHART)
            opened = True
            table, column = self._alert_column_table(title=self.DATES_CHART)
            return self._collect_scrolled_rows(table, column, key="header")
        finally:
            if opened:
                try:
                    self._leave_visual_table(self.DATES_CHART)
                except (AssertionError, Error):
                    self._dismiss_overlay()

    def read_hour_buckets(self) -> dict[str, int]:
        """Hour token to integer from hour-chart SVG labels.

        A label that names the average or a fractional number is omitted.
        """
        container = self._visual_container(self.HOUR_CHART)
        buckets: dict[str, int] = {}
        for raw in self._aria_labels(container, _SVG_MARKS):
            parsed = _hour_bucket(raw)
            if parsed is None:
                continue
            hour, value = parsed
            buckets[hour] = value
        if buckets:
            return buckets
        categories, _series = self.read_chart_categories(self.HOUR_CHART)
        for category in categories:
            found = _HOUR_TOKEN.search(category.label or "")
            if not found:
                continue
            value = _first_whole_number(category.values)
            if value is None:
                continue
            hour = f"{int(found.group(1)):02d}:{found.group(2)}"
            buckets[hour] = value
        if buckets:
            return buckets
        for name, value in self._labeled_mark_values(
            self.HOUR_CHART,
            {self.HOUR_CHART, self.SUM_MODE, self.AVERAGE_MODE},
        ).items():
            found = _HOUR_TOKEN.search(name)
            if not found:
                continue
            hour = f"{int(found.group(1)):02d}:{found.group(2)}"
            buckets[hour] = value
        if buckets:
            return buckets
        buckets = self._hour_tooltip_buckets(container)
        if buckets:
            return buckets
        buckets = self._hour_keyed(self._visual_table_map(self.HOUR_CHART, "התרעות"))
        if buckets:
            return buckets
        return self._hour_keyed(self._listbox_name_counts(container, "התרעות"))

    def read_hour_daily_avg(self) -> dict[str, int]:
        """Hour token to the integer daily-average count from the alerts column.

        ממוצע ליום values come from the התרעות column. Decimal ממוצע cells
        are not read and are not rounded.
        """
        # The sanity test does not toggle aggregation. Press the hour chart's
        # own ממוצע ליום control; the district toggle does not change this chart.
        self._press_average_on_chart(self.HOUR_CHART)
        return self._hour_keyed(self._visual_table_map(self.HOUR_CHART, "התרעות"))

    def _press_average_on_chart(self, title: str) -> None:
        """Press ממוצע ליום for one chart and wait until that button is pressed.

        The control sits beside the visual, so the search starts at the chart
        title and takes the next matching button. The district toggle is a
        different button and does not change this chart.
        """
        self._dismiss_overlay()
        anchor = self._title_anchor(title)
        target = (
            anchor.locator("xpath=following::*[@role='button']")
            .filter(has_text=self.AVERAGE_MODE)
            .first
        )
        expect(target).to_be_visible(timeout=self.timeout)
        pressed = (target.get_attribute("aria-pressed") or "").lower()
        if pressed != "true":
            target.click()
        expect(target).to_have_attribute("aria-pressed", "true", timeout=self.timeout)

    def _svg_mark_total(self, title: str) -> int:
        """Sum aria-label values on rect, path, and circle marks inside one chart."""
        container = self._visual_container(title)
        marks = container.locator(_SVG_MARKS)
        expect(marks.first).to_be_visible(timeout=self.timeout)
        total, included = self._sum_mark_labels(self._aria_labels(container, _SVG_MARKS))
        if included == 0:
            raise AssertionError(f"Chart {title!r} has no numeric values")
        return total

    def _dates_table_total(self) -> int:
        """Sum the alerts column in the table opened from the dates chart menu.

        The table is scrolled so virtualized rows render. A row is stored only
        while it is visible, and only once. The back control returns to the
        canvas even when the column cannot be read.
        """
        self._dismiss_overlay()
        opened = False
        try:
            container = self._visual_container(self.DATES_CHART)
            container.click(button="right")
            self._click_show_as_table(self.DATES_CHART)
            opened = True
            table, column = self._alert_column_table(title=self.DATES_CHART)
            collected = self._collect_scrolled_rows(table, column, key="stable")
            total = sum(collected.values())
            included = len(collected)
            if included == 0:
                raise AssertionError(f"Chart {self.DATES_CHART!r} has no numeric values")
            return total
        finally:
            if opened:
                try:
                    self._leave_visual_table(self.DATES_CHART)
                except (AssertionError, Error):
                    self._dismiss_overlay()

    def _click_show_as_table(self, title: str | None = None) -> None:
        """Click the bilingual menu item that opens a visual as a table.

        The menu opened by the right-click stays up until this click.
        A missing label uses a short visible wait so the other label still
        gets the rest of the timeout.
        """
        visual = title or self.DATES_CHART
        labels = ("הצג כטבלה", "Show as a table")
        deadline = time.monotonic() + self.timeout / 1000
        while time.monotonic() < deadline:
            for root in (self._report_frame(), self.page):
                for label in labels:
                    remaining_ms = int((deadline - time.monotonic()) * 1000)
                    if remaining_ms <= 0:
                        break
                    item = root.get_by_role("menuitem", name=label, exact=True).filter(
                        visible=True
                    )
                    try:
                        item.first.wait_for(
                            state="visible", timeout=min(500, remaining_ms)
                        )
                    except PlaywrightTimeoutError:
                        continue
                    item.first.click()
                    return
        raise AssertionError(f"Chart {visual!r} has no show-as-table menu item")

    def _alert_column_table(
        self,
        header: str = "התרעות",
        *,
        title: str | None = None,
        contains: bool = False,
    ) -> tuple[Locator, int]:
        """Visible grid, or else table, with a named column that has integers."""
        visual = title or self.DATES_CHART
        deadline = time.monotonic() + self.timeout / 1000
        frame = self._report_frame()
        while time.monotonic() < deadline:
            progressed = False
            for role in ("grid", "table"):
                remaining_ms = int((deadline - time.monotonic()) * 1000)
                if remaining_ms <= 0:
                    break
                tables = frame.get_by_role(role)
                try:
                    tables.first.wait_for(
                        state="visible", timeout=min(500, remaining_ms)
                    )
                except PlaywrightTimeoutError:
                    continue
                progressed = True
                found = self._last_table_with_header(
                    tables, header, contains=contains
                )
                if found is not None:
                    return found
            if progressed:
                # The grid is visible but the alerts integer is not ready.
                # This Playwright build has no expect.poll.
                self.page.wait_for_timeout(200)
        raise AssertionError(f"Chart {visual!r} has no accessible table")

    def _last_table_with_header(
        self, tables: Locator, header: str, *, contains: bool = False
    ) -> tuple[Locator, int] | None:
        found: tuple[Locator, int] | None = None
        try:
            count = tables.count()
        except Error:
            return None
        for index in range(count):
            table = tables.nth(index)
            try:
                if not table.is_visible():
                    continue
            except Error:
                continue
            column = self._header_index(table, header, contains=contains)
            if column is None:
                continue
            _total, included = self._sum_visible_alert_column(table, column)
            if included == 0:
                continue
            found = (table, column)
        return found

    def _header_index(
        self, table: Locator, header: str, *, contains: bool = False
    ) -> int | None:
        try:
            labels = table.get_by_role("columnheader").evaluate_all(
                "nodes => nodes.map(node => (node.textContent || '').trim())"
            )
        except Error:
            return None
        for index, label in enumerate(labels):
            cleaned = _plain_cell(label)
            if contains:
                if header in cleaned:
                    return index
            elif cleaned == header:
                return index
        return None

    def _sum_visible_alert_column(self, table: Locator, column: int) -> tuple[int, int]:
        """Integers in visible rows of one grid-cell column."""
        rows = table.get_by_role("row")
        try:
            count = rows.count()
        except Error:
            return 0, 0
        total = 0
        included = 0
        for index in range(count):
            row = rows.nth(index)
            try:
                if not row.is_visible():
                    continue
            except Error:
                continue
            parsed = self._visible_alert_value(row, column)
            if parsed is None:
                continue
            total += parsed
            included += 1
        return total, included

    def _visible_alert_value(self, row: Locator, column: int) -> int | None:
        """Integer in one visible row, or none when the row is a header or a summary."""
        try:
            payload = row.evaluate(_ROW_CELLS_JS)
        except Error:
            return None
        if not payload or not payload.get("cells"):
            return None
        cells = payload["cells"]
        if column >= len(cells):
            return None
        texts = [_plain_cell(cell["text"]) for cell in cells]
        if any(text == 'סה"כ' or text.startswith('סה"כ') for text in texts):
            return None
        if cells[column].get("role") not in ("gridcell", "cell"):
            return None
        return _table_integer(texts[column])

    def _collect_scrolled_rows(
        self, table: Locator, column: int, *, key: str
    ) -> dict[str, int]:
        """Scroll the dates table and store each visible alerts row once.

        ``stable`` keys by aria-rowindex or the row header. ``header`` keys
        by the row header only. Hidden rows are omitted. There is no
        scroll-to-end pass.
        """
        collected: dict[str, int] = {}
        deadline = time.monotonic() + self.timeout / 1000
        unchanged = 0
        self._scroll_dates_table(table, "top")
        self._wait_for_visible_row(table)
        while time.monotonic() < deadline and unchanged < 2:
            before = len(collected)
            self._collect_visible_keyed_rows(table, column, collected, key)
            previous = self._first_visible_row_key(table)
            moved = self._scroll_dates_table(table, "page")
            if moved:
                self._wait_for_row_shift(table, previous)
            if len(collected) == before and not moved:
                unchanged += 1
            else:
                unchanged = 0
        return collected

    def _collect_visible_keyed_rows(
        self,
        table: Locator,
        column: int,
        collected: dict[str, int],
        key: str,
    ) -> None:
        """Add visible rows that are not already stored."""
        rows = table.get_by_role("row")
        try:
            count = rows.count()
        except Error:
            return
        for index in range(count):
            row = rows.nth(index)
            try:
                if not row.is_visible():
                    continue
            except Error:
                continue
            if key == "header":
                label, value = self._visible_date_entry(row, column)
            else:
                label, value = self._visible_alert_entry(row, column)
            if label is None or value is None or label in collected:
                continue
            collected[label] = value

    def _first_visible_row_key(self, table: Locator) -> str:
        """Text of the first visible row, so a scroll can be seen to move."""
        rows = table.get_by_role("row")
        try:
            count = rows.count()
        except Error:
            return ""
        for index in range(count):
            row = rows.nth(index)
            try:
                if not row.is_visible():
                    continue
                text = row.inner_text(timeout=300) or ""
            except Error:
                continue
            cleaned = _plain_cell(" ".join(text.split()))
            if cleaned:
                return cleaned[:80]
        return ""

    def _wait_for_visible_row(self, table: Locator) -> None:
        """Wait until a row is visible. A missing row does not raise."""
        try:
            table.get_by_role("row").first.wait_for(state="visible", timeout=1000)
        except Error:
            return

    def _wait_for_row_shift(self, table: Locator, previous: str) -> None:
        """Poll until the first visible row changes or the step budget ends.

        expect.poll is not in this Playwright build, so the interval is a
        short wait inside the condition.
        """
        budget = time.monotonic() + 0.4
        while time.monotonic() < budget:
            if self._first_visible_row_key(table) != previous:
                return
            self.page.wait_for_timeout(100)

    def _visible_alert_entry(self, row: Locator, column: int) -> tuple[str | None, int | None]:
        """Key and alerts integer for one visible row, or empty when it is skipped."""
        try:
            payload = row.evaluate(_ROW_CELLS_JS)
        except Error:
            return None, None
        if not payload or not payload.get("cells"):
            return None, None
        cells = payload["cells"]
        if column >= len(cells):
            return None, None
        texts = [_plain_cell(cell["text"]) for cell in cells]
        if any(text == 'סה"כ' or text.startswith('סה"כ') for text in texts):
            return None, None
        if cells[column].get("role") != "gridcell":
            return None, None
        value = _table_integer(texts[column])
        if value is None:
            return None, None
        date_key = next(
            (
                text
                for cell, text in zip(cells, texts)
                if cell.get("role") == "rowheader" and text
            ),
            "",
        )
        key = (payload.get("rowIndex") or "").strip() or date_key
        if not key:
            return None, None
        return key, value

    def _visible_date_entry(self, row: Locator, column: int) -> tuple[str | None, int | None]:
        """Row-header text and alerts integer, or empty when the row is skipped."""
        try:
            payload = row.evaluate(_ROW_CELLS_JS)
        except Error:
            return None, None
        if not payload or not payload.get("cells"):
            return None, None
        cells = payload["cells"]
        if column >= len(cells):
            return None, None
        texts = [_plain_cell(cell["text"]) for cell in cells]
        if any(text == 'סה"כ' or text.startswith('סה"כ') for text in texts):
            return None, None
        if cells[column].get("role") != "gridcell":
            return None, None
        value = _table_integer(texts[column])
        if value is None:
            return None, None
        label = next(
            (
                text
                for cell, text in zip(cells, texts)
                if cell.get("role") == "rowheader" and text
            ),
            "",
        )
        if not label:
            return None, None
        return label, value

    def _scroll_dates_table(self, table: Locator, mode: str) -> bool:
        """Move the table scroll parent to the top, down one overlapping page, or to the end."""
        try:
            moved = table.evaluate(
                """(el, mode) => {
                    const nodes = [el];
                    let parent = el.parentElement;
                    for (let depth = 0; depth < 12 && parent; depth += 1) {
                        nodes.push(parent);
                        parent = parent.parentElement;
                    }
                    const host = el.parentElement || el;
                    host.querySelectorAll('*').forEach(node => nodes.push(node));
                    let best = null;
                    let room = 0;
                    for (const node of nodes) {
                        const extra = node.scrollHeight - node.clientHeight;
                        if (extra > room) {
                            best = node;
                            room = extra;
                        }
                    }
                    if (!best) return false;
                    const before = best.scrollTop;
                    if (mode === 'top') {
                        best.scrollTop = 0;
                    } else if (mode === 'end') {
                        best.scrollTop = best.scrollHeight;
                    } else {
                        const step = Math.max(best.clientHeight - 24, 40);
                        best.scrollTop = Math.min(before + step, best.scrollHeight);
                    }
                    return best.scrollTop !== before;
                }""",
                mode,
            )
        except Error:
            return False
        return bool(moved)

    def _leave_visual_table(self, title: str) -> None:
        """Close the data table so the named visual is on the canvas again.

        The back control is named in Hebrew or English.
        """
        labels = ("חזרה לדוח", "Back to report")
        deadline = time.monotonic() + self.timeout / 1000
        button = None
        while time.monotonic() < deadline and button is None:
            for root in (self._report_frame(), self.page):
                for label in labels:
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
                    button = candidate.first
                    break
                if button is not None:
                    break
        if button is None:
            raise AssertionError(f"Chart {title!r} data table has no back button")
        button.click()
        if title == self.HOUR_CHART:
            # The accessible name uses and/by and may not pass a visible check.
            group = self._report_frame().get_by_role(
                "group", name=self._HOUR_CHART_GROUP
            )
            expect(group.first).to_be_attached(timeout=self.timeout)
            return
        visible = self._report_frame().get_by_text(title).filter(visible=True)
        expect(visible.first).to_be_visible(timeout=self.timeout)

    def _visual_table_map(
        self, title: str, header: str, *, contains: bool = False
    ) -> dict[str, int]:
        """Name to count from the accessible table of one visual.

        The table is closed before this method returns, including when the
        column cannot be read. An empty mapping means the menu or table was
        not available.
        """
        self._dismiss_overlay()
        opened = False
        try:
            container = self._visual_container(title)
            container.click(button="right")
            self._click_show_as_table(title)
            opened = True
            table, column = self._alert_column_table(
                header, title=title, contains=contains
            )
            return self._collect_scrolled_rows(table, column, key="header")
        except (AssertionError, Error):
            self._dismiss_overlay()
            return {}
        finally:
            if opened:
                try:
                    self._leave_visual_table(title)
                except (AssertionError, Error):
                    self._dismiss_overlay()

    def _listbox_name_counts(self, container: Locator, measure: str) -> dict[str, int]:
        """Pair category listbox options with a measure listbox in draw order."""
        try:
            boxes = container.get_by_role("listbox")
            count = boxes.count()
        except Error:
            return {}
        categories: list[str] | None = None
        measures: list[str] | None = None
        for index in range(count):
            box = boxes.nth(index)
            label = ""
            try:
                label = (box.get_attribute("aria-label") or "").strip()
            except Error:
                label = ""
            texts = self._listbox_option_texts(box)
            if not texts:
                continue
            numeric = [_table_integer(text) is not None for text in texts]
            mostly_numeric = bool(numeric) and sum(numeric) >= max(
                1, (len(numeric) * 3) // 4
            )
            if measure in label:
                measures = texts
            elif measure == "התרעות" and mostly_numeric and measures is None:
                measures = texts
            elif not mostly_numeric:
                categories = texts
        if not categories or not measures:
            return {}
        found: dict[str, int] = {}
        for name, raw in zip(categories, measures):
            value = _table_integer(raw)
            if name and value is not None:
                found[name] = value
        return found

    def _listbox_option_texts(self, box: Locator) -> list[str]:
        """Visible option labels inside one listbox, in draw order."""
        options = box.get_by_role("option")
        texts: list[str] = []
        try:
            count = options.count()
        except Error:
            return texts
        for index in range(count):
            try:
                text = _plain_cell(options.nth(index).inner_text(timeout=500) or "")
            except Error:
                continue
            if text:
                texts.append(text)
        return texts

    def _hour_keyed(self, labels: dict[str, int]) -> dict[str, int]:
        """Keep entries whose names contain an HH:MM token."""
        buckets: dict[str, int] = {}
        for name, value in labels.items():
            found = _HOUR_TOKEN.search(name or "")
            if not found:
                continue
            buckets[f"{int(found.group(1)):02d}:{found.group(2)}"] = value
        return buckets

    def _aria_labels(self, container: Locator, selector: str) -> list[str]:
        """aria-label values for the selected marks. Text content is not read."""
        nodes = container.locator(selector)
        labels: list[str] = []
        try:
            count = nodes.count()
        except Error:
            return labels
        for index in range(count):
            try:
                raw = nodes.nth(index).get_attribute("aria-label", timeout=500) or ""
            except Error:
                continue
            cleaned = raw.strip()
            if cleaned:
                labels.append(cleaned)
        return labels

    def _sum_mark_labels(self, labels: list[str]) -> tuple[int, int]:
        total = 0
        included = 0
        for raw in labels:
            value = _integer_from_mark_label(raw)
            if value is None:
                continue
            total += value
            included += 1
        return total, included

    def _district_visible_total(self) -> int:
        """Settled sum of visible district values. The chart is not scrolled.

        A visible alerts row is used when the visual is a table. This chart
        draws the values on marks, so a hidden mark stays out of the sum.
        """
        title = self.district_chart_title()
        container = self._visual_container(title)
        previous: tuple[int, int] | None = None
        deadline = time.monotonic() + self.timeout / 1000
        while time.monotonic() < deadline:
            current = self._sum_visible_district(container)
            if previous is not None and current == previous and current[1] > 0:
                return current[0]
            previous = current
            self.page.wait_for_timeout(400)
        if previous is not None and previous[1] > 0:
            return previous[0]
        raise AssertionError(f"Chart {title!r} has no numeric values")

    def _sum_visible_district(self, container: Locator) -> tuple[int, int]:
        """Visible district rows, or visible mark labels when those rows have no integer."""
        total, included = self._sum_visible_district_rows(container)
        if included > 0:
            return total, included
        return self._sum_visible_district_marks(container)

    def _sum_visible_district_marks(self, container: Locator) -> tuple[int, int]:
        """Integers on visible district marks. A hidden mark contributes nothing."""
        marks = container.locator(_DISTRICT_MARKS)
        try:
            count = marks.count()
        except Error:
            return 0, 0
        total = 0
        included = 0
        for index in range(count):
            mark = marks.nth(index)
            try:
                if not mark.is_visible():
                    continue
            except Error:
                continue
            try:
                raw = mark.get_attribute("aria-label", timeout=300) or ""
            except Error:
                continue
            value = _integer_from_mark_label(raw)
            if value is None:
                continue
            total += value
            included += 1
        return total, included

    def _sum_visible_district_rows(self, container: Locator) -> tuple[int, int]:
        """Integers from visible district rows. A hidden row contributes nothing."""
        column = self._header_index(container, "התרעות")
        rows = container.get_by_role("row")
        try:
            count = rows.count()
        except Error:
            return 0, 0
        total = 0
        included = 0
        for index in range(count):
            row = rows.nth(index)
            try:
                if not row.is_visible():
                    continue
            except Error:
                continue
            value = self._visible_district_value(row, column)
            if value is None:
                continue
            total += value
            included += 1
        return total, included

    def _visible_district_value(self, row: Locator, column: int | None) -> int | None:
        """Alerts integer in one visible district row, or none for a header or a summary."""
        try:
            payload = row.evaluate(_ROW_CELLS_JS)
        except Error:
            return None
        if not payload or not payload.get("cells"):
            return None
        cells = payload["cells"]
        texts = [_plain_cell(cell["text"]) for cell in cells]
        if any(text == 'סה"כ' or text.startswith('סה"כ') for text in texts):
            return None
        if column is not None and column < len(cells):
            chosen = cells[column]
            if chosen.get("role") != "gridcell":
                return None
            return _table_integer(texts[column])
        for cell, text in zip(cells, texts):
            if cell.get("role") not in ("gridcell", "cell"):
                continue
            value = _table_integer(text)
            if value is not None:
                return value
        return None

    def _visible_district_label(
        self, row: Locator, column: int | None
    ) -> tuple[str | None, int | None]:
        """District name and alerts integer, or empty for a header or a summary."""
        try:
            payload = row.evaluate(_ROW_CELLS_JS)
        except Error:
            return None, None
        if not payload or not payload.get("cells"):
            return None, None
        cells = payload["cells"]
        texts = [_plain_cell(cell["text"]) for cell in cells]
        if any(text == 'סה"כ' or text.startswith('סה"כ') for text in texts):
            return None, None
        label = next(
            (
                text
                for cell, text in zip(cells, texts)
                if cell.get("role") == "rowheader" and text
            ),
            "",
        )
        if not label:
            return None, None
        if column is not None and column < len(cells):
            chosen = cells[column]
            if chosen.get("role") != "gridcell":
                return None, None
            value = _table_integer(texts[column])
            if value is None:
                return None, None
            return label, value
        for cell, text in zip(cells, texts):
            if cell.get("role") not in ("gridcell", "cell"):
                continue
            value = _table_integer(text)
            if value is not None:
                return label, value
        return None, None

    def _rows_for_total(self, title: str):
        """Category rows and series names for charts that are not read from SVG marks."""
        reading = self._chart.read(title, scope=self.PAGE_TITLE)
        if reading.state == "empty" or not reading.categories:
            raise AssertionError(f"Chart {title!r} is empty")
        return reading.categories, reading.series

    def _visual_container(self, title: str) -> Locator:
        """Nearest visual box that holds this title and a number.

        A header with no numbers is skipped. A box that also holds another
        chart title from this page is skipped. There is no page-wide fallback.
        """
        title_node = self._title_anchor(title)
        others = [
            name
            for name in (
                self.district_chart_title(),
                self.DATES_CHART,
                self.HOUR_CHART,
                self.SETTLEMENT_CHART,
            )
            if name != title
        ]
        ancestor = (
            "ancestor::*[contains(@class,'visualContainer')"
            " or contains(@class,'visual-container')]"
        )
        if self._container_is_one_chart(title_node, others):
            return title_node
        for index in range(1, 12):
            node = title_node.locator(f"xpath={ancestor}[{index}]")
            if node.count() == 0:
                break
            if self._container_is_one_chart(node, others):
                return node
        raise AssertionError(f"Chart {title!r} has no visual container")

    def _title_anchor(self, title: str) -> Locator:
        """Visible title, or the group whose accessible name is that title.

        The full hour title also sits in a hidden tooltip. That node is not the chart.
        Power BI sometimes marks the real hour title hidden, so that title may be
        attached inside a visual container without a visible filter.
        """
        frame = self._report_frame()
        visible = frame.get_by_text(title).filter(visible=True)
        if visible.count() > 0:
            return visible.first
        if title == self.HOUR_CHART:
            # Power BI exposes this title as "גרף התרעות and ממוצע by שעה".
            # That name is not the Hebrew constant, and it is often not visible.
            group = frame.get_by_role("group", name=self._HOUR_CHART_GROUP)
            try:
                if group.count() > 0:
                    return group.first
            except Error:
                pass
            # A hidden tooltip is not the chart. The title must sit in a visual.
            attached = self._node_in_visual(frame.get_by_text(title))
            if attached is None:
                attached = self._node_in_visual(
                    frame.get_by_role("group", name=title, exact=True)
                )
            if attached is not None:
                return attached
            raise AssertionError(f"Chart {title!r} title is not attached")
        named = frame.get_by_role("group", name=title, exact=True).filter(visible=True)
        if named.count() > 0:
            return named.first
        raise AssertionError(f"Chart {title!r} title is not visible")

    def _node_in_visual(self, nodes: Locator) -> Locator | None:
        """First node that sits inside a Power BI visual container."""
        ancestor = (
            "xpath=ancestor::*[contains(@class,'visualContainer')"
            " or contains(@class,'visual-container')][1]"
        )
        try:
            count = nodes.count()
        except Error:
            return None
        for index in range(count):
            node = nodes.nth(index)
            try:
                if node.locator(ancestor).count() > 0:
                    return node
            except Error:
                continue
        return None

    def _container_is_one_chart(self, node: Locator, other_titles: list[str]) -> bool:
        try:
            text = node.inner_text(timeout=2000) or ""
        except Error:
            return False
        if not any(character.isdigit() for character in text):
            return False
        return not any(other in text for other in other_titles)

    def _toggle(self, label: str) -> Locator:
        return self._report_frame().get_by_role("button", name=label, exact=True)

    def _is_pressed(self, label: str) -> bool:
        button = self._toggle(label)
        pressed = (button.get_attribute("aria-pressed") or "").lower()
        if pressed == "true":
            return True
        if pressed == "false":
            return False
        selected = (button.get_attribute("aria-selected") or "").lower()
        return selected == "true"

    def _fill_input(self, label_prefix: str, value: str) -> None:
        """Fill an input by Hebrew aria-label prefix, or the English pair."""
        frame = self._report_frame()
        field = frame.locator(f"input[aria-label^='{label_prefix}']")
        english = self._DATE_LABEL_EN.get(label_prefix)
        if english:
            field = field.or_(frame.locator(f"input[aria-label^='{english}']"))
        self._commit_field(field.first, value)

    def _fill_exact(self, label: str, value: str) -> None:
        field = self._report_frame().locator(f"input[aria-label='{label}']").first
        self._commit_field(field, value)

    def _dismiss_overlay(self) -> None:
        """Close a date picker or menu whose backdrop would block the next click."""
        backdrop = self._report_frame().locator(".cdk-overlay-backdrop-showing")
        if backdrop.count() == 0:
            return
        backdrop.first.click()

    def _commit_field(self, field: Locator, value: str) -> None:
        """Fill one input. A forced click reaches it under a leftover backdrop."""
        self._dismiss_overlay()
        expect(field).to_be_visible(timeout=self.timeout)
        field.click(force=True)
        field.fill(value)
        field.press("Enter")
        self._dismiss_overlay()
