"""First page of the Alerts Analysis report: status picture.

Opens the same catalog product as page 2 and stays on the landing page.
Titles and date labels stay here. Portal login and the iframe wait stay on
ReportShell.
"""

from __future__ import annotations

import re
import time

from playwright.sync_api import Locator, Page, expect

from core.components.chart import Chart
from core.components.kpi import KPI, extract_gauge_scale
from pages.alerts_analysis.page import AlertsAnalysisPage

_SVG_MARKS = "svg rect, svg path, svg circle"
_INTEGER_TEXT = re.compile(r"^(?:\d{1,3}(?:[,\u00a0\u202f ]\d{3})+|\d+)$")
_FRACTIONAL_NUMBER = re.compile(r"\d+\.\d+")


def _plain_cell(raw: str) -> str:
    """Cell text with a doubled Power BI label collapsed to one copy."""
    text = (raw or "").strip()
    if len(text) >= 2 and len(text) % 2 == 0 and text[: len(text) // 2] == text[len(text) // 2 :]:
        return text[: len(text) // 2]
    return text


def _split_doubled(text: str) -> list[str]:
    """Split a run of doubled Power BI labels into the single labels."""
    parts: list[str] = []
    remaining = text
    while remaining:
        split_at = None
        for size in range(len(remaining) // 2, 0, -1):
            if remaining[:size] == remaining[size : size * 2]:
                split_at = size
                break
        if split_at is None:
            parts.append(remaining)
            break
        parts.append(remaining[:split_at])
        remaining = remaining[split_at * 2 :]
    return [part for part in parts if part]


def _value_tokens(text: str) -> list[int]:
    """One integer, or two-digit groups when several counts share one text node."""
    number = _whole_number(text)
    if number is None:
        return []
    if "," in text:
        return [number]
    digits = re.sub(r"\D", "", text)
    if len(digits) >= 4 and len(digits) % 2 == 0:
        return [int(digits[index : index + 2]) for index in range(0, len(digits), 2)]
    return [number]


def _whole_number(raw: str) -> int | None:
    """Integer from one cell. Thousands separators and spaces are removed."""
    text = _plain_cell(raw)
    if not text or _FRACTIONAL_NUMBER.search(text):
        return None
    if not _INTEGER_TEXT.fullmatch(text):
        return None
    digits = re.sub(r"[,\u00a0\u202f ]", "", text)
    if digits.isdigit():
        return int(digits)
    return None


class StatusPicturePage(AlertsAnalysisPage):
    """Status picture. This page does not switch to the population page."""

    UNDER_FIRE_CARD = "אזורי התרעה תחת ירי"
    RANGE_TOTAL = 'סה"כ בטווח שנבחר'
    # Live accessible name. The golden description inserts an extra ה before התרעות.
    RANKING_TITLE = "עשרת היישובים עם כמות התרעות הגבוהה ביותר"
    # Neighboring chart. Its title ends with this phrase and is not the ranking.
    _OTHER_RANKING_PHRASE = "ביממה הנוכחית"

    _CATEGORY_SCOPES = {
        "category_1_rockets": "ירי רקטות וטילים",
        "category_2_aircraft": "חדירת מחבלים",
        "category_10_terrorists": "חדירת כלי טיס עוין",
    }
    # Screen 1 picks a named operation. This window is the עם כלביא option.
    _OPERATION_RANGES = {
        ("13/06/2025", "25/06/2025"): "עם כלביא",
    }
    POPULATION_GAUGE = "אוכלוסייה מותרעת"

    def __init__(self, page: Page):
        super().__init__(page)
        # Larger budget so slow Power BI rendering does not raise LoadTimeoutError.
        self.timeout = 120_000
        page.set_default_navigation_timeout(self.timeout)
        page.set_default_timeout(self.timeout)
        self._kpi = KPI(page=page, frame=self.dashboard, timeout_ms=self.timeout)
        self._chart = Chart(page=page, frame=self.dashboard, timeout_ms=self.timeout)

    def _report_ready_locator(self) -> Locator:
        # Consistently visible Screen 1 element: the warning-zones gauge card
        # renders regardless of the selected operation, so navigation does not
        # depend on filtered chart data. No behavioral change.
        return self._iframe_phrase_locator(self.UNDER_FIRE_CARD)

    def clear_filters(self) -> None:
        """Clear every slicer, then wait until the warning-zones gauge repeats."""
        self._dismiss_overlay()
        expect(self._iframe_phrase_locator(self.UNDER_FIRE_CARD)).to_be_visible(
            timeout=self.timeout
        )
        self._slicer.clear_all()
        self._wait_until_gauge_repeats()

    def set_date_range(self, start: str, end: str) -> None:
        """Apply the golden window, then wait until the warning-zones gauge repeats.

        This page's date control is the FilterName operation list. The June
        2025 window is the עם כלביא option. Text date fields are used only
        when they are actually on the page.
        """
        self._dismiss_overlay()
        if self._date_fields_visible():
            self._fill_input("תאריך התחלה", start)
            self._fill_input("תאריך סיום", end)
        else:
            operation = self._OPERATION_RANGES.get((start, end))
            if operation is None:
                raise AssertionError(
                    f"No Screen 1 date control for {start} through {end}"
                )
            before = self._gauge_current(self.UNDER_FIRE_CARD)
            self._slicer.select("date_range", operation)
            self._wait_until_gauge_changes(before)
            return
        expect(self._iframe_phrase_locator(self.UNDER_FIRE_CARD)).to_be_visible(
            timeout=self.timeout
        )
        self._wait_until_gauge_repeats()

    def select_operation(self, name: str) -> None:
        """Select a named operation on the FilterName slicer, then wait to settle.

        Screen 1's date control is the operation list. The golden run selects
        the operation by name directly instead of mapping a date pair to an
        option, so the chosen window is explicit and data-driven.
        """
        self._dismiss_overlay()
        before = self._gauge_current(self.UNDER_FIRE_CARD)
        try:
            # Reuse the generic slicer. A missing option is surfaced below.
            self._slicer.select("date_range", name)
        except Exception as exc:
            raise AssertionError(
                f"Operation {name!r} is not a selectable option on this page"
            ) from exc
        self._wait_until_gauge_changes(before)

    def read_cards(self) -> dict[str, int]:
        """Read the two gauges. All-time numbers are the maxima. Range numbers are the current values."""
        cards: dict[str, int] = {}
        zones = self._gauge_scale(self.UNDER_FIRE_CARD)
        population = self._gauge_scale(self.POPULATION_GAUGE)
        if zones is not None and zones["maximum"] is not None:
            cards["total_warning_zones"] = int(zones["maximum"])
        if zones is not None and zones["value"] is not None:
            cards["warning_zones_under_fire"] = int(zones["value"])
        if population is not None and population["maximum"] is not None:
            cards["total_alerted_population"] = int(population["maximum"])
        if population is not None and population["value"] is not None:
            cards["alerted_population"] = int(population["value"])
        return cards

    def read_alerts_by_category(self) -> dict[str, int]:
        """Selected-range totals for the three threat cards, in page order.

        The card text does not include the section title. On this page the
        cards are aircraft (id 10), then id 2, then rockets. An empty map
        means those cards could not be read.
        """
        buttons = self._report_frame().get_by_role("button", name=self.RANGE_TOTAL)
        try:
            count = buttons.count()
        except Exception:
            return {}
        order = (
            "category_10_terrorists",
            "category_2_aircraft",
            "category_1_rockets",
        )
        if count < len(order):
            return {}
        found: dict[str, int] = {}
        for index, key in enumerate(order):
            value = self._value_on_node(buttons.nth(index))
            if value is None:
                return {}
            found[key] = value
        return found

    def read_top_10_settlements(self) -> dict[str, int]:
        """Settlement name to alert count from the ranking chart.

        The chart draws about seven rows and scrolls for the rest.
        The chart about the current and previous day is not this metric.
        An empty map means names and counts could not be paired.
        """
        found: dict[str, int] = {}
        for _ in range(12):
            found.update(self._ranking_from_text())
            if not self._scroll_ranking():
                break
        return found

    def _pairs_from_blob(self, blob: str) -> dict[str, int]:
        """Pair doubled settlement labels with the trailing count run."""
        if self._OTHER_RANKING_PHRASE in blob or "כמות התרעות" not in blob:
            return {}
        marker = "כמות התרעות"
        tail = blob.rsplit(marker, 1)[-1] if marker in blob else blob
        match = re.search(r"(\d{8,})\s*$", tail)
        if match is None:
            return {}
        values = _value_tokens(match.group(1))
        name_text = tail[: match.start()].replace("\n", "").replace("\r", "").strip()
        names: list[str] = []
        for part in _split_doubled(name_text):
            part = part.strip()
            if not part or _whole_number(part) is not None:
                continue
            if "כמות" in part or "כלביא" in part or "מבצע" in part:
                continue
            names.append(part)
        if not names or len(values) < len(names):
            return {}
        return {name: values[index] for index, name in enumerate(names)}

    def _ranking_from_text(self) -> dict[str, int]:
        """Pair settlement labels with the counts drawn after them.

        Axis ticks sit before the names. A doubled Power BI label is one name.
        The current-and-previous-day chart is not this visual.
        """
        container = self._ranking_group()
        if container is None:
            return {}
        try:
            raw_lines = container.evaluate(
                """el => {
                    const walker = document.createTreeWalker(el, NodeFilter.SHOW_TEXT);
                    const found = [];
                    let node;
                    while ((node = walker.nextNode())) {
                        const text = (node.textContent || '').replace(/\\s+/g, ' ').trim();
                        if (text) found.push(text);
                    }
                    return found;
                }"""
            )
        except Exception:
            return {}
        lines: list[str] = []
        for item in raw_lines or []:
            raw = _plain_cell(str(item))
            if not raw or self._OTHER_RANKING_PHRASE in raw:
                continue
            if lines and lines[-1] == raw:
                continue
            lines.append(raw)
        ignored = {self.RANKING_TITLE, "כמות התרעות", "כמות ההתרעות", "עם כלביא"}
        names: list[str] = []
        values: list[int] = []
        for line in lines:
            if (
                line in ignored
                or line.startswith(self.RANKING_TITLE)
                or "מבצע" in line
                or "כלביא" in line
                or "כמות" in line
                or "הקש" in line
                or "Enter" in line
            ):
                continue
            if _whole_number(line) is None:
                for part in _split_doubled(line):
                    if part in ignored or "כמות" in part or _whole_number(part) is not None:
                        continue
                    names.append(part)
                continue
            if names:
                values.extend(_value_tokens(line))
        try:
            blob = container.text_content(timeout=2000) or ""
        except Exception:
            blob = ""
        paired = self._pairs_from_blob(blob)
        if len(paired) >= len(names) and paired:
            return paired
        if names and len(values) >= len(names):
            return {name: values[index] for index, name in enumerate(names)}
        return paired

    def _ranking_group(self) -> Locator | None:
        """Longest ranking chart. The day chart is left out."""
        frame = self._report_frame()
        groups = frame.get_by_role("group", name=self.RANKING_TITLE)
        try:
            count = min(groups.count(), 8)
        except Exception:
            return None
        container = None
        best_length = -1
        for index in range(count):
            group = groups.nth(index)
            label = group.get_attribute("aria-label") or ""
            if self._OTHER_RANKING_PHRASE in label or self.RANKING_TITLE not in label:
                continue
            try:
                text = group.text_content(timeout=2000) or ""
            except Exception:
                continue
            if self._OTHER_RANKING_PHRASE in text:
                continue
            if len(text) > best_length:
                container = group
                best_length = len(text)
        return container

    def _scroll_ranking(self) -> bool:
        """Drag the ranking scrollbar down one short step.

        A short step keeps the next rows overlapping the ones already read.
        False when the labels do not change.
        """
        container = self._ranking_group()
        if container is None:
            return False
        try:
            before = container.text_content(timeout=2000) or ""
        except Exception:
            return False
        try:
            container.scroll_into_view_if_needed(timeout=2000)
            container.hover(timeout=2000)
        except Exception:
            pass
        self._drag_ranking_thumb(container)
        self.page.wait_for_timeout(250)
        try:
            after = container.text_content(timeout=2000) or ""
        except Exception:
            return False
        if after != before:
            return True
        box = container.bounding_box()
        if box is None:
            return False
        self.page.mouse.move(box["x"] + box["width"] * 0.7, box["y"] + box["height"] * 0.5)
        self.page.mouse.wheel(0, 36)
        self.page.wait_for_timeout(250)
        try:
            after = container.text_content(timeout=2000) or ""
        except Exception:
            return False
        return after != before

    def _drag_ranking_thumb(self, container: Locator) -> None:
        """Drag the narrow bar at the chart's right edge downward."""
        try:
            handle = container.evaluate_handle(
                """el => {
                    const box = el.getBoundingClientRect();
                    let best = null;
                    let bestHeight = 0;
                    for (const node of el.querySelectorAll('div')) {
                        const r = node.getBoundingClientRect();
                        if (r.width < 3 || r.width > 16 || r.height < 16) continue;
                        if (box.right - r.right > 14) continue;
                        if (r.height > box.height * 0.92) continue;
                        if (r.height > bestHeight) {
                            best = node;
                            bestHeight = r.height;
                        }
                    }
                    return best;
                }"""
            )
        except Exception:
            return
        element = handle.as_element()
        if element is None:
            return
        box = element.bounding_box()
        if box is None:
            return
        start_x = box["x"] + box["width"] / 2
        start_y = box["y"] + min(box["height"] / 2, 10)
        self.page.mouse.move(start_x, start_y)
        self.page.mouse.down()
        self.page.mouse.move(start_x, start_y + 24, steps=6)
        self.page.mouse.up()

    def _value_on_node(self, node: Locator) -> int | None:
        """Integer from the last paragraph, otherwise the node's own text."""
        try:
            paragraphs = node.locator("p")
            if paragraphs.count() > 0:
                parsed = _whole_number(paragraphs.last.inner_text(timeout=2000) or "")
                if parsed is not None:
                    return parsed
        except Exception:
            pass
        try:
            return _whole_number(node.inner_text(timeout=2000) or "")
        except Exception:
            return None

    def _range_total_in_scope(self, scope: str, others: tuple[str, ...]) -> int | None:
        """Selected-range card inside one threat section."""
        frame = self._report_frame()
        groups = frame.get_by_role("group", name=scope)
        try:
            count = min(groups.count(), 8)
        except Exception:
            count = 0
        for index in range(count):
            group = groups.nth(index)
            try:
                text = group.inner_text(timeout=2000) or ""
            except Exception:
                continue
            if scope not in text or self.RANGE_TOTAL not in text:
                continue
            if any(other in text for other in others):
                continue
            button = group.get_by_role("button", name=self.RANGE_TOTAL)
            try:
                if button.count() > 0:
                    value = self._value_on_node(button.first)
                    if value is not None:
                        return value
            except Exception:
                pass
            try:
                return int(self._kpi.number(self.RANGE_TOTAL, scope=scope))
            except Exception:
                continue
        container = self._titled_container(scope, None, required=self.RANGE_TOTAL, blocked=others)
        if container is None:
            return None
        button = container.get_by_role("button", name=self.RANGE_TOTAL)
        try:
            if button.count() > 0:
                return self._value_on_node(button.first)
        except Exception:
            return None
        return None

    def _categories_from_chart(self, title: str) -> dict[str, int]:
        """Category labels from Chart.read when mark labels already name them."""
        try:
            reading = self._chart.read(title)
        except Exception:
            return {}
        if reading.state == "empty":
            return {}
        found: dict[str, int] = {}
        for category in reading.categories:
            label = (category.label or "").strip()
            if not label or label == title or self._OTHER_RANKING_PHRASE in label:
                continue
            if not category.values or category.values[0] is None:
                continue
            found[label] = int(category.values[0])
        return found

    def _pair_labels(self, container: Locator, ignored: set[str]) -> dict[str, int]:
        """Pair non-numeric lines with bare integer mark labels, in draw order."""
        try:
            raw_text = container.inner_text(timeout=self.timeout) or ""
        except Exception:
            return {}
        if self._OTHER_RANKING_PHRASE in raw_text:
            return {}
        names: list[str] = []
        for line in raw_text.splitlines():
            text = _plain_cell(line.strip())
            if not text or text in ignored or self._OTHER_RANKING_PHRASE in text:
                continue
            if _whole_number(text) is not None:
                continue
            names.append(text)
        values: list[int] = []
        for raw in self._aria_labels(container):
            value = _whole_number(raw)
            if value is None:
                continue
            values.append(value)
        if not names or len(values) < len(names):
            return {}
        return {name: values[index] for index, name in enumerate(names)}

    def _aria_labels(self, container: Locator) -> list[str]:
        """Accessible names of SVG marks inside one visual."""
        nodes = container.locator(_SVG_MARKS)
        labels: list[str] = []
        try:
            count = min(nodes.count(), 40)
        except Exception:
            return labels
        for index in range(count):
            raw = ""
            for attr in ("aria-label", "title"):
                try:
                    value = nodes.nth(index).get_attribute(attr, timeout=500)
                except Exception:
                    value = None
                if value:
                    raw = value
                    break
            if raw:
                labels.append(raw.strip())
        return labels

    def _titled_container(
        self,
        title: str,
        blocked_phrase: str | None,
        required: str | None = None,
        blocked: tuple[str, ...] = (),
    ) -> Locator | None:
        """Nearest box that holds this title and a number, without a blocked phrase."""
        frame = self._report_frame()
        visible = frame.get_by_text(title, exact=True).filter(visible=True)
        try:
            if visible.count() == 0:
                visible = frame.get_by_text(title).filter(visible=True)
            if visible.count() == 0:
                return None
        except Exception:
            return None
        title_node = visible.first
        ancestor = (
            "ancestor::*[contains(@class,'visualContainer')"
            " or contains(@class,'visual-container')"
            " or @role='group']"
        )
        nodes = [title_node]
        for index in range(1, 12):
            node = title_node.locator(f"xpath={ancestor}[{index}]")
            try:
                if node.count() == 0:
                    break
            except Exception:
                break
            nodes.append(node)
        for node in nodes:
            try:
                text = node.inner_text(timeout=2000) or ""
            except Exception:
                continue
            if title not in text:
                continue
            if required and required not in text:
                continue
            if blocked_phrase and blocked_phrase in text:
                continue
            if any(phrase in text for phrase in blocked):
                continue
            if not any(character.isdigit() for character in text):
                continue
            return node
        return None

    def _date_fields_visible(self) -> bool:
        """True when this page shows the start-date text field."""
        field = self._report_frame().locator("input[aria-label^='תאריך התחלה']")
        try:
            return field.count() > 0 and field.first.is_visible(timeout=500)
        except Exception:
            return False

    def _gauge_scale(self, title: str):
        """Current value and maximum from the gauge image for this title."""
        token = {
            self.UNDER_FIRE_CARD: "distinct_alerted_areas",
            self.POPULATION_GAUGE: "distinct_alerted_pop",
        }.get(title)
        if token is None:
            return None
        image = self._report_frame().locator(f"[aria-label^='{token}']")
        try:
            if image.count() == 0:
                return None
            raw = image.first.get_attribute("aria-label") or ""
        except Exception:
            return None
        if not raw:
            return None
        return extract_gauge_scale(raw)

    def _gauge_current(self, title: str) -> int | None:
        """Current integer on one gauge. The maximum is not this number."""
        scale = self._gauge_scale(title)
        if scale is None or scale["value"] is None:
            return None
        return int(scale["value"])

    def _wait_until_gauge_repeats(self) -> None:
        """Return when the warning-zones gauge reads the same integer twice."""
        previous = None
        deadline = time.monotonic() + self.timeout / 1000
        while time.monotonic() < deadline:
            current = self._gauge_current(self.UNDER_FIRE_CARD)
            if previous is not None and current is not None and current == previous:
                return
            previous = current
            self.page.wait_for_timeout(400)

    def _wait_until_gauge_changes(self, before: int | None) -> None:
        """Wait until the warning-zones gauge leaves its previous integer and settles."""
        previous = None
        deadline = time.monotonic() + self.timeout / 1000
        while time.monotonic() < deadline:
            current = self._gauge_current(self.UNDER_FIRE_CARD)
            settled = previous is not None and current is not None and current == previous
            if settled and current != before:
                return
            previous = current
            self.page.wait_for_timeout(400)

    def _pair_options(self, container: Locator) -> dict[str, int]:
        """Pair settlement option labels with integer options in the same chart."""
        options = container.get_by_role("option")
        names: list[str] = []
        values: list[int] = []
        ignored = {"אתמול", "היום", "תוויות סידרה", self.RANKING_TITLE}
        try:
            count = min(options.count(), 40)
        except Exception:
            return {}
        for index in range(count):
            node = options.nth(index)
            try:
                text = _plain_cell(node.text_content(timeout=500) or "")
            except Exception:
                continue
            if not text or text in ignored or self._OTHER_RANKING_PHRASE in text:
                continue
            value = _whole_number(text)
            if value is None:
                names.append(text)
            else:
                values.append(value)
        if not names or len(values) < len(names):
            return {}
        return {name: values[index] for index, name in enumerate(names)}

    def _fill_input(self, label_prefix: str, value: str) -> None:
        field = self._report_frame().locator(
            f"input[aria-label^='{label_prefix}']"
        ).first
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
