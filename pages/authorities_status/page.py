"""Authorities Status report — Screen 1 and Screen 2 readers."""

from __future__ import annotations

import re
from collections.abc import Callable, Sequence

from playwright.sync_api import Locator, Page, expect

from config.settings import settings
from core.components.slicer import Slicer, SlicerDefinition
from core.components.virtual_grid import collect_virtualized_rows
from core.components.visual_table import VisualTable
from core.portal.page import ReportShell

_BIDI = ("\u200f", "\u200e", "\u202a", "\u202b", "\u202c")
_HEBREW = re.compile(r"[\u0590-\u05FF]")
_FILTER_ROLES = (
    ("date", "בחירת תאריך"),
    ("district", "בחירת מחוז"),
    ("sub_district", "בחירת נפה"),
)
_STATUS_HEADINGS = (
    ("coping_well", "מתמודדות", True),
    ("may_struggle", "עלולות להתקשות", False),
    ("struggling", "מתקשות", True),
)
_FACILITY_HEADINGS = (
    ("operation_centers", "מרכזי הפעלה"),
    ("protection_facilities", "מתקני מיגון"),
    ("call_centers_106", "מוקדי 106"),
)
_SKIP_CELL = {
    "פתוחים",
    "סגורים",
    "בחירת שורה",
    "בחר שורה",
    "רשות",
    "ציון",
    "גלול למעלה",
    "גלול למטה",
    "גלול שמאלה",
    "גלול ימינה",
}
_VISUAL_XPATH = (
    "xpath=ancestor::*[contains(concat(' ', normalize-space(@class), ' '), "
    "' visualContainer ')][1]"
)
_DATE_CELL = re.compile(r"\d{1,2}/\d{1,2}/\d{2,4}")
_SCREEN_2_NAV_ROLES = ("tab", "button", "menuitem", "option", "link")
_SCREEN_2_PROFILE_LABELS = (
    ("average_final_score", ("ציון סופי ממוצע",)),
    ("national_average_score", ("ממוצע ארצי",)),
    ("number_of_residents", ("מספר תושבים",)),
    ("resilience_score_percentage", ("ציון חוסן",)),
    ("defense_policy", ("מדיניות התגוננות",)),
    (
        "total_alerts_last_24h",
        ('סה"כ התרעות', "סה״כ התרעות", "התרעות ב-24", "התרעות ב־24"),
    ),
)
_SCREEN_2_PROTECTION_LABELS = (
    ("mamad_mamak", ("ממד / ממ״ק", 'ממד / ממ"ק', "ממ״ק", 'ממ"ק')),
    ("shared_shelter", ("מיגון משותף", "מקלט משותף", "מקלטים משותפים")),
    ("public_shelters_capacity", ("קיבולת מקלטים ציבוריים",)),
    ("without_shelter", ("ללא מיגון",)),
)
_SCREEN_2_SECTION_LABELS = {
    "sector_profile": ("פרופיל גזרתי",),
    "protection_data": ("נתוני מיגון",),
    "service_targets": ("יעדי השירות",),
    "data": ("מגמת ציון מחוזי",),
}


def _plain(raw) -> str:
    """Trim display text and drop Power BI bidi marks."""
    text = "" if raw is None else str(raw)
    for mark in _BIDI:
        text = text.replace(mark, "")
    return text.strip()


def _fold_quotes(text: str) -> str:
    """Treat ASCII quotes and Hebrew gershayim as the same character."""
    return (
        _plain(text)
        .replace("\u05f4", '"')
        .replace("״", '"')
        .replace("\u05f3", "'")
        .replace("׳", "'")
    )


def _quote_spellings(text: str) -> list[str]:
    """Locator variants for one Hebrew string that may mix quote marks."""
    if not text:
        return []
    variants = {
        text,
        text.replace('"', "\u05f4").replace("'", "\u05f3"),
        text.replace("\u05f4", '"').replace("\u05f3", "'"),
        text.replace("״", '"').replace("׳", "'"),
        text.replace('"', "״").replace("'", "׳"),
    }
    return [item for item in variants if item]


def _trend_from_paint(css: str) -> str:
    """Red arrow paint is down. Green arrow paint is up. Gray and white are ignored."""
    match = re.search(r"rgba?\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)", css or "")
    if match is None:
        return ""
    red, green, blue = int(match.group(1)), int(match.group(2)), int(match.group(3))
    if abs(red - green) < 18 and abs(green - blue) < 18:
        return ""
    if red > green + 25 and red > blue + 25 and red > 120:
        return "down"
    if green > red + 25 and green > blue + 15 and green > 80:
        return "up"
    return ""


class AuthoritiesStatusPage(ReportShell):
    DASHBOARD_SEARCH_TERM = "הערכת מצב רשויות"

    def __init__(self, page: Page):
        super().__init__(page)
        self.url = settings.LOGIN_URL or settings.DASHBOARD_URL
        self._screen_2_title = ""

    def _report_ready_locator(self):
        return self._iframe_phrase_locator(self.DASHBOARD_SEARCH_TERM)

    def _role_name(self, slicer_id: str) -> str:
        """Hebrew accessible name for a golden slicer id."""
        for known_id, role_name in _FILTER_ROLES:
            if known_id == slicer_id:
                return role_name
        known = ", ".join(known_id for known_id, _name in _FILTER_ROLES)
        raise KeyError(f"Unknown slicer id {slicer_id!r}. Known: {known}")

    def _slicer(
        self,
        slicer_id: str,
        role_name: str,
        settle: Callable[..., bool | None] | None = None,
    ) -> Slicer:
        return Slicer(
            page=self.page,
            frame=self._report_frame(),
            definitions=(
                SlicerDefinition(
                    id=slicer_id,
                    role_name=role_name,
                    kind="dropdown",
                ),
            ),
            settle=settle or self._screen_1_settle,
            timeout_ms=self.timeout,
        )

    def _screen_1_settle(self, kind: str = "after_select", **_kwargs) -> bool:
        """Hide a visible spinner, then require the Screen 1 ready locator.

        Returning false lets ``Slicer.select`` confirm the combobox label.
        """
        if kind != "after_select":
            return False
        self.wait_for_screen_1_idle()
        return False

    def wait_for_screen_1_idle(self) -> None:
        """Wait until a visible spinner is gone and Screen 1 is ready."""
        frame = self._report_frame()
        spinner = frame.locator("[class*='spinner'], [aria-busy='true']").filter(
            visible=True
        )
        try:
            if spinner.count() > 0:
                expect(spinner.first).to_be_hidden(timeout=self.timeout)
        except Exception:
            pass
        expect(self._report_ready_locator()).to_be_visible(timeout=self.timeout)

    def select_screen_1_filter(self, slicer_id: str, value: str) -> None:
        """Select one label. A later call does not clear labels already chosen."""
        role_name = self._role_name(slicer_id)
        if slicer_id == "date":
            self._select_date(value)
            return
        slicer = self._slicer(slicer_id, role_name)
        control = slicer.control(slicer_id)
        try:
            has_combo = control.count() > 0
        except Exception:
            has_combo = False
        if has_combo:
            slicer.select(slicer_id, value)
            return
        # District and sub-district are sandbox inputs, not report comboboxes.
        self._select_sandbox(role_name, value)
        self.wait_for_screen_1_idle()

    def _select_date(
        self,
        value: str,
        settle: Callable[..., bool | None] | None = None,
    ) -> None:
        """Open the date combobox and choose ``value``.

        ``Slicer.select`` runs when the open listbox is named ``בחירת תאריך``
        or ``SlicerDate``. Otherwise the visible row or the slicer search is used.
        """
        settle = settle or self._screen_1_settle
        role_name = self._role_name("date")
        control = self._slicer("date", role_name, settle=settle).control("date")
        if control.count() == 0:
            raise KeyError(
                f"Slicer 'date' has no dropdown. Tried {role_name!r}."
            )
        expect(control).to_be_visible(timeout=self.timeout)
        control.click(force=True)
        listbox_name, listbox_frame = self._date_listbox()
        if listbox_name in {role_name, "SlicerDate"} and listbox_frame is not None:
            self.page.keyboard.press("Escape")
            Slicer(
                page=self.page,
                frame=listbox_frame,
                definitions=(
                    SlicerDefinition(
                        id="date",
                        role_name=listbox_name,
                        kind="dropdown",
                    ),
                ),
                settle=settle,
                timeout_ms=self.timeout,
            ).select("date", value)
        else:
            self._pick_open_date(control, value)
        settle("after_select")
        shown = _plain(control.inner_text(timeout=self.timeout))
        if value not in shown:
            raise AssertionError(
                f"Slicer 'date' combobox {shown!r} does not contain {value!r}"
            )

    def _date_listbox(self) -> tuple[str, object]:
        """Accessible name and frame of a visible open listbox, if one exists."""
        for frame in self.page.frames:
            boxes = frame.get_by_role("listbox")
            try:
                count = boxes.count()
            except Exception:
                continue
            for index in range(count):
                box = boxes.nth(index)
                try:
                    if not box.is_visible():
                        continue
                except Exception:
                    continue
                label = _plain(box.get_attribute("aria-label") or "")
                return label, frame
        return "", None

    def _pick_open_date(self, control: Locator, value: str) -> None:
        """Scroll the open date list until ``value`` is visible, then click it."""
        for _ in range(20):
            choice = self._visible_date_choice(value)
            if choice is not None:
                choice.click(force=True)
                self.page.keyboard.press("Escape")
                return
            if not self._scroll_date_list():
                break
        self._raise_date_not_visible(control, value)

    def _date_pattern(self, value: str) -> re.Pattern[str]:
        """Match the date even when the slash is a unicode divider."""
        parts = [re.escape(part) for part in re.split(r"\D+", value) if part]
        return re.compile(r"\D*".join(parts))

    def _visible_date_choice(self, value: str) -> Locator | None:
        """A visible radio, checkbox, option, or slicer row for ``value``."""
        pattern = self._date_pattern(value)
        for frame in self.page.frames:
            candidates = (
                frame.get_by_role("radio", name=pattern),
                frame.get_by_role("checkbox", name=pattern),
                frame.get_by_role("option", name=pattern),
                frame.locator("[class*='slicerText'], [class*='slicerItem']").filter(
                    has_text=pattern
                ),
            )
            for candidate in candidates:
                try:
                    count = min(candidate.count(), 8)
                except Exception:
                    continue
                for index in range(count):
                    node = candidate.nth(index)
                    try:
                        if node.is_visible():
                            return node
                    except Exception:
                        continue
        return None

    def _date_scroll_container(self) -> Locator | None:
        """Visible ``scrollRegion`` that holds the open date rows."""
        for frame in self.page.frames:
            regions = frame.locator("[class*='scrollRegion']")
            try:
                count = regions.count()
            except Exception:
                continue
            for index in range(count):
                region = regions.nth(index)
                try:
                    if not region.is_visible():
                        continue
                    if region.locator(
                        "[role='radio'], [role='checkbox'], [role='option'], "
                        "[class*='slicerText']"
                    ).count() == 0:
                        continue
                except Exception:
                    continue
                return region
        return None

    def _scroll_date_list(self) -> bool:
        """Move the open list down. False means ``scrollTop`` did not change."""
        container = self._date_scroll_container()
        if container is not None:
            moved = self._bump_scroll_top(container)
            if moved is not None:
                return moved
            try:
                container.press("PageDown")
            except Exception:
                self.page.keyboard.press("PageDown")
            return True
        row = self._visible_date_row()
        if row is not None:
            moved = self._bump_scroll_top(row)
            if moved is not None:
                return moved
        self.page.keyboard.press("PageDown")
        return True

    def _bump_scroll_top(self, node: Locator) -> bool | None:
        """Add 150 to the scrollable node. None when no scroller was found."""
        try:
            return node.evaluate(
                """node => {
                    const canScroll = (el) =>
                        !!el && el.scrollHeight > el.clientHeight + 1;
                    let target = canScroll(node) ? node : null;
                    if (!target) {
                        for (const el of node.querySelectorAll("*")) {
                            if (canScroll(el)) {
                                target = el;
                                break;
                            }
                        }
                    }
                    if (!target) {
                        let parent = node.parentElement;
                        while (parent) {
                            if (canScroll(parent)) {
                                target = parent;
                                break;
                            }
                            parent = parent.parentElement;
                        }
                    }
                    if (!target) {
                        return null;
                    }
                    const before = target.scrollTop;
                    target.scrollTop = before + 150;
                    return target.scrollTop !== before;
                }"""
            )
        except Exception:
            return None

    def _visible_date_row(self) -> Locator | None:
        """Any visible date row, used to find the list when it has no scroll region."""
        for frame in self.page.frames:
            rows = frame.locator(
                "[role='radio'], [role='checkbox'], [class*='slicerText']"
            )
            try:
                count = min(rows.count(), 8)
            except Exception:
                continue
            for index in range(count):
                row = rows.nth(index)
                try:
                    if row.is_visible():
                        return row
                except Exception:
                    continue
        return None

    def _raise_date_not_visible(self, control: Locator, value: str) -> None:
        """Fail with the rows on screen, same shape as the previous date error."""
        expanded = _plain(control.get_attribute("aria-expanded") or "")
        if expanded != "true":
            control.click(force=True)
        labels: list[str] = []
        for frame in self.page.frames:
            nodes = frame.locator(
                "[role='radio'], [role='checkbox'], [class*='slicerText']"
            )
            try:
                count = min(nodes.count(), 8)
            except Exception:
                continue
            for index in range(count):
                node = nodes.nth(index)
                try:
                    if not node.is_visible():
                        continue
                    labels.append(_plain(node.inner_text(timeout=300))[:40])
                except Exception:
                    continue
        raise AssertionError(
            f"Open date option {value!r} was not visible. rows={labels or 'none'}"
        )

    def _sandbox_input(self, placeholder: str) -> tuple[Locator | None, object]:
        """Smart-filter input inside the visual sandbox."""
        for frame in self.page.frames:
            url = frame.url or ""
            if "sandbox" not in url.lower():
                continue
            field = frame.locator(f"input[placeholder='{placeholder}']")
            try:
                if field.count() > 0:
                    return field.first, frame
            except Exception:
                continue
        return None, None

    def _select_sandbox(self, placeholder: str, value: str) -> None:
        """Add one chip in the sandbox multi-select. Do not clear existing chips."""
        field, frame = self._sandbox_input(placeholder)
        if field is None or frame is None:
            raise KeyError(
                f"Slicer {placeholder!r} has no dropdown. Tried {placeholder!r}."
            )
        shell = field.locator(
            "xpath=ancestor::ul[contains(@class, 'TokensContainer')][1]"
        )
        try:
            if shell.count() > 0:
                shell.click(timeout=5000)
        except Exception:
            pass
        field.click(force=True)
        field.fill(value, force=True)
        choice = frame.locator("li").get_by_text(value, exact=True)
        try:
            if choice.count() > 0 and choice.first.is_visible():
                choice.first.click(force=True)
            else:
                field.press("Enter")
        except Exception:
            field.press("Enter")
        self.page.keyboard.press("Escape")

    def _chips(self, placeholder: str) -> list[str]:
        """Selected labels in one sandbox box. The placeholder is not a chip."""
        field, _frame = self._sandbox_input(placeholder)
        if field is None:
            return []
        shell = field.locator(
            "xpath=ancestor::ul[contains(@class, 'TokensContainer')][1]"
        )
        try:
            if shell.count() == 0:
                return []
            raw = shell.inner_text(timeout=self.timeout) or ""
        except Exception:
            return []
        chips: list[str] = []
        for line in raw.splitlines():
            cleaned = (
                _plain(line).replace("×", "").replace("✕", "").replace("✖", "").strip()
            )
            if not cleaned or cleaned == placeholder or cleaned.startswith("בחר"):
                continue
            chips.append(cleaned)
        return chips

    def section_anchor_visible(self, section: str) -> bool:
        """True when that Screen 1 block is on the landing page."""
        try:
            if section == "date":
                control = self._report_frame().get_by_role(
                    "combobox", name="בחירת תאריך", exact=True
                )
                return control.count() > 0 and control.first.is_visible()
            if section == "filters":
                field, _frame = self._sandbox_input("בחירת מחוז")
                if field is None:
                    return False
                return field.is_visible()
            if section == "survey_status":
                return self._document_visible("רשויות הזינו את הסקר")
            if section == "authorities_status":
                return self._document_visible("מתמודדות", exact=True)
            if section == "facilities":
                return self._document_visible("מרכזי הפעלה")
            if section == "missing_daily_report":
                return self._document_visible("לא הוזן")
        except Exception:
            return False
        return False

    def _document_visible(self, label: str, *, exact: bool = False) -> bool:
        node = self._report_frame().get_by_role("document", name=label, exact=exact)
        return node.count() > 0 and node.first.is_visible()

    def _section(self, label: str, *, exact: bool = False) -> Locator | None:
        """Smallest visual that holds this heading and its numbers or grid."""
        frame = self._report_frame()
        title = frame.get_by_role("document", name=label, exact=exact)
        try:
            if title.count() == 0:
                return None
        except Exception:
            return None
        node = title.first
        for _ in range(6):
            host = node.locator(_VISUAL_XPATH)
            try:
                if host.count() == 0:
                    return node
            except Exception:
                return node
            current = host.first
            try:
                if current.locator("svg[aria-label], [role='grid']").count() > 0:
                    return current
            except Exception:
                return current
            node = current
        return node

    def _svg_text(self, section: Locator, aria_prefix: str) -> str:
        """Displayed digit of the first SVG whose accessible name starts with ``aria_prefix``."""
        node = section.locator(f"svg[aria-label^='{aria_prefix}']")
        try:
            if node.count() == 0:
                return ""
        except Exception:
            return ""
        return self._digit_text(node)

    def _digit_text(self, svg: Locator) -> str:
        """Digit painted inside ``svg``. Empty when that text never appears."""
        digit = re.compile(r"\d")
        try:
            expect(svg.first).to_be_visible(timeout=self.timeout)
        except Exception:
            return ""
        try:
            label = _plain(svg.first.get_attribute("aria-label") or "")
        except Exception:
            label = ""
        numbers = re.findall(r"\d+", label)
        if numbers:
            return numbers[0]
        text = svg.first.locator("text, tspan").filter(has_text=digit)
        try:
            expect(text.first).to_be_visible(timeout=self.timeout)
            expect(text.first).to_have_text(digit, timeout=self.timeout)
            return _plain(text.first.text_content(timeout=self.timeout) or "")
        except Exception:
            pass
        try:
            expect(svg.first).to_have_text(digit, timeout=self.timeout)
            return _plain(svg.first.text_content(timeout=self.timeout) or "")
        except Exception:
            return ""

    def read_screen_1_metrics(self) -> dict:
        """Screen 1 date, filters, survey, status, facilities, and missing report."""
        expect(self._report_ready_locator()).to_be_visible(timeout=self.timeout)
        district = self._chips("בחירת מחוז")
        return {
            "date": self._read_date(),
            "filters": {
                "district": district[0] if district else "",
                "sub_district": self._chips("בחירת נפה"),
            },
            "survey_status": self._read_survey_status(),
            "authorities_status": self._read_authorities_status(),
            "facilities": self._read_facilities(),
            "missing_daily_report": self._read_missing_daily_report(),
        }

    def _read_date(self) -> str:
        control = self._report_frame().get_by_role(
            "combobox", name="בחירת תאריך", exact=True
        )
        try:
            if control.count() == 0:
                return ""
            return _plain(control.first.inner_text(timeout=self.timeout))
        except Exception:
            return ""

    def _survey_measure_text(self, selector: str) -> str:
        """Digit painted inside one survey SVG. Empty when that text never appears."""
        return self._digit_text(self._report_frame().locator(selector))

    def _count_for_heading(self, label: str, *, exact: bool) -> str:
        """Status count nearest this heading. The column grid and the number sit apart."""
        frame = self._report_frame()
        heading = frame.get_by_role("document", name=label, exact=exact)
        try:
            if heading.count() == 0:
                return ""
            found = heading.first.evaluate(
                """(node) => {
                  const prefix = 'count_records';
                  const stale = node.ownerDocument.querySelector(
                    '[data-authorities-count="active"]'
                  );
                  if (stale) stale.removeAttribute('data-authorities-count');
                  const box = node.getBoundingClientRect();
                  const cx = box.left + box.width / 2;
                  const cy = box.top + box.height / 2;
                  let best = null;
                  let bestDist = Infinity;
                  for (const svg of node.ownerDocument.querySelectorAll('svg[aria-label]')) {
                    const name = svg.getAttribute('aria-label') || '';
                    if (!name.startsWith(prefix)) continue;
                    const rect = svg.getBoundingClientRect();
                    if (rect.width === 0 && rect.height === 0) continue;
                    const dist = Math.hypot(
                      rect.left + rect.width / 2 - cx,
                      rect.top + rect.height / 2 - cy
                    );
                    if (dist < bestDist) {
                      bestDist = dist;
                      best = svg;
                    }
                  }
                  if (!best) return false;
                  best.setAttribute('data-authorities-count', 'active');
                  return true;
                }"""
            )
        except Exception:
            return ""
        if not found:
            return ""
        svg = frame.locator('svg[data-authorities-count="active"]')
        try:
            return self._digit_text(svg)
        finally:
            try:
                svg.first.evaluate(
                    "node => node.removeAttribute('data-authorities-count')"
                )
            except Exception:
                pass

    def _grid_near_heading(self, label: str, *, exact: bool) -> Locator | None:
        """Authority grid nearest this heading. The count visual does not contain it."""
        frame = self._report_frame()
        heading = frame.get_by_role("document", name=label, exact=exact)
        try:
            if heading.count() == 0:
                return None
            found = heading.first.evaluate(
                """(node) => {
                  const stale = node.ownerDocument.querySelector(
                    '[data-authorities-grid="active"]'
                  );
                  if (stale) stale.removeAttribute('data-authorities-grid');
                  const box = node.getBoundingClientRect();
                  const cx = box.left + box.width / 2;
                  const cy = box.bottom;
                  let best = null;
                  let bestDist = Infinity;
                  for (const grid of node.ownerDocument.querySelectorAll('[role="grid"]')) {
                    const rect = grid.getBoundingClientRect();
                    if (rect.width < 20 || rect.height < 20) continue;
                    const dist = Math.hypot(
                      rect.left + rect.width / 2 - cx,
                      rect.top - cy
                    );
                    if (dist < bestDist) {
                      bestDist = dist;
                      best = grid;
                    }
                  }
                  if (!best) return false;
                  best.setAttribute('data-authorities-grid', 'active');
                  return true;
                }"""
            )
        except Exception:
            return None
        if not found:
            return None
        return frame.locator('[data-authorities-grid="active"]').first

    def _read_survey_status(self) -> dict:
        """Filled count and the out-of total from the report-frame measure SVGs."""
        return {
            "filled": self._survey_measure_text(
                "svg[aria-label^='GOALS_COUNT_MUNI']"
            ),
            "out_of": self._survey_measure_text("svg[aria-label*='Muni_Code']"),
        }

    def _read_authorities_status(self) -> dict:
        found = {}
        for key, heading, exact in _STATUS_HEADINGS:
            section = self._section(heading, exact=exact)
            count = ""
            if section is not None:
                count = self._svg_text(section, "count_records")
            if not count:
                count = self._count_for_heading(heading, exact=exact)
            grid = self._grid_near_heading(heading, exact=exact)
            if grid is None and section is not None:
                nested = section.get_by_role("grid")
                try:
                    if nested.count() > 0:
                        grid = nested.first
                except Exception:
                    grid = None
            found[key] = {
                "count": count,
                "authorities": self._status_rows(grid) if grid is not None else [],
            }
        return found

    def _header_index(self, grid: Locator, name: str) -> int:
        headers = grid.get_by_role("columnheader")
        try:
            count = headers.count()
        except Exception:
            return -1
        for index in range(count):
            label = _plain(headers.nth(index).inner_text(timeout=500) or "")
            if name in label:
                return index
        return -1

    def _row_trend(self, row: Locator) -> str:
        """Arrow word from an accessible name, otherwise from the triangle fill."""
        try:
            signals = row.evaluate(
                """(node) => {
                  const labels = [];
                  for (const el of node.querySelectorAll('[aria-label], [title]')) {
                    labels.push(
                      el.getAttribute('aria-label') || el.getAttribute('title') || ''
                    );
                  }
                  const paints = [];
                  for (const shape of node.querySelectorAll('path, polygon, circle')) {
                    const style = window.getComputedStyle(shape);
                    paints.push(style.fill || '');
                    paints.push(shape.getAttribute('fill') || '');
                  }
                  return {labels, paints};
                }"""
            )
        except Exception:
            signals = {}
        if not isinstance(signals, dict):
            return ""
        for label in signals.get("labels") or []:
            word = _plain(label)
            folded = word.lower()
            if folded in {"up", "down", "flat"}:
                return folded
            if "כלפי מטה" in word:
                return "down"
            if "כלפי מעלה" in word:
                return "up"
        for paint in signals.get("paints") or []:
            trend = _trend_from_paint(paint)
            if trend:
                return trend
        return ""

    def _status_rows(self, grid: Locator) -> list[dict]:
        def read_visible(current: Locator) -> list[dict]:
            name_index = self._header_index(current, "רשות")
            score_index = self._header_index(current, "ציון")
            rows = current.get_by_role("row")
            found: list[dict] = []
            try:
                count = rows.count()
            except Exception:
                return found
            for index in range(count):
                row = rows.nth(index)
                try:
                    if row.get_by_role("columnheader").count() > 0:
                        continue
                    cells = row.get_by_role("gridcell")
                    texts = []
                    for cell_index in range(cells.count()):
                        raw = cells.nth(cell_index).inner_text(timeout=500) or ""
                        texts.append(_plain(raw.split("\n")[0]))
                    name = texts[name_index] if 0 <= name_index < len(texts) else ""
                    score = texts[score_index] if 0 <= score_index < len(texts) else ""
                    if not name:
                        for text in texts:
                            if text in _SKIP_CELL or not text:
                                continue
                            if _HEBREW.search(text):
                                name = text
                            elif re.search(r"\d", text) and not score:
                                score = text
                    if not name:
                        continue
                    item = {"name": name, "score": score}
                    trend = self._row_trend(row)
                    if trend:
                        item["trend"] = trend
                    found.append(item)
                except Exception:
                    continue
            return found

        return collect_virtualized_rows(
            grid,
            read_visible,
            lambda row: row.get("name", ""),
            timeout_ms=self.timeout,
        )

    def _read_facilities(self) -> dict:
        found = {}
        for key, heading in _FACILITY_HEADINGS:
            section = self._section(heading)
            if section is None:
                sides = {
                    "open": {"count": "", "authorities": []},
                    "closed": {"count": "", "authorities": []},
                }
            else:
                sides = self._facility_sides(section)
            near = self._facility_near(heading)
            for side_name in ("open", "closed"):
                if not sides[side_name]["count"]:
                    sides[side_name]["count"] = near[side_name]["count"]
                if not sides[side_name]["authorities"]:
                    sides[side_name]["authorities"] = near[side_name]["authorities"]
                if (
                    not sides[side_name]["authorities"]
                    and sides[side_name]["count"] not in ("", "0")
                ):
                    word = "פתוחים" if side_name == "open" else "סגורים"
                    sides[side_name]["authorities"] = self._names_under(heading, word)
            block = {
                "open": sides["open"],
                "closed": sides["closed"],
            }
            if key == "operation_centers":
                block["unknown_in"] = self._survey_measure_text(
                    "svg[aria-label^='unknownCenter']"
                )
            if key == "protection_facilities":
                block["partially_open_count"] = self._survey_measure_text(
                    "svg[aria-label^='openPartMigun']"
                )
            found[key] = block
        return found

    def _names_under(self, heading: str, word: str) -> list[str]:
        """Hebrew names in the column under ``word``, nearest this facility heading."""
        frame = self._report_frame()
        try:
            names = frame.locator("body").evaluate(
                """(root, payload) => {
                  const plain = (value) => (value || '')
                    .replace(/[\\u200e\\u200f\\u202a-\\u202c]/g, '')
                    .replace(/\\s+/g, ' ')
                    .trim();
                  const hebrew = /[\\u0590-\\u05FF]/;
                  let title = null;
                  let titleLen = Infinity;
                  for (const el of root.querySelectorAll('[role="document"]')) {
                    const name = plain(el.getAttribute('aria-label') || el.textContent || '');
                    if (!name.includes(payload.heading) || name.length >= titleLen) continue;
                    titleLen = name.length;
                    title = el;
                  }
                  if (!title) return [];
                  const titleBox = title.getBoundingClientRect();
                  const tx = titleBox.left + titleBox.width / 2;
                  const ty = titleBox.bottom;
                  let label = null;
                  let labelDist = Infinity;
                  for (const el of root.querySelectorAll('*')) {
                    if (el.childElementCount) continue;
                    if (plain(el.textContent) !== payload.word) continue;
                    const rect = el.getBoundingClientRect();
                    if (rect.width === 0 || rect.height === 0) continue;
                    const dist = Math.hypot(rect.left + rect.width / 2 - tx, rect.top - ty);
                    if (dist < labelDist) {
                      labelDist = dist;
                      label = rect;
                    }
                  }
                  if (!label) return [];
                  const labelX = label.left + label.width / 2;
                  const found = [];
                  const seen = new Set();
                  for (const el of root.querySelectorAll('*')) {
                    if (el.childElementCount) continue;
                    const text = plain(el.textContent);
                    if (!text || !hebrew.test(text) || text === payload.word) continue;
                    if (text === 'פתוחים' || text === 'סגורים' || text === 'רשות') continue;
                    const rect = el.getBoundingClientRect();
                    if (rect.width === 0 || rect.height === 0) continue;
                    const sameCol = Math.abs(rect.left + rect.width / 2 - labelX) < 140;
                    const below = rect.top >= label.top - 4 && rect.top < label.bottom + 260;
                    if (!sameCol || !below || seen.has(text)) continue;
                    seen.add(text);
                    found.push(text);
                  }
                  return found;
                }""",
                {"heading": heading, "word": word},
            )
        except Exception:
            return []
        if not isinstance(names, list):
            return []
        return [str(name) for name in names if name]

    def _facility_near(self, heading: str) -> dict:
        """Open and closed counts nearest this facility heading."""
        sides = {
            "open": {"count": "", "authorities": []},
            "closed": {"count": "", "authorities": []},
        }
        frame = self._report_frame()
        try:
            paired = frame.locator("body").evaluate(
                """(root, heading) => {
                  const plain = (value) => (value || '')
                    .replace(/[\\u200e\\u200f\\u202a-\\u202c]/g, '')
                    .replace(/\\s+/g, ' ')
                    .trim();
                  let title = null;
                  let titleLen = Infinity;
                  for (const el of root.querySelectorAll('[role="document"]')) {
                    const name = plain(el.getAttribute('aria-label') || el.textContent || '');
                    if (!name.includes(heading) || name.length >= titleLen) continue;
                    titleLen = name.length;
                    title = el;
                  }
                  if (!title) return {open: '', closed: ''};
                  const box = title.getBoundingClientRect();
                  const cx = box.left + box.width / 2;
                  const cy = box.bottom;
                  const svgs = [];
                  for (const svg of root.querySelectorAll('svg[aria-label]')) {
                    const label = svg.getAttribute('aria-label') || '';
                    if (!label.includes('ספירת רשומות')) continue;
                    const rect = svg.getBoundingClientRect();
                    if (rect.width === 0 && rect.height === 0) continue;
                    const matched = label.match(/\\d+/);
                    svgs.push({
                      dist: Math.hypot(
                        rect.left + rect.width / 2 - cx,
                        rect.top + rect.height / 2 - cy
                      ),
                      number: matched ? matched[0] : '',
                      x: rect.left + rect.width / 2,
                      y: rect.top + rect.height / 2,
                    });
                  }
                  svgs.sort((a, b) => a.dist - b.dist);
                  const labels = [];
                  for (const el of root.querySelectorAll('*')) {
                    if (el.childElementCount) continue;
                    const text = plain(el.textContent);
                    if (text !== 'פתוחים' && text !== 'סגורים') continue;
                    const rect = el.getBoundingClientRect();
                    if (rect.width === 0 && rect.height === 0) continue;
                    labels.push({
                      side: text === 'פתוחים' ? 'open' : 'closed',
                      x: rect.left + rect.width / 2,
                      y: rect.top + rect.height / 2,
                    });
                  }
                  const counts = {open: '', closed: ''};
                  for (const svg of svgs.slice(0, 2)) {
                    let best = null;
                    let bestDist = Infinity;
                    for (const label of labels) {
                      const dist = Math.hypot(label.x - svg.x, label.y - svg.y);
                      if (dist < bestDist) {
                        bestDist = dist;
                        best = label;
                      }
                    }
                    if (!best || counts[best.side]) continue;
                    counts[best.side] = svg.number;
                    let grid = null;
                    let gridDist = Infinity;
                    for (const candidate of root.querySelectorAll('[role="grid"]')) {
                      if (candidate.getAttribute('data-facility-side')) continue;
                      const rect = candidate.getBoundingClientRect();
                      if (rect.width < 20 || rect.height < 20) continue;
                      const dist = Math.hypot(
                        rect.left + rect.width / 2 - best.x,
                        rect.top - best.y
                      );
                      if (dist < gridDist) {
                        gridDist = dist;
                        grid = candidate;
                      }
                    }
                    if (grid) grid.setAttribute('data-facility-side', best.side);
                  }
                  return counts;
                }""",
                heading,
            )
        except Exception:
            paired = None
        if isinstance(paired, dict):
            sides["open"]["count"] = paired.get("open") or ""
            sides["closed"]["count"] = paired.get("closed") or ""
        for side_name in ("open", "closed"):
            grid = frame.locator(f'[data-facility-side="{side_name}"]')
            try:
                if grid.count() > 0:
                    sides[side_name]["authorities"] = self._name_rows(grid.first)
            except Exception:
                continue
        return sides

    def _facility_sides(self, section: Locator) -> dict:
        """Open and closed counts plus authority names, paired by the nearby label."""
        sides = {
            "open": {"count": "", "authorities": []},
            "closed": {"count": "", "authorities": []},
        }
        try:
            paired = section.evaluate(
                """(root) => {
                  const plain = (value) => (value || '')
                    .replace(/[\\u200e\\u200f\\u202a-\\u202c]/g, '')
                    .replace(/\\s+/g, ' ')
                    .trim();
                  function side(node) {
                    let current = node;
                    for (let depth = 0; depth < 10 && current; depth += 1) {
                      const text = plain(current.innerText || '');
                      const open = text.includes('פתוחים');
                      const closed = text.includes('סגורים');
                      if (open !== closed) return open ? 'open' : 'closed';
                      if (current === root) break;
                      current = current.parentElement;
                    }
                    return '';
                  }
                  const counts = { open: '', closed: '' };
                  for (const svg of root.querySelectorAll('svg[aria-label]')) {
                    const label = svg.getAttribute('aria-label') || '';
                    if (!label.includes('ספירת רשומות')) continue;
                    const which = side(svg);
                    if (!which || counts[which]) continue;
                    const matched = label.match(/\d+/);
                    counts[which] = matched ? matched[0] : plain(svg.textContent);
                  }
                  return counts;
                }"""
            )
        except Exception:
            paired = {"open": "", "closed": ""}
        sides["open"]["count"] = paired.get("open", "") if isinstance(paired, dict) else ""
        sides["closed"]["count"] = paired.get("closed", "") if isinstance(paired, dict) else ""
        grids = section.get_by_role("grid")
        try:
            count = grids.count()
        except Exception:
            count = 0
        for index in range(count):
            grid = grids.nth(index)
            try:
                which = grid.evaluate(
                    """(node) => {
                      const plain = (value) => (value || '')
                        .replace(/[\\u200e\\u200f\\u202a-\\u202c]/g, '')
                        .replace(/\\s+/g, ' ')
                        .trim();
                      let current = node;
                      for (let depth = 0; depth < 10 && current; depth += 1) {
                        const text = plain(current.innerText || '');
                        const open = text.includes('פתוחים');
                        const closed = text.includes('סגורים');
                        if (open !== closed) return open ? 'open' : 'closed';
                        current = current.parentElement;
                      }
                      return '';
                    }"""
                )
            except Exception:
                which = ""
            if which not in sides:
                continue
            sides[which]["authorities"] = self._name_rows(grid)
        return sides

    def _name_rows(self, grid: Locator) -> list[str]:
        def read_visible(current: Locator) -> list[dict[str, str]]:
            rows = current.get_by_role("row")
            found: list[dict[str, str]] = []
            try:
                count = rows.count()
            except Exception:
                return found
            for index in range(count):
                row = rows.nth(index)
                try:
                    if row.get_by_role("columnheader").count() > 0:
                        continue
                    cells = row.get_by_role("gridcell")
                    name = ""
                    for cell_index in range(cells.count()):
                        raw = cells.nth(cell_index).inner_text(timeout=500) or ""
                        text = _plain(raw.split("\n")[0])
                        if not text or text in _SKIP_CELL or not _HEBREW.search(text):
                            continue
                        name = text
                        break
                    if name:
                        found.append({"name": name})
                except Exception:
                    continue
            return found

        rows = collect_virtualized_rows(
            grid,
            read_visible,
            lambda row: row.get("name", ""),
            timeout_ms=self.timeout,
        )
        return [row["name"] for row in rows if row.get("name")]

    def _read_missing_daily_report(self) -> dict:
        section = self._section("לא הוזן")
        count = self._survey_measure_text("svg[aria-label*='did enter data']")
        names: list[str] = []
        if section is None:
            return {"count": count, "authorities": names}
        grids = section.get_by_role("grid")
        try:
            if grids.count() > 0:
                names = self._name_rows(grids.first)
        except Exception:
            names = []
        return {"count": count, "authorities": names}

    def _screen_2_page_name(self) -> str:
        """Trailing segment of the stored Screen 2 title."""
        title = self._screen_2_title or ""
        if " - " in title:
            return title.rsplit(" - ", 1)[-1].strip()
        return title

    def _screen_2_ready_locator(self) -> Locator:
        """Exact page-name text, including quote variants."""
        frame = self._report_frame()
        locator: Locator | None = None
        for name in _quote_spellings(self._screen_2_page_name()):
            piece = frame.get_by_text(name, exact=True)
            locator = piece if locator is None else locator.or_(piece)
        if locator is None:
            return frame.get_by_text("\u0000", exact=True)
        return locator

    def _screen_2_settle(self, kind: str = "after_select", **_kwargs) -> bool:
        """Hide a visible spinner, then require the Screen 2 page name.

        Returning false lets ``Slicer.select`` confirm the combobox label.
        """
        if kind != "after_select":
            return False
        self.wait_for_screen_2_idle()
        return False

    def wait_for_screen_2_idle(self) -> None:
        """Wait until a visible spinner is gone and Screen 2 is ready."""
        frame = self._report_frame()
        spinner = frame.locator("[class*='spinner'], [aria-busy='true']").filter(
            visible=True
        )
        try:
            if spinner.count() > 0:
                expect(spinner.first).to_be_hidden(timeout=self.timeout)
        except Exception:
            pass
        expect(self._screen_2_ready_locator().first).to_be_visible(timeout=self.timeout)

    def _page_nav_labels(self, title: str) -> list[str]:
        """Full title and trailing page name, each quote spelling once."""
        labels: list[str] = []
        seen: set[str] = set()
        for variant in _quote_spellings(title):
            pieces = [variant]
            if " - " in variant:
                pieces.append(variant.rsplit(" - ", 1)[-1].strip())
            for piece in pieces:
                if piece and piece not in seen:
                    seen.add(piece)
                    labels.append(piece)
        return labels

    def _nav_name_matches(self, actual: str, labels: Sequence[str]) -> bool:
        """True when a control name equals a label or ends with the page name."""
        folded = " ".join(_fold_quotes(actual).replace(".", " ").split())
        for label in labels:
            needle = " ".join(_fold_quotes(label).split())
            if not needle:
                continue
            if folded == needle or folded.endswith(needle):
                return True
        return False

    def _click_page_nav(self, labels: Sequence[str]) -> bool:
        """Click the first visible page-navigation control matching ``labels``."""
        frame = self._report_frame()
        for role in _SCREEN_2_NAV_ROLES:
            try:
                nodes = frame.get_by_role(role).filter(visible=True)
                count = min(nodes.count(), 30)
            except Exception:
                continue
            for index in range(count):
                node = nodes.nth(index)
                try:
                    name = _plain(node.get_attribute("aria-label") or "")
                    if not name:
                        name = _plain(node.inner_text(timeout=1000) or "")
                except Exception:
                    continue
                if not self._nav_name_matches(name, labels):
                    continue
                node.click(force=True, timeout=5000)
                return True
        return False

    def _locator_visible(self, locator: Locator) -> bool:
        try:
            count = locator.count()
        except Exception:
            return False
        for index in range(min(count, 8)):
            try:
                if locator.nth(index).is_visible():
                    return True
            except Exception:
                continue
        return False

    def open_screen_2(self, title: str) -> None:
        """Open the Screen 2 page named by the golden title. Do not assert it."""
        self._screen_2_title = title
        labels = self._page_nav_labels(title)
        opened = self._click_page_nav(labels)
        if not opened and not self._locator_visible(self._screen_2_ready_locator()):
            raise AssertionError(
                f"Screen 2 navigation control for {title!r} was not visible"
            )
        self.wait_for_screen_2_idle()

    def select_screen_2_filter(self, slicer_id: str, value: str) -> None:
        """Select one label on Screen 2. A later call does not clear prior labels."""
        role_name = self._role_name(slicer_id)
        if slicer_id == "date":
            self._select_date(value, settle=self._screen_2_settle)
            return
        slicer = self._slicer(slicer_id, role_name, settle=self._screen_2_settle)
        control = slicer.control(slicer_id)
        try:
            has_combo = control.count() > 0
        except Exception:
            has_combo = False
        if has_combo:
            slicer.select(slicer_id, value)
            return
        self._select_sandbox(role_name, value)
        self.wait_for_screen_2_idle()

    def _first_visible_phrase(self, labels: Sequence[str]) -> Locator | None:
        """First visible heading, document, image, or text for these labels."""
        frame = self._report_frame()
        for label in labels:
            for variant in _quote_spellings(label):
                candidates = (
                    frame.get_by_role("document", name=variant),
                    frame.get_by_role("heading", name=variant),
                    frame.get_by_role("img", name=variant),
                    frame.get_by_text(variant, exact=True),
                    frame.get_by_text(variant, exact=False),
                )
                for candidate in candidates:
                    try:
                        if candidate.count() > 0 and candidate.first.is_visible():
                            return candidate.first
                    except Exception:
                        continue
        return None

    def _phrase_visible(self, labels: Sequence[str]) -> bool:
        """True when any locator candidate for these headings is on screen."""
        return self._first_visible_phrase(labels) is not None

    def screen_2_section_visible(self, section: str) -> bool:
        """True when that Screen 2 block is on the open page."""
        try:
            if section == "date":
                control = self._report_frame().get_by_role(
                    "combobox", name="בחירת תאריך", exact=True
                )
                return control.count() > 0 and control.first.is_visible()
            if section == "filters":
                field, _frame = self._sandbox_input("בחירת מחוז")
                if field is not None and field.is_visible():
                    return True
                control = self._report_frame().get_by_role(
                    "combobox", name="בחירת מחוז", exact=True
                )
                return control.count() > 0 and control.first.is_visible()
            if section == "sector_profile":
                return self._phrase_visible(_SCREEN_2_SECTION_LABELS["sector_profile"])
            if section == "protection_data":
                return self._phrase_visible(_SCREEN_2_SECTION_LABELS["protection_data"])
            if section == "service_targets":
                if self._service_targets_grid() is not None:
                    return True
                return self._phrase_visible(_SCREEN_2_SECTION_LABELS["service_targets"])
            if section == "data":
                return self._trends_heading() is not None
        except Exception:
            return False
        return False

    def _selected_filter_label(self, slicer_id: str) -> str:
        """One selected label for a Screen 2 filter. Empty when nothing is chosen."""
        role_name = self._role_name(slicer_id)
        chips = self._chips(role_name)
        if chips:
            return chips[0]
        try:
            control = self._slicer(slicer_id, role_name).control(slicer_id)
            if control.count() == 0:
                return ""
            return _plain(control.first.inner_text(timeout=self.timeout))
        except Exception:
            return ""

    def _visual_for_phrase(self, labels: Sequence[str]) -> Locator | None:
        """Smallest visual container that holds this heading."""
        node = self._first_visible_phrase(labels)
        if node is None:
            for label in labels:
                section = self._section(label)
                if section is not None:
                    return section
            return None
        host = node.locator(_VISUAL_XPATH)
        try:
            if host.count() > 0:
                return host.first
        except Exception:
            pass
        return node

    def _nearest_metric(self, labels: Sequence[str], kind: str) -> str:
        """Value painted nearest these headings. ``kind`` is digit, percent, or text."""
        heading = self._first_visible_phrase(labels)
        if heading is not None:
            try:
                expect(heading).to_be_visible(timeout=self.timeout)
            except Exception:
                pass
        try:
            result = self._report_frame().locator("body").evaluate(
                """(root, payload) => {
                  const plain = (value) => (value || '')
                    .replace(/[\\u200e\\u200f\\u202a-\\u202c]/g, '')
                    .replace(/\\s+/g, ' ')
                    .trim();
                  const fold = (value) => plain(value)
                    .replace(/\\u05f4/g, '"')
                    .replace(/״/g, '"');
                  const labels = (payload.labels || []).map(fold).filter(Boolean);
                  let title = null;
                  let titleLen = Infinity;
                  for (const el of root.querySelectorAll('*')) {
                    const aria = fold(el.getAttribute('aria-label') || '');
                    const text = fold(el.textContent || '');
                    for (const label of labels) {
                      const hit = aria.includes(label)
                        || text === label
                        || (text.includes(label) && text.length <= label.length + 40);
                      if (!hit) continue;
                      const len = Math.min(
                        aria.includes(label) ? aria.length : Infinity,
                        text.includes(label) ? text.length : Infinity
                      );
                      if (len >= titleLen) continue;
                      titleLen = len;
                      title = el;
                    }
                  }
                  if (!title) {
                    for (const el of root.querySelectorAll('*')) {
                      const text = fold(el.textContent || '');
                      for (const label of labels) {
                        if (!text.includes(label)) continue;
                        if (text.length >= titleLen) continue;
                        titleLen = text.length;
                        title = el;
                      }
                    }
                  }
                  if (!title) return '';
                  const box = title.getBoundingClientRect();
                  const cx = box.left + box.width / 2;
                  const cy = box.top + box.height / 2;
                  const kind = payload.kind;
                  let best = '';
                  let bestDist = Infinity;
                  const take = (text, rect) => {
                    if (!text || (rect.width === 0 && rect.height === 0)) return;
                    const dist = Math.hypot(
                      rect.left + rect.width / 2 - cx,
                      rect.top + rect.height / 2 - cy
                    );
                    if (dist >= bestDist) return;
                    bestDist = dist;
                    best = text;
                  };
                  for (const el of root.querySelectorAll('*')) {
                    if (el.childElementCount && el.tagName !== 'svg') continue;
                    const rect = el.getBoundingClientRect();
                    const text = plain(el.textContent || el.getAttribute('aria-label') || '');
                    if (kind === 'percent') {
                      const matched = text.match(/-?\\d[\\d,.\u00a0\u202f ]*%/);
                      if (matched) take(matched[0], rect);
                      continue;
                    }
                    if (kind === 'text') {
                      if (!/[\\u0590-\\u05FF]/.test(text)) continue;
                      if (labels.some((label) => fold(text).includes(label))) continue;
                      if (/\\d/.test(text)) continue;
                      take(text, rect);
                      continue;
                    }
                    if (/%/.test(text)) continue;
                    const matched = text.match(/-?\\d[\\d,.\u00a0\u202f ]+/);
                    if (!matched) continue;
                    take(matched[0], rect);
                  }
                  return best;
                }""",
                {"labels": list(labels), "kind": kind},
            )
        except Exception:
            return ""
        text = _plain(result)
        if kind == "text":
            text = text.strip("|").strip()
        if text:
            return text
        return self._metric_from_visual(labels, kind)

    def _metric_from_visual(self, labels: Sequence[str], kind: str) -> str:
        """Parse inner text of the heading visual when the nearest-node walk misses."""
        section = self._visual_for_phrase(labels)
        if section is None:
            return ""
        try:
            expect(section).to_be_visible(timeout=self.timeout)
            raw = _plain(section.inner_text(timeout=self.timeout) or "")
        except Exception:
            return ""
        if kind == "percent":
            match = re.search(r"-?\d[\d,.\u00a0\u202f ]*%", raw)
            return match.group(0) if match else ""
        if kind == "text":
            heading = _fold_quotes(labels[0]) if labels else ""
            for line in raw.splitlines():
                cleaned = _plain(line).strip("|").strip()
                if not cleaned or _fold_quotes(cleaned) == heading:
                    continue
                if re.search(r"\d", cleaned) or not _HEBREW.search(cleaned):
                    continue
                return cleaned
            return ""
        match = re.search(r"-?\d[\d,.\u00a0\u202f ]+", raw)
        return match.group(0) if match else ""

    def _read_sector_profile(self) -> dict:
        found: dict[str, str] = {}
        for key, labels in _SCREEN_2_PROFILE_LABELS:
            if key == "defense_policy":
                kind = "text"
            elif key.endswith("_percentage"):
                kind = "percent"
            else:
                kind = "digit"
            found[key] = self._nearest_metric(labels, kind)
        return found

    def _value_after_label(
        self, raw: str, labels: Sequence[str], kind: str
    ) -> str:
        """First number or percent after a card title in a text blob."""
        blob = _fold_quotes(raw)
        for label in labels:
            pattern = re.sub(r"\s+", r"\\s+", re.escape(_fold_quotes(label)))
            if not pattern:
                continue
            match = re.search(pattern, blob)
            if match is None:
                continue
            after = blob[match.end() :]
            if kind == "percent":
                found = re.search(r"-?\d[\d,.\u00a0\u202f ]*%", after)
            else:
                found = re.search(r"-?\d[\d,.\u00a0\u202f ]+", after)
            if found:
                return found.group(0)
        return ""

    def _protection_blob(self) -> str:
        """Visible text of the protection block, else the report body."""
        section = self._visual_for_phrase(_SCREEN_2_SECTION_LABELS["protection_data"])
        chunks: list[str] = []
        if section is not None:
            try:
                chunks.append(_plain(section.inner_text(timeout=self.timeout) or ""))
            except Exception:
                pass
        try:
            chunks.append(
                _plain(
                    self._report_frame().locator("body").inner_text(timeout=self.timeout)
                    or ""
                )
            )
        except Exception:
            pass
        return "\n".join(chunk for chunk in chunks if chunk)

    def _read_protection_data(self) -> dict:
        blob = self._protection_blob()
        found: dict[str, dict[str, str]] = {}
        for key, labels in _SCREEN_2_PROTECTION_LABELS:
            count = self._nearest_metric(labels, "digit")
            percent = self._nearest_metric(labels, "percent")
            if not count:
                count = self._value_after_label(blob, labels, "digit")
            if not percent:
                percent = self._value_after_label(blob, labels, "percent")
            found[key] = {"count": count, "population_percentage": percent}
        return found

    def _service_targets_grid(self) -> Locator | None:
        """Visible grid whose headers look like a name/score service table."""
        frame = self._report_frame()
        grids = frame.get_by_role("grid")
        try:
            count = grids.count()
        except Exception:
            return None
        for index in range(count):
            grid = grids.nth(index)
            try:
                if not grid.is_visible():
                    continue
            except Exception:
                continue
            score_at = self._header_index(grid, "ציון")
            name_at = self._header_index(grid, "יעד")
            if name_at < 0:
                name_at = self._header_index(grid, "שם")
            if score_at >= 0 or name_at >= 0:
                return grid
        heading = self._first_visible_phrase(_SCREEN_2_SECTION_LABELS["service_targets"])
        if heading is None:
            return None
        section = heading.locator(_VISUAL_XPATH)
        try:
            host = section.first if section.count() > 0 else heading
            nested = host.get_by_role("grid")
            if nested.count() > 0:
                return nested.first
        except Exception:
            return None
        return None

    def _map_service_rows(self, raw_rows: list[dict]) -> list[dict[str, str]]:
        """Map Show-as-a-table dicts to ``{name, score}``."""
        found: list[dict[str, str]] = []
        for raw in raw_rows:
            if not isinstance(raw, dict):
                continue
            name = ""
            score = ""
            for header, value in raw.items():
                cell = _plain(str(value))
                header_text = _plain(str(header))
                if _HEBREW.search(cell) and not re.search(r"\d", cell.replace(".", "")):
                    name = cell
                elif re.search(r"\d", cell):
                    score = cell
                elif _HEBREW.search(header_text) and not name:
                    name = header_text
                    if re.search(r"\d", cell):
                        score = cell
            if name:
                found.append({"name": name, "score": score})
        return found

    def _chart_skip(self) -> set[str]:
        """Headings that are not service names on the bar chart."""
        extra = (
            "פריטים",
            "פריט",
            "המהווים",
            "מהאוכלוסייה",
            "פרופיל גזרתי",
            "ציון חוסן",
            "ציון סופי",
            "מגמת ציון סופי",
            "מגמות ציונים",
            "ציונים",
            "הערכת מצב רשויות",
            'תמ"צ יעדי השירות',
            "תמ״צ יעדי השירות",
            "ניווט לעזר חזותי",
            "ממוצע ארצי",
            "טבלת",
            "טבלה",
        )
        labels = [
            *extra,
            *[label for group in _SCREEN_2_SECTION_LABELS.values() for label in group],
            *[label for _key, group in _SCREEN_2_PROFILE_LABELS for label in group],
            *[label for _key, group in _SCREEN_2_PROTECTION_LABELS for label in group],
        ]
        return {_fold_quotes(label) for label in labels}

    def _painted_chart_nodes(self) -> list[dict]:
        """Visible leaf text in the report, with on-screen position."""
        groups = self._painted_chart_groups()
        found: list[dict] = []
        for group in groups:
            found.extend(group)
        return found

    def _painted_chart_groups(self) -> list[list[dict]]:
        """Leaf text grouped by visual container, including nested visual frames."""
        script = """(root) => {
          const plain = (value) => (value || '')
            .replace(/[\\u200e\\u200f\\u202a-\\u202c]/g, '')
            .replace(/\\s+/g, ' ')
            .trim();
          const hostOf = (el) => {
            let current = el;
            while (current && current !== root) {
              const cls = (current.className && current.className.toString)
                ? current.className.toString() : '';
              if (cls.includes('visualContainer')) return current;
              current = current.parentElement;
            }
            return root;
          };
          const take = (el, text, buckets) => {
            const rect = el.getBoundingClientRect();
            if (rect.width === 0 && rect.height === 0) return;
            if (!text) return;
            const host = hostOf(el);
            if (!buckets.has(host)) buckets.set(host, []);
            buckets.get(host).push({
              text,
              x: rect.left + rect.width / 2,
              y: rect.top + rect.height / 2,
            });
          };
          const buckets = new Map();
          for (const el of root.querySelectorAll('*')) {
            const tag = (el.tagName || '').toLowerCase();
            if (tag === 'text' && el.querySelector('tspan')) {
              take(el, plain(el.textContent || ''), buckets);
              continue;
            }
            if (tag === 'tspan') continue;
            if (el.childElementCount) continue;
            take(
              el,
              plain(el.textContent || el.getAttribute('aria-label') || ''),
              buckets
            );
          }
          return [...buckets.values()];
        }"""
        found: list[list[dict]] = []
        frames = [self._report_frame()]
        for frame in self.page.frames:
            try:
                frames.append(frame)
            except Exception:
                continue
        seen = 0
        for frame in frames:
            try:
                groups = frame.locator("body").evaluate(script)
            except Exception:
                continue
            if not isinstance(groups, list):
                continue
            for group in groups:
                if isinstance(group, list) and group:
                    found.append(group)
                    seen += 1
            if seen > 80:
                break
        return found

    def _pair_paint_by_row(self, items: list[dict]) -> list[dict[str, str]]:
        """Pair a Hebrew label with the nearest number on the same row."""
        skip = self._chart_skip()
        names: list[dict] = []
        scores: list[dict] = []
        mixed_name = re.compile(
            r"^(?P<name>[\u0590-\u05FF][\u0590-\u05FF\s,\"״'\-]+?)\s+"
            r"(?P<score>-?\d+(?:[.,]\d+)?)$"
        )
        mixed_score = re.compile(
            r"^(?P<score>-?\d+(?:[.,]\d+)?)\s+"
            r"(?P<name>[\u0590-\u05FF][\u0590-\u05FF\s,\"״'\-]+)$"
        )
        for item in items:
            text = _plain(item.get("text"))
            if not text:
                continue
            folded = _fold_quotes(text)
            if folded in skip:
                continue
            mixed = mixed_name.fullmatch(text) or mixed_score.fullmatch(text)
            if mixed:
                names.append({**item, "text": mixed.group("name")})
                scores.append({**item, "text": mixed.group("score")})
                continue
            number = re.fullmatch(r"-?\d+(?:[.,]\d+)?%?", text.replace(",", ""))
            if number:
                if "%" in text:
                    continue
                digits = text.replace(",", "").replace("%", "")
                if re.fullmatch(r"-?\d+", digits):
                    continue
                scores.append({**item, "text": text})
                continue
            if _HEBREW.search(text) and not re.search(r"\d", text.replace(".", "")):
                names.append({**item, "text": text})
        found: list[dict[str, str]] = []
        used: set[int] = set()

        def pick(name: dict, max_dist: float) -> int:
            best_i = -1
            best_rank = (2, float("inf"))
            for index, score in enumerate(scores):
                if index in used:
                    continue
                dy = abs(float(name["y"]) - float(score["y"]))
                if dy > 40:
                    continue
                dist = abs(float(name["x"]) - float(score["x"]))
                if dist > max_dist:
                    continue
                raw = str(score["text"])
                whole = 0 if ("." in raw or "," in raw) else 1
                rank = (whole, dist)
                if rank >= best_rank:
                    continue
                best_rank = rank
                best_i = index
            return best_i

        for name in sorted(names, key=lambda item: -float(item["x"])):
            best_i = pick(name, 90)
            if best_i < 0:
                best_i = pick(name, 800)
            if best_i < 0:
                continue
            used.add(best_i)
            found.append(
                {"name": _plain(name["text"]), "score": _plain(scores[best_i]["text"])}
            )
        return found

    def _service_targets_from_paint(self) -> list[dict[str, str]]:
        """Read bar-chart name/score pairs from painted SVG text."""
        needles = {
            _fold_quotes(label)
            for label in _SCREEN_2_SECTION_LABELS["service_targets"]
        }
        headed: list[dict[str, str]] = []
        crowded: list[dict[str, str]] = []
        for group in self._painted_chart_groups():
            texts = {
                _fold_quotes(_plain(item.get("text"))) for item in group
            }
            rows = [
                {
                    "name": self._trim_service_name(row["name"]),
                    "score": row["score"],
                }
                for row in self._pair_paint_by_row(group)
            ]
            rows = [row for row in rows if row["name"]]
            if texts & needles and len(rows) > len(headed):
                headed = rows
            if len(rows) > len(crowded):
                crowded = rows
        if len(headed) >= 5:
            return headed
        if len(crowded) >= 5:
            return crowded
        return headed or crowded

    def _pairs_from_chart_text(self, text: str) -> list[dict[str, str]]:
        """Hebrew service name plus a score, from painted bar-chart text."""
        skip = self._chart_skip()
        skip.update(
            _fold_quotes(label)
            for _key, labels in (
                *_SCREEN_2_PROFILE_LABELS,
                *_SCREEN_2_PROTECTION_LABELS,
            )
            for label in labels
        )
        blob = _plain(text).replace("\u00a0", " ")
        found: list[dict[str, str]] = []
        seen: set[str] = set()
        chunks = re.split(r"\n+|  +", blob)
        for chunk in chunks:
            for match in re.finditer(
                r"([\u0590-\u05FF][\u0590-\u05FF0-9\s,\"״'\-]{1,40}?)\s+"
                r"(-?\d+(?:[.,]\d+)?)",
                chunk,
            ):
                name = _plain(match.group(1)).strip(" ,.|")
                folded = _fold_quotes(name)
                if not name or folded in skip or folded in seen:
                    continue
                seen.add(folded)
                found.append({"name": name, "score": match.group(2)})
        if found:
            return found
        found = []
        pending = ""
        for raw_line in (text or "").splitlines():
            line = _plain(raw_line)
            if not line or _fold_quotes(line) in skip:
                continue
            pair = re.search(
                r"([\u0590-\u05FF][\u0590-\u05FF0-9\s,\"״'\-]+?)\s+"
                r"(-?\d+(?:[.,]\d+)?)$",
                line,
            )
            if pair is None:
                pair = re.search(
                    r"(-?\d+(?:[.,]\d+)?)\s+"
                    r"([\u0590-\u05FF][\u0590-\u05FF0-9\s,\"״'\-]+)$",
                    line,
                )
                if pair is not None:
                    found.append({"name": _plain(pair.group(2)), "score": pair.group(1)})
                    pending = ""
                    continue
            if pair is not None:
                found.append({"name": _plain(pair.group(1)), "score": pair.group(2)})
                pending = ""
                continue
            if _HEBREW.search(line) and not re.search(r"\d", line.replace(".", "")):
                pending = line
                continue
            number = re.search(r"-?\d+(?:[.,]\d+)?", line)
            if pending and number:
                found.append({"name": pending, "score": number.group(0)})
                pending = ""
        return found

    def _read_service_targets(self) -> list[dict[str, str]]:
        grid = self._service_targets_grid()
        if grid is not None:

            def read_visible(current: Locator) -> list[dict[str, str]]:
                name_index = self._header_index(current, "יעד")
                if name_index < 0:
                    name_index = self._header_index(current, "שם")
                score_index = self._header_index(current, "ציון")
                rows = current.get_by_role("row")
                found: list[dict[str, str]] = []
                try:
                    count = rows.count()
                except Exception:
                    return found
                for index in range(count):
                    row = rows.nth(index)
                    try:
                        if row.get_by_role("columnheader").count() > 0:
                            continue
                        cells = row.get_by_role("gridcell")
                        texts = []
                        for cell_index in range(cells.count()):
                            raw = cells.nth(cell_index).inner_text(timeout=500) or ""
                            texts.append(_plain(raw.split("\n")[0]))
                        name = texts[name_index] if 0 <= name_index < len(texts) else ""
                        score = (
                            texts[score_index] if 0 <= score_index < len(texts) else ""
                        )
                        if not name:
                            for text in texts:
                                if text in _SKIP_CELL or not text:
                                    continue
                                if _HEBREW.search(text):
                                    name = text
                                elif re.search(r"\d", text) and not score:
                                    score = text
                        if not name:
                            continue
                        found.append({"name": name, "score": score})
                    except Exception:
                        continue
                return found

            rows = collect_virtualized_rows(
                grid,
                read_visible,
                lambda row: row.get("name", ""),
                timeout_ms=self.timeout,
            )
            if rows:
                return rows
        rows: list[dict[str, str]] = []
        hosts = [self._report_frame().locator("body")]
        hosts.extend(self._chart_candidates()[:3])
        for host in hosts:
            try:
                raw_rows = VisualTable(
                    self.page,
                    self._report_frame(),
                    timeout_ms=4000,
                ).read_rows(host, name="service_targets")
                mapped = self._map_service_rows(raw_rows)
            except Exception:
                mapped = []
            finally:
                try:
                    self.page.keyboard.press("Escape")
                except Exception:
                    pass
            if len(mapped) >= 5:
                return mapped
            if len(mapped) > len(rows):
                rows = mapped
        painted = self._service_targets_from_paint()
        if len(painted) >= 5:
            return painted
        located = self._service_targets_from_locators()
        if len(located) > len(rows):
            return located
        return rows or painted or located

    def _service_targets_from_locators(self) -> list[dict[str, str]]:
        """Pair visible Hebrew labels with scores across report frames."""
        skip = self._chart_skip()
        items: list[dict] = []
        best: list[dict[str, str]] = []
        pair_re = re.compile(
            r"[\u0590-\u05FF][\u0590-\u05FF0-9\s,\"״'\-]{1,40}?\s+"
            r"-?\d+(?:[.,]\d+)?"
        )

        def absorb(root, locator: Locator, limit: int) -> None:
            try:
                count = min(locator.count(), limit)
            except Exception:
                return
            for index in range(count):
                node = locator.nth(index)
                try:
                    if not node.is_visible():
                        continue
                    box = node.bounding_box()
                    text = _plain(node.inner_text(timeout=600) or "")
                except Exception:
                    continue
                line = text.split("\n")[0]
                if (
                    not box
                    or not line
                    or _fold_quotes(line) in skip
                    or len(line) > 42
                    or len(line.split()) > 5
                ):
                    continue
                items.append(
                    {
                        "text": line,
                        "x": box["x"] + box["width"] / 2,
                        "y": box["y"] + box["height"] / 2,
                    }
                )

        frames: list = [self._report_frame()]
        for frame in self.page.frames:
            frames.append(frame)
        for frame in frames[:12]:
            try:
                blob = _plain(frame.locator("body").inner_text(timeout=1500) or "")
            except Exception:
                blob = ""
            if blob:
                parsed = self._pairs_from_chart_text(blob)
                if len(parsed) > len(best):
                    best = parsed
            absorb(
                frame,
                frame.get_by_text(pair_re),
                40,
            )
            absorb(
                frame,
                frame.get_by_text(
                    re.compile(r"^[\u0590-\u05FF][\u0590-\u05FF\s,\"״'\-]{1,40}$")
                ),
                40,
            )
            absorb(
                frame,
                frame.get_by_text(re.compile(r"^-?\d{1,3}(?:[.,]\d{1,2})?$")),
                40,
            )
        for group in self._painted_chart_groups():
            for item in group:
                line = _plain(item.get("text"))
                if not line or _fold_quotes(line) in skip or len(line) > 42:
                    continue
                items.append(
                    {
                        "text": line.split("\n")[0],
                        "x": float(item.get("x") or 0),
                        "y": float(item.get("y") or 0),
                    }
                )
        paired = [
            {
                "name": self._trim_service_name(row["name"]),
                "score": row["score"],
            }
            for row in self._pair_paint_by_row(items)
        ]
        paired = [row for row in paired if row["name"]]
        cleaned = []
        seen: set[str] = set()
        for row in best:
            name = self._trim_service_name(row["name"])
            folded = _fold_quotes(name)
            if not name or folded in seen or "  " in name:
                continue
            seen.add(folded)
            cleaned.append({"name": name, "score": row["score"]})
        if len(paired) >= 5:
            return paired
        if len(cleaned) > len(paired):
            return cleaned
        return paired

    def _trim_service_name(self, name: str) -> str:
        """Drop chart/page headings that inner-text glued onto a service name."""
        text = _plain(name)
        for label in sorted(self._chart_skip(), key=len, reverse=True):
            if not label:
                continue
            text = re.sub(re.sub(r"\s+", r"\\s+", re.escape(label)), " ", text)
        text = re.sub(r"\s+", " ", text).strip(" -|,")
        words = text.split()
        if len(words) > 5:
            text = " ".join(words[-2:])
        return text

    def _aria_blob(self, host: Locator) -> str:
        """aria-label text on this visual, including zero-size access nodes."""
        try:
            labels = host.evaluate(
                """(root) => {
                  const plain = (value) => (value || '')
                    .replace(/[\\u200e\\u200f\\u202a-\\u202c]/g, '')
                    .replace(/\\s+/g, ' ')
                    .trim();
                  const found = [];
                  for (const el of [root, ...root.querySelectorAll('*')]) {
                    const text = plain(
                      (el.getAttribute && el.getAttribute('aria-label'))
                      || (el.getAttribute && el.getAttribute('title'))
                      || ''
                    );
                    if (text) found.push(text);
                  }
                  return found.join('\\n');
                }"""
            )
        except Exception:
            return ""
        return _plain(labels)

    def _service_targets_from_aria(self) -> list[dict[str, str]]:
        """Bar values exposed on img/visual aria-labels, including nested frames."""
        best: list[dict[str, str]] = []
        for frame in self.page.frames:
            try:
                blobs = frame.locator("body").evaluate(
                    """(root) => {
                      const plain = (value) => (value || '')
                        .replace(/[\\u200e\\u200f\\u202a-\\u202c]/g, '')
                        .replace(/\\s+/g, ' ')
                        .trim();
                      const found = [];
                      for (const el of root.querySelectorAll('*')) {
                        const text = plain(
                          el.getAttribute('aria-label')
                          || el.getAttribute('title')
                          || ''
                        );
                        if (text.length > 8) found.push(text);
                      }
                      return found;
                    }"""
                )
            except Exception:
                continue
            for blob in blobs or []:
                rows = self._pairs_from_chart_text(str(blob))
                if len(rows) > len(best):
                    best = rows
        return best

    def _service_chart_heading(self) -> Locator | None:
        """Service-targets title, skipping a bar-chart column header."""
        frame = self._report_frame()
        for label in _SCREEN_2_SECTION_LABELS["service_targets"]:
            for variant in _quote_spellings(label):
                nodes = frame.get_by_text(variant, exact=False)
                try:
                    count = min(nodes.count(), 16)
                except Exception:
                    continue
                for index in range(count):
                    node = nodes.nth(index)
                    try:
                        if not node.is_visible():
                            continue
                        if (node.get_attribute("role") or "") == "columnheader":
                            continue
                    except Exception:
                        continue
                    return node
        return self._first_visible_phrase(_SCREEN_2_SECTION_LABELS["service_targets"])

    def _nested_frame_text(self, host: Locator) -> str:
        """Visible text of iframes mounted inside this visual."""
        chunks: list[str] = []
        for frame in self.page.frames:
            try:
                element = frame.frame_element()
                inside = host.evaluate(
                    "(node, nested) => Boolean(nested && node.contains(nested))",
                    element,
                )
            except Exception:
                continue
            if not inside:
                continue
            try:
                chunks.append(_plain(frame.locator("body").inner_text(timeout=2000) or ""))
            except Exception:
                continue
        return "\n".join(chunk for chunk in chunks if chunk)

    def _trends_heading(self) -> Locator | None:
        """Trends heading when it is not the service-targets bar visual."""
        trends = self._first_visible_phrase(_SCREEN_2_SECTION_LABELS["data"])
        if trends is None:
            return None
        services = self._first_visible_phrase(_SCREEN_2_SECTION_LABELS["service_targets"])
        if services is None:
            return trends
        marked = False
        try:
            services.evaluate(
                """node => {
                  let current = node;
                  while (current) {
                    const cls = (current.className && current.className.toString)
                      ? current.className.toString() : '';
                    if (cls.includes('visualContainer')) {
                      current.setAttribute('data-authorities-s2-svc-ref', '1');
                      return;
                    }
                    current = current.parentElement;
                  }
                  node.setAttribute('data-authorities-s2-svc-ref', '1');
                }"""
            )
            marked = True
            same = trends.evaluate(
                """(node) => {
                  const hostOf = (el) => {
                    let current = el;
                    while (current) {
                      const cls = (current.className && current.className.toString)
                        ? current.className.toString() : '';
                      if (cls.includes('visualContainer')) return current;
                      current = current.parentElement;
                    }
                    return null;
                  };
                  const other = node.ownerDocument.querySelector(
                    '[data-authorities-s2-svc-ref="1"]'
                  );
                  return !!other && hostOf(node) === hostOf(other);
                }"""
            )
        except Exception:
            same = False
        finally:
            if marked:
                try:
                    self._report_frame().locator(
                        '[data-authorities-s2-svc-ref="1"]'
                    ).first.evaluate(
                        "node => node.removeAttribute('data-authorities-s2-svc-ref')"
                    )
                except Exception:
                    pass
        if same:
            return None
        return trends

    def _chart_host(self, node: Locator, attr: str) -> Locator | None:
        """Mark a visual body large enough to right-click, then return it."""
        try:
            found = node.evaluate(
                """(node, attr) => {
                  const stale = node.ownerDocument.querySelector(
                    '[' + attr + '="active"]'
                  );
                  if (stale) stale.removeAttribute(attr);
                  const plotOf = (host) => {
                    for (const child of host.querySelectorAll('svg, canvas')) {
                      const box = child.getBoundingClientRect();
                      if (box.width >= 120 && box.height >= 80) return child;
                    }
                    return null;
                  };
                  const usable = (host) => {
                    const rect = host.getBoundingClientRect();
                    if (rect.width < 220 || rect.width > 1100) return false;
                    if (rect.height < 140 || rect.height > 720) return false;
                    return !!plotOf(host);
                  };
                  const mark = (host) => {
                    host.setAttribute(attr, 'active');
                  };
                  let current = node;
                  for (let depth = 0; depth < 14 && current; depth += 1) {
                    if (usable(current)) {
                      mark(current);
                      return true;
                    }
                    current = current.parentElement;
                  }
                  const hb = node.getBoundingClientRect();
                  let best = null;
                  let bestArea = 0;
                  for (const el of node.ownerDocument.querySelectorAll('*')) {
                    if (!usable(el)) continue;
                    const rect = el.getBoundingClientRect();
                    const overlapX = Math.min(hb.right, rect.right)
                      - Math.max(hb.left, rect.left);
                    if (overlapX < 40) continue;
                    const area = rect.width * rect.height;
                    if (area <= bestArea) continue;
                    bestArea = area;
                    best = el;
                  }
                  if (!best) return false;
                  mark(best);
                  return true;
                }""",
                attr,
            )
        except Exception:
            return None
        if not found:
            return None
        return self._report_frame().locator(f'[{attr}="active"]').first

    def _largest_plot(self, attr: str) -> Locator | None:
        """Largest on-screen plot that is a visual, not the whole report canvas."""
        try:
            found = self._report_frame().locator("body").evaluate(
                """(root, attr) => {
                  const stale = root.querySelector('[' + attr + '="active"]');
                  if (stale) stale.removeAttribute(attr);
                  const plotOf = (host) => {
                    for (const child of host.querySelectorAll('svg, canvas')) {
                      const box = child.getBoundingClientRect();
                      if (box.width >= 120 && box.height >= 80) return child;
                    }
                    return null;
                  };
                  let best = null;
                  let bestArea = 0;
                  for (const el of root.querySelectorAll('[class*="visualContainer"]')) {
                    const rect = el.getBoundingClientRect();
                    if (rect.width < 220 || rect.width > 1100) continue;
                    if (rect.height < 140 || rect.height > 720) continue;
                    if (!plotOf(el)) continue;
                    const area = rect.width * rect.height;
                    if (area <= bestArea) continue;
                    bestArea = area;
                    best = el;
                  }
                  if (!best) return false;
                  best.setAttribute(attr, 'active');
                  return true;
                }""",
                attr,
            )
        except Exception:
            return None
        if not found:
            return None
        return self._report_frame().locator(f'[{attr}="active"]').first

    def _chart_candidates(self) -> list[Locator]:
        """Sized visual containers, largest first, for Show-as-a-table."""
        frame = self._report_frame()
        nodes = frame.locator("[class*='visualContainer']")
        found: list[tuple[float, Locator]] = []
        try:
            count = min(nodes.count(), 24)
        except Exception:
            return []
        for index in range(count):
            node = nodes.nth(index)
            try:
                if not node.is_visible():
                    continue
                box = node.bounding_box()
            except Exception:
                continue
            if box is None:
                continue
            if box["width"] < 220 or box["width"] > 1100:
                continue
            if box["height"] < 140 or box["height"] > 720:
                continue
            found.append((box["width"] * box["height"], node))
        found.sort(key=lambda item: item[0], reverse=True)
        return [node for _area, node in found]

    def _map_trend_rows(self, raw_rows: list[dict]) -> list[dict]:
        """Turn Show-as-a-table dicts into ``{date, scores}`` rows."""
        if not raw_rows:
            return []
        first = raw_rows[0] if isinstance(raw_rows[0], dict) else {}
        headers = [_plain(header) for header in first.keys()]
        date_headers = [header for header in headers if _DATE_CELL.search(header)]
        if len(date_headers) >= 2:
            by_date: dict[str, dict[str, str]] = {}
            for raw in raw_rows:
                if not isinstance(raw, dict):
                    continue
                category = ""
                pending: list[tuple[str, str]] = []
                for header, value in raw.items():
                    label = _plain(header)
                    cell = _plain(str(value))
                    date_match = _DATE_CELL.search(label)
                    if date_match:
                        pending.append((date_match.group(0), cell))
                    elif (
                        not category
                        and cell
                        and not re.search(r"\d", cell.replace(".", ""))
                    ):
                        category = cell
                if not category:
                    continue
                for date, score in pending:
                    by_date.setdefault(date, {})[category] = score
            return [
                {"date": date, "scores": scores} for date, scores in by_date.items()
            ]
        parsed: list[dict] = []
        for raw in raw_rows:
            if not isinstance(raw, dict):
                continue
            date = ""
            scores: dict[str, str] = {}
            for header, value in raw.items():
                label = _plain(header)
                cell = _plain(str(value))
                date_match = _DATE_CELL.search(cell)
                if date_match and not date:
                    date = date_match.group(0)
                    continue
                if label and cell:
                    scores[label] = cell
            if date:
                parsed.append({"date": date, "scores": scores})
        return parsed

    def _read_grade_trends(self) -> list[dict]:
        heading = self._trends_heading()
        if heading is None:
            return []
        host = self._chart_host(heading, "data-authorities-s2-trend")
        if host is None:
            return []
        try:
            raw_rows = VisualTable(
                self.page,
                self._report_frame(),
                timeout_ms=self.timeout,
            ).read_rows(host, name="grade_trends")
        finally:
            try:
                host.evaluate(
                    "node => node.removeAttribute('data-authorities-s2-trend')"
                )
            except Exception:
                pass
        return self._map_trend_rows(raw_rows)

    def read_screen_2_metrics(self) -> dict:
        """Screen 2 date, filters, profile, protection, services, and trends."""
        expect(self._screen_2_ready_locator().first).to_be_visible(timeout=self.timeout)
        return {
            "date": self._read_date(),
            "filters": {
                "district": self._selected_filter_label("district"),
                "sub_district": self._selected_filter_label("sub_district"),
            },
            "sector_profile": self._read_sector_profile(),
            "protection_data": self._read_protection_data(),
            "service_targets": self._read_service_targets(),
            "grade_trends": None,
            "data": self._read_grade_trends()
            if self.screen_2_section_visible("data")
            else [],
        }
