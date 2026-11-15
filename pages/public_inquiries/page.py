"""Public Inquiries (Hasbara) report.

Layer 0 portal steps stay on ReportShell. Tab labels, slicer names, chart
titles, and grid headers live on this page.
"""

from __future__ import annotations

import re
import time

from playwright.sync_api import Error, FrameLocator, Locator, Page, expect
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

from config.settings import settings
from core.components.kpi import KPI
from core.components.slicer import Slicer, SlicerDefinition
from core.components.visual_table import VisualTable
from core.portal.page import ReportShell

_BIDI_MARKS = ("\u200f", "\u200e", "\u202a", "\u202b", "\u202c")
_DATE_RANGE = re.compile(r"(\d{2}/\d{2}/\d{4})\s*-\s*(\d{2}/\d{2}/\d{4})")
_DURATION = re.compile(r"\d{2}:\d{2}:\d{2}:\d{2}")
_HOUR_LABEL = re.compile(r"\d{2}:\d{2}")
_FEEDBACK_HEADER = re.compile(r"שליחת הסקר")
_CANVAS_COUNT_PERCENT = re.compile(
    r"(\d[\d,]*)\s*\(\s*(\d+(?:[.,]\d+)?%)\s*\)"
)
_COUNT_TOKEN = re.compile(r"^\d[\d,]*$")
# Runs in the report iframe. Returns the visible total|open token only when
# two polls see the same numbers. Tooltips and hidden nodes are ignored.
_INQUIRY_SETTLED_JS = """() => {
    const norm = (value) => (value || "").replace(/[\\u200e\\u200f\\u202a\\u202b\\u202c]/g, "").replace(/\\s+/g, " ").trim();
    const visible = (el) => {
        if (!el || el.getAttribute("aria-hidden") === "true") return false;
        if (el.getAttribute("role") === "tooltip" || (el.closest && el.closest("[role='tooltip']"))) return false;
        const style = window.getComputedStyle(el);
        if (style.display === "none" || style.visibility === "hidden") return false;
        const box = el.getBoundingClientRect();
        return box.width >= 1 && box.height >= 1;
    };
    const metricOf = (el) => {
        const label = norm(el.getAttribute && el.getAttribute("aria-label") || "");
        const labelled = label.match(/(\\d[\\d,]*)\\s*\\.?$/);
        if (labelled) return labelled[1];
        const text = norm(el.innerText || el.textContent || "");
        return /^\\d[\\d,]*$/.test(text) ? text : "";
    };
    const countNear = (aliases) => {
        const labels = Array.from(document.body.querySelectorAll("*")).filter((el) => {
            if (!visible(el) || (el.closest && el.closest("a"))) return false;
            const text = norm(el.innerText || el.textContent || "");
            if (!aliases.some((title) => text.includes(title))) return false;
            return text.length <= 40;
        });
        labels.sort((left, right) => {
            const a = left.getBoundingClientRect();
            const b = right.getBoundingClientRect();
            return (a.width * a.height) - (b.width * b.height);
        });
        const label = labels[0];
        if (!label) return "";
        const box = label.getBoundingClientRect();
        const labelCy = box.y + box.height / 2;
        const labelCx = box.x + box.width / 2;
        let best = "";
        let bestScore = 1e9;
        for (const node of document.body.querySelectorAll("*")) {
            if (!visible(node)) continue;
            const metric = metricOf(node);
            if (!metric) continue;
            const rect = node.getBoundingClientRect();
            const dx = Math.abs((rect.x + rect.width / 2) - labelCx);
            const dy = (rect.y + rect.height / 2) - labelCy;
            if (dx > 160 || dy < -40 || dy > 120) continue;
            const score = Math.abs(dy) + dx;
            if (score < bestScore) {
                bestScore = score;
                best = metric;
            }
        }
        return best;
    };
    const total = countNear(['סה"כ פניות', "סה״כ פניות"]);
    const opened = countNear(["פניות פתוחות"]);
    if (!/\\d/.test(total) || !/\\d/.test(opened)) {
        window.__vcInquiryToken = "";
        return false;
    }
    const token = total + "|" + opened;
    if (window.__vcInquiryToken === token) return true;
    window.__vcInquiryToken = token;
    return false;
}"""
# Runs in the report iframe. Returns true only when each survey card shows the
# same visible metric on two polls and that metric is not inside a tooltip.
_SURVEY_SETTLED_JS = """() => {
    const norm = (value) => (value || "").replace(/[\\u200e\\u200f\\u202a\\u202b\\u202c]/g, "").replace(/\\s+/g, " ").trim();
    const visible = (el) => {
        if (!el || el.getAttribute("aria-hidden") === "true") return false;
        if (el.getAttribute("role") === "tooltip" || el.closest("[role='tooltip']")) return false;
        const style = window.getComputedStyle(el);
        if (style.display === "none" || style.visibility === "hidden") return false;
        const box = el.getBoundingClientRect();
        return box.width >= 1 && box.height >= 1;
    };
    const groups = [
        ["מוקד טלפוני"],
        ["מענה כתוב"],
        ["אחוז תקינות", "שיחות שנבדקו", "בקרת איכות"],
    ];
    const metricOf = (el) => {
        const label = norm(el.getAttribute && el.getAttribute("aria-label") || "");
        const labelled = label.match(/(\\d[\\d,]*|לא ידוע|אין מידע)\\s*\\.?$/);
        if (labelled) return labelled[1];
        const text = norm(el.innerText || el.textContent || "");
        return /^(?:\\d[\\d,]*|לא ידוע|אין מידע)$/.test(text) ? text : "";
    };
    const metricUnder = (titleNode) => {
        const label = titleNode.getBoundingClientRect();
        const labelCenter = label.x + label.width / 2;
        const labelCy = label.y + label.height / 2;
        let best = "";
        let bestScore = 1e9;
        for (const node of document.body.querySelectorAll("*")) {
            if (!visible(node)) continue;
            const text = metricOf(node);
            if (!text) continue;
            const rect = node.getBoundingClientRect();
            const dx = Math.abs((rect.x + rect.width / 2) - labelCenter);
            const dy = (rect.y + rect.height / 2) - labelCy;
            if (dx > 180 || dy < -40 || dy > 140) continue;
            const score = Math.abs(dy) + dx;
            if (score < bestScore) {
                bestScore = score;
                best = text;
            }
        }
        return best;
    };
    const parts = [];
    for (const aliases of groups) {
        let titleNode = null;
        for (const title of aliases) {
            const nodes = Array.from(document.body.querySelectorAll("h1,h2,h3,h4,h5,h6,[role='heading']")).filter((el) => {
                if (!visible(el) || (el.closest && el.closest("a"))) return false;
                const text = norm(el.innerText || el.textContent || "");
                return text.includes(title);
            });
            nodes.sort((left, right) => {
                const a = left.getBoundingClientRect();
                const b = right.getBoundingClientRect();
                return (a.width * a.height) - (b.width * b.height);
            });
            if (nodes.length) {
                titleNode = nodes[0];
                break;
            }
        }
        if (!titleNode) {
            window.__vcSurveyToken = "";
            return false;
        }
        const card = titleNode.closest("[class*='visualContainer'], [class*='visual-container']") || titleNode.parentElement;
        if (card) {
            const spinning = Array.from(card.querySelectorAll("[class*='spinner'], [aria-busy='true']")).some(visible);
            if (spinning) {
                window.__vcSurveyToken = "";
                return false;
            }
        }
        const metric = metricUnder(titleNode);
        if (!metric) {
            window.__vcSurveyToken = "";
            return false;
        }
        parts.push(metric);
    }
    const token = parts.join("|");
    if (window.__vcSurveyToken === token) return true;
    window.__vcSurveyToken = token;
    return false;
}"""
_VISUAL_HOST_SELECTOR = (
    "[class*='visualContainerHost'], [class*='visual-container-host'], "
    "[class*='visualContainer'], [class*='visual-container']"
)


def _looks_like_metric(line: str) -> bool:
    """True when a survey line is a number or a known empty-state phrase."""
    text = line.strip()
    if text in ("לא ידוע", "אין מידע"):
        return True
    return bool(re.search(r"\d", text))


def _plain(raw: str) -> str:
    """Trim one cell and drop the bidi marks Power BI inserts."""
    text = raw or ""
    for mark in _BIDI_MARKS:
        text = text.replace(mark, "")
    text = text.strip()
    if len(text) >= 4 and len(text) % 2 == 0:
        half = len(text) // 2
        if text[:half] == text[half:]:
            return text[:half]
    return text


class PublicInquiriesPage(ReportShell):
    """Hasbara inquiries report. Screen 1 is the landing written-response page."""

    DASHBOARD_SEARCH_TERM = "ניתוח פניות הסברה"

    SCREEN_TITLES = {
        "screen_1": "ניתוח פניות הסברה - תחקור פניות מענה כתוב",
        "screen_2": "ניתוח פניות הסברה - תחקור פניות מענה כתוב",
        "screen_3": "ניתוח פניות הסברה - ניתוח משובי שביעות רצון",
        "screen_4": "ניתוח פניות הסברה - ניתוח משובי שביעות רצון (תחקור משובים)",
    }
    # Page-navigation accessible names. Screen 3's rail label is the shorter "משובים".
    TAB_LABELS = {
        "screen_2": ("תחקור מענה כתוב",),
        "screen_3": ("ניתוח משובי שביעות רצון", "משובים"),
        "screen_4": ("תחקור משובים",),
    }
    _SCREEN_1_TAB_CANDIDATES = ("מענה כתוב",)

    # Combobox accessible names from the live report. Hebrew captions sit beside them.
    _SLICER_DEFINITIONS = (
        SlicerDefinition(id="hours", role_name="Hour_Formatted", kind="dropdown"),
        SlicerDefinition(id="language", role_name="LanguageLabel", kind="dropdown"),
        SlicerDefinition(id="platform", role_name="InboxChannelName", kind="dropdown"),
        SlicerDefinition(id="topic", role_name="נושא", kind="dropdown"),
        SlicerDefinition(id="settlement", role_name="city", kind="dropdown"),
        SlicerDefinition(id="information", role_name="info_desc", kind="dropdown"),
        SlicerDefinition(id="service_orientation", role_name="serve_desc", kind="dropdown"),
        SlicerDefinition(id="professionalism", role_name="prof_desc", kind="dropdown"),
    )
    _SLICER_ALIASES = {
        "hours": ("Hour_Formatted", "שעות"),
        "language": ("LanguageLabel", "שפה"),
        "platform": ("InboxChannelName", "PLATFORM", "פלטפורמה"),
        "topic": ("נושא", "Label"),
        "settlement": ("city", "יישוב"),
        "information": ("info_desc", "מידע"),
        "service_orientation": ("serve_desc", "אופן השירות"),
        "professionalism": ("prof_desc", "מקצועיות"),
    }

    # Measure id is the live img aria-label. Headings are the visible card titles.
    # Duration widgets are not in this list: each one holds two captions.
    _KPI_SPECS: tuple[tuple[tuple[str, ...], str, tuple[str, ...]], ...] = (
        (("inquiries_summary", "total_chats"), "CountConversationsID", ('סה"כ שיחות', "סה״כ שיחות")),
        (("inquiries_summary", "total_requests"), "CountTotalTickets", ('סה"כ פניות', "סה״כ פניות")),
        (("inquiries_summary", "open_requests"), "CountOpen", ("פניות פתוחות",)),
        (("inquiries_summary", "closed_requests"), "CountTickets", ("פניות סגורות",)),
    )
    # One visual per golden block. The second closing-times title omits the yod.
    _DURATION_WIDGETS: tuple[tuple[str, tuple[str, ...]], ...] = (
        ("request_closing_times", ("זמני סגירת פנייה", "זמני סגירת פניה")),
        ("response_wait_times", ("זמני המתנה למענה",)),
    )
    _DURATION_CAPTIONS: tuple[tuple[str, str], ...] = (
        ("average", "ממוצע"),
        ("maximum", "מקסימלי"),
    )
    _CHART_TITLES = {
        "written_media_breakdown": ("פילוח פניות במדיה כתובה", "פילוח לפי מדיה"),
        "language_breakdown": ("פילוח שפות",),
        "recurring_requests_breakdown": ("פילוח פניות חוזרות",),
        "leading_topics": ("נושאים מובילים",),
        "requests_by_hour_trend": ("מספר פניות לפי שעה",),
        "message_reception": ("האם המידע שהתקבל סייע",),
        "service_reception": (
            "האם השירות שהתקבל היה אדיב",
            "האם השירות שהתקבל היה מקצועי",
        ),
        "leading_contact_channels": (
            "ערוצי פנייה מובילים",
            "ערוצי פניה מובילים",
            "ערוצי יצירת קשר מובילים",
            "ערוצי התקשרות מובילים",
        ),
        "platforms_breakdown": ("פילוח פלטפורמות", "פלטפורמות"),
    }
    # Courtesy sub-tabs sit above the chart in this section. Not a page-rail label.
    _SATISFACTION_SECTION_TITLE = "התקבלות השירות"
    # Each sub-tab shows one question. The reader uses the tab that was clicked.
    _SATISFACTION_TAB_QUESTIONS = {
        "אופן אדיב": "האם השירות שהתקבל היה אדיב",
        "אופן מקצועי": "האם השירות שהתקבל היה מקצועי",
    }
    _CHART_LABEL_FIELD = {
        "written_media_breakdown": "platform",
        "language_breakdown": "language",
        "recurring_requests_breakdown": "type",
        "leading_topics": "topic",
        "message_reception": "level",
        "service_reception": "level",
        "leading_contact_channels": "channel",
        "platforms_breakdown": "platform",
    }
    _SURVEY_SECTIONS = {
        "phone_center": ("מוקד טלפוני",),
        "written_response": ("מענה כתוב",),
        "quality_control": ("אחוז תקינות", "שיחות שנבדקו", "בקרת איכות"),
    }
    _SURVEY_LABELS = {
        "surveys_sent": ("סקרים שנשלחו", "נשלחו"),
        "surveys_filled": ("סקרים שמולאו", "מולאו"),
        "valid_calls_checked": (
            "שיחות שנבדקו ויצאו תקינות",
            "שיחות תקינות שנבדקו",
            "נבדקו",
        ),
        "validity_percentage": ("אחוז תקינות", "אחוז"),
    }
    _INVESTIGATION_HEADERS = {
        "request_id": ("מזהה פנייה", "מזהה פניה", "מזהה בקשה"),
        "handling_time": ("זמן טיפול",),
        "platform": ("פלטפורמה",),
        "topic": ("נושא",),
        "initial_response_wait_time": ("זמן המתנה למענה ראשוני", "המתנה למענה"),
        "initial_response_time": ("זמן מענה ראשוני", "מועד מענה ראשוני"),
        "opening_time": ("זמן פתיחה", "מועד פתיחה"),
        "language": ("שפה",),
        "agent_name": ("שם נציג", "נציג"),
        "customer_name": ("שם לקוח", "לקוח"),
        "chat_id": ("מזהה צ'אט", "מזהה צ׳אט", "מזהה שיחה"),
    }
    _FEEDBACK_HEADERS = {
        "inquiry_id": ("מזהה פנייה", "מזהה פניה", "מזהה בירור"),
        "comments": ("הערות", "הערה"),
        "opening_time": ("זמן פתיחה", "מועד פתיחה"),
        "initial_response_time": ("זמן מענה ראשוני", "מועד מענה ראשוני"),
        "platform": ("פלטפורמה",),
        "customer_name": ("שם לקוח", "לקוח"),
        "agent_name": ("שם נציג", "נציג"),
        "survey_sent_time": ("זמן שליחת סקר", "מועד שליחת סקר"),
        "is_service_courteous": ("האם השירות היה אדיב", "אדיב"),
        "is_service_professional": ("האם השירות היה מקצועי", "מקצועי"),
        "did_info_help": ("האם המידע סייע", "המידע סייע"),
        "phone_number": ("מספר טלפון", "טלפון"),
    }

    _PERIOD_TOGGLE_LABELS = ("כלל התאריכים", "יום נוכחי")

    def __init__(self, page: Page):
        super().__init__(page)
        self._current_screen_id = "screen_1"
        self.url = settings.LOGIN_URL or settings.DASHBOARD_URL
        frame = page.frame_locator("main iframe")
        self._kpi = KPI(page=page, frame=frame, timeout_ms=self.timeout)
        self._charts = VisualTable(page=page, frame=frame, timeout_ms=self.timeout)
        self._slicer = Slicer(
            page=page,
            frame=frame,
            definitions=self._SLICER_DEFINITIONS,
            settle=lambda *_args, **_kwargs: False,
            timeout_ms=self.timeout,
        )

    def _report_ready_locator(self):
        return self._report_frame().get_by_text(
            "ניתוח פניות הסברה",
            exact=True,
        )

    def phrase_is_visible(self, phrase: str, timeout_ms: int = 2_000) -> bool:
        """True when the report iframe shows this phrase."""
        if not phrase:
            return False
        locator = self._iframe_phrase_locator(phrase)
        try:
            if locator.is_visible(timeout=timeout_ms):
                return True
        except Error:
            pass
        if self._body_contains(phrase):
            return True
        # The live header omits a trailing parenthetical and splits the rest on " - ".
        core = re.sub(r"\s*\([^)]*\)\s*$", "", phrase).strip()
        parts = [part.strip() for part in core.split(" - ") if part.strip()]
        return bool(parts) and all(self._body_contains(part) for part in parts)

    def visual_is_rendered(self, title: str) -> bool:
        """True when a chart or card title is visible. Does not open a table."""
        return self.phrase_is_visible(title)

    def chart_is_rendered(self, chart_key: str) -> bool:
        """True when any live title for this golden chart key is visible."""
        return self._first_visible_title(self._CHART_TITLES.get(chart_key, ())) is not None

    def grid_is_rendered(self, screen_id: str) -> bool:
        """True when this screen's grid is visible.

        Screen 4 uses the survey-sent column header, which is on screen in the
        live grid. Other screens still require their title and a grid.
        """
        if screen_id == "screen_4":
            return self._comments_header_visible()
        title = self.SCREEN_TITLES.get(screen_id, "")
        if title and not self.phrase_is_visible(title):
            return False
        return self._visible_grid() is not None

    def kpi_cards_rendered(self) -> bool:
        """True when at least one screen 1 KPI title is visible."""
        return self._any_kpi_visible()

    def apply_date_range(self, date_range: str) -> None:
        """Show the YAML range. One toggle click unlocks hidden date inputs."""
        target = self._normalize_range(date_range)
        start, separator, end = target.partition(" - ")
        if (
            not separator
            or not re.fullmatch(r"\d{2}/\d{2}/\d{4}", start)
            or not re.fullmatch(r"\d{2}/\d{2}/\d{4}", end)
        ):
            raise ValueError(
                f"date_range must be DD/MM/YYYY - DD/MM/YYYY, got {date_range!r}"
            )
        if self.read_date_range() == target:
            return
        if not self._date_inputs_ready():
            self._click_period_toggle()
            self._expect_date_inputs_ready()
        filled_start = self._fill_date_input("תאריך התחלה", "Start date", start)
        filled_end = self._fill_date_input("תאריך סיום", "End date", end)
        if not filled_start or not filled_end:
            raise AssertionError(
                "Date inputs stayed unavailable after the period toggle"
            )
        self._wait_for_report_settled()

    def read_date_range(self) -> str:
        """Range from the two date inputs, or an empty string when they are locked."""
        start = self._input_value("תאריך התחלה", "Start date")
        end = self._input_value("תאריך סיום", "End date")
        if re.fullmatch(r"\d{2}/\d{2}/\d{4}", start) and re.fullmatch(
            r"\d{2}/\d{2}/\d{4}", end
        ):
            return f"{start} - {end}"
        return ""

    def slicer_is_visible(self, slicer_id: str) -> bool:
        """True when this slicer id has a visible combobox. Does not open it."""
        control = self._slicer_control(slicer_id)
        if control is None:
            return False
        try:
            return control.is_visible(timeout=1_500)
        except Error:
            return False

    def read_slicer_text(self, slicer_id: str) -> str:
        """Visible slicer text. Does not open the dropdown or select a value."""
        control = self._slicer_control(slicer_id)
        if control is None:
            return ""
        try:
            return _plain(control.inner_text(timeout=self.timeout))
        except Error:
            return ""

    def open_screen(self, screen_id: str) -> None:
        """Open one of the four screens and wait until its title and data locator show."""
        if screen_id not in self.SCREEN_TITLES:
            raise ValueError(f"Unknown screen_id {screen_id!r}")
        self._current_screen_id = screen_id
        if screen_id == "screen_1":
            if not self._any_kpi_visible():
                for label in self._SCREEN_1_TAB_CANDIDATES:
                    if self._tab_is_visible(label):
                        self._click_tab(label)
                        break
        else:
            self._open_tab(self.TAB_LABELS[screen_id])
        self._wait_for_report_settled()

    def read_kpi_metrics(self) -> dict:
        """Nested kpi_metrics. Counts and durations stay display strings.

        Inquiry counts are the visible text inside the inquiries widget, read
        after that widget has settled. Each duration widget is read inside its
        own visual. A caption that is not in that visual is omitted.
        """
        self._wait_for_inquiries_widget()
        container = self._inquiries_container()
        result: dict = {}
        for path, measure_id, titles in self._KPI_SPECS:
            value = self._read_kpi_value(container, measure_id, titles)
            if value is None:
                continue
            cursor = result
            for key in path[:-1]:
                cursor = cursor.setdefault(key, {})
            cursor[path[-1]] = value
        for key, titles in self._DURATION_WIDGETS:
            pair = self._read_duration_widget(titles)
            if pair:
                result[key] = pair
        return result

    def read_screen1_charts(self) -> dict:
        """Screen 1 charts. Counts stay display strings. Hourly entry has no Y values."""
        charts: dict = {}
        for key, label_field in self._CHART_LABEL_FIELD.items():
            if key in ("message_reception", "service_reception", "leading_contact_channels", "platforms_breakdown"):
                continue
            if key == "requests_by_hour_trend":
                continue
            charts[key] = self._read_category_chart(key, label_field)
        charts["requests_by_hour_trend"] = self._read_hourly_trend()
        return charts

    def read_investigation_rows(self) -> list[dict]:
        """Investigation grid rows keyed by the YAML field names. Blank cells are ''."""
        return self._read_grid(self._INVESTIGATION_HEADERS)

    def read_feedback_rows(self) -> list[dict]:
        """Feedback grid rows, including comments. Blank cells are ''."""
        return self._read_grid(self._FEEDBACK_HEADERS)

    def select_satisfaction_tab(self, label: str) -> None:
        """Select a courtesy-question tab such as the YAML active_tab. Does not load YAML."""
        locator = self._satisfaction_tab_locator(label)
        expect(locator).to_be_visible(timeout=self.timeout)
        self._click_satisfaction_control(locator)
        self._selected_satisfaction_question = self._SATISFACTION_TAB_QUESTIONS.get(label)
        self._hide_satisfaction_spinner()
        expect(self._iframe_phrase_locator(label)).to_be_visible(timeout=self.timeout)

    def _satisfaction_tab_locator(self, label: str) -> Locator:
        """Exact visible courtesy sub-tab in the report frame.

        Search order is tab, button, link, then exact text. Each candidate
        must be visible. A host that contains the service-reception section
        is preferred. Hidden nodes and tooltips are not candidates. This is
        not the page-rail control.
        """

        def match_in(scope: Locator | FrameLocator) -> Locator | None:
            candidates = (
                scope.get_by_role("tab", name=label, exact=True),
                scope.get_by_role("button", name=label, exact=True),
                scope.get_by_role("link", name=label, exact=True),
                scope.get_by_text(label, exact=True),
            )
            for candidate in candidates:
                visible = candidate.filter(visible=True)
                try:
                    if visible.count() == 0:
                        continue
                except Error:
                    continue
                return self._first_outside_tooltip(visible)
            return None

        frame = self._report_frame()
        host: Locator | None
        try:
            host = self._visual_container(self._SATISFACTION_SECTION_TITLE)
        except (AssertionError, Error):
            host = None
        if host is not None:
            found = match_in(host)
            if found is not None:
                return found
        found = match_in(frame)
        if found is not None:
            return found
        return self._first_outside_tooltip(
            frame.get_by_text(label, exact=True).filter(visible=True)
        )

    def _click_satisfaction_control(self, label_node: Locator) -> None:
        """Click the button surface that covers this visible label.

        The text run is visible, and a transparent path over it receives the
        pointer. The fill whose box contains the label center is the control.
        A label with no covering fill is clicked directly.
        """
        box = None
        try:
            box = label_node.bounding_box(timeout=1_000)
        except Error:
            box = None
        fill = self._button_fill_over(box) if box is not None else None
        if fill is not None:
            fill.click()
            return
        label_node.click(force=True)

    def _button_fill_over(self, box: dict) -> Locator | None:
        """Visible button fill in the report frame that contains this box."""
        fills = self._report_frame().locator(".ui-role-button-fill").filter(visible=True)
        try:
            count = min(fills.count(), 30)
        except Error:
            return None
        center_x = box["x"] + box["width"] / 2
        center_y = box["y"] + box["height"] / 2
        for index in range(count):
            fill = fills.nth(index)
            try:
                fill_box = fill.bounding_box(timeout=500)
            except Error:
                continue
            if fill_box is None or fill_box["width"] < 1 or fill_box["height"] < 1:
                continue
            inside_x = fill_box["x"] <= center_x <= fill_box["x"] + fill_box["width"]
            inside_y = fill_box["y"] <= center_y <= fill_box["y"] + fill_box["height"]
            if inside_x and inside_y:
                return fill
        return None

    def _hide_satisfaction_spinner(self) -> None:
        """Hide a visible spinner in the service-reception section.

        When that section has no visual host, hide a visible spinner in the
        report frame instead. A missing spinner is not a failure.
        """
        try:
            scope: Locator | FrameLocator = self._visual_container(self._SATISFACTION_SECTION_TITLE)
        except (AssertionError, Error):
            scope = self._report_frame()
        spinner = scope.locator("[class*='spinner'], [aria-busy='true']").filter(visible=True)
        try:
            if spinner.count() > 0:
                expect(spinner.first).to_be_hidden(timeout=self.timeout)
        except Error:
            return

    def _wait_for_survey_cards(self) -> None:
        """Wait until each survey section has finished painting a visible metric.

        The three section titles must be visible. A visible spinner inside a
        card must be hidden. The metric under each title must then be unchanged
        on two successive reads. Golden display strings are not the ready signal.
        """
        frame = self._report_frame()
        for _section, titles in self._SURVEY_SECTIONS.items():
            pattern = re.compile("|".join(re.escape(title) for title in titles))
            expect(
                self._first_outside_tooltip(
                    frame.get_by_role("heading", name=pattern).filter(visible=True)
                )
            ).to_be_visible(timeout=self.timeout)
            self._hide_card_spinner(titles[0])
        self._expect_survey_metrics_settled()

    def _hide_card_spinner(self, title: str) -> None:
        """Hide a visible spinner inside the visual that contains this title."""
        try:
            container = self._visual_container(title)
        except (AssertionError, Error, PlaywrightTimeoutError):
            return
        spinner = container.locator("[class*='spinner'], [aria-busy='true']").filter(visible=True)
        try:
            if spinner.count() > 0:
                expect(spinner.first).to_be_hidden(timeout=self.timeout)
        except Error:
            return

    def _expect_survey_metrics_settled(self) -> None:
        """Poll the iframe body until two reads of the visible survey metrics match."""
        self._poll_body_script(
            "() => { window.__vcSurveyToken = ''; }",
            _SURVEY_SETTLED_JS,
            "Survey cards did not settle",
        )

    def read_satisfaction(self) -> dict:
        """Survey cards plus the distributions and channel charts currently on screen."""
        self._wait_for_survey_cards()
        return {
            "surveys_summary": self._read_surveys_summary(),
            "message_reception": {
                "question": "האם המידע שהתקבל סייע",
                "responses": self._read_category_chart("message_reception", "level"),
            },
            "service_reception": {
                "question": "האם השירות שהתקבל היה אדיב",
                "responses": self._read_category_chart("service_reception", "level"),
            },
            "leading_contact_channels": self._read_category_chart(
                "leading_contact_channels", "channel"
            ),
            "platforms_breakdown": self._read_category_chart("platforms_breakdown", "platform"),
        }

    def _wait_until_ready(self, screen_id: str) -> None:
        """Wait on a screen-specific locator. The full title is split across text runs."""
        frame = self._report_frame()
        if screen_id == "screen_1":
            expect(
                self._first_outside_tooltip(
                    frame.get_by_text("תחקור פניות מענה כתוב", exact=False).filter(visible=True)
                )
            ).to_be_visible(timeout=self.timeout)
            self._wait_for_inquiries_widget()
            return
        if screen_id == "screen_3":
            expect(
                self._first_outside_tooltip(
                    frame.get_by_text("ניתוח משובי שביעות רצון", exact=False).filter(visible=True)
                )
            ).to_be_visible(timeout=self.timeout)
            self._wait_for_survey_cards()
            return
        if screen_id == "screen_4":
            # Headers can show before the October range is applied. Do not wait
            # for a data cell here; the default view may have none.
            expect(self._feedback_comments_header()).to_be_visible(timeout=self.timeout)
            return
        expect(frame.get_by_role("grid").or_(frame.get_by_role("row")).first).to_be_visible(
            timeout=self.timeout
        )

    def _any_kpi_visible(self) -> bool:
        """True when a painted inquiries image or card title is on screen.

        A hidden or tooltip image does not count. The ready check is not an
        iframe-wide match on the first measure image in DOM order.
        """
        frame = self._report_frame()
        images = frame.locator("img[aria-label*='CountTotalTickets']").filter(visible=True)
        try:
            count = images.count()
        except Error:
            return False
        for index in range(count):
            if self._node_is_paintable(images.nth(index)):
                return True
        return self._first_visible_title(('סה"כ פניות', "פניות פתוחות")) is not None

    def _read_duration_widget(self, titles: tuple[str, ...]) -> dict:
        """Average and maximum durations inside one metric-bar widget.

        The value is the DD:HH:MM:SS that follows each caption. A caption with
        no following duration is omitted. An absent title returns {}.
        """
        title = self._first_visible_title(titles)
        if title is None:
            return {}
        frame = self._report_frame()
        try:
            expect(
                self._first_outside_tooltip(
                    frame.get_by_text(title, exact=False).filter(visible=True)
                )
            ).to_be_visible(timeout=self.timeout)
        except (Error, PlaywrightTimeoutError, AssertionError):
            return {}
        window = self._duration_window(self._duration_source_text(title, titles), title, titles)
        found: dict[str, str] = {}
        for key, caption in self._DURATION_CAPTIONS:
            # Do not treat a longer label such as "ממוצע פניות" as this caption.
            located = re.search(re.escape(caption) + r"(?![\u0590-\u05FF])", window)
            if located is None:
                continue
            duration = _DURATION.search(window, located.end())
            if duration is None:
                continue
            found[key] = duration.group(0)
        return found

    def _duration_source_text(self, title: str, titles: tuple[str, ...]) -> str:
        """Text that contains this widget's durations.

        The smallest visual host is sometimes only the title. The durations
        then sit in the report body immediately after that title.
        """
        try:
            container = self._visual_container(title)
            hosted = _plain(container.inner_text(timeout=self.timeout))
        except (Error, PlaywrightTimeoutError, AssertionError):
            hosted = ""
        if _DURATION.search(self._duration_window(hosted, title, titles)):
            return hosted
        try:
            return _plain(self._report_frame().locator("body").inner_text(timeout=self.timeout))
        except (Error, PlaywrightTimeoutError, AssertionError):
            return hosted

    def _duration_window(self, text: str, title: str, titles: tuple[str, ...]) -> str:
        """Slice from this title to the other duration widget, if that title follows."""
        collapsed = re.sub(r"\s+", " ", text or "")
        start = 0
        title_at = collapsed.find(title)
        if title_at >= 0:
            start = title_at + len(title)
        end = len(collapsed)
        for _block, other_titles in self._DURATION_WIDGETS:
            for other in other_titles:
                if other in titles:
                    continue
                other_at = collapsed.find(other, start)
                if other_at >= 0:
                    end = min(end, other_at)
        return collapsed[start:end]

    def _wait_for_inquiries_widget(self) -> None:
        """Wait until the inquiries widget has finished painting its visible counts.

        A visible spinner inside the widget must be hidden. The visible total
        and open counts must then be unchanged on two successive reads.
        """
        frame = self._report_frame()
        expect(
            self._first_outside_tooltip(
                frame.get_by_text("פניות פתוחות", exact=False).filter(visible=True)
            )
        ).to_be_visible(timeout=self.timeout)
        try:
            container = self._inquiries_container()
        except (AssertionError, Error, PlaywrightTimeoutError):
            container = None
        if container is not None:
            spinner = container.locator("[class*='spinner'], [aria-busy='true']").filter(
                visible=True
            )
            try:
                if spinner.count() > 0:
                    expect(spinner.first).to_be_hidden(timeout=self.timeout)
            except Error:
                pass
        self._expect_inquiry_counts_settled()

    def _expect_inquiry_counts_settled(self) -> None:
        """Poll the iframe body until two reads of the visible counts match.

        ``FrameLocator`` has no ``evaluate`` or ``wait_for_function``. The token
        reset and the settle script both run on the report body.
        """
        self._poll_body_script(
            "() => { window.__vcInquiryToken = ''; }",
            _INQUIRY_SETTLED_JS,
            "Inquiries widget counts did not settle",
        )

    def _poll_body_script(self, reset_js: str, script: str, failure: str) -> None:
        """Evaluate a script on the iframe body until it returns true.

        The report frame is a FrameLocator, so this does not call evaluate or
        wait_for_function on that object. This Playwright build has no
        expect.poll. The script's true result is the ready signal. The short
        pause only paces those reads.
        """
        body = self._report_frame().locator("body")
        try:
            body.evaluate(reset_js)
        except Error as exc:
            raise AssertionError("Report frame is not available") from exc
        deadline = time.monotonic() + (self.timeout / 1000)
        while True:
            try:
                if body.evaluate(script):
                    return
            except Error:
                pass
            if time.monotonic() >= deadline:
                raise AssertionError(failure)
            time.sleep(0.25)

    def _node_is_paintable(self, node: Locator) -> bool:
        """True when the node is on screen and not inside a tooltip.

        An ``aria-hidden`` node, a tooltip, and an empty box are not values.
        """
        try:
            if node.get_attribute("aria-hidden") == "true":
                return False
            box = node.bounding_box(timeout=300)
            if box is None or box["width"] < 1 or box["height"] < 1:
                return False
            hidden = node.evaluate(
                """el => {
                    if (el.closest("[role='tooltip']")) return true;
                    const style = window.getComputedStyle(el);
                    return style.display === "none" || style.visibility === "hidden";
                }"""
            )
        except Error:
            return False
        return not hidden

    def _first_outside_tooltip(self, locator: Locator) -> Locator:
        """First visible match that is not inside a tooltip."""
        try:
            count = min(locator.count(), 20)
        except Error:
            count = 0
        for index in range(count):
            node = locator.nth(index)
            if self._node_is_paintable(node):
                return node
        return locator.first

    def _inquiries_container(self) -> Locator:
        """Smallest visual host that contains the total and open inquiry cards."""
        frame = self._report_frame()
        hosts = (
            frame.locator(_VISUAL_HOST_SELECTOR)
            .filter(has_text="פניות פתוחות")
            .filter(visible=True)
        )
        best: Locator | None = None
        best_area: float | None = None
        try:
            count = hosts.count()
        except Error:
            count = 0
        for index in range(min(count, 40)):
            host = hosts.nth(index)
            if not self._node_is_paintable(host):
                continue
            try:
                text = _plain(host.inner_text(timeout=500))
                box = host.bounding_box(timeout=500)
            except Error:
                continue
            if not self._contains_inquiry_pair(text):
                continue
            if box is None or box["width"] < 40 or box["height"] < 40:
                continue
            area = box["width"] * box["height"]
            if best_area is None or area < best_area:
                best = host
                best_area = area
        if best is not None:
            return best
        for role in ("heading", "group"):
            named = frame.get_by_role(role, name="פניות", exact=True).filter(visible=True)
            try:
                if named.count() == 0:
                    continue
                title_node = self._first_outside_tooltip(named)
                if not self._node_is_paintable(title_node):
                    continue
                host = self._ancestor_visual_host(title_node)
                if not self._node_is_paintable(host):
                    continue
                text = _plain(host.inner_text(timeout=500))
                box = host.bounding_box(timeout=500)
            except Error:
                continue
            if not self._contains_inquiry_pair(text):
                continue
            if box is None or box["width"] < 40 or box["height"] < 40:
                continue
            return host
        raise AssertionError("Inquiries widget has no visual container")

    def _contains_inquiry_pair(self, text: str) -> bool:
        """True when this host shows both the total-requests and open-requests cards."""
        has_total = 'סה"כ פניות' in text or "סה״כ פניות" in text
        return has_total and "פניות פתוחות" in text

    def _ancestor_visual_host(self, title_node: Locator) -> Locator:
        """Visual container that wraps this title node."""
        for xpath in (
            "ancestor::*[contains(@class,'visualContainerHost')][1]",
            "ancestor::*[contains(@class,'visual-container-host')][1]",
            "ancestor::*[contains(@class,'visualContainer')][1]",
            "ancestor::*[contains(@class,'visual-container')][1]",
        ):
            node = title_node.locator(f"xpath={xpath}")
            try:
                if node.count() > 0:
                    return node.first
            except Error:
                continue
        return title_node

    def _read_kpi_value(
        self, container: Locator, measure_id: str, titles: tuple[str, ...]
    ) -> str | None:
        """Visible display text for one inquiry card inside the inquiries widget."""
        try:
            return self._visible_inquiry_text(container, measure_id, titles)
        except Error:
            return None

    def _visible_inquiry_text(
        self, container: Locator, measure_id: str, titles: tuple[str, ...]
    ) -> str | None:
        """Visible card text, or a visible measure image in the same widget.

        A hidden image is ignored. When the visible text and the image label
        disagree, the visible text is kept.
        """
        visible = self._visible_card_count(container, titles)
        image = self._visible_measure_text(container, measure_id)
        if visible and image and re.sub(r"\D", "", visible) != re.sub(r"\D", "", image):
            return visible
        if visible:
            return visible
        return image

    def _visible_card_count(self, container: Locator, titles: tuple[str, ...]) -> str | None:
        """Number painted for this card, taken from visible text in the widget."""
        runs = self._visible_svg_runs(container)
        found = self._count_after_title(runs, titles) if runs else None
        if found:
            return found
        try:
            body = _plain(container.inner_text(timeout=1_000))
        except Error:
            return None
        lines = [line.strip() for line in re.split(r"[\r\n]+", body) if line.strip()]
        return self._count_after_title(lines, titles)

    def _visible_svg_runs(self, container: Locator) -> list[str]:
        """Visible SVG text runs inside the widget, in document order."""
        runs: list[str] = []
        nodes = container.locator("svg text").filter(visible=True)
        try:
            count = nodes.count()
        except Error:
            return runs
        for index in range(min(count, 40)):
            node = nodes.nth(index)
            if not self._node_is_paintable(node):
                continue
            try:
                raw = _plain(node.text_content(timeout=300) or "")
            except Error:
                continue
            compact = raw.replace("\u00a0", "").replace("\u202f", "").strip()
            if compact:
                runs.append(compact)
        return runs

    def _count_after_title(self, runs: list[str], titles: tuple[str, ...]) -> str | None:
        """First grouped integer after this card title and before the next card."""
        others = [
            title
            for _path, _measure, card_titles in self._KPI_SPECS
            for title in card_titles
            if title not in titles
        ]
        for index, run in enumerate(runs):
            matched = next((title for title in titles if title in run), None)
            if matched is None:
                continue
            parts = [run.split(matched, 1)[1]]
            for later in runs[index + 1 :]:
                if any(other in later for other in others):
                    break
                parts.append(later)
            for part in parts:
                match = re.search(r"\d[\d,]*", part.replace(" ", ""))
                if match and _COUNT_TOKEN.fullmatch(match.group(0)):
                    return match.group(0)
        return None

    def _visible_measure_text(self, container: Locator, measure_id: str) -> str | None:
        """Trailing count on a visible measure image inside the widget."""
        images = container.locator(f"img[aria-label*='{measure_id}']").filter(visible=True)
        try:
            count = images.count()
        except Error:
            return None
        for index in range(count):
            image = images.nth(index)
            if not self._node_is_paintable(image):
                continue
            try:
                label = _plain(image.get_attribute("aria-label") or "")
            except Error:
                continue
            match = re.search(r"(\d[\d,]*)\s*\.?$", label)
            if match:
                return match.group(1)
        return None

    def _chart_title(self, chart_key: str) -> str | None:
        """Visible title for this chart.

        After a courtesy sub-tab click, the service question that belongs to
        that tab wins. A hidden copy of the other question does not.
        """
        titles = self._CHART_TITLES.get(chart_key, ())
        if chart_key == "service_reception":
            preferred = getattr(self, "_selected_satisfaction_question", None)
            if preferred:
                visible = self._visible_exact_title((preferred,))
                if visible is not None:
                    return visible
        return self._first_visible_title(titles)

    def _visible_exact_title(self, titles: tuple[str, ...]) -> str | None:
        """First title with a visible exact text node. Body text does not count."""
        frame = self._report_frame()
        for title in titles:
            locator = frame.get_by_text(title, exact=True).filter(visible=True)
            try:
                if locator.count() == 0:
                    continue
            except Error:
                continue
            if self._node_is_paintable(self._first_outside_tooltip(locator)):
                return title
        return None

    def _first_visible_title(self, titles: tuple[str, ...]) -> str | None:
        for title in titles:
            if self.phrase_is_visible(title, timeout_ms=800):
                return title
        return None

    def _read_category_chart(self, chart_key: str, label_field: str) -> list[dict]:
        title = self._chart_title(chart_key)
        if title is None:
            return []
        try:
            container = self._visual_container(title)
            try:
                canvas = _plain(container.inner_text(timeout=2_000))
            except Error:
                canvas = ""
            rows = self._charts.read_rows(container, name=title)
        except (Error, PlaywrightTimeoutError, AssertionError):
            return []
        mapped: list[dict] = []
        for row in rows:
            item = self._map_category_row(row, label_field)
            if item.get(label_field):
                mapped.append(item)
        self._fill_percentages_from_canvas(mapped, label_field, canvas)
        return mapped

    def _map_category_row(self, row: dict[str, str], label_field: str) -> dict:
        """Map one Show-as-a-table row onto label, count, and percentage."""
        label_aliases = {
            "platform": ("פלטפורמה", "מדיה", "ערוץ", "Platform"),
            "language": ("שפה", "Language"),
            "type": ("סוג", "Type"),
            "topic": ("נושא", "Topic"),
            "level": ("רמה", "תשובה", "Level"),
            "channel": ("ערוץ", "ערוץ יצירת קשר", "Channel"),
        }
        header_map = {
            label_field: label_aliases.get(label_field, (label_field,)),
            "count": ("כמות", "מספר", "ספירה", "Count", "פניות"),
            "percentage": ("אחוז", "Percentage", "%"),
        }
        item = {label_field: "", "count": "", "percentage": ""}
        for header, value in row.items():
            field = self._field_for_header(header, header_map)
            if field and not item[field]:
                item[field] = _plain(value)
        cells = [_plain(value) for value in row.values() if _plain(value)]
        for cell in cells:
            combined = re.search(
                r"(\d[\d,]*)\s*\(\s*(\d+(?:[.,]\d+)?%)\s*\)",
                cell,
            )
            if combined:
                if not item["count"]:
                    item["count"] = combined.group(1)
                if not item["percentage"]:
                    item["percentage"] = combined.group(2)
            if not item["percentage"] and "%" in cell:
                item["percentage"] = cell.replace(" ", "")
            elif not item["count"] and re.fullmatch(r"-?\d[\d,]*", cell.replace(" ", "")):
                item["count"] = cell
            elif not item[label_field]:
                item[label_field] = cell
        if item["percentage"]:
            item["percentage"] = item["percentage"].replace(" ", "")
        if not item["percentage"]:
            item.pop("percentage")
        if not item["count"]:
            item.pop("count")
        return item

    def _fill_percentages_from_canvas(
        self, items: list[dict], label_field: str, canvas: str
    ) -> None:
        """Copy ``N (P%)`` from the visual when the data table has no percent column."""
        flat = re.sub(r"\s+", " ", canvas or "")
        if not flat:
            return
        pairs = [
            (match.group(1).replace(",", "").replace(" ", ""), match.group(2).replace(" ", ""))
            for match in _CANVAS_COUNT_PERCENT.finditer(flat)
        ]
        for item in items:
            if item.get("percentage"):
                continue
            digits = str(item.get("count", "")).replace(",", "").replace(" ", "")
            if not digits:
                continue
            for count, percentage in pairs:
                if count == digits:
                    item["percentage"] = percentage
                    break

    def _read_hourly_trend(self) -> dict:
        """Series names and hour labels. Point values are not part of the golden file."""
        title = self._first_visible_title(self._CHART_TITLES["requests_by_hour_trend"])
        if title is None:
            return {"series": [], "x_axis_labels": []}
        try:
            rows = self._charts.read_rows(self._visual_container(title), name=title)
        except (Error, PlaywrightTimeoutError, AssertionError):
            return {"series": [], "x_axis_labels": []}
        return self._hourly_from_rows(rows)

    def _hourly_from_rows(self, rows: list[dict[str, str]]) -> dict:
        headers: list[str] = []
        for row in rows:
            for key in row:
                if key not in headers:
                    headers.append(key)
        time_header = None
        for header in headers:
            hits = sum(
                1 for row in rows if _HOUR_LABEL.fullmatch(_plain(row.get(header, "")))
            )
            if hits and hits >= max(1, len(rows) // 2):
                time_header = header
                break
        labels: list[str] = []
        if time_header is not None:
            for row in rows:
                label = _plain(row.get(time_header, ""))
                if _HOUR_LABEL.fullmatch(label) and label not in labels:
                    labels.append(label)
            series = [
                header
                for header in headers
                if header and header != time_header and not _HOUR_LABEL.fullmatch(_plain(header))
            ]
        else:
            series = []
        return {
            "series": [{"name": name} for name in series],
            "x_axis_labels": labels,
        }

    def _read_surveys_summary(self) -> dict:
        summary: dict = {}
        for section, titles in self._SURVEY_SECTIONS.items():
            title = self._first_visible_title(titles)
            text = self._survey_section_text(title) if title is not None else ""
            block: dict[str, str] = {}
            for field, labels in self._SURVEY_LABELS.items():
                if section == "quality_control" and field in ("surveys_sent", "surveys_filled"):
                    continue
                if section != "quality_control" and field in (
                    "valid_calls_checked",
                    "validity_percentage",
                ):
                    continue
                value = self._value_after_label(text, labels)
                if value is None and title is not None:
                    value = self._metric_near_label(labels, title)
                if value is not None:
                    block[field] = value
            if block:
                summary[section] = block
        return summary

    def _metric_near_label(self, labels: tuple[str, ...], anchor: str) -> str | None:
        """Value painted under a survey label. The number often sits in a sibling visual."""
        frame = self._report_frame()
        try:
            anchor_box = self._first_outside_tooltip(
                frame.get_by_role(
                    "heading", name=re.compile(re.escape(anchor))
                ).filter(visible=True)
            ).bounding_box()
        except Error:
            anchor_box = None
        if anchor_box is None:
            try:
                anchor_box = self._first_outside_tooltip(
                    frame.get_by_text(anchor, exact=False).filter(visible=True)
                ).bounding_box()
            except Error:
                anchor_box = None
        if anchor_box is None:
            return None
        best_value = None
        best_distance = None
        for label in sorted(labels, key=len, reverse=True):
            nodes = frame.get_by_text(label, exact=True).filter(visible=True)
            try:
                count = nodes.count()
            except Error:
                continue
            for index in range(count):
                label_node = nodes.nth(index)
                if not self._node_is_paintable(label_node):
                    continue
                try:
                    box = label_node.bounding_box()
                except Error:
                    continue
                if box is None:
                    continue
                # A label above this heading belongs to the previous card.
                dy = box["y"] - anchor_box["y"]
                if dy < -30:
                    continue
                distance = dy + abs(box["x"] - anchor_box["x"])
                if distance > 320:
                    continue
                if best_distance is not None and distance >= best_distance:
                    continue
                value = self._metric_under_box(label_node)
                if not value:
                    continue
                best_distance = distance
                best_value = value
        return best_value

    def _metric_under_box(self, label_node: Locator) -> str | None:
        """Short metric painted just under a label. Both boxes are measured in the iframe."""
        try:
            hits = label_node.evaluate(
                """(el) => {
                    const label = el.getBoundingClientRect();
                    const labelCenter = label.x + label.width / 2;
                    const labelBottom = label.y + label.height;
                    const hidden = (node) => {
                        if (!node || node.getAttribute("aria-hidden") === "true") return true;
                        if (node.getAttribute("role") === "tooltip" || node.closest("[role='tooltip']")) return true;
                        const style = window.getComputedStyle(node);
                        if (style.display === "none" || style.visibility === "hidden") return true;
                        const rect = node.getBoundingClientRect();
                        return rect.width < 2 || rect.height < 2;
                    };
                    const hits = [];
                    const root = el.ownerDocument.body;
                    for (const node of root.querySelectorAll('*')) {
                        if (hidden(node)) continue;
                        const text = (node.innerText || '').trim();
                        if (!text || text.length > 24 || text.includes('\\n')) continue;
                        if (!/^(\\d[\\d,]*|לא ידוע|אין מידע)$/.test(text)) continue;
                        const rect = node.getBoundingClientRect();
                        if (rect.width < 2 || rect.height < 2) continue;
                        const center = rect.x + rect.width / 2;
                        const dy = rect.y - labelBottom;
                        if (Math.abs(center - labelCenter) > 80) continue;
                        if (dy < -30 || dy > 70) continue;
                        hits.push({text, dy});
                    }
                    return hits;
                }"""
            )
        except Error:
            return None
        if not hits:
            return None
        hits.sort(key=lambda item: item["dy"] if item["dy"] >= 0 else 1_000 + abs(item["dy"]))
        return str(hits[0]["text"])

    def _value_after_label(self, text: str, labels: tuple[str, ...]) -> str | None:
        """Metric on the label's line, the next line, or the previous line."""
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        ordered = tuple(sorted(labels, key=len, reverse=True))
        for index, line in enumerate(lines):
            for label in ordered:
                if label not in line:
                    continue
                rest = line.split(label, 1)[-1].strip(" :|-")
                if _looks_like_metric(rest):
                    return rest
                if index + 1 < len(lines) and _looks_like_metric(lines[index + 1]):
                    return lines[index + 1]
                if index > 0 and _looks_like_metric(lines[index - 1]):
                    return lines[index - 1]
                break
        return None

    def _read_grid(self, header_map: dict[str, tuple[str, ...]]) -> list[dict]:
        """Open Show as a table on the grid visual and map rows onto header_map.

        The canvas grid is not a fallback. A missing menu, back button, or data
        cell raises. After the data view closes, the screen ready locator must
        be visible again.
        """
        grid = self._visible_grid()
        if grid is None:
            return []
        host = self._grid_visual_host(grid)
        name = "feedback grid" if "inquiry_id" in header_map else "investigation grid"
        rows = self._charts.read_rows(host, name=name)
        mapped = self._map_table_rows(rows, header_map)
        self._wait_until_ready(self._current_screen_id)
        return mapped

    def _grid_visual_host(self, grid: Locator) -> Locator:
        """Smallest visual container around this grid, so the right-click hits it."""
        xpaths = (
            "ancestor::*[contains(@class,'visualContainerHost')][1]",
            "ancestor::*[contains(@class,'visual-container-host')][1]",
            "ancestor::*[contains(@class,'visualContainer')][1]",
            "ancestor::*[contains(@class,'visual-container')][1]",
        )
        best: Locator | None = None
        best_area: float | None = None
        for xpath in xpaths:
            node = grid.locator(f"xpath={xpath}")
            try:
                if node.count() == 0:
                    continue
            except Error:
                continue
            host = node.first
            if not self._node_is_paintable(host):
                continue
            try:
                box = host.bounding_box(timeout=500)
            except Error:
                continue
            if box is None or box["width"] < 40 or box["height"] < 40:
                continue
            area = box["width"] * box["height"]
            if best_area is None or area < best_area:
                best = host
                best_area = area
        if best is not None:
            return best
        return grid

    def _map_table_rows(
        self,
        rows: list[dict[str, str]],
        header_map: dict[str, tuple[str, ...]],
    ) -> list[dict]:
        """Map expanded-grid headers onto header_map and keep the first id."""
        id_field = "inquiry_id" if "inquiry_id" in header_map else "request_id"
        found: dict[str, dict] = {}
        order: list[str] = []
        for row in rows:
            values = [_plain(str(value)) for value in row.values()]
            first = values[0] if values else ""
            if first.startswith('סה"כ') or first.startswith("סה״כ"):
                continue
            item = {field: "" for field in header_map}
            for header, cell in row.items():
                key = _plain(str(header).split("\x00", 1)[0])
                field = self._field_for_header(key, header_map)
                if field and not item[field]:
                    item[field] = _plain(str(cell))
            if not any(item.values()):
                continue
            row_id = str(item.get(id_field, "") or "").strip()
            if not row_id or row_id in found:
                continue
            found[row_id] = item
            order.append(row_id)
        return [found[key] for key in order]

    def _feedback_comments_header(self) -> Locator:
        """Visible survey-sent header. The live grid shows this column, not הערות."""
        frame = self._report_frame()
        by_name = frame.get_by_role("columnheader", name=_FEEDBACK_HEADER)
        by_text = frame.get_by_text("שליחת הסקר", exact=False)
        return by_name.or_(by_text).filter(visible=True).first

    def _comments_header_visible(self) -> bool:
        """True when the screen 4 comments header is on screen."""
        try:
            return self._feedback_comments_header().is_visible(timeout=2_000)
        except Error:
            return False

    def _field_for_header(
        self, header: str, header_map: dict[str, tuple[str, ...]]
    ) -> str | None:
        text = _plain(header)
        if not text:
            return None
        for field, aliases in header_map.items():
            if text in aliases:
                return field
        best = None
        best_len = 0
        for field, aliases in header_map.items():
            for alias in aliases:
                if len(alias) >= 4 and alias in text and len(alias) > best_len:
                    best = field
                    best_len = len(alias)
        return best

    def _visible_grid(self) -> Locator | None:
        frame = self._report_frame()
        for role in ("grid", "table"):
            tables = frame.get_by_role(role)
            try:
                count = tables.count()
            except Error:
                continue
            for index in range(count):
                candidate = tables.nth(index)
                try:
                    if candidate.is_visible():
                        return candidate
                except Error:
                    continue
        return None

    def _visual_container(self, title: str) -> Locator:
        """Smallest visual host that contains this title, so the right-click hits that chart."""
        frame = self._report_frame()
        hosts = (
            frame.locator(
                "[class*='visualContainerHost'], [class*='visual-container-host'], "
                "[class*='visualContainer'], [class*='visual-container']"
            )
            .filter(has_text=title)
            .filter(visible=True)
        )
        best: Locator | None = None
        best_area: float | None = None
        try:
            count = hosts.count()
        except Error:
            count = 0
        for index in range(min(count, 12)):
            host = hosts.nth(index)
            if not self._node_is_paintable(host):
                continue
            try:
                box = host.bounding_box(timeout=500)
            except Error:
                continue
            if box is None or box["width"] < 40 or box["height"] < 40:
                continue
            area = box["width"] * box["height"]
            if best_area is None or area < best_area:
                best = host
                best_area = area
        if best is not None:
            return best
        visible = frame.get_by_text(title, exact=False).filter(visible=True)
        if visible.count() == 0:
            named = frame.get_by_role("group", name=title, exact=False).filter(visible=True)
            if named.count() == 0:
                raise AssertionError(f"Chart {title!r} has no visual container")
            title_node = self._first_outside_tooltip(named)
        else:
            title_node = self._first_outside_tooltip(visible)
        for xpath in (
            "ancestor::*[contains(@class,'visualContainerHost')][1]",
            "ancestor::*[contains(@class,'visual-container-host')][1]",
            "ancestor::*[contains(@class,'visualContainer')][1]",
            "ancestor::*[contains(@class,'visual-container')][1]",
        ):
            node = title_node.locator(f"xpath={xpath}")
            if node.count() > 0:
                return node.first
        return title_node

    def _visible_block_text(self, node: Locator) -> str:
        """Visible text of one node, skipping tooltips and aria-hidden descendants."""
        try:
            raw = node.evaluate(
                """el => {
                    const hidden = (current) => {
                        if (!current || current.nodeType !== 1) return false;
                        if (current.getAttribute("aria-hidden") === "true") return true;
                        if (current.getAttribute("role") === "tooltip" || current.closest("[role='tooltip']")) return true;
                        const style = window.getComputedStyle(current);
                        return style.display === "none" || style.visibility === "hidden";
                    };
                    const parts = [];
                    const walk = (current) => {
                        if (current.nodeType === 3) {
                            const text = (current.textContent || "").replace(/\\s+/g, " ").trim();
                            if (text) parts.push(text);
                            return;
                        }
                        if (current.nodeType !== 1 || hidden(current)) return;
                        for (const child of current.childNodes) walk(child);
                    };
                    if (hidden(el)) return "";
                    for (const child of el.childNodes) walk(child);
                    return parts.join("\\n");
                }"""
            )
        except Error:
            return ""
        return _plain(str(raw or ""))

    def _survey_section_text(self, title: str) -> str:
        """Card text for one survey block, including both metric lines."""
        frame = self._report_frame()
        node = self._first_outside_tooltip(
            frame.get_by_role(
                "heading", name=re.compile(re.escape(title))
            ).filter(visible=True)
        )
        current = next(
            (aliases for aliases in self._SURVEY_SECTIONS.values() if title in aliases),
            (title,),
        )
        others = [
            alias
            for aliases in self._SURVEY_SECTIONS.values()
            for alias in aliases
            if alias not in current
        ]
        chosen = ""
        scoped = ""
        for _ in range(8):
            try:
                chosen = self._visible_block_text(node)
            except Error:
                break
            if any(other in chosen for other in others):
                break
            scoped = chosen
            has_pair = ("מולאו" in chosen and "נשלחו" in chosen) or (
                "נבדקו" in chosen and "אחוז" in chosen
            )
            has_value = bool(re.search(r"\d", chosen)) or "לא ידוע" in chosen or "אין מידע" in chosen
            parent = node.locator("xpath=..")
            try:
                if parent.count() == 0:
                    break
            except Error:
                break
            node = parent
            if has_pair and has_value and re.search(r"\d", chosen):
                return chosen
        return scoped

    def _slicer_control(self, slicer_id: str) -> Locator | None:
        aliases = self._SLICER_ALIASES.get(slicer_id)
        if not aliases:
            return None
        frame = self._report_frame()
        for name in aliases:
            locator = frame.get_by_role("combobox", name=name, exact=True)
            try:
                if locator.count() > 0 and locator.first.is_visible(timeout=400):
                    return locator.first
            except Error:
                continue
        try:
            control = self._slicer.control(slicer_id)
        except KeyError:
            return None
        try:
            if control.count() > 0:
                return control.first
        except Error:
            return None
        return None

    def _tab_is_visible(self, label: str) -> bool:
        locator = self._tab_locator(label)
        try:
            return locator.is_visible(timeout=800)
        except Error:
            return False

    def _open_tab(self, labels: tuple[str, ...]) -> None:
        for label in labels:
            if self._tab_is_visible(label):
                self._click_tab(label)
                return
        self._click_tab(labels[0])

    def _wait_for_report_settled(self) -> None:
        """Hide a visible loading spinner, then require this screen's ready locator."""
        frame = self._report_frame()
        spinner = frame.locator("[class*='spinner'], [aria-busy='true']").filter(
            visible=True
        )
        try:
            if spinner.count() > 0:
                expect(spinner.first).to_be_hidden(timeout=self.timeout)
        except Error:
            pass
        self._wait_until_ready(self._current_screen_id)

    def _date_inputs_ready(self) -> bool:
        """True when both date inputs are visible and enabled."""
        start = self._date_field("תאריך התחלה", "Start date")
        end = self._date_field("תאריך סיום", "End date")
        try:
            return (
                start.is_visible(timeout=1_000)
                and start.is_enabled(timeout=1_000)
                and end.is_visible(timeout=1_000)
                and end.is_enabled(timeout=1_000)
            )
        except Error:
            return False

    def _expect_date_inputs_ready(self) -> None:
        """Fail when the toggle click does not reveal both date inputs."""
        start = self._date_field("תאריך התחלה", "Start date")
        end = self._date_field("תאריך סיום", "End date")
        expect(start).to_be_visible(timeout=self.timeout)
        expect(start).to_be_enabled(timeout=self.timeout)
        expect(end).to_be_visible(timeout=self.timeout)
        expect(end).to_be_enabled(timeout=self.timeout)

    def _click_period_toggle(self) -> None:
        """Click the filter-bar label כלל התאריכים or יום נוכחי, once."""
        toggle = self._period_toggle()
        expect(toggle).to_be_visible(timeout=self.timeout)
        toggle.click(force=True)

    def _period_toggle(self) -> Locator:
        """Visible action button that unlocks the start and end date inputs."""
        frame = self._report_frame()
        toggle = frame.locator(".visual-actionButton").filter(has_text=self._PERIOD_TOGGLE_LABELS[0])
        for label in self._PERIOD_TOGGLE_LABELS:
            toggle = toggle.or_(frame.locator(".visual-actionButton").filter(has_text=label))
            toggle = toggle.or_(frame.get_by_role("button", name=label, exact=True))
        return toggle.filter(visible=True).first

    def _date_field(self, hebrew: str, english: str) -> Locator:
        """Bilingual date input. Visibility is checked by the caller."""
        frame = self._report_frame()
        return (
            frame.locator(f"input[aria-label^='{hebrew}']")
            .or_(frame.locator(f"input[aria-label^='{english}']"))
            .first
        )

    def _click_tab(self, label: str) -> None:
        locator = self._tab_locator(label)
        expect(locator).to_be_visible(timeout=self.timeout)
        locator.click(force=True)

    def _tab_locator(self, label: str) -> Locator:
        """Page-rail name is 'ניווט בין עמודים . {label}', anchored so משובים is not תחקור משובים."""
        frame = self._report_frame()
        pattern = re.compile(rf"ניווט בין עמודים\s*\.\s*{re.escape(label)}$")
        return (
            frame.get_by_role("link", name=pattern)
            .or_(frame.get_by_role("img", name=pattern))
            .or_(frame.get_by_role("button", name=pattern))
            .filter(visible=True)
            .first
        )

    def _fill_date_input(self, hebrew: str, english: str, value: str) -> bool:
        field = self._date_input(hebrew, english)
        if field is None:
            return False
        try:
            field.click(force=True)
            field.fill(value)
            field.press("Enter")
        except Error:
            return False
        try:
            self.page.keyboard.press("Escape")
        except Error:
            return True
        return True

    def _body_contains(self, phrase: str) -> bool:
        """True when split text runs still contain the phrase once whitespace is collapsed."""
        try:
            text = self._report_frame().locator("body").inner_text(timeout=2_000)
        except Error:
            return False
        collapsed = re.sub(r"\s+", " ", _plain(text))
        return phrase in collapsed

    def _date_input(self, hebrew: str, english: str) -> Locator | None:
        field = self._date_field(hebrew, english)
        try:
            if field.is_visible(timeout=1_000):
                return field
        except Error:
            return None
        return None

    def _input_value(self, hebrew: str, english: str) -> str:
        field = self._date_input(hebrew, english)
        if field is None:
            return ""
        try:
            return _plain(field.input_value(timeout=1_000))
        except Error:
            return ""

    @staticmethod
    def _normalize_range(date_range: str) -> str:
        match = _DATE_RANGE.search(date_range or "")
        if match is None:
            return _plain(date_range)
        return f"{match.group(1)} - {match.group(2)}"
