"""Hosen Status report — Screen 1 through Screen 4 readers."""

from __future__ import annotations

import re
import time

from playwright.sync_api import Locator, Page, expect

from config.settings import settings
from core.components.kpi import KPI
from core.components.slicer import Slicer, SlicerDefinition
from core.components.virtual_grid import collect_virtualized_rows
from core.components.visual_table import VisualTable
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
    ("district", ("בחר מחוז", "בחירת מחוז", "מחוז")),
    ("subdistrict", ("בחר נפה", "בחירת נפה", "נפה", "נפות")),
    ("date", ("SlicerDate", "תאריך")),
)
_PAGE_NAV = ("ניווט בין עמודים", "Page navigation")
_SCREEN2_HEADERS = (
    ("authority", "רשות"),
    ("leadership", "מנהיגות"),
    ("welfare", "דאגה לרווחה"),
    ("effective_behavior", "התנהגות אפקטיבית"),
    ("belonging", "שייכות וסולידריות"),
    ("functional_continuity", "רציפות תפקודית"),
    ("narrative", "נרטיב"),
    ("community_resources", "מיצוי משאבי קהילה"),
    ("information", "מידע ותקשורת"),
    ("resilience_score", "ציון חוסן"),
)
_SUMMARY_LABELS = ("ממוצע", "ממוצע ארצי", 'סה"כ', "סה״כ", "Total")
_DATE_CELL = re.compile(r"\d{2}/\d{2}/\d{4}")
# Live chart title on the investigation screen.
_TRENDS_VISUAL_TITLE = "מגמות המרכיבים לפי תאריך"
# Final-score chart on the geographic screen. The full golden sentence stays in the YAML.
_FINAL_SCORE_HINT = "ציון חוסן סופי"
# Screen 3 and Screen 4 placeholder hints. Not part of _FILTER_ROLES, so Screen 1
# chip indexes stay district then subdistrict.
_SCREEN3_FILTERS = (
    ("level_selected", ("בחר רמה", "רמת תחקור", "בחירת רמה", "רמה")),
    ("district", ("בחר מחוז", "בחירת מחוז", "מחוז")),
    ("subdistrict", ("בחר נפה", "בחירת נפה", "נפה", "נפות")),
    ("authority", ("בחר רשות", "בחירת רשות", "רשות")),
)
_SCREEN4_FILTERS = (
    ("sector", ("בחר מגזר", "בחירת מגזר", "מגזר", "סקטור")),
    ("district", ("בחר מחוז", "בחירת מחוז", "מחוז")),
    ("subdistrict", ("בחר נפה", "בחירת נפה", "נפה", "נפות")),
    ("authority", ("בחר רשות", "בחירת רשות", "רשות")),
)
_SCREEN4_HEADERS = (
    ("authority", "רשות"),
    ("care_for_welfare", "דאגה לרווחה"),
    ("effective_behavior", "התנהגות אפקטיבית"),
    ("belonging_and_solidarity", "שייכות וסולידאריות"),
    ("belonging_and_solidarity", "שייכות וסולידריות"),
    ("functional_continuity", "רציפות תפקודית"),
    ("narrative", "נרטיב"),
    ("community_resources", "מיצוי משאבי קהילה"),
    ("information_and_communication", "מידע ותקשורת"),
    ("leadership", "מנהיגות"),
    ("final_score", "ציון חוסן סופי"),
    ("final_score", "ציון סופי"),
    ("final_score", "ציון חוסן"),
)
_NAV_ROLES = ("button", "tab", "link", "option")
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


def _fold_quotes(text: str) -> str:
    """Treat ASCII quotes and Hebrew gershayim as the same character."""
    return (
        _plain(text)
        .replace("״", '"')
        .replace("׳", "'")
        .replace("“", '"')
        .replace("”", '"')
    )


def _quote_variants(label: str) -> tuple[str, ...]:
    """Spellings of one label with either quote character."""
    folded = _fold_quotes(label)
    gershayim = folded.replace('"', "״")
    seen: list[str] = []
    for item in (label, folded, gershayim):
        if item and item not in seen:
            seen.append(item)
    return tuple(seen)


def _percent_token(raw: str) -> str:
    """Compact percent display text. An empty or non-percent cell is ''."""
    match = _PERCENT.search(_plain(raw))
    if match is None:
        return ""
    return match.group(0).replace(" ", "")


def _is_summary_label(label: str) -> bool:
    """True when the cell is the summary/average row, not an authority name."""
    folded = _fold_quotes(label)
    if not folded:
        return False
    return any(folded == _fold_quotes(token) for token in _SUMMARY_LABELS)


def _field_for_screen4_header(label: str) -> str:
    """YAML field for an export-grid header. Empty when the header is unknown."""
    folded = " ".join(_fold_quotes(label).split())
    if not folded:
        return ""
    best = ""
    best_len = 0
    for field, header in _SCREEN4_HEADERS:
        needle = _fold_quotes(header)
        if needle and needle in folded and len(needle) > best_len:
            best = field
            best_len = len(needle)
    return best


def _field_for_header(label: str) -> str:
    """YAML field for a Hebrew column header. Empty when the header is unknown."""
    folded = _fold_quotes(label)
    if not folded:
        return ""
    best = ""
    best_len = 0
    for field, header in _SCREEN2_HEADERS:
        needle = _fold_quotes(header)
        if needle and needle in folded and len(needle) > best_len:
            best = field
            best_len = len(needle)
    return best


_ROW_TEXT_JS = """
(el) => {
  const nodes = el.querySelectorAll(
    '[role="rowheader"], [role="gridcell"], [role="cell"]'
  );
  return Array.from(nodes).map((node) => (node.innerText || node.textContent || ''));
}
"""


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
        self._screen_2_title = ""
        self._screen_3_title = ""
        self._screen_4_title = ""

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
            if section in ("active_filters", "filters"):
                return frame.get_by_role("combobox").count() > 0
            if section == "date":
                control, _names = self._filter_control(
                    "date", self._filter_role_names("date")
                )
                if control is None:
                    return False
                return control.count() > 0 and control.first.is_visible()
        except Exception:
            return False
        return False

    def _screen_1_settle(self, kind: str = "after_select", **_kwargs) -> bool:
        """Hide a visible spinner, then require the Screen 1 ready locator.

        Returning false lets ``Slicer.select`` confirm the combobox label.
        """
        if kind != "after_select":
            return False
        self._wait_for_screen_1_settled()
        return False

    def wait_for_screen_1_idle(self) -> None:
        """Wait until a visible spinner is gone and Screen 1 is ready."""
        self._wait_for_screen_1_settled()

    def _hide_visible_spinner(self) -> None:
        """Hide a visible report spinner. A spinner that is not showing is ignored."""
        frame = self._report_frame()
        spinner = frame.locator("[class*='spinner'], [aria-busy='true']").filter(
            visible=True
        )
        try:
            if spinner.count() > 0:
                expect(spinner.first).to_be_hidden(timeout=self.timeout)
        except Exception:
            pass

    def _wait_for_screen_1_settled(self) -> None:
        """Expect a visible loading spinner to hide, then the ready locator."""
        self._hide_visible_spinner()
        expect(self._report_ready_locator()).to_be_visible(timeout=self.timeout)

    def _select_smart_filter(
        self,
        role_names: tuple[str, ...],
        value: str,
        settle=None,
    ) -> bool:
        """Choose a label in the Smart Filter visual.

        District and sub-district are a hidden multi-select. The visible search
        box placeholder is the Hebrew title.
        """
        hook = settle or self._screen_1_settle
        try:
            self._report_frame().wait_for_function(
                """(hints) => {
                  const docs = [document];
                  for (const iframe of document.querySelectorAll('iframe')) {
                    try {
                      if (iframe.contentDocument) docs.push(iframe.contentDocument);
                    } catch (err) {}
                  }
                  return docs.some((doc) =>
                    [...doc.querySelectorAll('input')].some((node) =>
                      hints.some((hint) => (node.placeholder || '').includes(hint))
                    )
                  );
                }""",
                arg=list(role_names),
                timeout=self.timeout,
            )
        except Exception:
            pass
        field = None
        owner = None
        viewport = self.page.viewport_size or {"width": 1600, "height": 900}
        for frame in self.page.frames:
            if "Sandbox" not in (frame.url or ""):
                continue
            for hint in role_names:
                candidate = frame.locator(f"input[placeholder*='{hint}']")
                try:
                    count = candidate.count()
                except Exception:
                    continue
                for index in range(count):
                    item = candidate.nth(index)
                    try:
                        box = item.bounding_box()
                    except Exception:
                        continue
                    if box is None or box["width"] < 8 or box["height"] < 8:
                        continue
                    center_x = box["x"] + box["width"] / 2
                    center_y = box["y"] + box["height"] / 2
                    if not (0 <= center_x <= viewport["width"] and 0 <= center_y <= viewport["height"]):
                        continue
                    field = item
                    owner = frame
                    break
                if field is not None:
                    break
            if field is not None:
                break
        if field is None or owner is None:
            self._dropdown_trace = "no-field"
            return False
        shell = field.locator(
            "xpath=ancestor::ul[contains(@class, 'TokensContainer')][1]"
        )
        try:
            box = shell.bounding_box()
            if box is None or box["width"] > 450 or box["height"] > 80:
                self._dropdown_trace = "no-arrow"
                return False
            search_input = field
            shell.click(timeout=5000)
            # force=True bypasses the ul.TokensContainer overlay that intercepts pointer events.
            search_input.click(force=True)
            search_input.fill(value, force=True)
            search_input.press("Enter")
            if self._smart_filter_label(role_names) != value and not self._filter_value_visible(value):
                choice = owner.locator("li").get_by_text(value, exact=True).filter(
                    visible=True
                )
                expect(choice.first).to_be_visible(timeout=5000)
                choice.first.click(force=True)
        except Exception as exc:
            self._dropdown_trace = f"{type(exc).__name__}:{str(exc).splitlines()[0][:140]}"
            self.page.keyboard.press("Escape")
            return False
        self.page.keyboard.press("Escape")
        if self._smart_filter_label(role_names) == value or self._filter_value_visible(value):
            hook("after_select")
            return True
        self._dropdown_trace = "arrow-clicked-no-token"
        return False

    def _click_open_choice(self, frame, value: str) -> bool:
        """Click a visible list row whose text is the golden label."""
        exact = re.compile(rf"^{re.escape(value)}$")
        for scope in (frame, self.page):
            choice = scope.locator("li, [role='option']").filter(has_text=exact)
            try:
                count = min(choice.count(), 8)
            except Exception:
                continue
            for index in range(count):
                item = choice.nth(index)
                try:
                    if not item.is_visible():
                        continue
                    item.click(timeout=3000)
                    return True
                except Exception:
                    continue
        return False

    def _filter_value_visible(self, value: str) -> bool:
        """True when the selected chip is on screen.

        The chip text is the golden label. An open list row is hidden after Escape.
        """
        for frame in self.page.frames:
            if "Sandbox" not in (frame.url or ""):
                continue
            chip = frame.get_by_text(value, exact=True).filter(visible=True)
            try:
                if chip.count() > 0:
                    return True
            except Exception:
                continue
        return False

    def _smart_filter_label(self, role_names: tuple[str, ...]) -> str:
        """Selected chip in the right-hand Smart Filter boxes.

        District is the top box. Sub-district is the next one. The chip replaces
        the placeholder, so the box text is the selected label.
        """
        index = 0
        for known_id, names in _FILTER_ROLES:
            if names != role_names:
                continue
            index = 1 if known_id == "subdistrict" else 0
            break
        for frame in self.page.frames:
            if "Sandbox" not in (frame.url or ""):
                continue
            shells = frame.locator("ul.TokensContainer")
            try:
                count = shells.count()
            except Exception:
                continue
            boxes: list[tuple[float, Locator]] = []
            for item_index in range(count):
                item = shells.nth(item_index)
                try:
                    box = item.bounding_box()
                except Exception:
                    continue
                if box is None or box["width"] < 8 or box["width"] > 450:
                    continue
                if box["height"] < 8 or box["height"] > 120:
                    continue
                boxes.append((box["y"], item))
            boxes.sort(key=lambda pair: pair[0])
            chips: list[str] = []
            for _top, item in boxes:
                try:
                    text = item.inner_text(timeout=2000)
                except Exception:
                    continue
                cleaned = (
                    _plain(text).replace("×", "").replace("✕", "").replace("✖", "").strip()
                )
                if not cleaned or cleaned.startswith("בחר"):
                    continue
                chips.append(cleaned)
            if index < len(chips):
                return chips[index]
        return ""

    def _report_frames(self) -> list:
        """The report iframe and the frames nested inside it."""
        try:
            host = self.page.locator("main iframe, iframe").first.element_handle()
            report = host.content_frame() if host is not None else None
        except Exception:
            return []
        if report is None:
            return []
        frames = [report]
        for child in self.page.frames:
            parent = child.parent_frame
            while parent is not None:
                if parent == report:
                    frames.append(child)
                    break
                parent = parent.parent_frame
        return frames

    def _unnamed_comboboxes(self) -> list[Locator]:
        """Visible dropdowns whose accessible name is empty.

        The district and sub-district slicers expose no Hebrew title in the
        accessibility tree. The date slicer is named ``SlicerDate`` and is skipped.
        """
        found: list[Locator] = []
        for child in self._report_frames():
            try:
                combos = child.get_by_role("combobox")
                count = combos.count()
            except Exception:
                continue
            for index in range(count):
                combo = combos.nth(index)
                label = _plain(combo.get_attribute("aria-label") or "")
                if label:
                    continue
                try:
                    if not combo.is_visible():
                        continue
                except Exception:
                    continue
                found.append(combo)
        return found

    def _select_unnamed_combobox(self, value: str) -> bool:
        """Open each unnamed dropdown until one lists the golden value."""
        for combo in self._unnamed_comboboxes():
            try:
                combo.click(force=True)
                owner = combo.element_handle().owner_frame()
                choice = owner.get_by_role("option", name=value, exact=True)
                if choice.count() == 0:
                    choice = owner.get_by_role("checkbox", name=value, exact=True)
                if choice.count() == 0:
                    self.page.keyboard.press("Escape")
                    continue
                expect(choice.first).to_be_visible(timeout=self.timeout)
                choice.first.click(force=True)
            except Exception:
                self.page.keyboard.press("Escape")
                continue
            self.page.keyboard.press("Escape")
            self._screen_1_settle("after_select")
            return True
        return False

    def _filter_role_names(self, slicer_id: str) -> tuple[str, ...]:
        """Role-name hints for a golden filter id."""
        for known_id, role_names in _FILTER_ROLES:
            if known_id == slicer_id:
                return role_names
        known = ", ".join(known_id for known_id, _names in _FILTER_ROLES)
        raise KeyError(f"Unknown slicer id {slicer_id!r}. Known: {known}")

    def select_screen_1_filter(self, slicer_id: str, value: str) -> None:
        """Select one golden dropdown label, then wait for Screen 1 to settle."""
        role_names = self._filter_role_names(slicer_id)
        if slicer_id in ("district", "subdistrict"):
            if self._select_smart_filter(role_names, value):
                return
            trace = getattr(self, "_dropdown_trace", "")
            raise KeyError(
                f"Slicer {slicer_id!r} has no dropdown. Tried {role_names!r}. {trace}"
            )
        control, _names = self._filter_control(slicer_id, role_names)
        if slicer_id == "date":
            if control is None:
                trace = getattr(self, "_dropdown_trace", "")
                raise KeyError(
                    f"Slicer {slicer_id!r} has no dropdown. Tried {role_names!r}. {trace}"
                )
            self._select_date_combobox(control, value)
            return
        if control is None and self._select_smart_filter(role_names, value):
            return
        if control is None:
            if self._select_unnamed_combobox(value):
                return
            trace = getattr(self, "_dropdown_trace", "")
            raise KeyError(
                f"Slicer {slicer_id!r} has no dropdown. Tried {role_names!r}. {trace}"
            )

    def _select_combobox(self, slicer_id: str, role_name: str, value: str) -> None:
        """Choose a dropdown option through Layer 2 ``Slicer.select``."""
        slicer = Slicer(
            page=self.page,
            frame=self._report_frame(),
            definitions=(
                SlicerDefinition(
                    id=slicer_id,
                    role_name=role_name,
                    kind="dropdown",
                ),
            ),
            settle=self._screen_1_settle,
            timeout_ms=self.timeout,
        )
        slicer.select(slicer_id, value)

    def _frames_under(self, host) -> list:
        """A frame plus the iframes nested inside it."""
        if host is None:
            return []
        frames = [host]
        stack = [host]
        while stack:
            current = stack.pop()
            try:
                children = list(current.child_frames)
            except Exception:
                continue
            for child in children:
                frames.append(child)
                stack.append(child)
        return frames

    def _visible_listbox(self, frames) -> tuple[Locator | None, object]:
        """Visible open listbox in these frames. Prefer the one named SlicerDate."""
        fallback: Locator | None = None
        fallback_frame = None
        for frame in frames:
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
                if label == "SlicerDate":
                    return box, frame
                if fallback is None:
                    fallback = box
                    fallback_frame = frame
        return fallback, fallback_frame

    def _frame_has_slicer_date_combobox(self, frame) -> bool:
        """True when this frame holds the combobox ``Slicer.select`` will click."""
        try:
            return (
                frame.get_by_role("combobox", name="SlicerDate", exact=True).count()
                > 0
            )
        except Exception:
            return False

    def _select_date_combobox(self, control: Locator, value: str, settle=None) -> None:
        """Open the resolved date combobox once and choose ``value``.

        The option is taken from this control's frame, including a nested iframe.
        ``Slicer.select`` runs only for an open listbox named ``SlicerDate`` in the
        same frame as that combobox. A miss after settle raises.
        ``settle`` defaults to the Screen 1 hook. Screen 1 callers omit it.
        """
        hook = settle or self._screen_1_settle
        expect(control).to_be_visible(timeout=self.timeout)
        # One open click on the combobox _filter_control already returned.
        control.click(force=True)
        host = control.element_handle().owner_frame()
        if host is None:
            raise AssertionError("Date combobox has no owner frame")
        frames, listbox, listbox_frame = self._wait_for_date_popup(host, value)
        listbox_name = ""
        if listbox is not None:
            listbox_name = _plain(listbox.get_attribute("aria-label") or "")
        if (
            listbox_name == "SlicerDate"
            and listbox_frame is not None
            and self._frame_has_slicer_date_combobox(listbox_frame)
        ):
            self._select_slicer_date(listbox_frame, value, settle=hook)
        else:
            self._click_open_date_option(frames, listbox, value)
        hook("after_select")
        shown = _plain(control.inner_text(timeout=self.timeout))
        if value not in shown:
            raise AssertionError(
                f"Slicer 'date' combobox {shown!r} does not contain {value!r}"
            )

    def _wait_for_date_popup(self, host, value: str):
        """Wait until the open list or its option is visible under the combobox frame."""
        deadline = time.monotonic() + (self.timeout / 1000)
        frames = self._frames_under(host)
        listbox: Locator | None = None
        listbox_frame = None
        while True:
            frames = self._frames_under(host)
            listbox, listbox_frame = self._visible_listbox(frames)
            if listbox is not None:
                label = _plain(listbox.get_attribute("aria-label") or "")
                if label == "SlicerDate" or self._visible_named_option(listbox, value) is not None:
                    return frames, listbox, listbox_frame
            for frame in frames:
                if self._visible_named_option(frame, value) is not None:
                    return frames, listbox, listbox_frame
            if time.monotonic() >= deadline:
                return frames, listbox, listbox_frame

    def _select_slicer_date(self, frame, value: str, settle=None) -> None:
        """Choose ``value`` through Layer 2 when the open listbox is SlicerDate."""
        hook = settle or self._screen_1_settle
        Slicer(
            page=self.page,
            frame=frame,
            definitions=(
                SlicerDefinition(
                    id="date",
                    role_name="SlicerDate",
                    kind="dropdown",
                ),
            ),
            settle=hook,
            timeout_ms=self.timeout,
        ).select("date", value)

    def _click_open_date_option(self, frames, listbox: Locator | None, value: str) -> None:
        """Click the already-open option. Do not click the combobox again."""
        option = None
        if listbox is not None:
            option = self._visible_named_option(listbox, value)
        if option is None:
            for frame in frames:
                option = self._visible_named_option(frame, value)
                if option is not None:
                    break
        if option is None:
            raise AssertionError(f"Open date option {value!r} was not visible")
        option.click(force=True)

    def _visible_named_option(self, scope, value: str) -> Locator | None:
        """A visible option named ``value`` inside a listbox or a frame."""
        options = scope.get_by_role("option", name=value, exact=True)
        try:
            count = options.count()
        except Exception:
            return None
        for index in range(min(count, 8)):
            item = options.nth(index)
            try:
                if item.is_visible():
                    return item
            except Exception:
                continue
        return None

    def _choose_dropdown_option(self, control: Locator, value: str) -> None:
        """Open a titled dropdown that is not a combobox and choose one option."""
        expect(control).to_be_visible(timeout=self.timeout)
        control.click(force=True)
        owner = control.element_handle().owner_frame()
        option = owner.get_by_role("option", name=value, exact=True)
        if option.count() == 0:
            option = owner.get_by_text(value, exact=True)
        expect(option.first).to_be_visible(timeout=self.timeout)
        option.first.click(force=True)
        self.page.keyboard.press("Escape")

    def read_screen_1_metrics(self) -> dict:
        """Landing-screen survey, KPIs, resilience rows, filters, and the date."""
        expect(self._report_ready_locator()).to_be_visible(timeout=self.timeout)
        return {
            "survey_status": self._read_survey_status(),
            "kpis": self._read_kpis(),
            "resilience_scores": self._read_resilience_scores(),
            "filters": self._read_active_filters(),
            "date": self._read_screen_1_date(),
        }

    def _read_screen_1_date(self) -> str:
        """Selected date label. The golden date stays in the YAML."""
        try:
            control, names = self._filter_control(
                "date", self._filter_role_names("date")
            )
        except Exception:
            return ""
        if control is None:
            return ""
        try:
            if control.count() == 0 or not control.first.is_visible():
                return ""
        except Exception:
            return ""
        return self._selected_label(control, names)

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
        titled = self._locate_titled_dropdown(role_names)
        if titled is not None:
            label = _plain(titled.get_attribute("aria-label") or "")
            if label:
                return titled, (label, *role_names)
            return titled, role_names
        return None, role_names

    def _locate_titled_dropdown(self, role_names: tuple[str, ...]) -> Locator | None:
        """Dropdown inside the visual whose title matches a role hint."""
        for child in self._report_frames():
            located = self._mark_titled_dropdown(child, role_names)
            if located is not None:
                return located
        return None

    def _mark_titled_dropdown(self, frame, role_names: tuple[str, ...]) -> Locator | None:
        """Mark the dropdown in one frame, including a nested visual frame."""
        try:
            found = frame.evaluate(
                """(needles) => {
                  const selector = '[role="combobox"], button, [role="button"], [aria-haspopup="listbox"], [class*="slicer-dropdown"], [class*="dropdown-menu"]';
                  const nodes = [...document.querySelectorAll('div, span, h3, p, button, label')];
                  const mark = (target) => {
                    document.querySelectorAll('[data-hosen-slicer]').forEach((el) => {
                      el.removeAttribute('data-hosen-slicer');
                    });
                    target.setAttribute('data-hosen-slicer', 'active');
                    return true;
                  };
                  const visible = (el) => {
                    const style = window.getComputedStyle(el);
                    if (style.visibility === 'hidden' || style.display === 'none') return false;
                    const rect = el.getBoundingClientRect();
                    return rect.width > 0 && rect.height > 0;
                  };
                  const isClear = (el) => {
                    const label = el.getAttribute('aria-label') || '';
                    const cls = typeof el.className === 'string' ? el.className : '';
                    return label.includes('נקה') || cls.includes('clear');
                  };
                  const dropdownIn = (el) => {
                    const found = [];
                    if (el.matches && el.matches(selector)) found.push(el);
                    found.push(...el.querySelectorAll(selector));
                    const choices = found.filter((node) => visible(node) && !isClear(node));
                    return choices.find((node) => node.getAttribute('role') === 'combobox') || choices[0] || null;
                  };
                  const consider = (node, needle, exact) => {
                    const own = [...node.childNodes]
                      .filter((child) => child.nodeType === Node.TEXT_NODE)
                      .map((child) => child.textContent || '')
                      .join('')
                      .replace(/\\s+/g, ' ')
                      .trim();
                    const label = (node.getAttribute('aria-label') || '').trim();
                    const text = own || (node.innerText || '').replace(/\\s+/g, ' ').trim();
                    const hit = exact
                      ? text === needle || label === needle
                      : (text.length > 0 && text.length <= 40 && text.includes(needle))
                        || (label.length > 0 && label.length <= 40 && label.includes(needle));
                    if (!hit) return false;
                    let current = node;
                    for (let depth = 0; depth < 8 && current; depth += 1) {
                      const hostText = (current.innerText || '').replace(/\\s+/g, ' ').trim();
                      if (hostText.length > 240) break;
                      const target = dropdownIn(current);
                      const name = target ? (target.getAttribute('aria-label') || '') : '';
                      if (target && name !== 'SlicerDate') return mark(target);
                      current = current.parentElement;
                    }
                    return false;
                  };
                  for (const exact of [true, false]) {
                    for (const needle of needles) {
                      for (const node of nodes) {
                        if (consider(node, needle, exact)) return true;
                      }
                    }
                  }
                  return false;
                }""",
                list(role_names),
            )
        except Exception:
            return None
        if not found:
            return None
        marked = frame.locator("[data-hosen-slicer='active']")
        if marked.count() == 0:
            return None
        return marked.first

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
                label = self._smart_filter_label(role_names)
            else:
                label = self._selected_label(control, names)
            if not label or label in role_names:
                chip = self._smart_filter_label(role_names)
                if chip:
                    label = chip
            if label and label not in role_names:
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

    def _svg_grade(self, root: Locator) -> str:
        """Percent painted in the card SVG. innerText is empty on tspan."""
        node = root.locator(".value tspan").first
        if node.count() == 0:
            node = root.locator(
                "xpath=.//*[local-name()='text' and contains("
                "concat(' ', normalize-space(@class), ' '), ' value ')]"
                "/*[local-name()='tspan']"
            ).first
        if node.count() == 0:
            return ""
        raw = node.text_content(timeout=self.timeout) or ""
        grade = _main_percentage(_plain(raw))
        return grade or _plain(raw)

    def _read_card(self, title: str) -> dict | None:
        """One assessment card. KPI is used when the title is the card name."""
        try:
            card = self._kpi().card(title)
            if card.count() > 0 and card.is_visible():
                percentage = self._svg_grade(card)
                if not percentage:
                    raw = ""
                    try:
                        raw = self._kpi().read_text(title)
                    except Exception:
                        raw = ""
                    percentage = _main_percentage(_plain(raw))
                try:
                    signals = card.evaluate(_CARD_SIGNALS_JS)
                except Exception:
                    signals = []
                return {
                    "title": title,
                    "percentage": percentage,
                    "trend": _trend_word(signals if isinstance(signals, list) else []),
                }
        except Exception:
            pass
        host = self._mark_card(title)
        if host is None:
            return None
        percentage = ""
        snapshot = ""
        signals: list = []
        try:
            percentage = self._svg_grade(host)
            snapshot = host.aria_snapshot() or ""
            try:
                evaluated = host.evaluate(_CARD_SIGNALS_JS)
                signals = evaluated if isinstance(evaluated, list) else []
            except Exception:
                signals = []
        except Exception:
            pass
        finally:
            self._clear_card_mark(host)
        if not percentage:
            percentage = self._percentage_from_snapshot(snapshot)
        if not percentage:
            percentage = _main_percentage(_plain(snapshot))
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
            if record is None:
                continue
            categories.append({
                "title": record["title"],
                "score": record["percentage"],
                "trend_direction": record["trend"],
            })
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
                extracted_text = cells.nth(authority_index).inner_text(timeout=500) or ""
                authority = _plain(extracted_text.split("\n")[0])
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

    def _title_segments(self) -> list[str]:
        """Golden title split on ' - '. The last segment is the page name."""
        title = self._screen_2_title or ""
        if " - " not in title:
            return [title] if title else []
        return [part.strip() for part in title.split(" - ") if part.strip()]

    def _segment_locator(self, segment: str) -> Locator:
        """Exact text of one title segment, with either quote spelling."""
        frame = self._report_frame()
        locator: Locator | None = None
        for variant in _quote_variants(segment):
            piece = frame.get_by_text(variant, exact=True)
            locator = piece if locator is None else locator.or_(piece)
        if locator is None:
            return frame.get_by_text("\u0000", exact=True)
        return locator

    def _screen_2_anchor(self) -> Locator:
        """Page-name paragraph. The live title is two paragraphs, not one string."""
        segments = self._title_segments()
        page_name = segments[-1] if segments else ""
        return self._segment_locator(page_name)

    def _screen_2_settle(self, kind: str = "after_select", **_kwargs) -> bool:
        """Hide a visible spinner, then require the investigation title.

        Returning false lets ``Slicer.select`` confirm the combobox label.
        """
        if kind != "after_select":
            return False
        self._hide_visible_spinner()
        expect(self._screen_2_anchor().first).to_be_visible(timeout=self.timeout)
        return False

    def wait_for_screen_2_idle(self) -> None:
        """Wait until a visible spinner is gone and Screen 2 is showing."""
        self._screen_2_settle()

    def _node_visible(self, locator: Locator) -> bool:
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

    def _control_name_matches(self, actual: str, labels: list[str]) -> bool:
        """True when a page button's name is the title or ends with its page segment."""
        folded = " ".join(_fold_quotes(actual).replace(".", " ").split())
        page_part = folded
        for prefix in ("ניווט בין עמודים", "Page navigation"):
            if prefix in folded:
                page_part = folded.split(prefix, 1)[-1].strip()
                break
        for label in labels:
            needle = " ".join(_fold_quotes(label).split())
            if not needle:
                continue
            if folded == needle or folded.endswith(needle):
                return True
            # The rail can be shorter than the visual title: ייצוא נתונים vs ייצוא נתונים לאקסל.
            if len(page_part) >= 4 and needle.startswith(page_part):
                return True
        return False

    def _click_named_control(self, scope, labels: list[str]) -> bool:
        """Click the page button whose name equals a title or ends with its page segment.

        Power BI names the control ``ניווט בין עמודים . מסך תחקור``, not the
        visual title alone.
        """
        for role in _NAV_ROLES:
            try:
                nodes = scope.get_by_role(role).filter(visible=True)
                count = min(nodes.count(), 20)
            except Exception:
                continue
            for index in range(count):
                node = nodes.nth(index)
                try:
                    label = _plain(node.get_attribute("aria-label") or "")
                    if not label:
                        label = _plain(node.inner_text(timeout=1000) or "")
                except Exception:
                    continue
                if not self._control_name_matches(label, labels):
                    continue
                node.click(force=True, timeout=5000)
                return True
        return False

    def _navigation_scopes(self) -> list:
        """Page-navigation groups in the report iframe, then the iframe itself."""
        frame = self._report_frame()
        scopes: list = []
        for name in _PAGE_NAV:
            for finder in (
                frame.get_by_role("navigation", name=name),
                frame.get_by_role("group", name=name),
                frame.get_by_label(name),
            ):
                visible = finder.filter(visible=True)
                try:
                    if visible.count() > 0:
                        scopes.append(visible.first)
                except Exception:
                    continue
        scopes.append(frame)
        return scopes

    def open_investigation_screen(self, title: str) -> None:
        """Open the investigation screen named by the golden title."""
        self._screen_2_title = title
        labels = [title]
        if " - " in title:
            labels.append(title.rsplit(" - ", 1)[-1].strip())
        opened = False
        for scope in self._navigation_scopes():
            if self._click_named_control(scope, labels):
                opened = True
                break
        if not opened and not self._node_visible(self._screen_2_anchor()):
            raise AssertionError(
                f"Investigation screen control for {title!r} was not visible"
            )
        expect(self._screen_2_anchor().first).to_be_visible(timeout=self.timeout)
        self._screen_2_settle()

    def select_screen_2_filter(self, slicer_id: str, value: str) -> None:
        """Select one golden label on Screen 2, then wait for its title."""
        role_names = self._filter_role_names(slicer_id)
        if slicer_id in ("district", "subdistrict"):
            if self._select_smart_filter(role_names, value, settle=self._screen_2_settle):
                return
            trace = getattr(self, "_dropdown_trace", "")
            raise KeyError(
                f"Slicer {slicer_id!r} has no dropdown. Tried {role_names!r}. {trace}"
            )
        if slicer_id == "date":
            control, _names = self._filter_control(slicer_id, role_names)
            if control is None:
                trace = getattr(self, "_dropdown_trace", "")
                raise KeyError(
                    f"Slicer {slicer_id!r} has no dropdown. Tried {role_names!r}. {trace}"
                )
            self._select_date_combobox(control, value, settle=self._screen_2_settle)
            return
        known = ", ".join(known_id for known_id, _names in _FILTER_ROLES)
        raise KeyError(f"Unknown slicer id {slicer_id!r}. Known: {known}")

    def _smart_filter_shell_visible(self) -> bool:
        scopes = [self._report_frame()]
        for frame in self.page.frames:
            if "Sandbox" in (frame.url or ""):
                scopes.append(frame)
        for scope in scopes:
            shells = scope.locator("ul.TokensContainer")
            try:
                count = shells.count()
            except Exception:
                continue
            for index in range(min(count, 6)):
                try:
                    if shells.nth(index).is_visible():
                        return True
                except Exception:
                    continue
        return False

    def _summary_label_visible(self) -> bool:
        frame = self._report_frame()
        for token in _SUMMARY_LABELS:
            if self._node_visible(frame.get_by_text(token, exact=True)):
                return True
        return False

    def screen_2_section_visible(self, section: str) -> bool:
        """True when that Screen 2 block is on the investigation screen."""
        frame = self._report_frame()
        try:
            if section == "title":
                return self._node_visible(self._screen_2_anchor())
            if section == "date":
                control, _names = self._filter_control(
                    "date", self._filter_role_names("date")
                )
                return control is not None and self._node_visible(control)
            if section == "filters":
                return self._smart_filter_shell_visible() or self._node_visible(
                    frame.get_by_role("combobox")
                )
            if section == "authorities_breakdown_table":
                authority = frame.get_by_role("columnheader", name=re.compile("רשות"))
                leadership = frame.get_by_role(
                    "columnheader", name=re.compile("מנהיגות")
                )
                return self._node_visible(authority) and self._node_visible(leadership)
            if section == "totals_row":
                return self._summary_label_visible()
            if section == "trends_by_date_table":
                return self._trends_title_visible()
        except Exception:
            return False
        return False

    def _read_screen_2_title(self) -> str:
        """Join the visible title paragraphs in golden order."""
        parts: list[str] = []
        for segment in self._title_segments():
            locator = self._segment_locator(segment)
            text = ""
            try:
                count = min(locator.count(), 4)
            except Exception:
                return ""
            for index in range(count):
                node = locator.nth(index)
                try:
                    if not node.is_visible():
                        continue
                    text = _plain(node.inner_text(timeout=1000)).split("\n")[0].strip()
                except Exception:
                    continue
                if text:
                    break
            if not text:
                return ""
            parts.append(text)
        return " - ".join(parts)

    def _header_fields(self, grid: Locator) -> list[str]:
        headers = grid.get_by_role("columnheader")
        fields: list[str] = []
        try:
            count = headers.count()
        except Exception:
            return fields
        for index in range(count):
            try:
                label = _plain(headers.nth(index).inner_text(timeout=500) or "")
            except Exception:
                label = ""
            fields.append(_field_for_header(label))
        return fields

    def _breakdown_grid(self) -> Locator | None:
        frame = self._report_frame()
        header = frame.get_by_role("columnheader", name=re.compile("מנהיגות"))
        try:
            count = header.count()
        except Exception:
            return None
        for index in range(count):
            item = header.nth(index)
            try:
                if not item.is_visible():
                    continue
            except Exception:
                continue
            grid = item.locator(
                "xpath=ancestor::*[@role='grid' or @role='treegrid' or @role='table'][1]"
            )
            try:
                if grid.count() > 0:
                    return grid
            except Exception:
                continue
        return None

    def _visible_breakdown_rows(self, grid: Locator) -> list[dict[str, str]]:
        fields = self._header_fields(grid)
        rows = grid.get_by_role("row")
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
                cells = row.evaluate(_ROW_TEXT_JS)
            except Exception:
                continue
            if not isinstance(cells, list) or not cells:
                continue
            record = {field: "" for field, _header in _SCREEN2_HEADERS}
            for col, field in enumerate(fields):
                if not field or col >= len(cells):
                    continue
                raw = str(cells[col])
                if field == "authority":
                    record[field] = _plain(raw.split("\n")[0])
                else:
                    record[field] = _percent_token(raw)
            if not record.get("authority") and not any(
                record[field] for field, _header in _SCREEN2_HEADERS if field != "authority"
            ):
                continue
            found.append(record)
        return found

    def _mark_visual_host(self, node: Locator, attr: str) -> Locator | None:
        """Mark ``vcGroupBody``, the node that wraps the title strip and the chart.

        The title text sits in a 38px ``visualContainer`` header
        (``visualHeaderAbove``). That header's menu has no show-as-table item.
        ``vcGroupBody`` is the wrapper whose menu does.
        """
        frame = self._report_frame()
        try:
            marked = node.evaluate(
                """(el, attr) => {
                  let current = el.parentElement;
                  for (let depth = 0; depth < 16 && current; depth += 1) {
                    const box = current.getBoundingClientRect();
                    const cls = String(current.className || '');
                    if (
                      box.width >= 200
                      && box.height >= 120
                      && cls.includes('vcGroupBody')
                    ) {
                      current.setAttribute(attr, 'active');
                      return true;
                    }
                    current = current.parentElement;
                  }
                  return false;
                }""",
                attr,
            )
        except Exception:
            return None
        if not marked:
            return None
        marked_node = frame.locator(f"[{attr}='active']")
        try:
            if marked_node.count() == 0:
                return None
        except Exception:
            return None
        return marked_node.first

    def _clear_mark(self, host: Locator, attr: str) -> None:
        try:
            host.evaluate("(el, attr) => el.removeAttribute(attr)", attr)
        except Exception:
            return

    def _metrics_near_label(self, text: str) -> dict[str, str]:
        """Percent that follows each Hebrew header inside one visual's text."""
        metrics = {field: "" for field, _header in _SCREEN2_HEADERS if field != "authority"}
        plain = _plain(text)
        for field, header in _SCREEN2_HEADERS:
            if field == "authority":
                continue
            match = re.search(
                re.escape(header) + r".{0,48}?(\d+(?:[.,]\d+)?\s*%)",
                plain,
            )
            if match:
                metrics[field] = _percent_token(match.group(1))
        return metrics

    def _read_totals_sibling(self) -> dict[str, str]:
        """Nine percents from a summary visual that is not an authority row."""
        frame = self._report_frame()
        for token in _SUMMARY_LABELS:
            nodes = frame.get_by_text(token, exact=False)
            try:
                count = min(nodes.count(), 4)
            except Exception:
                continue
            for index in range(count):
                node = nodes.nth(index)
                try:
                    if not node.is_visible():
                        continue
                except Exception:
                    continue
                host = self._mark_visual_host(node, "data-hosen-totals")
                if host is None:
                    continue
                try:
                    text = host.inner_text(timeout=self.timeout) or ""
                except Exception:
                    text = ""
                finally:
                    self._clear_mark(host, "data-hosen-totals")
                metrics = self._metrics_near_label(text)
                if any(metrics.values()):
                    return metrics
        return {}

    def _read_breakdown(self) -> tuple[list[dict[str, str]], dict[str, str]]:
        grid = self._breakdown_grid()
        if grid is None:
            return [], self._read_totals_sibling()
        expect(grid).to_be_visible(timeout=self.timeout)
        rows = collect_virtualized_rows(
            grid,
            self._visible_breakdown_rows,
            lambda row: row.get("authority")
            or "|".join(
                row.get(field, "")
                for field, _header in _SCREEN2_HEADERS
                if field != "authority"
            ),
            timeout_ms=max(self.timeout, 120_000),
        )
        authorities: list[dict[str, str]] = []
        totals: dict[str, str] = {}
        for row in rows:
            label = row.get("authority", "")
            metrics = {
                field: row.get(field, "")
                for field, _header in _SCREEN2_HEADERS
                if field != "authority"
            }
            if _is_summary_label(label) or (not label and any(metrics.values())):
                if not totals and any(metrics.values()):
                    totals = metrics
                continue
            if label:
                authorities.append({"authority": label, **metrics})
        if not totals:
            totals = self._read_totals_sibling()
        return authorities, totals

    def _trends_title_visible(self) -> bool:
        frame = self._report_frame()
        for phrase in (_TRENDS_VISUAL_TITLE,):
            if self._node_visible(frame.get_by_text(phrase, exact=False)):
                return True
        return False

    def _trends_container(self) -> Locator | None:
        frame = self._report_frame()
        for phrase in (_TRENDS_VISUAL_TITLE,):
            nodes = frame.get_by_text(phrase, exact=False)
            try:
                count = min(nodes.count(), 6)
            except Exception:
                continue
            for index in range(count):
                node = nodes.nth(index)
                try:
                    if not node.is_visible():
                        continue
                except Exception:
                    continue
                host = self._mark_visual_host(node, "data-hosen-trend")
                if host is not None:
                    return host
        return None

    def _map_trend_row(self, raw: dict) -> dict[str, str]:
        metrics = {field: "" for field, _header in _SCREEN2_HEADERS if field != "authority"}
        creation = ""
        for header, value in raw.items():
            plain_value = _plain(str(value))
            date_match = _DATE_CELL.search(plain_value)
            if date_match and not creation:
                creation = date_match.group(0)
            field = _field_for_header(str(header))
            if field and field != "authority":
                metrics[field] = _percent_token(plain_value)
        if not creation:
            return {}
        return {"creation_date": creation, **metrics}

    def _read_trends(self) -> list[dict[str, str]]:
        container = self._trends_container()
        if container is None:
            return []
        try:
            raw_rows = VisualTable(
                self.page,
                self._report_frame(),
                timeout_ms=self.timeout,
            ).read_rows(container, name="trends_by_date")
        finally:
            self._clear_mark(container, "data-hosen-trend")
        parsed: list[dict[str, str]] = []
        for raw in raw_rows:
            if not isinstance(raw, dict):
                continue
            mapped = self._map_trend_row(raw)
            if mapped.get("creation_date"):
                parsed.append(mapped)
        return parsed

    def read_screen_2_metrics(self) -> dict:
        """Investigation-screen title, date, filters, and the three table blocks."""
        authorities, totals = self._read_breakdown()
        trends: list[dict[str, str]] = []
        if self.screen_2_section_visible("trends_by_date_table"):
            trends = self._read_trends()
        return {
            "title": self._read_screen_2_title(),
            "date": self._read_screen_1_date(),
            "filters": self._read_active_filters(),
            "tables": {
                "authorities_breakdown_table": authorities,
                "totals_row": totals,
                "trends_by_date_table": trends,
            },
        }

    def _page_name_anchor(self, title: str) -> Locator:
        """Page-name paragraph for a stored golden title, either quote spelling."""
        page_name = title.rsplit(" - ", 1)[-1].strip() if " - " in title else title
        return self._segment_locator(page_name)

    def _screen_3_anchor(self) -> Locator:
        """Geographic page name. The live title is split across paragraphs."""
        return self._page_name_anchor(self._screen_3_title)

    def _screen_4_anchor(self) -> Locator:
        """Export page name. The live title is split across paragraphs."""
        return self._page_name_anchor(self._screen_4_title)

    def _screen_3_settle(self, kind: str = "after_select", **_kwargs) -> bool:
        """Hide a visible spinner, then require the geographic title."""
        if kind != "after_select":
            return False
        self._hide_visible_spinner()
        expect(self._screen_3_anchor().first).to_be_visible(timeout=self.timeout)
        self._wait_for_visuals()
        return False

    def _wait_for_visuals(self) -> None:
        """Wait until Power BI finishes the 'loading visual' placeholders."""
        loading = self._report_frame().get_by_text(
            "מתבצעת טעינה של ערכים חזותיים"
        ).filter(visible=True)
        try:
            expect(loading).to_have_count(0, timeout=self.timeout)
        except AssertionError:
            return

    def _screen_4_settle(self, kind: str = "after_select", **_kwargs) -> bool:
        """Hide a visible spinner, then require the export title."""
        if kind != "after_select":
            return False
        self._hide_visible_spinner()
        expect(self._screen_4_anchor().first).to_be_visible(timeout=self.timeout)
        return False

    def wait_for_screen_3_idle(self) -> None:
        """Wait until a visible spinner is gone and Screen 3 is showing."""
        self._screen_3_settle()

    def wait_for_screen_4_idle(self) -> None:
        """Wait until a visible spinner is gone and Screen 4 is showing."""
        self._screen_4_settle()

    def _open_by_title(self, title: str, anchor: Locator, settle, missing: str) -> None:
        """Click the page-navigation control Screen 2 already uses, then settle."""
        labels = [title]
        if " - " in title:
            labels.append(title.rsplit(" - ", 1)[-1].strip())
        opened = False
        for scope in self._navigation_scopes():
            if self._click_named_control(scope, labels):
                opened = True
                break
        if not opened and not self._node_visible(anchor):
            raise AssertionError(missing)
        expect(anchor.first).to_be_visible(timeout=self.timeout)
        settle()

    def open_geographic_screen(self, title: str) -> None:
        """Open the geographic screen named by the golden title."""
        self._screen_3_title = title
        self._open_by_title(
            title,
            self._screen_3_anchor(),
            self._screen_3_settle,
            f"Geographic screen control for {title!r} was not visible",
        )

    def open_excel_export_screen(self, title: str) -> None:
        """Open the Excel export screen named by the golden title."""
        self._screen_4_title = title
        self._open_by_title(
            title,
            self._screen_4_anchor(),
            self._screen_4_settle,
            f"Excel export screen control for {title!r} was not visible",
        )

    def _date_textbox(self, label: str) -> Locator | None:
        """Geographic date input. The live control is a textbox, not SlicerDate."""
        frame = self._report_frame()
        field = frame.locator(f"input[aria-label^='{label}']")
        try:
            if field.count() > 0 and field.first.is_visible():
                return field.first
        except Exception:
            pass
        box = frame.get_by_role("textbox", name=re.compile(rf"^{re.escape(label)}"))
        try:
            visible = box.filter(visible=True)
            if visible.count() > 0:
                return visible.first
        except Exception:
            return None
        return None

    def _read_textbox_date(self, label: str) -> str:
        """Value typed into a geographic date textbox."""
        field = self._date_textbox(label)
        if field is None:
            return ""
        try:
            return _plain(field.input_value(timeout=1000))
        except Exception:
            return ""

    def _fill_date_textbox(self, label: str, value: str) -> None:
        """Type one geographic date and commit it with Enter."""
        shown = ""
        for _attempt in range(2):
            field = self._date_textbox(label)
            if field is None:
                raise KeyError(f"Slicer 'date_range' has no textbox {label!r}.")
            expect(field).to_be_visible(timeout=self.timeout)
            field.click(force=True)
            field.fill(value)
            field.press("Enter")
            self._screen_3_settle("after_select")
            try:
                expect(field).to_have_value(
                    re.compile(re.escape(value)), timeout=8_000
                )
                return
            except AssertionError:
                shown = self._read_textbox_date(label)
                if value in shown:
                    return
        raise AssertionError(
            f"Slicer 'date_range' textbox {shown!r} does not contain {value!r}"
        )

    def _read_date_range_labels(self) -> tuple[str, str]:
        """Selected start and end labels from the two geographic textboxes."""
        return (
            self._read_textbox_date("תאריך התחלה"),
            self._read_textbox_date("תאריך סיום"),
        )

    def select_screen_3_date_range(self, start: str, end: str) -> None:
        """Apply the geographic start date, then the end date."""
        self._fill_date_textbox("תאריך התחלה", start)
        self._fill_date_textbox("תאריך סיום", end)

    def _roles_from(self, table: tuple, slicer_id: str) -> tuple[str, ...]:
        """Placeholder hints for one screen-local filter id."""
        for known_id, role_names in table:
            if known_id == slicer_id:
                return role_names
        known = ", ".join(known_id for known_id, _names in table)
        raise KeyError(f"Unknown slicer id {slicer_id!r}. Known: {known}")

    def _filter_shell_texts(self) -> list[str]:
        """Smart-filter shell texts from top to bottom, including empty placeholders."""
        for frame in self.page.frames:
            if "Sandbox" not in (frame.url or ""):
                continue
            shells = frame.locator("ul.TokensContainer")
            try:
                count = shells.count()
            except Exception:
                continue
            boxes: list[tuple[float, str]] = []
            for index in range(count):
                item = shells.nth(index)
                try:
                    box = item.bounding_box()
                    text = item.inner_text(timeout=2000)
                except Exception:
                    continue
                if box is None or box["width"] < 8 or box["width"] > 450:
                    continue
                if box["height"] < 8 or box["height"] > 120:
                    continue
                cleaned = (
                    _plain(text).replace("×", "").replace("✕", "").replace("✖", "").strip()
                )
                boxes.append((box["y"], cleaned))
            if boxes:
                boxes.sort(key=lambda pair: pair[0])
                return [text for _top, text in boxes]
        return []

    def _chip_for_role_names(self, role_names: tuple[str, ...]) -> str | None:
        """Chip whose search placeholder matches. None when that input is absent."""
        viewport = self.page.viewport_size or {"width": 1600, "height": 900}
        hints = {_plain(name) for name in role_names}
        for frame in self.page.frames:
            if "Sandbox" not in (frame.url or ""):
                continue
            for hint in role_names:
                candidate = frame.locator(f"input[placeholder*='{hint}']")
                try:
                    count = candidate.count()
                except Exception:
                    continue
                for index in range(count):
                    item = candidate.nth(index)
                    try:
                        box = item.bounding_box()
                    except Exception:
                        continue
                    if box is None or box["width"] < 8 or box["height"] < 8:
                        continue
                    center_x = box["x"] + box["width"] / 2
                    center_y = box["y"] + box["height"] / 2
                    if not (
                        0 <= center_x <= viewport["width"]
                        and 0 <= center_y <= viewport["height"]
                    ):
                        continue
                    shell = item.locator(
                        "xpath=ancestor::ul[contains(@class, 'TokensContainer')][1]"
                    )
                    try:
                        text = shell.inner_text(timeout=2000)
                    except Exception:
                        return ""
                    cleaned = (
                        _plain(text).replace("×", "").replace("✕", "").replace("✖", "").strip()
                    )
                    if not cleaned or cleaned.startswith("בחר") or _plain(cleaned) in hints:
                        return ""
                    return cleaned
        return None

    def _read_screen_filter(self, table: tuple, slicer_id: str) -> str:
        """Selected chip for one id. Empty when the box still shows its placeholder."""
        role_names = self._roles_from(table, slicer_id)
        found = self._chip_for_role_names(role_names)
        if found is not None:
            return found
        # level_selected is a button, not a TokensContainer, so it must not
        # consume a chip index. District stays the first shell.
        chip_ids = [
            known_id
            for known_id, _names in table
            if known_id != "level_selected"
        ]
        if slicer_id not in chip_ids:
            return ""
        index = chip_ids.index(slicer_id)
        shells = self._filter_shell_texts()
        if index >= len(shells):
            return ""
        text = shells[index]
        hints = {_plain(name) for name in role_names}
        if not text or text.startswith("בחר") or _plain(text) in hints:
            return ""
        return text

    def _pressed_level(self) -> str:
        """Label of the pressed geographic level button. Empty when none is pressed."""
        frame = self._report_frame()
        for label in ("מחוז", "נפה", "רשות"):
            button = frame.get_by_role("button", name=label, exact=True).filter(visible=True)
            try:
                if button.count() == 0:
                    continue
                target = button.first
                state = " ".join(
                    (
                        target.get_attribute("aria-pressed") or "",
                        target.get_attribute("aria-selected") or "",
                        target.get_attribute("aria-checked") or "",
                    )
                ).lower()
                if "true" in state:
                    return label
            except Exception:
                continue
        return ""

    def _read_filter_map(self, table: tuple) -> dict[str, str]:
        """Every id in ``table``. A placeholder box is an empty string."""
        selected = {
            slicer_id: self._read_screen_filter(table, slicer_id)
            for slicer_id, _names in table
        }
        if "level_selected" in selected:
            pressed = self._pressed_level()
            if pressed:
                selected["level_selected"] = pressed
        return selected

    def _press_level_button(self, value: str) -> bool:
        """Click the geographic level button (מחוז, נפה, or רשות) when it is not already pressed."""
        frame = self._report_frame()
        button = frame.get_by_role("button", name=value, exact=True).filter(visible=True)
        try:
            if button.count() == 0:
                return False
            target = button.first
            pressed = (target.get_attribute("aria-pressed") or "").lower()
            if pressed != "true":
                target.click(force=True)
        except Exception:
            return False
        self._screen_3_settle("after_select")
        return True

    def select_screen_3_filter(self, slicer_id: str, value: str) -> None:
        """Select one non-null geographic filter, then wait for Screen 3."""
        if slicer_id == "level_selected":
            if self._press_level_button(value):
                return
            raise KeyError(f"Slicer {slicer_id!r} has no button {value!r}.")
        role_names = self._roles_from(_SCREEN3_FILTERS, slicer_id)
        if self._select_smart_filter(role_names, value, settle=self._screen_3_settle):
            return
        trace = getattr(self, "_dropdown_trace", "")
        raise KeyError(
            f"Slicer {slicer_id!r} has no dropdown. Tried {role_names!r}. {trace}"
        )

    def select_screen_4_filter(self, slicer_id: str, value: str) -> None:
        """Select one export-screen label, then wait for Screen 4."""
        if slicer_id == "date":
            role_names = self._filter_role_names("date")
            control, _names = self._filter_control("date", role_names)
            if control is None:
                trace = getattr(self, "_dropdown_trace", "")
                raise KeyError(
                    f"Slicer {slicer_id!r} has no dropdown. Tried {role_names!r}. {trace}"
                )
            self._select_date_combobox(control, value, settle=self._screen_4_settle)
            return
        role_names = self._roles_from(_SCREEN4_FILTERS, slicer_id)
        if self._select_smart_filter(role_names, value, settle=self._screen_4_settle):
            return
        trace = getattr(self, "_dropdown_trace", "")
        raise KeyError(
            f"Slicer {slicer_id!r} has no dropdown. Tried {role_names!r}. {trace}"
        )

    def _read_split_title(self, title: str) -> str:
        """Join the visible title paragraphs in golden order."""
        if not title:
            return ""
        segments = (
            [part.strip() for part in title.split(" - ") if part.strip()]
            if " - " in title
            else [title]
        )
        parts: list[str] = []
        for segment in segments:
            locator = self._segment_locator(segment)
            text = ""
            try:
                count = min(locator.count(), 4)
            except Exception:
                return ""
            for index in range(count):
                node = locator.nth(index)
                try:
                    if not node.is_visible():
                        continue
                    text = _plain(node.inner_text(timeout=1000)).split("\n")[0].strip()
                except Exception:
                    continue
                if text:
                    break
            if not text:
                return ""
            parts.append(text)
        return " - ".join(parts)

    def _smart_filter_shell_present(self) -> bool:
        """True when a smart-filter shell or any combobox is on the current screen."""
        if self._smart_filter_shell_visible():
            return True
        return self._node_visible(self._report_frame().get_by_role("combobox"))

    def screen_3_section_visible(self, section: str) -> bool:
        """True when that Screen 3 block is on the geographic screen."""
        try:
            if section == "title":
                return bool(self._screen_3_title) and self._node_visible(self._screen_3_anchor())
            if section == "date_range":
                return (
                    self._date_textbox("תאריך התחלה") is not None
                    and self._date_textbox("תאריך סיום") is not None
                )
            if section == "filters":
                return self._smart_filter_shell_present()
            if section == "final_resilience_score":
                return self._chart_present(_FINAL_SCORE_HINT, exact=False)
            if section == "categories":
                return any(
                    self._chart_present(title, exact=True) for title in _CATEGORY_TITLES
                )
        except Exception:
            return False
        return False

    def screen_4_section_visible(self, section: str) -> bool:
        """True when that Screen 4 block is on the export screen."""
        frame = self._report_frame()
        try:
            if section == "title":
                return bool(self._screen_4_title) and self._node_visible(self._screen_4_anchor())
            if section == "date":
                control, _names = self._filter_control(
                    "date", self._filter_role_names("date")
                )
                return control is not None and self._node_visible(control)
            if section == "filters":
                return self._smart_filter_shell_present()
            if section == "data_table":
                header = frame.get_by_role("columnheader", name=re.compile("רשות"))
                return self._node_visible(header)
        except Exception:
            return False
        return False

    def _host_has_plot(self, host: Locator) -> bool:
        """True when the marked body is one chart, not the page group.

        A page-level ``vcGroupBody`` is tall enough to pass the marker and its
        center is not the graph, so the context menu has no show-as-table item.
        """
        try:
            box = host.bounding_box()
        except Exception:
            return False
        if box is None or box["width"] < 200 or box["height"] < 120:
            return False
        if box["height"] > 720 or box["width"] > 1200:
            return False
        try:
            plots = host.locator("svg, canvas")
            count = min(plots.count(), 8)
        except Exception:
            return False
        for index in range(count):
            try:
                plot_box = plots.nth(index).bounding_box()
            except Exception:
                continue
            if plot_box and plot_box["width"] >= 120 and plot_box["height"] >= 80:
                return True
        return False

    def _chart_present(self, phrase: str, *, exact: bool) -> bool:
        """True when the phrase has a graph body. The probe mark is cleared."""
        found = self._chart_host(phrase, exact=exact)
        if found is None:
            return False
        _node, host = found
        self._clear_mark(host, "data-hosen-chart")
        return True

    def _ranked_chart_nodes(self, phrase: str, *, exact: bool) -> list[Locator]:
        """Visible title nodes for one phrase, chart titles before summary labels."""
        frame = self._report_frame()
        nodes = frame.get_by_text(phrase, exact=False)
        try:
            count = min(nodes.count(), 24)
        except Exception:
            return []
        ranked: list[tuple[int, int, Locator]] = []
        for index in range(count):
            node = nodes.nth(index)
            try:
                if not node.is_visible():
                    continue
                if (node.get_attribute("role") or "") == "columnheader":
                    continue
                if node.evaluate("el => Boolean(el.closest('svg, canvas'))"):
                    continue
                text = _plain(node.inner_text(timeout=500))
            except Exception:
                continue
            first_line = text.splitlines()[0].strip() if text else ""
            if exact and first_line != phrase:
                continue
            score = 0
            if "שבועיים" in text:
                score += 10
            if len(text) <= 180:
                score += 4
            if len(text) <= 90:
                score += 2
            try:
                box = node.bounding_box()
            except Exception:
                box = None
            if box is not None:
                # The chart title sits lower than the same word in a summary strip.
                score += int(box["y"] // 120)
            ranked.append((score, -index, node))
        if exact:
            labeled = frame.locator(f"[aria-label='{phrase}'], [title='{phrase}']")
            try:
                extra = min(labeled.count(), 4)
            except Exception:
                extra = 0
            for index in range(extra):
                ranked.append((40, -100 - index, labeled.nth(index)))
        ranked.sort(reverse=True)
        return [node for _score, _order, node in ranked]

    def _title_visual(self, node: Locator) -> Locator | None:
        """Smallest chart-sized ancestor of a title span. Not the page group."""
        frame = self._report_frame()
        try:
            marked = node.evaluate(
                """el => {
                  let current = el.parentElement;
                  for (let depth = 0; depth < 14 && current; depth += 1) {
                    const box = current.getBoundingClientRect();
                    const plot = current.querySelector('svg, canvas');
                    const sized = box.width >= 220 && box.width <= 1100
                      && box.height >= 140 && box.height <= 480;
                    if (!plot || !sized) {
                      current = current.parentElement;
                      continue;
                    }
                    const plotBox = plot.getBoundingClientRect();
                    if (plotBox.width < 120 || plotBox.height < 80) {
                      current = current.parentElement;
                      continue;
                    }
                    current.setAttribute('data-hosen-chart', 'active');
                    return true;
                  }
                  return false;
                }"""
            )
        except Exception:
            return None
        if not marked:
            return None
        target = frame.locator("[data-hosen-chart='active']")
        try:
            if target.count() == 0:
                return None
        except Exception:
            return None
        return target.first

    def _chart_host(
        self, phrase: str, *, exact: bool
    ) -> tuple[Locator, Locator] | None:
        """Title node and its graph body. Skips a column header and the title strip."""
        frame = self._report_frame()
        try:
            stale = frame.locator("[data-hosen-chart='active']")
            for _attempt in range(8):
                if stale.count() == 0:
                    break
                self._clear_mark(stale.first, "data-hosen-chart")
        except Exception:
            pass
        for node in self._ranked_chart_nodes(phrase, exact=exact):
            host = self._mark_visual_host(node, "data-hosen-chart")
            if host is None:
                continue
            if self._host_has_plot(host):
                return node, host
            self._clear_mark(host, "data-hosen-chart")
        return None

    def _chart_title_text(self, node: Locator, phrase: str) -> str:
        """Visible title line that contains ``phrase``."""
        try:
            text = _plain(node.inner_text(timeout=1000))
        except Exception:
            return phrase
        for line in text.splitlines():
            cleaned = line.strip()
            if phrase in cleaned and len(cleaned) <= 160:
                return cleaned
        first = text.split("\n")[0].strip()
        if first and len(first) <= 160:
            return first
        return phrase

    def _sandbox_text(self, host: Locator) -> str:
        """Text of visual sandboxes painted inside this graph body."""
        parts: list[str] = []
        for frame in self.page.frames:
            try:
                element = frame.frame_element()
                inside = host.evaluate("(host, node) => Boolean(node && host.contains(node))", element)
            except Exception:
                continue
            if not inside:
                continue
            try:
                parts.append(frame.locator("body").inner_text(timeout=2_000))
            except Exception:
                continue
        return " ".join(parts)

    def _legend_near(self, node: Locator) -> str:
        """Geography name painted next to the chart title, before the page text."""
        try:
            chunks = node.evaluate(
                """el => {
                  const chunks = [];
                  let current = el;
                  for (let depth = 0; depth < 6 && current; depth += 1) {
                    chunks.push((current.innerText || '').slice(0, 500));
                    current = current.parentElement;
                  }
                  return chunks;
                }"""
            )
        except Exception:
            return ""
        if not isinstance(chunks, list):
            return ""
        for chunk in chunks:
            collapsed = " ".join(_plain(chunk).split())
            if len(collapsed) > 400:
                continue
            match = re.search(r"מחוז\s+\S+|נפת\s+\S+", collapsed)
            if match:
                return match.group(0).strip(" ,.;")
        return ""

    def _legend_from_host(self, host: Locator, title: str) -> str:
        """Short Hebrew line inside the chart host that is not the title or a value."""
        try:
            text = host.inner_text(timeout=self.timeout) or ""
        except Exception:
            text = ""
        try:
            labels = host.evaluate(
                """el => {
                  const bits = [];
                  for (const node of el.querySelectorAll('[aria-label], [title]')) {
                    const value = node.getAttribute('aria-label') || node.getAttribute('title') || '';
                    if (value) bits.push(value);
                    if (bits.length >= 40) break;
                  }
                  return bits.join(' ');
                }"""
            ) or ""
        except Exception:
            labels = ""
        collapsed = " ".join(
            _plain(f"{text} {labels} {self._sandbox_text(host)}").split()
        )
        geography = re.search(r"מחוז\s+\S+|נפת\s+\S+", collapsed)
        if geography:
            return geography.group(0).strip(" ,.;")
        skipped = set(_CATEGORY_TITLES)
        skipped.update({_FINAL_SCORE_HINT, "מחוז", "נפה", "רשות"})
        candidates: list[str] = []
        for line in text.splitlines():
            plain = _plain(line)
            if not plain or plain in title or title in plain or plain in skipped:
                continue
            if plain.startswith("בחר"):
                continue
            if _DATE_CELL.search(plain) or _PERCENT.search(plain) or _NUMBER.search(plain):
                continue
            if _HEBREW.search(plain) and len(plain) <= 40:
                candidates.append(plain)
        for plain in candidates:
            if plain.startswith(("מחוז", "נפת", "נפה", "רשות")):
                return plain
        return candidates[0] if candidates else ""

    def _map_chart_row(self, raw: dict) -> dict[str, str]:
        """One chart row: the first date cell and the first percent."""
        found_date = ""
        score = ""
        for _header, value in raw.items():
            plain_value = _plain(str(value))
            date_match = _DATE_CELL.search(plain_value)
            if date_match and not found_date:
                found_date = date_match.group(0)
            token = _percent_token(plain_value)
            if token and not score:
                score = token
        if not found_date:
            return {}
        return {"date": found_date, "score": score}

    def _read_chart(self, phrase: str, *, exact: bool, name: str) -> dict | None:
        """Right-click the graph body and map date/score rows. Legend is read first."""
        nodes = self._ranked_chart_nodes(phrase, exact=exact)
        if not nodes:
            return None
        table = VisualTable(
            self.page,
            self._report_frame(),
            timeout_ms=self.timeout,
        )
        for node in nodes[:4]:
            host = None
            if phrase == "נרטיב":
                host = self._title_visual(node)
            if host is None:
                host = self._mark_visual_host(node, "data-hosen-chart")
            if host is None or not self._host_has_plot(host):
                if host is not None:
                    self._clear_mark(host, "data-hosen-chart")
                    host = None
                if phrase != "נרטיב":
                    host = self._title_visual(node)
            if host is None:
                continue
            legend = self._legend_from_host(host, phrase) or self._legend_near(node)
            title = self._chart_title_text(node, phrase)
            try:
                node.scroll_into_view_if_needed(timeout=self.timeout)
                host.scroll_into_view_if_needed(timeout=self.timeout)
            except Exception:
                pass
            target = self._plot_click_target(host, node)
            try:
                try:
                    raw_rows = table.read_rows(target, name=name)
                except AssertionError:
                    raw_rows = table.read_rows(host, name=name)
            except AssertionError:
                self._clear_mark(host, "data-hosen-chart")
                self._clear_plot_mark()
                continue
            finally:
                self._clear_mark(host, "data-hosen-chart")
                self._clear_plot_mark()
            data: list[dict[str, str]] = []
            for raw in raw_rows:
                if not isinstance(raw, dict):
                    continue
                if not legend:
                    legend = self._legend_from_headers(raw)
                mapped = self._map_chart_row(raw)
                if mapped.get("date"):
                    data.append(mapped)
            if data or not name.startswith("category_"):
                return {"title": title, "legend": legend, "data": data}
        return None

    def _legend_from_headers(self, raw: dict) -> str:
        """Series name exposed as a show-as-table column."""
        for header in raw:
            collapsed = " ".join(_plain(str(header)).split())
            match = re.search(r"מחוז\s+\S+|נפת\s+\S+", collapsed)
            if match:
                return match.group(0).strip(" ,.;")
        return ""

    def _read_final_score_chart(self) -> dict:
        """Final resilience chart. Empty when its title is not on screen."""
        chart = self._read_chart(
            _FINAL_SCORE_HINT, exact=False, name="final_resilience_score"
        )
        if chart is None:
            return {"title": "", "legend": "", "data": []}
        return chart

    def _read_category_charts(self) -> list[dict]:
        """Category charts whose titles are already page constants. YAML stays the golden list."""
        charts: list[dict] = []
        for index, title in enumerate(_CATEGORY_TITLES):
            chart = self._read_chart(title, exact=True, name=f"category_{index}")
            if chart is None:
                continue
            charts.append({"title": chart["title"], "data": chart["data"]})
        return charts

    def read_screen_3_metrics(self) -> dict:
        """Geographic title, date range, filters, and the chart blocks."""
        start, end = self._read_date_range_labels()
        final = {"title": "", "legend": "", "data": []}
        categories: list[dict] = []
        if self.screen_3_section_visible("final_resilience_score"):
            final = self._read_final_score_chart()
        if self.screen_3_section_visible("categories"):
            categories = self._read_category_charts()
        return {
            "title": self._read_split_title(self._screen_3_title),
            "date_range": {"start": start, "end": end},
            "filters": self._read_filter_map(_SCREEN3_FILTERS),
            "graphs": {
                "final_resilience_score": final,
                "categories": categories,
            },
        }

    def _blank_export_row(self) -> dict[str, str]:
        """One export row with every Screen 4 field, values still empty."""
        row: dict[str, str] = {}
        for field, _header in _SCREEN4_HEADERS:
            row.setdefault(field, "")
        return row

    def _export_grid(self) -> Locator | None:
        """Grid on this screen whose header contains the authority column."""
        frame = self._report_frame()
        header = frame.get_by_role("columnheader", name=re.compile("רשות"))
        try:
            count = header.count()
        except Exception:
            return None
        for index in range(count):
            item = header.nth(index)
            try:
                if not item.is_visible():
                    continue
            except Exception:
                continue
            grid = item.locator(
                "xpath=ancestor::*[@role='grid' or @role='treegrid' or @role='table'][1]"
            )
            try:
                if grid.count() > 0:
                    return grid
            except Exception:
                continue
        return None

    def _plot_click_target(self, host: Locator, title_node: Locator) -> Locator:
        """The plot directly under this chart title, never the title strip.

        A point in the middle of a tall group can land on the next chart.
        The svg that sits just below the title belongs to this visual.
        """
        frame = self._report_frame()
        try:
            marked = title_node.evaluate(
                """(el) => {
                  const titleBox = el.getBoundingClientRect();
                  const plots = [...el.ownerDocument.querySelectorAll('svg, canvas')];
                  let best = null;
                  let bestDy = Infinity;
                  for (const plot of plots) {
                    const box = plot.getBoundingClientRect();
                    if (box.width < 120 || box.height < 80) continue;
                    if (box.width > 1200 || box.height > 720) continue;
                    const overlap = Math.min(titleBox.right, box.right) - Math.max(titleBox.left, box.left);
                    if (overlap < 40) continue;
                    const dy = box.top - titleBox.bottom;
                    if (dy < -30 || dy > 280) continue;
                    if (dy < bestDy) {
                      bestDy = dy;
                      best = plot;
                    }
                  }
                  if (!best) return false;
                  best.setAttribute('data-hosen-plot', 'active');
                  return true;
                }"""
            )
        except Exception:
            marked = False
        if not marked:
            return host
        target = frame.locator("[data-hosen-plot='active']")
        try:
            if target.count() == 0:
                return host
        except Exception:
            return host
        return target.first

    def _clear_plot_mark(self) -> None:
        try:
            marked = self._report_frame().locator("[data-hosen-plot='active']")
            if marked.count() == 0:
                return
            self._clear_mark(marked.first, "data-hosen-plot")
        except Exception:
            return

    def _export_header_label(self, header: Locator) -> str:
        """Header text plus its accessible name. A wrapped header still matches."""
        parts: list[str] = []
        try:
            text = _plain(header.inner_text(timeout=500) or "")
        except Exception:
            text = ""
        if text:
            parts.append(text)
        for attr in ("aria-label", "title"):
            try:
                value = _plain(header.get_attribute(attr) or "")
            except Exception:
                value = ""
            if value and value not in parts:
                parts.append(value)
        return " ".join(parts)

    def _visible_export_rows(self, grid: Locator) -> list[dict[str, str]]:
        """Authority rows currently painted. Metric cells stay percent text."""
        headers = grid.get_by_role("columnheader")
        fields: list[str] = []
        try:
            count = headers.count()
        except Exception:
            return []
        for index in range(count):
            fields.append(
                _field_for_screen4_header(self._export_header_label(headers.nth(index)))
            )
        rows = grid.get_by_role("row")
        found: list[dict[str, str]] = []
        try:
            row_count = rows.count()
        except Exception:
            return found
        for index in range(row_count):
            row = rows.nth(index)
            try:
                if row.get_by_role("columnheader").count() > 0:
                    continue
                cells = row.evaluate(_ROW_TEXT_JS)
            except Exception:
                continue
            if not isinstance(cells, list) or not cells:
                continue
            record = self._blank_export_row()
            for col, field in enumerate(fields):
                if not field or col >= len(cells):
                    continue
                raw = str(cells[col])
                if field == "authority":
                    record[field] = _plain(raw.split("\n")[0])
                else:
                    record[field] = _percent_token(raw)
            label = record.get("authority", "")
            if _is_summary_label(label):
                continue
            if not label and not any(
                record[field] for field in record if field != "authority"
            ):
                continue
            found.append(record)
        return found

    def _read_export_table(self) -> list[dict[str, str]]:
        """Authority grid already shown as a table. No workbook download."""
        grid = self._export_grid()
        if grid is None:
            return []
        expect(grid).to_be_visible(timeout=self.timeout)
        rows = collect_virtualized_rows(
            grid,
            self._visible_export_rows,
            lambda row: row.get("authority", ""),
            timeout_ms=max(self.timeout, 120_000),
        )
        return [row for row in rows if row.get("authority")]

    def read_screen_4_metrics(self) -> dict:
        """Export-screen title, date, filters, and the authority table."""
        table: list[dict[str, str]] = []
        if self.screen_4_section_visible("data_table"):
            table = self._read_export_table()
        return {
            "title": self._read_split_title(self._screen_4_title),
            "date": self._read_screen_1_date(),
            "filters": self._read_filter_map(_SCREEN4_FILTERS),
            "data_table": table,
        }
