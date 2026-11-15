"""Hosen Status report — landing screen (Screen 1) readers."""

from __future__ import annotations

import re

from playwright.sync_api import Locator, Page, expect

from config.settings import settings
from core.components.kpi import KPI
from core.components.slicer import Slicer, SlicerDefinition
from core.components.virtual_grid import collect_virtualized_rows
from core.portal.page import ReportShell

_BIDI = ("\u200f", "\u200e", "\u202a", "\u202b", "\u202c")
_PERCENT = re.compile(r"\d+(?:[.,]\d+)?\s*%")
_HEBREW = re.compile(r"[\u0590-\u05FF]")
_NUMBER = re.compile(r"\d")
# Live accessible name uses an ASCII quote. The gershayim form is accepted too.
_NATIONAL_TITLES = (
    'הערכת קה"א - ממוצע ארצי',
    "הערכת קה״א - ממוצע ארצי",
)
_RESILIENCE_TITLE = "ציון חוסן"
_CATEGORY_TITLES = (
    "מנהיגות",
    "דאגה לרווחה",
    "התנהגות אפקטיבית",
    "שייכות וסולידריות",
    "רציפות תפקודית",
    "נרטיב",
    "מיצוי משאבי קהילה",
    "מידע ותקשורת",
)
_AUTHORITY_HEADER = "רשות"
_FILTER_ROLES = (
    ("district", ("מחוז",)),
    ("sub_district", ("נפה", "נפות")),
    ("date", ("SlicerDate", "תאריך")),
)
_UP = re.compile(r"\bup\b|עלייה|עולה|increase|▲|⬆", re.I)
_DOWN = re.compile(r"\bdown\b|ירידה|יורד|decrease|▼|⬇", re.I)
_FLAT = re.compile(r"\bflat\b|ללא שינוי|יציב|unchanged|►|↔", re.I)

_MISSING_HEADER = "שלא הזינו"

_CARD_SIGNALS_JS = """
(el) => {
  const nodes = [...el.querySelectorAll('svg, path, i, img')];
  const out = [];
  for (const node of nodes) {
    if (node.tagName === 'CANVAS' || node.closest('canvas')) continue;
    const label = node.getAttribute('aria-label') || node.getAttribute('title') || '';
    const style = window.getComputedStyle(node);
    const fill = style.fill && style.fill !== 'none' ? style.fill : '';
    out.push({label, fill, color: style.color || ''});
    if (out.length >= 24) break;
  }
  return out;
}
"""

_ROW_COLORS_JS = """
(el) => {
  const colors = [];
  const push = (node) => {
    if (!node || node.tagName === 'CANVAS' || (node.closest && node.closest('canvas'))) return;
    const style = window.getComputedStyle(node);
    if (style.backgroundColor) colors.push(style.backgroundColor);
    if (node.tagName === 'RECT' || node.tagName === 'PATH') colors.push(style.fill || '');
  };
  push(el);
  let parent = el.parentElement;
  for (let depth = 0; depth < 4 && parent; depth += 1) {
    push(parent);
    parent = parent.parentElement;
  }
  for (const node of [...el.querySelectorAll('div, span, rect, path')].slice(0, 12)) push(node);
  return colors;
}
"""


def _plain(raw) -> str:
    """Drop Power BI bidi marks and trim."""
    text = "" if raw is None else str(raw)
    for mark in _BIDI:
        text = text.replace(mark, "")
    return text.strip()


def _channels(css: str) -> tuple[int, int, int] | None:
    """Parse an rgb or rgba color. None when the string is not a color."""
    match = re.search(r"rgba?\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)", css or "")
    if match is None:
        return None
    return int(match.group(1)), int(match.group(2)), int(match.group(3))


def _blank_color(css: str) -> bool:
    """White, black, and transparent paints are not a status."""
    channels = _channels(css)
    if channels is None:
        return True
    if "0, 0, 0, 0" in (css or "").replace(" ", ""):
        return True
    red, green, blue = channels
    if red > 245 and green > 245 and blue > 245:
        return True
    if red < 20 and green < 20 and blue < 20:
        return True
    return False


def _paint_word(css: str, *, green: str, yellow: str) -> str:
    """Map a computed color onto the caller's green and yellow words."""
    if _blank_color(css):
        return ""
    channels = _channels(css)
    if channels is None:
        return ""
    red, green_ch, blue = channels
    if red > 170 and green_ch > 140 and blue < 130 and green_ch > blue + 30:
        return yellow
    if green_ch > 80 and green_ch > red + 15 and green_ch > blue + 15:
        return green
    return ""


def _trend_word(signals: list[dict]) -> str:
    """Arrow direction first, then green, red, or yellow on a non-canvas glyph."""
    for signal in signals:
        label = _plain(signal.get("label") or "")
        if label in {"תמונה", "image", ""}:
            continue
        if _UP.search(label):
            return "up"
        if _DOWN.search(label):
            return "down"
        if _FLAT.search(label):
            return "flat"
    for signal in signals:
        label = _plain(signal.get("label") or "")
        if "ממוצע" in label or "Grade" in label or "%" in label or "ריק" in label:
            continue
        for paint in (signal.get("fill") or "", signal.get("color") or ""):
            word = _paint_word(paint, green="up", yellow="flat")
            if word:
                return word
            channels = _channels(paint)
            if channels is None or _blank_color(paint):
                continue
            red, green_ch, blue = channels
            if red > green_ch + 15 and red > blue + 15 and red > 80:
                return "down"
    return ""


def _row_status(colors: list[str]) -> str:
    """green, yellow, or the first meaningful rgb() string."""
    raw = ""
    for color in colors:
        word = _paint_word(color, green="green", yellow="yellow")
        if word:
            return word
        if color and not _blank_color(color) and not raw:
            raw = color
    return raw


def _main_percentage(text: str) -> str:
    """Grade shown on the card, ignoring the previous-day percent."""
    before, separator, _after = text.partition("יממה")
    source = before if separator else text
    if "ריק" in source:
        return "(ריק)"
    match = _PERCENT.search(source)
    if match is None:
        return ""
    return match.group(0).replace(" ", "")


def _display_value(label: str) -> str:
    """Visible grade token from an image label. Empty grades stay '(ריק)'."""
    text = _plain(label).rstrip(".")
    if "ריק" in text:
        return "(ריק)"
    match = _PERCENT.search(text)
    if match is not None:
        return match.group(0).replace(" ", "")
    return ""


class HosenStatusPage(ReportShell):
    DASHBOARD_SEARCH_TERM = 'תמ"צ חוסן'
    # This dashboard labels its freshness timestamp "מועד רענון" instead of
    # the generic Layer 0 caption ("הדשבורד עודכן לאחרונה ב:").
    LAST_REFRESH_PHRASE = "מועד רענון"

    def __init__(self, page: Page):
        super().__init__(page)
        self.url = settings.LOGIN_URL or settings.DASHBOARD_URL

    def _report_ready_locator(self):
        return self._report_frame().get_by_text(
            'תמ"צ ארצי - דיווחי קה"א יקל"ר',
            exact=True,
        )

    def _kpi(self) -> KPI:
        return KPI(self.page, self._report_frame(), timeout_ms=self.timeout)

    def _slicer(self, slicer_id: str, role_name: str) -> Slicer:
        return Slicer(
            page=self.page,
            frame=self._report_frame(),
            definitions=(
                SlicerDefinition(id=slicer_id, role_name=role_name, kind="dropdown"),
            ),
            timeout_ms=self.timeout,
        )

    def section_anchor_visible(self, section: str) -> bool:
        """True when that Screen 1 block is on the landing page."""
        frame = self._report_frame()
        try:
            if section == "survey_status":
                locator = frame.get_by_text("הזינו את הסקר", exact=False)
                return locator.count() > 0 and locator.first.is_visible()
            if section == "kpis":
                return self._national_title() != ""
            if section == "resilience_scores":
                header = frame.get_by_role("columnheader", name=_RESILIENCE_TITLE)
                return header.count() > 0 and header.first.is_visible()
            if section == "active_filters":
                return frame.get_by_role("combobox").count() > 0
        except Exception:
            return False
        return False

    def read_screen_1_metrics(self) -> dict:
        """Landing-screen survey, KPIs, resilience rows, and selected filters."""
        expect(self._report_ready_locator()).to_be_visible(timeout=self.timeout)
        return {
            "survey_status": self._read_survey_status(),
            "kpis": self._read_kpis(),
            "resilience_scores": self._read_resilience_scores(),
            "active_filters": self._read_active_filters(),
        }

    def _national_title(self) -> str:
        frame = self._report_frame()
        for title in _NATIONAL_TITLES:
            locator = frame.get_by_text(title, exact=False)
            for index in range(min(locator.count(), 6)):
                if locator.nth(index).is_visible():
                    return title
        return ""

    def _filter_control(
        self, slicer_id: str, role_names: tuple[str, ...]
    ) -> tuple[Locator | None, tuple[str, ...]]:
        """Dropdown for this filter via ``Slicer.control``, then a name scan."""
        frame = self._report_frame()
        for role_name in role_names:
            control = self._slicer(slicer_id, role_name).control(slicer_id)
            if control.count() > 0:
                return control, (role_name,)
        combos = frame.get_by_role("combobox")
        for index in range(combos.count()):
            combo = combos.nth(index)
            label = _plain(
                combo.get_attribute("aria-label")
                or combo.inner_text(timeout=1000)
                or ""
            )
            if not any(role_name in label for role_name in role_names):
                continue
            exact = combo.get_attribute("aria-label") or label.splitlines()[0]
            control = self._slicer(slicer_id, exact).control(slicer_id)
            if control.count() > 0:
                return control, (exact, *role_names)
            return combo, (exact, *role_names)
        return None, role_names

    def _selected_label(self, control: Locator, role_names: tuple[str, ...]) -> str:
        expect(control).to_be_visible(timeout=self.timeout)
        text = _plain(control.inner_text(timeout=self.timeout))
        banned = {_plain(name) for name in role_names}
        lines = [line.strip(" ") for line in text.splitlines() if line.strip()]
        values = [line for line in lines if _plain(line) not in banned and line]
        if values:
            return values[-1]
        return text

    def _read_active_filters(self) -> dict:
        selected: dict[str, str] = {}
        for slicer_id, role_names in _FILTER_ROLES:
            control, names = self._filter_control(slicer_id, role_names)
            if control is None:
                continue
            label = self._selected_label(control, names)
            if label:
                selected[slicer_id] = label
        return selected

    def _visible_text(self, title: str) -> Locator | None:
        frame = self._report_frame()
        locator = frame.get_by_text(title, exact=False)
        for index in range(min(locator.count(), 6)):
            candidate = locator.nth(index)
            if candidate.is_visible():
                return candidate
        return None

    def _mark_card(self, title: str) -> Locator | None:
        """Mark the smallest parent that contains this title and an image."""
        frame = self._report_frame()
        node = self._visible_text(title)
        if node is None:
            locator = frame.get_by_text(title, exact=False)
            if locator.count() == 0:
                return None
            node = locator.first
        try:
            marked = node.evaluate(
                """(el) => {
                  const needle = (el.textContent || '').trim().slice(0, 24);
                  let current = el.parentElement;
                  for (let depth = 0; depth < 14 && current; depth += 1) {
                    const text = current.innerText || '';
                    if (text.length > 900) break;
                    const hasVisual = current.querySelector('[role="img"], img, svg');
                    if (hasVisual && needle && text.includes(needle)) {
                      current.setAttribute('data-hosen-card', 'active');
                      return true;
                    }
                    current = current.parentElement;
                  }
                  return false;
                }"""
            )
        except Exception:
            return None
        if not marked:
            return None
        return frame.locator("[data-hosen-card='active']")

    def _clear_card_mark(self, host: Locator) -> None:
        try:
            host.evaluate("el => el.removeAttribute('data-hosen-card')")
        except Exception:
            return

    def _percentage_from_snapshot(self, snapshot: str) -> str:
        """Main grade from image accessible names. Yesterday's figure is skipped."""
        for name in re.findall(r'img "([^"]*)"', snapshot or ""):
            if "yesterday" in name.lower():
                continue
            value = _display_value(name)
            if value:
                return value
        return ""

    def _read_card(self, title: str) -> dict | None:
        """One assessment card. KPI is used when the title is the card name."""
        try:
            card = self._kpi().card(title)
            if card.count() > 0 and card.is_visible():
                raw = ""
                try:
                    raw = self._kpi().read_text(title)
                except Exception:
                    raw = ""
                text = _plain(raw) or _plain(card.inner_text(timeout=self.timeout))
                try:
                    signals = card.evaluate(_CARD_SIGNALS_JS)
                except Exception:
                    signals = []
                return {
                    "title": title,
                    "percentage": _main_percentage(text),
                    "trend": _trend_word(signals if isinstance(signals, list) else []),
                }
        except Exception:
            pass
        host = self._mark_card(title)
        if host is None:
            return None
        try:
            snapshot = host.aria_snapshot()
            try:
                signals = host.evaluate(_CARD_SIGNALS_JS)
            except Exception:
                signals = []
        finally:
            self._clear_card_mark(host)
        percentage = self._percentage_from_snapshot(snapshot)
        if not percentage:
            percentage = _main_percentage(_plain(snapshot))
        if not percentage:
            return None
        return {
            "title": title,
            "percentage": percentage,
            "trend": _trend_word(signals if isinstance(signals, list) else []),
        }

    def _read_kpis(self) -> dict:
        empty = {
            "national_average": {"title": "", "percentage": "", "trend": ""},
            "categories": [],
        }
        national = self._national_title()
        if not national:
            return empty
        national_card = self._read_card(national) or {
            "title": national,
            "percentage": "",
            "trend": "",
        }
        categories = []
        for title in _CATEGORY_TITLES:
            record = self._read_card(title)
            if record is not None:
                categories.append(record)
        return {"national_average": national_card, "categories": categories}

    def _card_paragraph(self, name_pattern: re.Pattern[str]) -> str:
        frame = self._report_frame()
        button = frame.get_by_role("button", name=name_pattern).first
        expect(button).to_be_visible(timeout=self.timeout)
        paragraph = button.locator("p").last
        return _plain(paragraph.inner_text(timeout=self.timeout))

    def _missing_grid(self) -> Locator | None:
        frame = self._report_frame()
        header = frame.get_by_role("columnheader", name=re.compile(_MISSING_HEADER)).first
        expect(header).to_be_visible(timeout=self.timeout)
        return header.locator("xpath=ancestor::*[@role='grid'][1]")

    def _visible_missing_rows(self, grid: Locator) -> list[dict[str, str]]:
        rows = grid.get_by_role("row")
        found: list[dict[str, str]] = []
        for index in range(rows.count()):
            row = rows.nth(index)
            try:
                if row.get_by_role("columnheader").count() > 0:
                    continue
                cells = row.get_by_role("gridcell")
                authority = ""
                for cell_index in range(cells.count()):
                    text = _plain(cells.nth(cell_index).inner_text(timeout=500) or "")
                    if text and text not in {"בחר שורה", "בחירת שורה"} and _HEBREW.search(text):
                        authority = text
                if authority:
                    found.append({"authority": authority})
            except Exception:
                continue
        return found

    def _read_survey_status(self) -> dict:
        """Submitted count, authority total, and authorities that have not submitted."""
        submitted = self._card_paragraph(re.compile(r"CountMuniSendSelectedDate"))
        total = self._card_paragraph(re.compile(r"Muni_Code"))
        missing: list[str] = []
        grid = self._missing_grid()
        if grid is not None:
            expect(grid).to_be_visible(timeout=self.timeout)
            rows = collect_virtualized_rows(
                grid,
                self._visible_missing_rows,
                lambda row: row.get("authority", ""),
                timeout_ms=max(self.timeout, 120_000),
            )
            missing = [row["authority"] for row in rows if row.get("authority")]
        return {
            "submitted": submitted,
            "total": total,
            "missing_authorities": missing,
        }

    def _resilience_grid(self) -> Locator | None:
        frame = self._report_frame()
        header = frame.get_by_role("columnheader", name=_RESILIENCE_TITLE)
        if header.count() == 0 or not header.first.is_visible():
            return None
        return header.first.locator("xpath=ancestor::*[@role='grid'][1]")

    def _column_index(self, grid: Locator, name: str) -> int:
        headers = grid.get_by_role("columnheader")
        for index in range(headers.count()):
            label = _plain(headers.nth(index).inner_text(timeout=500) or "")
            if name in label:
                return index
        return -1

    def _visible_resilience_rows(self, grid: Locator) -> list[dict[str, str]]:
        score_index = self._column_index(grid, _RESILIENCE_TITLE)
        authority_index = self._column_index(grid, _AUTHORITY_HEADER)
        rows = grid.get_by_role("row")
        found: list[dict[str, str]] = []
        for index in range(rows.count()):
            row = rows.nth(index)
            try:
                if row.get_by_role("columnheader").count() > 0:
                    continue
                cells = row.get_by_role("gridcell")
                if cells.count() == 0:
                    continue
                if authority_index < 0 or authority_index >= cells.count():
                    continue
                authority = _plain(cells.nth(authority_index).inner_text(timeout=500) or "")
                if not authority or not _HEBREW.search(authority):
                    continue
                score = ""
                if 0 <= score_index < cells.count():
                    score = _plain(cells.nth(score_index).inner_text(timeout=500) or "")
                    colors = cells.nth(score_index).evaluate(_ROW_COLORS_JS)
                else:
                    colors = []
            except Exception:
                continue
            status = _row_status(colors if isinstance(colors, list) else [])
            found.append(
                {"authority": authority, "score": score, "status": status}
            )
        return found

    def _read_resilience_scores(self) -> list[dict[str, str]]:
        grid = self._resilience_grid()
        if grid is None:
            return []
        expect(grid).to_be_visible(timeout=self.timeout)
        return collect_virtualized_rows(
            grid,
            self._visible_resilience_rows,
            lambda row: row.get("authority", ""),
            timeout_ms=max(self.timeout, 120_000),
        )
