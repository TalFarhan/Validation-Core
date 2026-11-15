"""Credit Consumption report: Screen 1 summary and Screen 2 data export.

Layer 0 portal steps stay on ReportShell. Domain titles, bilingual locators,
toggles, Show-as-a-table reads, and the export grid live here.
"""

from __future__ import annotations

import re
import time
from typing import Any

from playwright.sync_api import Error, Locator, Page, expect
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

from config.settings import settings
from core.components.kpi import KPI
from core.components.slicer import Slicer, SlicerDefinition
from core.portal.page import ReportShell

_POPUP_CLOSE_NAME = re.compile(r"Close|סגור|סגירה|Dismiss|×|✕|^X$", re.I)
_VISUAL_CONTAINER = (
    ".visualContainerHost, .visual-container-host, "
    "[class*='visualContainerHost'], "
    ".visualContainer, .visual-container, "
    ".visual-container-component, "
    "[class*='visualContainer'], [class*='visual-container']"
)
_CLOSE_VISUAL_SELECTOR = (
    "div.visual-image, div.visual-shape, "
    "div[class*='visual-image'], div[class*='visual-shape'], "
    "div.visual:has(img), div.visual:has(svg), "
    f"{_VISUAL_CONTAINER}:has(img), {_VISUAL_CONTAINER}:has(svg), "
    "iframe.visual-sandbox"
)
_BIDI_MARKS = ("\u200f", "\u200e", "\u202a", "\u202b", "\u202c")
_WEEKDAYS = {"ראשון", "שני", "שלישי", "רביעי", "חמישי", "שישי", "שבת"}
_DATE_TOKEN = re.compile(r"\d{1,2}/\d{1,2}/\d{4}")
_NUMBER_TOKEN = re.compile(r"-?\d[\d,]*(?:\.\d+)?")
_DEFAULT_FILTER = "הכל"


def _plain_cell(raw: str) -> str:
    """Cell text with a doubled Power BI label collapsed to one copy."""
    text = (raw or "").strip()
    for mark in _BIDI_MARKS:
        text = text.replace(mark, "")
    text = text.strip()
    if len(text) >= 2 and len(text) % 2 == 0 and text[: len(text) // 2] == text[len(text) // 2 :]:
        return text[: len(text) // 2]
    return text


def _parse_number(raw: str) -> int | float | None:
    """Parse one numeric cell. None when the text has no number."""
    text = _plain_cell(raw).replace(",", "").replace("\u00a0", "").strip()
    if not text:
        return None
    match = _NUMBER_TOKEN.search(text)
    if match is None:
        return None
    token = match.group(0).replace(",", "")
    try:
        number = float(token)
    except ValueError:
        return None
    if number.is_integer():
        return int(number)
    return number


class CreditConsumptionPage(ReportShell):
    """Credit Consumption. Screen 1 is the default; Screen 2 is the export page."""

    DASHBOARD_SEARCH_TERM = "צריכת אשראי"
    READY_VISUAL = "ממוצע הוצאות לקנייה בשגרה"
    SCREEN_1_TITLE = "תמ״צ צריכת אשראי"
    SCREEN_2_TITLE = "צריכת אשראי - ייצוא נתונים"
    TRENDS_CHART = "מגמת הוצאות"
    AUTHORITY_CHART = "הוצאות לפי רשות"
    ALERTS_CHART = "התרעות לפי תאריך"

    _PAGE_NAV_HE = "ניווט בין עמודים"
    _PAGE_NAV_EN = "Page navigation"
    _SHOW_TABLE = ("הצג כטבלה", "Show as a table")
    _BACK_TO_REPORT = ("חזרה לדוח", "Back to report")

    # Live-copied Power BI labels for this report's slicers and cards.
    _SLICER_DEFINITIONS = (
        SlicerDefinition(id="guidelines_area", role_name="אזור הנחיות", kind="dropdown"),
        SlicerDefinition(id="district", role_name="מחוז", kind="dropdown"),
        SlicerDefinition(id="sub_district", role_name="נפה", kind="dropdown"),
        SlicerDefinition(id="time_range", role_name="תקופה", kind="dropdown"),
        SlicerDefinition(id="period", role_name="תקופה", kind="dropdown"),
        SlicerDefinition(id="sector", role_name="מגזר", kind="dropdown"),
        SlicerDefinition(id="purchase_nature", role_name="אופי רכישה", kind="dropdown"),
        SlicerDefinition(id="vitality_status", role_name="חיוניות", kind="dropdown"),
        SlicerDefinition(id="category", role_name="קטגוריה", kind="dropdown"),
        SlicerDefinition(id="index", role_name="מדד", kind="dropdown"),
        SlicerDefinition(id="authority", role_name="רשות", kind="dropdown"),
        SlicerDefinition(id="date", role_name="תאריך", kind="dropdown"),
        SlicerDefinition(id="day_of_week", role_name="יום בשבוע", kind="dropdown"),
    )

    _KPI_SPECS: tuple[tuple[tuple[str, ...], str, str], ...] = (
        (("num_population",), "אוכלוסייה", "number"),
        (
            ("average_purchase_expense_routine", "physical_purchase"),
            READY_VISUAL,
            "number",
        ),
        (
            ("average_purchase_expense_selected_range", "total"),
            "ממוצע הוצאות לקנייה בטווח שנבחר",
            "number",
        ),
        (
            ("average_purchase_expense_selected_range", "physical_purchase"),
            "ממוצע הוצאה לקנייה פיזית",
            "number",
        ),
        (
            ("average_purchase_expense_selected_range", "online_purchase"),
            "ממוצע הוצאה לקנייה מקוונת",
            "number",
        ),
        (
            ("average_change_percentage_vs_routine", "physical_purchase"),
            "שינוי ממוצע מול שגרה פיזית",
            "percent",
        ),
        (
            ("average_change_percentage_vs_routine", "online_purchase"),
            "שינוי ממוצע מול שגרה מקוונת",
            "percent",
        ),
    )

    _METRIC_NAMES = {
        "expense_amount": ("סכום הוצאה", "Expense amount"),
        "transactions_count": ("מספר עסקאות", "Transactions count"),
    }
    _VIZ_NAMES = {
        "line": ("גרף קו", "Line"),
        "bar": ("גרף עמודות", "Bar"),
    }
    _EXPORT_HEADERS = {
        "transaction_date": ("תאריך עסקה", "תאריך", "Transaction date"),
        "authority_name": ("שם רשות", "רשות", "Authority"),
        "vitality_status": ("חיוניות", "Vitality"),
        "category": ("קטגוריה", "Category"),
        "sub_category": ("תת קטגוריה", "תת-קטגוריה", "Sub category"),
        "quantity": ("כמות", "Quantity"),
        "amount": ("סכום", "Amount"),
        "purchase_nature": ("אופי רכישה", "Purchase nature"),
    }

    def __init__(self, page: Page):
        super().__init__(page)
        self.url = settings.LOGIN_URL or settings.DASHBOARD_URL
        self.timeout = 120_000
        page.set_default_navigation_timeout(self.timeout)
        page.set_default_timeout(self.timeout)
        self.dashboard = page.frame_locator("main iframe")
        self._on_export_page = False
        self._active_metric = "expense_amount"
        self._active_visualization = "line"
        self._kpi = KPI(page=page, frame=self.dashboard, timeout_ms=self.timeout)
        self._slicer = Slicer(
            page=page,
            frame=self.dashboard,
            definitions=self._SLICER_DEFINITIONS,
            settle=self._slicer_settle,
            timeout_ms=self.timeout,
        )

    def _slicer_settle(self, kind: str, **_kwargs) -> bool:
        """Wait until the current screen's ready phrase is visible again."""
        if kind not in ("after_select", "after_clear"):
            return False
        expect(self._report_ready_locator()).to_be_visible(timeout=self.timeout)
        return True

    def _report_ready_locator(self):
        if self._on_export_page:
            return self._iframe_phrase_locator(self.SCREEN_2_TITLE)
        return self._iframe_phrase_locator(self.READY_VISUAL)

    def before_report_ready_check(self) -> None:
        self._close_info_popup(wait_ms=200)

    def after_navigate(self) -> None:
        self._on_export_page = False
        for _ in range(2):
            if not self._info_popup_visible(wait_ms=800):
                return
            self._close_info_popup(wait_ms=800)
            self.page.wait_for_timeout(400)

    def export_page_is_open(self) -> bool:
        """True when the Screen 2 export title is visible in the report iframe."""
        locator = self._iframe_phrase_locator(self.SCREEN_2_TITLE)
        try:
            return locator.is_visible(timeout=2_000)
        except Error:
            return False

    def open_export_page(self) -> None:
        """Switch to the data-export page through a bilingual page-rail control."""
        if self.export_page_is_open():
            self._on_export_page = True
            return
        frame = self._report_frame()
        he = self._PAGE_NAV_HE
        en = self._PAGE_NAV_EN
        nav = (
            frame.get_by_role("link", name=he)
            .or_(frame.get_by_role("button", name=he))
            .or_(frame.get_by_label(he, exact=False))
            .or_(frame.get_by_role("link", name=en))
            .or_(frame.get_by_role("button", name=en))
            .or_(frame.get_by_label(en, exact=False))
        )
        visible = nav.filter(visible=True)
        expect(visible.first).to_be_visible(timeout=self.timeout)
        visible.first.click(force=True)
        expect(self._iframe_phrase_locator(self.SCREEN_2_TITLE)).to_be_visible(
            timeout=self.timeout
        )
        self._on_export_page = True

    def apply_filters(self, filters: dict[str, str]) -> None:
        """Apply YAML active_filters. Values of הכל are the default and are skipped."""
        for slicer_id, value in filters.items():
            if value is None or str(value).strip() == _DEFAULT_FILTER:
                continue
            if slicer_id in ("start_date", "end_date"):
                continue
            if slicer_id not in {item.id for item in self._SLICER_DEFINITIONS}:
                continue
            self._slicer.select(slicer_id, str(value))
        start = filters.get("start_date")
        end = filters.get("end_date")
        if start and end:
            self._fill_input("תאריך התחלה", "Start date", str(start))
            self._fill_input("תאריך סיום", "End date", str(end))
        expect(self._report_ready_locator()).to_be_visible(timeout=self.timeout)

    def _fill_input(self, hebrew: str, english: str, value: str) -> None:
        """Fill a date field through a bilingual aria-label prefix."""
        frame = self._report_frame()
        field = frame.locator(f"input[aria-label^='{hebrew}']").or_(
            frame.locator(f"input[aria-label^='{english}']")
        ).first
        try:
            if not field.is_visible(timeout=1_000):
                return
        except Error:
            return
        self._dismiss_overlay()
        expect(field).to_be_visible(timeout=self.timeout)
        field.click(force=True)
        field.fill(value)
        field.press("Enter")
        self._dismiss_overlay()

    def _dismiss_overlay(self) -> None:
        """Close a leftover menu or date-picker backdrop."""
        try:
            self.page.keyboard.press("Escape")
        except Error:
            pass
        backdrop = self._report_frame().locator(".cdk-overlay-backdrop-showing")
        try:
            if backdrop.count() > 0:
                backdrop.first.click()
        except Error:
            pass

    def read_kpi_metrics(self) -> dict[str, Any]:
        """Nested KPI values matching golden kpi_metrics. Missing cards are omitted."""
        result: dict[str, Any] = {}
        for path, title, kind in self._KPI_SPECS:
            value = self._read_kpi_card(title, kind)
            if value is None:
                continue
            cursor = result
            for key in path[:-1]:
                cursor = cursor.setdefault(key, {})
            cursor[path[-1]] = value
        return result

    def _read_kpi_card(self, title: str, kind: str) -> int | float | str | None:
        """Read one card. None when the title is not visible."""
        card = self._kpi.card(title)
        try:
            if card.count() == 0 or not card.is_visible(timeout=1_500):
                return None
        except Error:
            return None
        try:
            if kind == "percent":
                raw = self._kpi.read_text(title) or ""
                text = _plain_cell(raw)
                if "%" not in text:
                    number = self._kpi.value(title)
                    return f"{number}%" if number else None
                match = re.search(r"-?\d+(?:\.\d+)?%", text.replace(",", ""))
                return match.group(0) if match else text
            return self._kpi.number(title)
        except (Error, ValueError, AssertionError):
            return None

    def set_metric(self, kind: str) -> None:
        """Select expense amount or transactions count on the Screen 1 toggle."""
        names = self._METRIC_NAMES[kind]
        self._click_bilingual(*names)
        self._active_metric = kind
        self.page.wait_for_timeout(400)

    def set_visualization(self, kind: str) -> None:
        """Select line or bar for the Screen 1 trends visual."""
        names = self._VIZ_NAMES[kind]
        self._click_bilingual(*names)
        self._active_visualization = kind
        self.page.wait_for_timeout(400)

    def _click_bilingual(self, hebrew: str, english: str) -> None:
        """Click a button, tab, or labeled control under either language."""
        frame = self._report_frame()
        control = (
            frame.get_by_role("button", name=hebrew)
            .or_(frame.get_by_role("tab", name=hebrew))
            .or_(frame.get_by_label(hebrew, exact=False))
            .or_(frame.get_by_text(hebrew, exact=True))
            .or_(frame.get_by_role("button", name=english))
            .or_(frame.get_by_role("tab", name=english))
            .or_(frame.get_by_label(english, exact=False))
            .or_(frame.get_by_text(english, exact=True))
        )
        visible = control.filter(visible=True)
        expect(visible.first).to_be_visible(timeout=self.timeout)
        visible.first.click(force=True)

    def read_daily_trends(self) -> list[dict[str, Any]]:
        """Rows from the active trends chart via Show as a table."""
        rows = self._show_as_table_rows(self.TRENDS_CHART)
        if not rows:
            return []
        use_list = (
            self._active_metric == "transactions_count"
            and self._active_visualization == "bar"
        )
        parsed: list[dict[str, Any]] = []
        for row in rows:
            item = self._trend_row(row, use_list=use_list)
            if item is not None:
                parsed.append(item)
        return parsed

    def read_expenses_by_authority(self) -> list[dict[str, Any]]:
        """Authority name and amount in millions from Show as a table."""
        rows = self._show_as_table_rows(self.AUTHORITY_CHART)
        result: list[dict[str, Any]] = []
        for row in rows:
            authority = None
            amount = None
            for key, value in row.items():
                if _parse_number(value) is not None and amount is None:
                    amount = _parse_number(value)
                elif _plain_cell(value) and _parse_number(value) is None:
                    authority = _plain_cell(value)
            if authority and amount is not None:
                result.append({"authority": authority, "amount": amount})
        return result

    def read_daily_alerts(self) -> list[dict[str, Any]]:
        """Optional daily-alert series. Empty when the visual is not readable."""
        rows = self._show_as_table_rows(self.ALERTS_CHART)
        result: list[dict[str, Any]] = []
        for row in rows:
            date = self._row_date(row)
            day = self._row_day(row)
            count = None
            for value in row.values():
                number = _parse_number(value)
                if number is not None and _DATE_TOKEN.search(_plain_cell(value)) is None:
                    count = int(number) if isinstance(number, int) else number
            if date and count is not None:
                item: dict[str, Any] = {"date": date, "alerts_count": count}
                if day:
                    item["day"] = day
                result.append(item)
        return result

    def read_export_table(self) -> list[dict[str, Any]]:
        """Screen 2 matrix rows mapped to export_table_data keys."""
        rows = self._visible_table_rows()
        if not rows:
            return []
        mapped: list[dict[str, Any]] = []
        for row in rows:
            item: dict[str, Any] = {}
            for yaml_key, aliases in self._EXPORT_HEADERS.items():
                raw = self._cell_by_aliases(row, aliases)
                if raw is None:
                    continue
                if yaml_key == "quantity":
                    number = _parse_number(raw)
                    if number is None:
                        continue
                    item[yaml_key] = int(number)
                elif yaml_key == "amount":
                    item[yaml_key] = _plain_cell(raw)
                else:
                    item[yaml_key] = _plain_cell(raw)
            if item:
                mapped.append(item)
        return mapped

    def _cell_by_aliases(self, row: dict[str, str], aliases: tuple[str, ...]) -> str | None:
        """Return the first cell whose header matches an alias."""
        for header, value in row.items():
            cleaned = _plain_cell(header)
            for alias in aliases:
                if cleaned == alias or alias in cleaned:
                    return value
        return None

    def _trend_row(self, row: dict[str, str], *, use_list: bool) -> dict[str, Any] | None:
        """Turn one table row into a daily-trend record."""
        date = self._row_date(row)
        if not date:
            return None
        day = self._row_day(row)
        numbers: list[int | float] = []
        for key, value in row.items():
            cleaned = _plain_cell(value)
            if _DATE_TOKEN.fullmatch(cleaned) or cleaned in _WEEKDAYS:
                continue
            if key and _plain_cell(key) in _WEEKDAYS:
                continue
            number = _parse_number(value)
            if number is not None:
                numbers.append(number)
        if not numbers:
            return None
        item: dict[str, Any] = {"date": date}
        if day:
            item["day"] = day
        if use_list:
            item["values"] = numbers
        else:
            item["value"] = numbers[0]
        return item

    def _row_date(self, row: dict[str, str]) -> str | None:
        for value in row.values():
            match = _DATE_TOKEN.search(_plain_cell(value))
            if match:
                return match.group(0)
        return None

    def _row_day(self, row: dict[str, str]) -> str | None:
        for value in row.values():
            cleaned = _plain_cell(value)
            if cleaned in _WEEKDAYS:
                return cleaned
        return None

    def _show_as_table_rows(self, title: str) -> list[dict[str, str]]:
        """Right-click a visual, open Show as a table, read rows, leave the table."""
        self._dismiss_overlay()
        try:
            container = self._visual_container(title)
            container.click(button="right")
            self._click_show_as_table(title)
        except (AssertionError, Error):
            self._dismiss_overlay()
            return []
        opened = False
        try:
            rows = self._visible_table_rows()
            opened = True
            return rows
        except (AssertionError, Error):
            return []
        finally:
            if opened:
                try:
                    self._leave_visual_table(title)
                except (AssertionError, Error):
                    self._dismiss_overlay()

    def _visual_container(self, title: str) -> Locator:
        """Nearest visual host that contains this title."""
        frame = self._report_frame()
        visible = frame.get_by_text(title, exact=False).filter(visible=True)
        if visible.count() == 0:
            named = frame.get_by_role("group", name=title, exact=False).filter(
                visible=True
            )
            if named.count() == 0:
                raise AssertionError(f"Chart {title!r} has no visual container")
            title_node = named.first
        else:
            title_node = visible.first
        ancestor = (
            "ancestor::*[contains(@class,'visualContainer')"
            " or contains(@class,'visual-container')][1]"
        )
        node = title_node.locator(f"xpath={ancestor}")
        if node.count() > 0:
            return node
        return title_node

    def _click_show_as_table(self, title: str) -> None:
        """Click the bilingual menu item that opens a visual as a table."""
        deadline = time.monotonic() + self.timeout / 1000
        while time.monotonic() < deadline:
            for root in (self._report_frame(), self.page):
                for label in self._SHOW_TABLE:
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
        raise AssertionError(f"Chart {title!r} has no show-as-table menu item")

    def _leave_visual_table(self, title: str) -> None:
        """Close the data table so the named visual is on the canvas again."""
        button = None
        for root in (self._report_frame(), self.page):
            for name in self._BACK_TO_REPORT:
                candidate = root.get_by_role("button", name=name, exact=True).filter(
                    visible=True
                )
                try:
                    if candidate.count() > 0:
                        button = candidate.first
                        break
                except Error:
                    continue
            if button is not None:
                break
        if button is None:
            raise AssertionError(f"Chart {title!r} data table has no back button")
        button.click()
        visible = self._report_frame().get_by_text(title).filter(visible=True)
        expect(visible.first).to_be_visible(timeout=self.timeout)

    def _visible_table_rows(self) -> list[dict[str, str]]:
        """Map each visible grid/table data row to header → cell text."""
        frame = self._report_frame()
        deadline = time.monotonic() + min(self.timeout, 20_000) / 1000
        table = None
        while time.monotonic() < deadline:
            for role in ("grid", "table"):
                tables = frame.get_by_role(role)
                try:
                    tables.first.wait_for(state="visible", timeout=500)
                except PlaywrightTimeoutError:
                    continue
                try:
                    count = tables.count()
                except Error:
                    continue
                for index in range(count):
                    candidate = tables.nth(index)
                    try:
                        if candidate.is_visible():
                            table = candidate
                    except Error:
                        continue
            if table is not None:
                break
            self.page.wait_for_timeout(200)
        if table is None:
            return []
        try:
            headers = [
                _plain_cell(text)
                for text in table.get_by_role("columnheader").evaluate_all(
                    "nodes => nodes.map(node => (node.textContent || '').trim())"
                )
            ]
        except Error:
            headers = []
        rows: list[dict[str, str]] = []
        seen: set[tuple[str, ...]] = set()
        body = table.get_by_role("row")
        try:
            count = body.count()
        except Error:
            return []
        for index in range(count):
            row = body.nth(index)
            try:
                if not row.is_visible():
                    continue
                cells = [
                    _plain_cell(text)
                    for text in row.get_by_role("gridcell").or_(
                        row.get_by_role("cell")
                    ).evaluate_all(
                        "nodes => nodes.map(node => (node.textContent || '').trim())"
                    )
                ]
            except Error:
                continue
            if not cells:
                continue
            if headers and cells == headers:
                continue
            if any(cell.startswith('סה"כ') or cell == 'סה"כ' for cell in cells):
                continue
            key = tuple(cells)
            if key in seen:
                continue
            seen.add(key)
            if headers and len(headers) == len(cells):
                rows.append(dict(zip(headers, cells)))
            else:
                rows.append({str(i): cell for i, cell in enumerate(cells)})
        return rows

    def _close_info_popup(self, wait_ms: int = 400) -> None:
        """Force-click the overlay X visual; no-op when the popup is absent.

        The Credit Consumption "דף מידע" overlay is a Power BI visual, not a
        HTML dialog — Escape does not dismiss it. The close control is an
        unlabeled shape/image (two crossing lines) in the top-left of the
        modal (RTL). ``force=True`` bypasses overlay hit-testing.
        """
        marker = self._info_popup_marker(wait_ms)
        if marker is None:
            return

        print("\n[popup] Info overlay visible — force-clicking close X in iframe\n")

        for close in (self._info_popup_close_locator(), self._sandbox_close_locator()):
            try:
                if close.count() > 0 and close.first.is_visible(timeout=400):
                    close.first.click(force=True, timeout=1500)
                    if not self._info_popup_visible(wait_ms=250):
                        return
            except Exception:
                continue

        if self._click_overlay_close_visual(marker):
            if not self._info_popup_visible(wait_ms=250):
                return

        self._click_info_overlay_close_shape(marker)

    def _info_popup_visible(self, wait_ms: int = 250) -> bool:
        return self._info_popup_marker(wait_ms) is not None

    def _info_popup_marker(self, wait_ms: int = 250):
        """Return a visible locator for the overlay title/body, else None."""
        for phrase in ("דף מידע", "מושגים חשובים"):
            loc = self._iframe_phrase_locator(phrase)
            try:
                if loc.is_visible(timeout=wait_ms):
                    return loc
            except Exception:
                continue
        try:
            page_title = self.page.get_by_text("דף מידע", exact=False).first
            if page_title.is_visible(timeout=wait_ms):
                return page_title
        except Exception:
            pass
        return None

    def _info_popup_close_locator(self):
        frame = self._report_frame()
        return (
            frame.get_by_role("button", name=_POPUP_CLOSE_NAME)
            .or_(frame.get_by_label(_POPUP_CLOSE_NAME))
            .or_(
                frame.locator(
                    "[aria-label*='Close' i], [aria-label*='סגור'], "
                    "[title*='Close' i], [title*='סגור'], "
                    "[aria-label*='Dismiss' i], [title*='Dismiss' i]"
                )
            )
            .or_(frame.get_by_text("✕", exact=True))
            .or_(frame.get_by_text("×", exact=True))
            .or_(frame.get_by_text("X", exact=True))
            .first
        )

    def _sandbox_close_locator(self):
        sandbox = self._report_frame().frame_locator("iframe.visual-sandbox")
        return (
            sandbox.get_by_role("button", name=_POPUP_CLOSE_NAME)
            .or_(sandbox.get_by_label(_POPUP_CLOSE_NAME))
            .or_(sandbox.get_by_text("✕", exact=True))
            .or_(sandbox.get_by_text("×", exact=True))
            .or_(sandbox.get_by_text("X", exact=True))
            .first
        )

    def _iter_visual_boxes(self):
        """Visible iframe visuals/images/shapes with viewport bounding boxes."""
        frame = self._report_frame()
        scopes = [
            frame.locator(_CLOSE_VISUAL_SELECTOR),
            frame.locator(_VISUAL_CONTAINER),
            frame.locator("img, svg"),
        ]
        seen: set[tuple[int, int, int, int]] = set()
        for candidates in scopes:
            try:
                n = min(candidates.count(), 50)
            except Exception:
                continue
            for i in range(n):
                el = candidates.nth(i)
                try:
                    if not el.is_visible(timeout=120):
                        continue
                    box = el.bounding_box()
                except Exception:
                    continue
                if box is None or box["x"] < 0 or box["y"] < 0:
                    continue
                key = (
                    round(box["x"]),
                    round(box["y"]),
                    round(box["width"]),
                    round(box["height"]),
                )
                if key in seen:
                    continue
                seen.add(key)
                yield el, box

    def _click_overlay_close_visual(self, marker) -> bool:
        """Force-click the small X visual in the overlay header (RTL, top-left)."""
        try:
            title_box = marker.bounding_box(timeout=400)
        except Exception:
            title_box = None
        if title_box is None:
            return False

        print(
            "\n[popup] marker box "
            f"x={title_box['x']:.0f} y={title_box['y']:.0f} "
            f"{title_box['width']:.0f}x{title_box['height']:.0f}\n"
        )

        modal = self._overlay_box_from_marker(marker)
        hits: list[tuple[float, object, dict]] = []
        for el, box in self._iter_visual_boxes():
            if not (8 <= box["width"] <= 120 and 8 <= box["height"] <= 120):
                continue
            same_row = (title_box["y"] - 56) <= box["y"] <= (
                title_box["y"] + title_box["height"] + 40
            )
            left_of_title = (box["x"] + box["width"] / 2) < title_box["x"]
            in_modal_corner = False
            if modal is not None:
                in_modal_corner = (
                    modal["x"] - 8 <= box["x"] <= modal["x"] + min(140.0, modal["width"] * 0.25)
                    and modal["y"] - 8 <= box["y"] <= modal["y"] + 90
                )
            if not ((same_row and left_of_title) or in_modal_corner):
                continue
            hits.append((box["x"], el, box))

        hits.sort(key=lambda item: item[0])
        for _x, el, box in hits:
            try:
                el.click(force=True, timeout=1500)
                self.page.mouse.click(
                    box["x"] + box["width"] / 2,
                    box["y"] + box["height"] / 2,
                )
                print(
                    "\n[popup] force-clicked close visual "
                    f"{box['width']:.0f}x{box['height']:.0f} "
                    f"at ({box['x']:.0f},{box['y']:.0f})\n"
                )
                if not self._info_popup_visible(wait_ms=250):
                    return True
            except Exception:
                continue
        return False

    def _overlay_box_from_marker(self, marker):
        """Smallest modal-sized container that still contains the overlay title."""
        viewport = self.page.viewport_size or {"width": 1920, "height": 1080}
        try:
            title_box = marker.bounding_box(timeout=400)
        except Exception:
            title_box = None
        if title_box is None:
            return None

        cx = title_box["x"] + title_box["width"] / 2
        cy = title_box["y"] + title_box["height"] / 2
        best = None
        best_area = float("inf")
        for _el, box in self._iter_visual_boxes():
            if box["width"] < 400 or box["height"] < 220:
                continue
            if box["width"] > viewport["width"] * 0.92:
                continue
            if box["height"] > viewport["height"] * 0.88:
                continue
            if not (
                box["x"] <= cx <= box["x"] + box["width"]
                and box["y"] <= cy <= box["y"] + box["height"]
            ):
                continue
            area = box["width"] * box["height"]
            if area < best_area:
                best_area = area
                best = box
        return best

    def _click_info_overlay_close_shape(self, marker) -> None:
        """Mouse-click the top-left of the white modal so the X is the topmost hit."""
        box = self._overlay_box_from_marker(marker)
        if box is None:
            try:
                title = marker.bounding_box(timeout=400)
            except Exception:
                return
            if title is None:
                return
            # RTL header: X is left of the title, same row — estimate if no modal host.
            box = {
                "x": max(0.0, title["x"] - 420),
                "y": max(0.0, title["y"] - 24),
                "width": 80,
                "height": 80,
            }
        print(
            "\n[popup] modal box "
            f"x={box['x']:.0f} y={box['y']:.0f} "
            f"{box['width']:.0f}x{box['height']:.0f}\n"
        )
        self._click_topmost_at(box["x"] + 22, box["y"] + 22)
        if not self._info_popup_visible(wait_ms=200):
            return
        for dx, dy in ((18, 18), (28, 18), (18, 28), (40, 22), (22, 40)):
            self.page.mouse.click(box["x"] + dx, box["y"] + dy)
            if not self._info_popup_visible(wait_ms=200):
                print(f"\n[popup] mouse-clicked modal X at offset ({dx},{dy})\n")
                return
        print("\n[popup] mouse-clicked modal top-left; overlay still open\n")

    def _click_topmost_at(self, viewport_x: float, viewport_y: float) -> None:
        """Click whichever iframe node is painted at the modal X (not a covered host)."""
        try:
            iframe_box = self._dashboard_iframe().bounding_box()
            frame = self._dashboard_iframe().content_frame
        except Exception:
            return
        if iframe_box is None or frame is None:
            return
        rel_x = viewport_x - iframe_box["x"]
        rel_y = viewport_y - iframe_box["y"]
        try:
            hit = frame.evaluate(
                """([x, y]) => {
                    const el = document.elementFromPoint(x, y);
                    if (!el) return null;
                    el.dispatchEvent(new PointerEvent('pointerdown', {
                        bubbles: true, cancelable: true, view: window,
                        clientX: x, clientY: y
                    }));
                    el.dispatchEvent(new PointerEvent('pointerup', {
                        bubbles: true, cancelable: true, view: window,
                        clientX: x, clientY: y
                    }));
                    el.dispatchEvent(new MouseEvent('click', {
                        bubbles: true, cancelable: true, view: window,
                        clientX: x, clientY: y
                    }));
                    return (el.tagName || '') + ' ' + (el.className || '');
                }""",
                [rel_x, rel_y],
            )
            print(f"\n[popup] elementFromPoint click → {hit!r}\n")
        except Exception as exc:
            print(f"\n[popup] elementFromPoint click skipped: {exc}\n")
