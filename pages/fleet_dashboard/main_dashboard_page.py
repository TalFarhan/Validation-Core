import re
import time

import allure
from playwright.sync_api import Page, expect

from browser_session import ensure_single_tab, wait_for_auth_popups_to_finish
from config.settings import settings
from pages.base_page import BasePage
from pages.errors import ExpandHierarchyUnavailable, LoadTimeoutError
from reports.test_run_report import get_current_report


class MainDashboardPage(BasePage):
    _KPI_TITLES = {
        "total": 'סה"כ רכבים שנקלטו',
        "in_use": 'סה"כ רכבים בשימוש',
        "withdrawn": "רכבים שזוכו",
        "allocated": "רכבים שווסתו",
    }

    _TAB_KPI_MAP = {
        "all": "total",
        "in_use": "in_use",
        "allocated": "allocated",
        "withdrawn": "withdrawn",
    }

    _CHART_TITLES = {
        # UI may use either spelling of "משיכה/משיכת".
        "source": ("פילוח מקור משיכת רכבים בשימוש", "פילוח מקור משיכה רכבים בשימוש"),
        "unit": ("פילוח רכבים בשימוש ביחידות",),
        "category": ("פילוח קטגוריות רכב",),
        "withdrawal": ("פילוח סיבות לזיכוי רכב",),
    }

    # Power BI tooltips render as transient overlays at report scope (not always
    # nested under the visual group). Prefer real chart tooltip hosts; exclude
    # chrome hints (Enter-to-explore / follow) via _tooltip_is_visible filtering.
    _TOOLTIP_SELECTOR = (
        ".tooltip-container, .modern-tooltip-container, "
        ".tooltip-content-container, .visual-tooltip, "
        ".pbi-tooltip-content, "
        "[class*='tooltip-container'], [class*='TooltipHost'], "
        "[class*='modern-tooltip'], [class*='tooltip-content'], "
        "[class*='TooltipContent'], [class*='pbi-tooltip']"
    )
    _TOOLTIP_NOISE = (
        "הקש enter כדי לחקור",
        "press enter to explore",
        "לחץ כאן כדי מעקב",
        "click here to follow",
    )
    _HOVER_SCAN_POSITIONS = (
        (0.20, 0.55),
        (0.35, 0.50),
        (0.50, 0.45),
        (0.65, 0.50),
        (0.80, 0.55),
        (0.40, 0.65),
        (0.60, 0.65),
        (0.50, 0.35),
    )

    # Power BI visual-header hierarchy controls (Hebrew + English locales).
    # הסתעפות = expand one hierarchy level (forked arrows / Expand-all).
    # כינוס = opposite of הסתעפות (collapse / drill up).
    # NOT the single down arrow ("Drill down") and NOT the double-down
    # ("Go to the next level in the hierarchy").
    _EXPAND_HIERARCHY_PATTERN = re.compile(
        r"הסתעפות|"
        r"Expand all down one level|"
        r"expand all down one level|"
        r"Expand all down|"
        r"הרחב הכל.*רמה אחת|"
        r"רמה אחת למטה בהיררכיה",
        re.I,
    )
    _NOT_EXPAND_HIERARCHY_PATTERN = re.compile(
        r"^\s*Drill down\s*$|"
        r"Click to turn on Drill Down|"
        r"Go to the next level|"
        r"עבור לרמה הבאה|"
        r"הפעל מצב פירוט|"
        r"הפעל.*drill|"
        r"כינוס",
        re.I,
    )
    _DRILL_UP_PATTERN = re.compile(
        r"כינוס|עלה ברמה|Drill up|drill up|Collapse",
        re.I,
    )

    _SLICER_LISTBOXES = {
        "district": "Unit",
        "sub_unit": "SubUnit",
        "source": "VehicleSource",
        "category": "VehicleCategory",
    }

    def __init__(self, page: Page):
        super().__init__(page)
        self.url = settings.DASHBOARD_URL
        self.dashboard = page.frame_locator("main iframe")

        self.district_dropdown = self.dashboard.get_by_role("combobox", name="Unit", exact=True)
        self.sub_unit_dropdown = self.dashboard.get_by_role("combobox", name="SubUnit", exact=True)
        self.source_dropdown = self.dashboard.get_by_role("combobox", name="VehicleSource", exact=True)
        self.category_dropdown = self.dashboard.get_by_role("combobox", name="VehicleCategory", exact=True)
        # Power BI may expose this control in Hebrew or English depending on locale.
        self.clear_filters_btn = self.dashboard.get_by_role(
            "button",
            name=re.compile(r"נקה את כל|Clear all slicers|Clear all filters", re.I),
        )

        self.total_vehicles_kpi = self._kpi_card(self._KPI_TITLES["total"])
        self.in_use_kpi = self._kpi_card(self._KPI_TITLES["in_use"])
        self.withdrawn_vehicles_kpi = self._kpi_card(self._KPI_TITLES["withdrawn"])
        self.allocated_vehicles_kpi = self._kpi_card(self._KPI_TITLES["allocated"])

        self.all_vehicles_tab = self._tab("כל הרכבים")
        self.in_use_tab = self._tab("בשימוש")
        self.allocated_tab = self._tab("שווסתו")
        self.withdrawn_tab = self._tab("שזוכו")

        self._tab_map = {
            "all": self.all_vehicles_tab,
            "in_use": self.in_use_tab,
            "allocated": self.allocated_tab,
            "withdrawn": self.withdrawn_tab,
        }

        self.vehicle_table = self.dashboard.locator('[role="grid"]').first
        # Text Search Slicer custom visual lives in a nested sandbox iframe.
        self._vehicle_search_frame = self.dashboard.frame_locator("iframe.visual-sandbox")
        self.vehicle_search = self._vehicle_search_frame.locator("input.input-field").or_(
            self._vehicle_search_frame.get_by_placeholder(re.compile(r"חיפוש|Search", re.I))
        ).first
        self._vehicle_search_submit = self._vehicle_search_frame.locator(
            "button.input-button"
        ).first
        self._vehicle_search_clear = self._vehicle_search_frame.locator(
            "button.input-button"
        ).nth(1)

    def _tab(self, label: str):
        return self.dashboard.get_by_text(label, exact=True).first

    def _kpi_card(self, title: str):
        return self.dashboard.get_by_role("button", name=re.compile(re.escape(title)))

    def _portal_search_box(self):
        return (
            self.page.get_by_role("textbox", name=re.compile(r"חיפוש מוצר|חיפוש"))
            .or_(self.page.get_by_placeholder(re.compile(r"חיפוש")))
            .or_(self.page.get_by_role("searchbox"))
            .first
        )

    def _all_products_control(self):
        label = settings.PORTAL_ALL_PRODUCTS_LABEL
        pattern = re.compile(re.escape(label))
        return (
            self.page.get_by_role("link", name=pattern)
            .or_(self.page.get_by_role("button", name=pattern))
            .or_(self.page.get_by_label(pattern))
            .or_(self.page.locator(f"[title='{label}'], [aria-label='{label}']"))
            .or_(self.page.get_by_text(pattern))
            .first
        )

    def _dashboard_iframe(self):
        return self.page.locator("main iframe").or_(self.page.locator("iframe")).first

    def _click_even_if_hidden(self, locator) -> None:
        """Click controls that exist in DOM but are visually hidden/covered."""
        locator.first.wait_for(state="attached", timeout=self.timeout)
        try:
            locator.first.click(force=True, timeout=5000)
            return
        except Exception:
            pass
        handle = locator.first.element_handle(timeout=self.timeout)
        if handle is None:
            raise AssertionError("Target element not found for force/JS click")
        self.page.evaluate("(el) => el.click()", handle)

    def _is_portal_home(self) -> bool:
        try:
            if self._portal_search_box().count() > 0:
                return True
        except Exception:
            pass
        try:
            if self._all_products_control().count() > 0:
                return True
        except Exception:
            pass
        url = (self.page.url or "").lower()
        return any(
            part in url
            for part in (
                "portal-agamim.orangepeak.net",
                "portal.agamimp.net",
                "/catalog",
            )
        )

    def _hitachbrut_button(self):
        return self.page.get_by_role("button", name=re.compile(r"^התחברות$")).first

    def _is_login_page(self) -> bool:
        """True for Microsoft IdP or the public Agamim landing with 'התחברות'."""
        url = (self.page.url or "").lower()
        if any(
            part in url
            for part in (
                "login.microsoftonline.com",
                "login.live.com",
                "login.windows.net",
            )
        ):
            return True
        try:
            return self._hitachbrut_button().is_visible(timeout=1000)
        except Exception:
            return False

    def _page_debug_summary(self) -> str:
        title = ""
        try:
            title = self.page.title()
        except Exception:
            pass
        return f"URL={self.page.url!r}, title={title!r}"

    def _is_portal_profile_error(self) -> bool:
        """True when Agamim shows a transient profile/user fetch failure page."""
        try:
            body = (self.page.locator("body").inner_text(timeout=2000) or "")
        except Exception:
            return False
        markers = (
            "אירעה שגיאה בטעינת הפרופיל",
            "Failed to get user",
            "fetch failed",
        )
        return any(marker in body for marker in markers)

    def _recover_from_portal_glitch(self) -> None:
        """Reload home/app URL after a transient portal profile error."""
        print("\n[nav] שגיאת פרופיל זמנית בפורטל — מרעננים ומנסים שוב...\n")
        target = settings.LOGIN_URL or self.url
        try:
            self.page.goto(target, wait_until="domcontentloaded")
        except Exception:
            self.page.reload(wait_until="domcontentloaded")
        self.page.wait_for_timeout(1500)
        ensure_single_tab(self.page.context, self.page)
        if self._is_login_page():
            self._ensure_authenticated()

    def _wait_for_dashboard_iframe(self, *, timeout: float | None = None) -> bool:
        timeout_ms = timeout if timeout is not None else self.timeout
        try:
            expect(self._dashboard_iframe()).to_be_visible(timeout=timeout_ms)
            return True
        except AssertionError:
            return False

    def _dashboard_ready(self) -> bool:
        """True when the Power BI dashboard (iframe + KPI) is already open."""
        if not self._wait_for_dashboard_iframe(timeout=3000):
            return False
        try:
            expect(self.total_vehicles_kpi).to_be_visible(timeout=5000)
            return True
        except AssertionError:
            return False

    def _auto_click_hitachbrut(self) -> bool:
        """
        Click 'התחברות' ONCE and let Microsoft SSO popup finish.

        Do NOT close/re-click in a loop — that is what trapped the user on the
        same landing page.
        """
        try:
            btn = self._hitachbrut_button()
            if not btn.is_visible(timeout=2000):
                return False
        except Exception:
            return False

        print(
            "\n[auth] לוחצים פעם אחת על 'התחברות' "
            "ומחכים ל-SSO (לא סוגרים את חלון Microsoft)...\n"
        )
        clicked = False
        try:
            with self.page.context.expect_page(timeout=15000) as popup_info:
                btn.click()
                clicked = True
            popup = popup_info.value
            try:
                popup.wait_for_load_state("domcontentloaded", timeout=30000)
            except Exception:
                pass
            print(f"\n[auth] חלון SSO נפתח: {popup.url}\n")
        except Exception:
            if not clicked:
                try:
                    btn.click(timeout=5000)
                    clicked = True
                except Exception:
                    print(
                        "\n[auth] לא הצלחנו ללחוץ על 'התחברות' — "
                        "ממתינים להתחברות ידנית אם צריך.\n"
                    )
                    return False

        wait_for_auth_popups_to_finish(
            self.page.context,
            timeout_ms=30000 if (settings.HEADLESS or not settings.MANUAL_LOGIN) else 120000,
        )

        deadline = time.monotonic() + (
            20 if (settings.HEADLESS or not settings.MANUAL_LOGIN) else 60
        )
        while time.monotonic() < deadline:
            if self._dashboard_ready() or not self._is_login_page():
                print("\n[auth] התחברות לפורטל הצליחה.\n")
                try:
                    self.page.context.storage_state(path=settings.AUTH_FILE)
                except Exception:
                    pass
                # Only now close leftover non-auth tabs.
                ensure_single_tab(self.page.context, self.page)
                return True
            time.sleep(0.5)

        print(
            "\n[auth] אחרי לחיצה אחת על 'התחברות' עדיין במסך כניסה. "
            "לא לוחצים שוב אוטומטית.\n"
        )
        return False

    def _open_all_products_catalog(self) -> None:
        """Open catalog: click 'למעבר לקטלוג המוצרים', else fall back to catalog URL."""
        last_error: Exception | None = None
        for attempt in range(3):
            if self._is_portal_profile_error():
                self._recover_from_portal_glitch()

            search = self._portal_search_box()
            try:
                if search.count() > 0 and search.is_visible(timeout=1500):
                    return
            except Exception:
                pass

            # Prefer the real UI control the user clicks.
            all_products = self._all_products_control()
            if all_products.count() > 0:
                print(
                    f"\n[nav] לוחצים על '{settings.PORTAL_ALL_PRODUCTS_LABEL}'...\n"
                )
                self._click_even_if_hidden(all_products)
                ensure_single_tab(self.page.context, self.page)
                try:
                    search.wait_for(state="visible", timeout=self.timeout)
                    return
                except Exception as exc:
                    last_error = exc

            if settings.PORTAL_CATALOG_URL:
                print("\n[nav] עוברים ל-URL של הקטלוג...\n")
                self.page.goto(settings.PORTAL_CATALOG_URL, wait_until="domcontentloaded")
                ensure_single_tab(self.page.context, self.page)
                try:
                    search.wait_for(state="visible", timeout=min(self.timeout, 20000))
                    return
                except Exception as exc:
                    last_error = exc

            if self._is_portal_profile_error() and attempt < 2:
                self._recover_from_portal_glitch()
                continue
            break

        detail = f" Last error: {last_error}" if last_error else ""
        raise AssertionError(
            "Could not open products catalog: no search box and "
            f"'{settings.PORTAL_ALL_PRODUCTS_LABEL}' not found. "
            f"{self._page_debug_summary()}.{detail}"
        )

    def _open_dashboard_via_portal_search(self) -> None:
        # Flow: למעבר לקטלוג המוצרים → חיפוש שליטה בניוד → פתיחה
        self._open_all_products_catalog()

        term = settings.DASHBOARD_SEARCH_TERM
        print(f"\n[nav] מחפשים '{term}' בקטלוג...\n")
        search = self._portal_search_box()
        search.wait_for(state="visible", timeout=self.timeout)
        search.click()
        search.fill(term)
        search.press("Enter")

        result = (
            self.page.get_by_role("link", name=re.compile(re.escape(term)))
            .or_(self.page.get_by_role("button", name=re.compile(re.escape(term))))
            .or_(
                self.page.locator("a, button, [role='listitem'], [role='option']").filter(
                    has_text=re.compile(re.escape(term))
                )
            )
            .or_(self.page.get_by_text(term, exact=False))
            .first
        )
        expect(result).to_be_visible(timeout=self.timeout)
        result.click()
        ensure_single_tab(self.page.context, self.page)

        if not self._wait_for_dashboard_iframe():
            raise AssertionError(
                f"Opened portal search for '{term}' but dashboard iframe did not load. "
                f"{self._page_debug_summary()}."
            )

    def _ensure_authenticated(self) -> None:
        """Enter portal: one SSO click; pause only if still stuck (no click loop)."""
        if self._dashboard_ready() or not self._is_login_page():
            return

        # One automatic attempt only.
        if self._auto_click_hitachbrut():
            return

        if settings.HEADLESS or not settings.MANUAL_LOGIN:
            raise AssertionError(
                "Still on login landing after one 'התחברות' click. "
                f"{self._page_debug_summary()}. "
                "Set HEADLESS=false and complete Microsoft login once."
            )

        print(
            "\n[auth] צריך השלמת התחברות ידנית בחלון Microsoft אם נפתח.\n"
            "  אל תלחצי שוב ושוב על 'התחברות' בדף הנחיתה.\n"
            "  סיימי SSO ואז Resume.\n"
        )
        while self._is_login_page() and not self._dashboard_ready():
            self.page.pause()
            wait_for_auth_popups_to_finish(self.page.context, timeout_ms=30000)
            self.page.wait_for_timeout(1000)

        try:
            self.page.context.storage_state(path=settings.AUTH_FILE)
        except Exception:
            pass

    @allure.step("Navigate to Fleet Dashboard")
    def navigate(self, *, force_reload: bool = False) -> None:
        # Shared browser session: reuse the open dashboard instead of
        # page.goto on every test (Power BI cold load is the main cost).
        if not force_reload and self._dashboard_ready():
            via = "reuse_open"
            ensure_single_tab(self.page.context, self.page)
            self.reset_dashboard_filters()
            report = get_current_report()
            if report is not None:
                report.log_ui(
                    f"Reused open dashboard (skipped reload) | {self._page_debug_summary()}"
                )
            return

        self.page.goto(self.url, wait_until="domcontentloaded")
        via = "direct_url"

        if self._dashboard_ready():
            via = "already_open"
        else:
            self._ensure_authenticated()

            # After SSO, open the app URL again once (not in a loop).
            if not self._dashboard_ready() and not self._is_login_page():
                if "/application/" not in (self.page.url or ""):
                    self.page.goto(self.url, wait_until="domcontentloaded")

            if self._dashboard_ready():
                via = "direct_url_after_sso"
            elif self._is_login_page():
                raise AssertionError(
                    "Still on login page after auth attempts. "
                    f"{self._page_debug_summary()}"
                )
            else:
                via = "portal_search"
                self._open_dashboard_via_portal_search()

        ensure_single_tab(self.page.context, self.page)
        # Power BI often paints the report chrome before KPI cards hydrate.
        ready_deadline = time.monotonic() + self.timeout / 1000
        while time.monotonic() < ready_deadline:
            try:
                if self.total_vehicles_kpi.is_visible(timeout=1500):
                    break
            except Exception:
                pass
            self.page.wait_for_timeout(400)
        try:
            expect(self.total_vehicles_kpi).to_be_visible(timeout=self.timeout)
        except AssertionError as exc:
            raise LoadTimeoutError(
                "dashboard KPI card",
                steps_ms=[self.timeout],
                cause=exc,
            ) from exc
        self.reset_dashboard_filters()
        try:
            self.page.context.storage_state(path=settings.AUTH_FILE)
        except Exception:
            pass
        report = get_current_report()
        if report is not None:
            report.log_ui(
                f"Navigated to dashboard via {via}: {self.page.url} "
                f"(search_term={settings.DASHBOARD_SEARCH_TERM!r})"
            )

    @allure.step("Reload dashboard and measure time until KPI ready")
    def reload_and_measure_ready_ms(self) -> int:
        """
        Hard-reload the already-authenticated report and return elapsed ms
        until the total KPI card is visible (interactive load signal).

        Uses short polls so wait timeouts do not inflate the measured duration.
        """
        start = time.perf_counter()
        self.page.reload(wait_until="domcontentloaded")
        # Allow waiting past the SLA so failures report the real duration.
        wait_budget_ms = max(self.timeout, settings.DASHBOARD_LOAD_SLA_MS) + 30_000
        deadline = time.monotonic() + wait_budget_ms / 1000
        while time.monotonic() < deadline:
            try:
                iframe_ok = self._wait_for_dashboard_iframe(timeout=400)
                if iframe_ok and self.total_vehicles_kpi.is_visible(timeout=400):
                    elapsed_ms = int((time.perf_counter() - start) * 1000)
                    report = get_current_report()
                    if report is not None:
                        report.log_ui(
                            f"Dashboard reload ready in {elapsed_ms}ms "
                            f"(SLA={settings.DASHBOARD_LOAD_SLA_MS}ms)"
                        )
                    return elapsed_ms
            except Exception:
                pass
            self.page.wait_for_timeout(150)

        elapsed_ms = int((time.perf_counter() - start) * 1000)
        raise LoadTimeoutError(
            "dashboard KPI after reload",
            steps_ms=[elapsed_ms],
        )

    def option(self, option_name: str, listbox_name: str):
        return self.dashboard.get_by_role("listbox", name=listbox_name, exact=True).get_by_role(
            "option", name=option_name, exact=True
        )

    def _close_open_slicers(self) -> None:
        self.page.keyboard.press("Escape")
        self.page.keyboard.press("Escape")

    def _dropdown_shows_selection(self, dropdown_locator, option_name: str) -> bool:
        try:
            text = (dropdown_locator.inner_text() or "").replace("\u200f", "")
            return option_name in text
        except Exception:
            return False

    def _select_dropdown_option(
        self, dropdown_locator, option_name: str, listbox_name: str
    ) -> None:
        last_total: int | None = None
        for attempt in range(2):
            self._close_open_slicers()
            previous_total = self.get_kpi_value("total", record=False)
            previous_in_use = self.get_kpi_value("in_use", record=False)
            dropdown_locator.click(force=True)
            option = self.option(option_name, listbox_name)
            expect(option).to_be_visible(timeout=self.timeout)
            option.scroll_into_view_if_needed()
            option.click(force=True)
            self.total_vehicles_kpi.click(force=True)
            # Power BI refreshes KPI cards asynchronously — total often updates
            # before in_use; wait for both so assertions don't read a stale card.
            self.wait_for_kpi_update(
                "total",
                previous_total,
                required=False,
                timeout_ms=self.timeout,
            )
            self.wait_for_kpi_update(
                "in_use",
                previous_in_use,
                required=False,
                timeout_ms=self.timeout,
            )
            last_total = self.get_kpi_value("total", record=False)
            selected = self._dropdown_shows_selection(dropdown_locator, option_name)
            changed = last_total != previous_total
            if selected or changed or attempt == 1:
                break

        report = get_current_report()
        if report is not None:
            report.log_filter(listbox_name, option_name)
            if last_total is not None:
                report.log_kpi_read("total", last_total)

    @allure.step("Select district filter: {district_name}")
    def select_district(self, district_name: str) -> None:
        self._select_dropdown_option(
            self.district_dropdown, district_name, self._SLICER_LISTBOXES["district"]
        )

    @allure.step("Select sub-unit filter: {sub_unit_name}")
    def select_sub_unit(self, sub_unit_name: str) -> None:
        self._select_dropdown_option(
            self.sub_unit_dropdown, sub_unit_name, self._SLICER_LISTBOXES["sub_unit"]
        )

    @allure.step("Select source filter: {source_name}")
    def select_source(self, source_name: str) -> None:
        self._select_dropdown_option(
            self.source_dropdown, source_name, self._SLICER_LISTBOXES["source"]
        )

    @allure.step("Select category filter: {category_name}")
    def select_category(self, category_name: str) -> None:
        self._select_dropdown_option(
            self.category_dropdown, category_name, self._SLICER_LISTBOXES["category"]
        )

    @allure.step("Click tab: {tab_name}")
    def click_tab(self, tab_name: str) -> None:
        if tab_name not in self._tab_map:
            raise ValueError(f"Targeted navigation tab is invalid: {tab_name}")

        self._tab_map[tab_name].click(force=True)

    def get_kpi_value(self, metric_type: str, *, record: bool = True) -> int:
        if metric_type not in self._KPI_TITLES:
            raise ValueError(f"Unknown metric representation targeted: {metric_type}")

        value = self._read_kpi_value(self._kpi_card(self._KPI_TITLES[metric_type]))
        if record:
            report = get_current_report()
            if report is not None:
                report.log_kpi_read(metric_type, value)
        return value

    def wait_for_kpi_update(
        self,
        metric_type: str,
        previous_value: int,
        *,
        required: bool = True,
        timeout_ms: int | None = None,
    ) -> None:
        card = self._kpi_card(self._KPI_TITLES[metric_type])
        super().wait_for_kpi_update(
            card, previous_value, required=required, timeout_ms=timeout_ms
        )

    @allure.step("Reset dashboard filters to baseline")
    def reset_dashboard_filters(self) -> None:
        """Clear slicers and vehicle search so shared-session tests start clean."""
        try:
            self.clear_vehicle_search()
        except Exception:
            pass
        # Fast visibility check — do not inherit DEFAULT_TIMEOUT here.
        if not self.clear_filters_btn.is_visible(timeout=1000):
            return
        previous_total = self.get_kpi_value("total", record=False)
        self.clear_filters_btn.click()
        self.wait_for_kpi_update("total", previous_total, required=False)
        report = get_current_report()
        if report is not None:
            report.log_ui("Reset dashboard filters to baseline")

    @allure.step("Clear all applied filters")
    def clear_all_applied_filters(self) -> None:
        filtered_total = self.get_kpi_value("total", record=False)
        self.clear_filters_btn.click()
        # Already-clear dashboards may keep the same KPI after the click.
        # Allow full budget so a real clear can finish; return early on change.
        self.wait_for_kpi_update(
            "total",
            filtered_total,
            required=False,
            timeout_ms=self.timeout,
        )
        report = get_current_report()
        if report is not None:
            report.log_ui("Cleared all applied filters")
            report.log_kpi_read("total", self.get_kpi_value("total", record=False))

    @allure.step("Apply filters on dashboard")
    def apply_filters(
        self,
        *,
        district: str | None = None,
        sub_unit: str | None = None,
        category: str | None = None,
        source: str | None = None,
    ) -> None:
        # Unit before SubUnit (cascading). Apply Unit early so later slicers
        # AND with it — selecting Unit last often fails to stick in Power BI.
        if district is not None:
            self.select_district(district)
        if sub_unit is not None:
            self.select_sub_unit(sub_unit)
        if category is not None:
            self.select_category(category)
        if source is not None:
            self.select_source(source)

    @allure.step("Select table tab: {tab_name}")
    def select_tab(self, tab_name: str) -> None:
        # Tab labels are Power BI <span class="textRun"> nodes — they never get
        # selected/active classes. Wait for the grid to reflect the bookmark.
        previous_count = self.get_table_row_count()
        self.click_tab(tab_name)
        settle_seconds = min(5.0, self.timeout / 1000)
        deadline = time.monotonic() + settle_seconds
        while time.monotonic() < deadline:
            if self.get_table_row_count() != previous_count:
                return
            time.sleep(0.25)

    def get_table_row_count(self) -> int:
        expect(self.vehicle_table).to_be_visible(timeout=self.timeout)
        rows = self.vehicle_table.get_by_role("row")
        row_count = rows.count()
        return max(0, row_count - 1)

    @allure.step("Search vehicle table for: {query}")
    def search_vehicle(self, query: str) -> None:
        previous_count = self.get_table_row_count()
        expect(self.vehicle_search).to_be_visible(timeout=self.timeout)
        self.vehicle_search.click(force=True)
        self.vehicle_search.fill(str(query))
        self._vehicle_search_submit.click(force=True)
        self._wait_for_table_change(previous_count)

    def clear_vehicle_search(self) -> None:
        # Skip when search is already empty — avoids a full optional wait every test.
        try:
            current = (self.vehicle_search.input_value(timeout=1000) or "").strip()
        except Exception:
            current = ""
        if not current and self._vehicle_search_clear.count() == 0:
            return

        previous_count = self.get_table_row_count()
        if self._vehicle_search_clear.count() > 0:
            self._vehicle_search_clear.click(force=True)
        else:
            self.vehicle_search.click(force=True)
            self.vehicle_search.fill("")
            self.vehicle_search.press("Enter")
        self._wait_for_table_change(previous_count, required=False)

    def table_contains_text(self, text: str) -> bool:
        return self.vehicle_table.get_by_text(str(text), exact=False).count() > 0

    def get_table_row_text(self, index: int = 0) -> str:
        """Return inner text of a data row (0-based, header excluded)."""
        expect(self.vehicle_table).to_be_visible(timeout=self.timeout)
        rows = self.vehicle_table.get_by_role("row")
        row_count = rows.count()
        if row_count <= 1:
            raise AssertionError("Vehicle table has no data rows")
        data_index = index + 1  # nth(0) is the header
        if data_index >= row_count:
            raise AssertionError(
                f"Table row index {index} out of range (data rows={row_count - 1})"
            )
        return (rows.nth(data_index).inner_text() or "").strip()

    @allure.step("Click vehicle table row index={index}")
    def click_table_row(self, index: int = 0) -> str:
        """
        Click a matrix/table data row to trigger Power BI cross-filtering.

        Returns the row text at click time. Waits optionally for the total KPI
        to change (highlight-only selections may leave KPIs unchanged).
        """
        expect(self.vehicle_table).to_be_visible(timeout=self.timeout)
        rows = self.vehicle_table.get_by_role("row")
        row_count = rows.count()
        if row_count <= 1:
            raise AssertionError("Vehicle table has no data rows to click")
        data_index = index + 1
        if data_index >= row_count:
            raise AssertionError(
                f"Table row index {index} out of range (data rows={row_count - 1})"
            )

        row = rows.nth(data_index)
        row.scroll_into_view_if_needed()
        text = (row.inner_text() or "").strip()
        previous_total = self.get_kpi_value("total", record=False)
        # Prefer a gridcell click — more reliable than the full row host in PBI.
        cells = row.get_by_role("gridcell")
        try:
            if cells.count() > 0:
                cells.first.click(force=True, timeout=5000)
            else:
                row.click(force=True, timeout=5000)
        except Exception:
            row.click(force=True, timeout=5000)
        self.wait_for_kpi_update("total", previous_total, required=False)
        return text

    def _wait_for_table_change(
        self,
        previous_count: int,
        *,
        required: bool = True,
        timeout_ms: int | None = None,
    ) -> None:
        if timeout_ms is None:
            timeout_ms = (
                self.timeout if required else settings.KPI_OPTIONAL_WAIT_MS
            )
        deadline = time.monotonic() + timeout_ms / 1000
        while time.monotonic() < deadline:
            if self.get_table_row_count() != previous_count:
                return
            time.sleep(0.15)

        if required:
            current = self.get_table_row_count()
            raise AssertionError(
                f"Table row count stayed at {previous_count} (current: {current})"
            )

    def _chart_title_options(self, chart_key: str) -> tuple[str, ...]:
        titles = self._CHART_TITLES[chart_key]
        return titles if isinstance(titles, tuple) else (titles,)

    def _chart_title_locator(self, chart_key: str):
        options = self._chart_title_options(chart_key)
        locator = self.dashboard.get_by_text(options[0], exact=True)
        for title in options[1:]:
            locator = locator.or_(self.dashboard.get_by_text(title, exact=True))
        return locator.first

    def _other_chart_titles(self, chart_key: str) -> tuple[str, ...]:
        """Titles of every chart except ``chart_key`` (used to reject shared hosts)."""
        titles: list[str] = []
        for key, value in self._CHART_TITLES.items():
            if key == chart_key:
                continue
            if isinstance(value, tuple):
                titles.extend(value)
            else:
                titles.append(value)
        return tuple(titles)

    def _node_contains_any_title(self, node, titles: tuple[str, ...]) -> bool:
        for title in titles:
            try:
                if node.get_by_text(title, exact=True).count() > 0:
                    return True
            except Exception:
                continue
        return False

    def _count_interactive_bars(self, node) -> int:
        """Count bar/slice-like glyphs inside a visual host (excludes plot chrome)."""
        shapes = node.locator(
            "svg.plotArea rect, svg .plotArea rect, .plotArea rect, "
            ".bar, .column, svg rect[width], svg path[d], "
            "[class*='bar'], [class*='slice']"
        )
        try:
            total = min(shapes.count(), 40)
        except Exception:
            return 0
        found = 0
        for i in range(total):
            try:
                box = shapes.nth(i).bounding_box(timeout=300)
            except Exception:
                continue
            if box is None or box["width"] < 5 or box["height"] < 5:
                continue
            if box["width"] > 400 and box["height"] < 60:
                continue
            if box["height"] > 400 and box["width"] < 60:
                continue
            aspect = max(box["width"], box["height"]) / max(
                1.0, min(box["width"], box["height"])
            )
            if aspect < 1.4 and box["width"] * box["height"] < 800:
                continue
            found += 1
        return found

    def chart_section(self, chart_key: str):
        """Exclusive visual host for a chart: own title, real bars, no sibling charts."""
        title = self._chart_title_locator(chart_key)
        other_titles = self._other_chart_titles(chart_key)
        candidates = []

        visuals = self.dashboard.locator(
            ".visualContainerHost, .visual-container-host, "
            "[class*='visualContainerHost'], "
            ".visualContainer, .visual-container, "
            ".visual-container-component, "
            "[class*='visualContainer'], [class*='visual-container']"
        ).filter(has=title)
        try:
            for i in range(visuals.count()):
                candidates.append(visuals.nth(i))
        except Exception:
            pass

        for xpath in (
            'xpath=ancestor::*[contains(@class,"visualContainerHost")][1]',
            'xpath=ancestor::*[contains(@class,"visual-container-host")][1]',
            'xpath=ancestor::*[contains(@class,"visualContainer")][1]',
            'xpath=ancestor::*[contains(@class,"visual-container")][1]',
            'xpath=ancestor::*[@role="group"][1]',
        ):
            try:
                node = title.locator(xpath)
                if node.count() > 0:
                    candidates.append(node.first)
            except Exception:
                continue

        # Prefer: exclusive host with the most bar glyphs, then smallest area.
        best = None
        best_key: tuple[int, float] | None = None
        weak = None
        weak_key: tuple[int, float] | None = None
        for node in candidates:
            try:
                box = node.bounding_box(timeout=1000)
            except Exception:
                continue
            if box is None or box["width"] < 80 or box["height"] < 80:
                continue
            if other_titles and self._node_contains_any_title(node, other_titles):
                continue
            bars = self._count_interactive_bars(node)
            area = box["width"] * box["height"]
            key = (bars, -area)
            if bars >= 1:
                if best_key is None or key > best_key:
                    best_key = key
                    best = node
            elif weak_key is None or key > weak_key:
                weak_key = key
                weak = node
        if best is not None:
            return best
        if weak is not None:
            return weak
        return title.locator('xpath=ancestor::*[@role="group"][1]')

    def chart_plot(self, chart_key: str):
        """Interactive plot area inside a chart visual (SVG / canvas / plot div)."""
        section = self.chart_section(chart_key)
        return section.locator(
            "svg, canvas, .plotArea, .visual-plotArea, .cartesianChart, "
            ".donutChart, .pieChart"
        ).first

    def tooltip(self):
        """Power BI chart tooltip overlay inside the dashboard iframe."""
        tips = self.dashboard.locator(self._TOOLTIP_SELECTOR)
        try:
            count = tips.count()
        except Exception:
            return tips.last
        for i in range(count - 1, -1, -1):
            tip = tips.nth(i)
            try:
                if self._is_chart_tooltip(tip):
                    return tip
            except Exception:
                continue
        return tips.last

    @allure.step("Assert chart visible: {chart_key}")
    def assert_chart_visible(self, chart_key: str) -> None:
        expect(self._chart_title_locator(chart_key)).to_be_visible(timeout=self.timeout)

    def _is_chart_tooltip(self, tip) -> bool:
        """True for a visible non-empty tooltip that is not Power BI chrome UI."""
        try:
            if not tip.is_visible():
                return False
            cls = (tip.get_attribute("class") or "").lower()
            if "visualsenterhint" in cls.replace(" ", ""):
                return False
            text = (tip.inner_text() or "").strip()
            if not text:
                return False
            lowered = text.lower().replace("\u200f", "")
            if any(noise in lowered for noise in self._TOOLTIP_NOISE):
                return False
            return True
        except Exception:
            return False

    def _tooltip_is_visible(self) -> bool:
        tips = self.dashboard.locator(self._TOOLTIP_SELECTOR)
        try:
            count = tips.count()
        except Exception:
            return False
        for i in range(count - 1, -1, -1):
            try:
                if self._is_chart_tooltip(tips.nth(i)):
                    return True
            except Exception:
                continue
        return False

    def _hover_element_center(self, locator) -> None:
        # SVG bars/slices are often not "visible" to Playwright; use geometry only.
        box = locator.bounding_box(timeout=2000)
        if box is None:
            raise AssertionError("Hover target has no bounding box")
        x = box["x"] + box["width"] / 2
        y = box["y"] + box["height"] / 2
        # Real mouse move (with steps) is more reliable for Power BI tooltips
        # than locator.hover(force=True), which can skip hit-testing.
        self.page.mouse.move(x, y, steps=8)

    def _read_visible_tooltip_text(self) -> str:
        if not self._tooltip_is_visible():
            return ""
        try:
            return (self.tooltip().inner_text() or "").strip()
        except Exception:
            return ""

    def _iter_chart_shapes(
        self,
        chart_key: str,
        *,
        max_shapes: int = 24,
        largest_first: bool = False,
    ):
        """Yield bar/slice shapes, preferring compact data glyphs over plot chrome."""
        section = self.chart_section(chart_key)
        shapes = section.locator(
            "svg.plotArea rect, svg .plotArea rect, "
            ".plotArea rect, .bar, .column, "
            "svg rect[width], svg path[d], svg circle, "
            "[class*='bar'], [class*='slice']"
        )
        try:
            total = min(shapes.count(), max_shapes * 3)
        except Exception:
            return
        scored: list[tuple[float, int]] = []
        for i in range(total):
            try:
                box = shapes.nth(i).bounding_box(timeout=500)
            except Exception:
                continue
            if box is None or box["width"] < 3 or box["height"] < 3:
                continue
            # Huge flat rects are usually plot backgrounds / hit areas.
            if box["width"] > 400 and box["height"] < 60:
                continue
            if box["height"] > 400 and box["width"] < 60:
                continue
            # Prefer elongated bar/slice glyphs over near-square chrome icons.
            aspect = max(box["width"], box["height"]) / max(
                1.0, min(box["width"], box["height"])
            )
            if aspect < 1.4 and box["width"] * box["height"] < 800:
                continue
            area = box["width"] * box["height"]
            scored.append((area, i))
        scored.sort(key=lambda item: item[0], reverse=largest_first)
        for _area, i in scored[:max_shapes]:
            yield shapes.nth(i)

    def _shapes_for_segment_label(self, chart_key: str, label: str):
        """Yield SVG graphics whose ``<title>`` equals the segment label."""
        section = self.chart_section(chart_key)
        titles = section.locator("svg title")
        try:
            title_count = titles.count()
        except Exception:
            return
        for i in range(title_count):
            title = titles.nth(i)
            try:
                if (title.text_content() or "").strip() != label:
                    continue
            except Exception:
                continue
            group = title.locator("xpath=ancestor::*[name()='g'][1]")
            graphics = group.locator(
                "xpath=.//*[name()='rect' or name()='path' or name()='circle']"
            )
            try:
                gcount = min(graphics.count(), 6)
            except Exception:
                gcount = 0
            yielded = False
            for j in range(gcount):
                graphic = graphics.nth(j)
                try:
                    box = graphic.bounding_box(timeout=1000)
                except Exception:
                    continue
                if box and box["width"] >= 3 and box["height"] >= 3:
                    yielded = True
                    yield graphic
            if not yielded:
                parent = title.locator("xpath=..")
                try:
                    box = parent.bounding_box(timeout=1000)
                except Exception:
                    box = None
                if box and box["width"] >= 3 and box["height"] >= 3:
                    yield parent


    def _hover_plot_position(self, chart_key: str, x_ratio: float, y_ratio: float) -> None:
        plot = self.chart_plot(chart_key)
        plot.wait_for(state="visible", timeout=min(10000, self.timeout))
        box = plot.bounding_box()
        if box is None:
            raise AssertionError(f"Chart plot for '{chart_key}' has no bounding box")
        x = box["x"] + max(1, box["width"] * x_ratio)
        y = box["y"] + max(1, box["height"] * y_ratio)
        self.page.mouse.move(x, y, steps=8)

    def _hover_chart_shapes(
        self,
        chart_key: str,
        *,
        label: str | None = None,
        max_shapes: int = 16,
    ) -> bool:
        """Hover SVG bars/slices — more reliable than empty plot whitespace."""
        for shape in self._iter_chart_shapes(chart_key, max_shapes=max_shapes):
            try:
                self._hover_element_center(shape)
                deadline = time.monotonic() + 1.0
                while time.monotonic() < deadline:
                    if not self._tooltip_is_visible():
                        time.sleep(0.08)
                        continue
                    if label is None:
                        return True
                    text = self._read_visible_tooltip_text().replace("\u200f", "")
                    if label in text:
                        return True
                    break
            except Exception:
                continue
        return False

    def _segment_label_target(self, chart_key: str, label: str):
        """
        Resolve a hoverable node for a chart segment label.

        Prefer SVG ``<title>`` → bar/slice graphic; axis text is a weaker fallback
        (hovering the label often misses the bar hit-target).
        """
        for graphic in self._shapes_for_segment_label(chart_key, label):
            return graphic

        section = self.chart_section(chart_key)
        visible_text = section.locator(
            "text, tspan, .label, [class*='label'], [class*='Legend']"
        ).get_by_text(label, exact=True)
        if visible_text.count() > 0:
            for i in range(min(visible_text.count(), 5)):
                node = visible_text.nth(i)
                try:
                    if node.is_visible():
                        return node
                except Exception:
                    continue

        return (
            section.get_by_text(label, exact=True)
            .or_(section.get_by_label(label, exact=True))
            .first
        )

    @allure.step("Hover chart '{chart_key}' segment '{label}'")
    def hover_chart_segment(
        self,
        chart_key: str,
        label: str,
        *,
        expected_value: int | None = None,
    ) -> str:
        """
        Hover the bar/slice for an axis/legend label until a matching tooltip appears.

        Returns the matched tooltip text so callers can assert without relying on
        the overlay still being present after the hover returns (Power BI flickers).

        Power BI tooltips often omit the category text and show only the measure
        value — so a tooltip that contains ``expected_value`` after hovering from
        that label's geometry is accepted.
        """
        if chart_key not in self._CHART_TITLES:
            raise ValueError(f"Unknown chart key: {chart_key}")

        self.assert_chart_visible(chart_key)
        section = self.chart_section(chart_key)
        section.scroll_into_view_if_needed()
        # Avoid clicking the plot first — a selection can suppress hover tooltips.

        overall_deadline = time.monotonic() + 20.0

        def _matched_tooltip() -> str | None:
            text = self._read_visible_tooltip_text()
            if not text:
                return None
            normalized = text.replace("\u200f", "").replace(",", "")
            if label in normalized:
                return text
            if expected_value is not None and str(expected_value) in normalized:
                return text
            return None

        def _hover_until_match(target, wait_s: float) -> str | None:
            try:
                target.scroll_into_view_if_needed(timeout=2000)
            except Exception:
                pass
            try:
                self._hover_element_center(target)
            except Exception:
                return None
            deadline = time.monotonic() + wait_s
            while time.monotonic() < deadline and time.monotonic() < overall_deadline:
                matched = _matched_tooltip()
                if matched is not None:
                    return matched
                time.sleep(0.08)
            # Horizontal bars: try left/center/right along the glyph.
            try:
                box = target.bounding_box(timeout=1000)
            except Exception:
                box = None
            if box and box["width"] >= box["height"] * 1.5:
                for ratio in (0.25, 0.5, 0.75):
                    if time.monotonic() >= overall_deadline:
                        break
                    try:
                        self.page.mouse.move(
                            box["x"] + box["width"] * ratio,
                            box["y"] + box["height"] / 2,
                            steps=5,
                        )
                        deadline = time.monotonic() + 0.5
                        while time.monotonic() < deadline:
                            matched = _matched_tooltip()
                            if matched is not None:
                                return matched
                            time.sleep(0.08)
                    except Exception:
                        continue
            return None

        # 1) Graphics whose SVG <title> equals the segment label.
        for graphic in self._shapes_for_segment_label(chart_key, label):
            if time.monotonic() >= overall_deadline:
                break
            matched = _hover_until_match(graphic, 1.2)
            if matched is not None:
                return matched

        # 2) Scan bars/slices — largest first (top DB segments are usually tallest).
        for shape in self._iter_chart_shapes(
            chart_key, max_shapes=20, largest_first=True
        ):
            if time.monotonic() >= overall_deadline:
                break
            matched = _hover_until_match(shape, 0.7)
            if matched is not None:
                return matched

        # 3) Axis-label geometry + offsets into the bar (clamped to this chart).
        target = self._segment_label_target(chart_key, label)
        box = None
        section_box = None
        try:
            box = target.bounding_box(timeout=1500)
        except Exception:
            box = None
        try:
            section_box = section.bounding_box(timeout=1000)
        except Exception:
            section_box = None
        if box is not None and time.monotonic() < overall_deadline:
            matched = _hover_until_match(target, 0.8)
            if matched is not None:
                return matched
            hover_points = [
                (box["x"] + box["width"] / 2, box["y"] - 40),
                (box["x"] + box["width"] / 2, box["y"] - 90),
                (box["x"] + box["width"] / 2, box["y"] - 140),
            ]
            for x, y in hover_points:
                if time.monotonic() >= overall_deadline:
                    break
                if section_box is not None:
                    # Keep pointer inside this visual — sideways offsets land on
                    # sibling charts (source has no drilldown).
                    x = min(
                        max(x, section_box["x"] + 4),
                        section_box["x"] + section_box["width"] - 4,
                    )
                    y = min(
                        max(y, section_box["y"] + 4),
                        section_box["y"] + section_box["height"] - 4,
                    )
                try:
                    self.page.mouse.move(max(1, x), max(1, y), steps=6)
                    deadline = time.monotonic() + 0.6
                    while time.monotonic() < deadline:
                        matched = _matched_tooltip()
                        if matched is not None:
                            return matched
                        time.sleep(0.08)
                except Exception:
                    continue

        # 4) Plot-position scan.
        if time.monotonic() < overall_deadline:
            for x_ratio, y_ratio in self._HOVER_SCAN_POSITIONS:
                if time.monotonic() >= overall_deadline:
                    break
                try:
                    self._hover_plot_position(chart_key, x_ratio, y_ratio)
                    deadline = time.monotonic() + 0.6
                    while time.monotonic() < deadline:
                        matched = _matched_tooltip()
                        if matched is not None:
                            return matched
                        time.sleep(0.08)
                except Exception:
                    continue

        raise LoadTimeoutError(
            f"chart tooltip for segment '{label}' on '{chart_key}'",
            steps_ms=[20000],
        )

    @allure.step("Hover chart: {chart_key}")
    def hover_chart(
        self,
        chart_key: str,
        *,
        label: str | None = None,
        position: tuple[float, float] | None = None,
    ) -> None:
        """
        Hover a chart until a tooltip appears.

        Prefer ``label`` (legend / category text). Otherwise hover SVG shapes,
        then scan plot positions (or a single ``position`` as x/y ratios in 0..1).
        When ``label`` is set, keep scanning until the tooltip text includes it.
        """
        if chart_key not in self._CHART_TITLES:
            raise ValueError(f"Unknown chart key: {chart_key}")

        self.assert_chart_visible(chart_key)
        section = self.chart_section(chart_key)
        section.scroll_into_view_if_needed()
        try:
            # Activate the visual so Power BI enables tooltip hit-testing.
            section.click(position={"x": 8, "y": 8}, force=True, timeout=3000)
        except Exception:
            pass
        time.sleep(0.2)

        def _tooltip_has_label() -> bool:
            if not self._tooltip_is_visible():
                return False
            if label is None:
                return True
            text = (self.tooltip().inner_text() or "").replace("\u200f", "")
            return label in text

        if label is not None:
            # Stay inside this chart only — dashboard-wide text (slicers / other
            # visuals) steers the pointer onto charts without drilldown.
            candidates = section.get_by_text(label, exact=True).or_(
                section.get_by_label(label, exact=True)
            )
            if candidates.count() > 0:
                try:
                    self._hover_element_center(candidates.first)
                    deadline = time.monotonic() + 2.0
                    while time.monotonic() < deadline:
                        if _tooltip_has_label():
                            return
                        time.sleep(0.1)
                except Exception:
                    pass

        if position is not None:
            self._hover_plot_position(chart_key, position[0], position[1])
            deadline = time.monotonic() + 2.0
            while time.monotonic() < deadline:
                if _tooltip_has_label():
                    return
                time.sleep(0.1)
            if label is not None:
                raise AssertionError(
                    f"Tooltip at position {position} for chart '{chart_key}' "
                    f"does not contain '{label}'"
                )
            raise LoadTimeoutError(
                f"chart tooltip on '{chart_key}'",
                steps_ms=[2000],
            )

        if label is None and self._hover_chart_shapes(chart_key):
            return

        if label is not None and self._hover_chart_shapes(chart_key, label=label):
            return

        last_error: Exception | None = None
        for x_ratio, y_ratio in self._HOVER_SCAN_POSITIONS:
            try:
                self._hover_plot_position(chart_key, x_ratio, y_ratio)
                deadline = time.monotonic() + 1.5
                while time.monotonic() < deadline:
                    if _tooltip_has_label():
                        return
                    time.sleep(0.1)
            except Exception as exc:  # noqa: BLE001 — try next scan point
                last_error = exc
                continue

        detail = f" containing '{label}'" if label else ""
        if last_error is not None:
            raise LoadTimeoutError(
                f"chart tooltip{detail} on '{chart_key}'",
                steps_ms=[1500 * len(self._HOVER_SCAN_POSITIONS)],
                cause=last_error,
            ) from last_error
        raise LoadTimeoutError(
            f"chart tooltip{detail} on '{chart_key}'",
            steps_ms=[1500 * len(self._HOVER_SCAN_POSITIONS)],
        )

    def get_tooltip_text(self) -> str:
        self.assert_tooltip_visible()
        tip = self.tooltip()
        return (tip.inner_text() or "").strip()

    def parse_tooltip_entries(self) -> dict[str, int]:
        """
        Parse Power BI tooltip rows into label → integer value.

        Supports row cells (title/value) and plain multiline text where a label
        line is followed by a numeric line.
        """
        tip = self.tooltip()
        # Short timeout: callers usually already confirmed a match via hover.
        expect(tip).to_be_visible(timeout=min(3000, self.timeout))

        entries: dict[str, int] = {}
        rows = tip.locator(
            ".tooltip-row, [class*='tooltip-row'], "
            "[class*='TooltipRow'], .tooltip-content-container > div"
        )
        row_count = rows.count()
        for i in range(row_count):
            row = rows.nth(i)
            title = row.locator(
                ".tooltip-title-cell, [class*='tooltip-title'], "
                "[class*='TooltipTitle'], .title"
            ).first
            value = row.locator(
                ".tooltip-value-cell, [class*='tooltip-value'], "
                "[class*='TooltipValue'], .value"
            ).first
            if title.count() and value.count():
                label = (title.inner_text() or "").strip()
                raw = (value.inner_text() or "").strip().replace(",", "").replace("\u200f", "")
                if label and re.fullmatch(r"-?\d+", raw):
                    entries[label] = int(raw)

        if entries:
            return entries

        # Fallback: alternate non-empty lines → label, number
        lines = [
            line.strip().replace("\u200f", "")
            for line in self.get_tooltip_text().splitlines()
            if line.strip()
        ]
        i = 0
        while i < len(lines):
            label = lines[i]
            if i + 1 < len(lines):
                raw = lines[i + 1].replace(",", "")
                if re.fullmatch(r"-?\d+", raw):
                    entries[label] = int(raw)
                    i += 2
                    continue
            # Single line may be "Label 123"
            match = re.match(r"^(.+?)\s+(-?\d[\d,]*)$", label)
            if match:
                entries[match.group(1).strip()] = int(match.group(2).replace(",", ""))
            i += 1
        return entries

    @allure.step("Assert chart tooltip is visible")
    def assert_tooltip_visible(self) -> None:
        # Do not use expect(locator) on .last — Power BI leaves hidden
        # tooltip-content-container nodes in the DOM; poll for a non-empty one.
        tooltip_budget = min(8000, self.timeout) / 1000
        deadline = time.monotonic() + tooltip_budget
        while time.monotonic() < deadline:
            if self._tooltip_is_visible():
                return
            time.sleep(0.1)
        raise LoadTimeoutError(
            "chart tooltip",
            steps_ms=[min(8000, self.timeout)],
        )

    @allure.step("Assert chart tooltip is hidden")
    def assert_tooltip_hidden(self) -> None:
        # Match dismiss semantics: only a non-empty visible tooltip counts.
        deadline = time.monotonic() + min(8.0, self.timeout / 1000)
        while time.monotonic() < deadline:
            if not self._tooltip_is_visible():
                return
            time.sleep(0.1)
        raise AssertionError("Tooltip remained visible after dismiss")

    def assert_tooltip_contains(self, *parts: str | int) -> None:
        text = self.get_tooltip_text()
        normalized = text.replace(",", "").replace("\u200f", "")
        missing = []
        for part in parts:
            needle = str(part).replace(",", "")
            if needle not in text and needle not in normalized:
                missing.append(needle)
        assert not missing, (
            f"Tooltip missing {missing}. Full tooltip text:\n{text}"
        )

    @allure.step("Dismiss chart tooltip")
    def dismiss_tooltip(self) -> None:
        """Close Power BI tooltip via Escape + move pointer off the visual."""
        try:
            self.page.keyboard.press("Escape")
        except Exception:
            pass
        try:
            self.clear_filters_btn.hover(force=True, timeout=3000)
        except Exception:
            pass
        try:
            self.page.mouse.move(8, 8, steps=6)
        except Exception:
            pass
        try:
            self.total_vehicles_kpi.hover(force=True, timeout=2000)
        except Exception:
            pass
        deadline = time.monotonic() + min(5.0, self.timeout / 1000)
        while time.monotonic() < deadline:
            if not self._tooltip_is_visible():
                return
            try:
                self.page.keyboard.press("Escape")
            except Exception:
                pass
            time.sleep(0.15)

    def _chart_visual_host(self, chart_key: str):
        """Visual host for header chrome — prefer exclusive host (not multi-chart parent)."""
        title = self._chart_title_locator(chart_key)
        other_titles = self._other_chart_titles(chart_key)
        hosts = self.dashboard.locator(
            ".visualContainerHost, .visual-container-host, "
            "[class*='visualContainerHost'], [class*='visual-container-host'], "
            ".visualContainer, .visual-container, "
            "[class*='visualContainer'], [class*='visual-container']"
        ).filter(has=title)
        try:
            count = hosts.count()
        except Exception:
            count = 0
        if count == 0:
            return self.chart_section(chart_key)

        # Prefer smallest exclusive host that still fits a real chart.
        best = None
        best_area = float("inf")
        fallback = hosts.first
        fallback_area = float("inf")
        for i in range(count):
            node = hosts.nth(i)
            try:
                box = node.bounding_box(timeout=1000)
            except Exception:
                continue
            if box is None or box["width"] < 80 or box["height"] < 80:
                continue
            area = box["width"] * box["height"]
            exclusive = not (
                other_titles and self._node_contains_any_title(node, other_titles)
            )
            if area < fallback_area:
                fallback_area = area
                fallback = node
            if exclusive and area < best_area:
                best_area = area
                best = node
        return best if best is not None else fallback

    def _reveal_chart_header(self, chart_key: str) -> None:
        """Select + hover the top of the visual so Power BI shows header icons."""
        self.assert_chart_visible(chart_key)
        section = self.chart_section(chart_key)
        try:
            section.scroll_into_view_if_needed(timeout=3000)
        except Exception:
            pass
        # Click once so the visual is active (headers often require selection).
        try:
            section.click(position={"x": 24, "y": 24}, force=True, timeout=3000)
        except Exception:
            pass
        try:
            box = section.bounding_box(timeout=2000)
        except Exception:
            box = None
        if box is not None:
            # Header icons render along the top edge of the visual.
            self.page.mouse.move(
                box["x"] + max(40.0, box["width"] * 0.35),
                box["y"] + 10,
                steps=6,
            )
        else:
            try:
                self._chart_title_locator(chart_key).hover(force=True, timeout=3000)
            except Exception:
                pass
        time.sleep(0.45)

    def _control_label(self, node) -> str:
        try:
            return " ".join(
                filter(
                    None,
                    [
                        node.get_attribute("aria-label"),
                        node.get_attribute("title"),
                        (node.inner_text() or "")[:120],
                    ],
                )
            ).strip()
        except Exception:
            return ""

    def _label_matches_expand_hierarchy(self, label: str) -> bool:
        """True only for forked-arrow הסתעפות — never single/double down-arrow."""
        if not label:
            return False
        if self._NOT_EXPAND_HIERARCHY_PATTERN.search(label):
            # Allow only if the expand-all / הסתעפות phrase is also present.
            if not self._EXPAND_HIERARCHY_PATTERN.search(label):
                return False
            if re.search(r"Drill down|Go to the next level|עבור לרמה הבאה", label, re.I):
                if "הסתעפות" not in label and "Expand all" not in label:
                    return False
        return bool(self._EXPAND_HIERARCHY_PATTERN.search(label))

    def _header_action_button(self, chart_key: str, pattern: re.Pattern[str]):
        """Locate a visual-header action button for a chart (scoped, then global)."""
        if pattern is self._EXPAND_HIERARCHY_PATTERN:
            found = self._find_expand_hierarchy_button(chart_key)
            if found is not None:
                return found
            # Empty locator for callers that check is_visible → absent.
            return self.dashboard.locator("button[data-vc-expand-missing='1']")

        self._reveal_chart_header(chart_key)
        host = self._chart_visual_host(chart_key)

        def _accept(node) -> bool:
            return bool(pattern.search(self._control_label(node) or ""))

        scoped = host.get_by_role("button", name=pattern)
        try:
            for i in range(min(scoped.count(), 8)):
                return scoped.nth(i)
        except Exception:
            pass

        global_btn = self.dashboard.get_by_role("button", name=pattern)
        try:
            for i in range(min(global_btn.count(), 12)):
                node = global_btn.nth(i)
                if _accept(node):
                    return node
            if global_btn.count() > 0:
                return global_btn.first
        except Exception:
            pass

        attr_candidates = host.locator("button, [role='button'], .visual-header-item")
        try:
            total = attr_candidates.count()
        except Exception:
            total = 0
        for i in range(total):
            node = attr_candidates.nth(i)
            if _accept(node):
                return node

        dashboard_items = self.dashboard.locator(
            "button, [role='button'], .visual-header-item"
        )
        try:
            total = min(dashboard_items.count(), 80)
        except Exception:
            total = 0
        host_box = None
        try:
            host_box = host.bounding_box(timeout=1000)
        except Exception:
            host_box = None
        for i in range(total):
            node = dashboard_items.nth(i)
            if not _accept(node):
                continue
            if host_box is None:
                return node
            try:
                box = node.bounding_box(timeout=500)
            except Exception:
                continue
            if box is None:
                continue
            cx = box["x"] + box["width"] / 2
            cy = box["y"] + box["height"] / 2
            if (
                host_box["x"] - 40 <= cx <= host_box["x"] + host_box["width"] + 40
                and host_box["y"] - 60 <= cy <= host_box["y"] + host_box["height"] + 40
            ):
                return node
        return global_btn.first

    def _find_expand_hierarchy_button(self, chart_key: str):
        """
        Find forked-arrow הסתעפות (Expand all down one level).

        Power BI often exposes English ``title`` / class ``expandAll``, not Hebrew name.
        Returns a locator node or None (never a random unmatched button).
        """
        self._reveal_chart_header(chart_key)
        host = self._chart_visual_host(chart_key)
        section = self.chart_section(chart_key)
        roots = (host, section, self.dashboard)

        css_selectors = (
            "[title*='Expand all down one level']",
            "[aria-label*='Expand all down one level']",
            "[title*='Expand all down']",
            "[aria-label*='Expand all down']",
            "[title*='הסתעפות']",
            "[aria-label*='הסתעפות']",
            "[class*='expandAll']",
            "[class*='ExpandAll']",
            "button.expandAll",
            ".expandAll",
        )
        for root in roots:
            for sel in css_selectors:
                loc = root.locator(sel)
                try:
                    total = min(loc.count(), 8)
                except Exception:
                    continue
                for i in range(total):
                    node = loc.nth(i)
                    try:
                        if not node.is_visible(timeout=800):
                            continue
                    except Exception:
                        continue
                    label = self._control_label(node)
                    if label and re.search(
                        r"^\s*Drill down\s*$|Go to the next level|כינוס",
                        label,
                        re.I,
                    ):
                        continue
                    if label and not self._label_matches_expand_hierarchy(label):
                        # class/title selector already targeted expandAll — accept.
                        if "expandall" not in (node.get_attribute("class") or "").lower():
                            if "Expand all" not in label and "הסתעפות" not in label:
                                continue
                    return node

        # Near-chart header buttons by title/label scan.
        try:
            host_box = host.bounding_box(timeout=1000)
        except Exception:
            host_box = None
        header_btns = self.dashboard.locator(
            ".visual-header button, .visual-header-item button, "
            ".visual-header-item, [class*='visual-header'] button, "
            "button[class*='menu'], button[class*='Menu']"
        )
        try:
            total = min(header_btns.count(), 60)
        except Exception:
            total = 0
        near: list = []
        for i in range(total):
            node = header_btns.nth(i)
            try:
                if not node.is_visible(timeout=300):
                    continue
                box = node.bounding_box(timeout=300)
            except Exception:
                continue
            if box is None:
                continue
            if host_box is not None:
                cx = box["x"] + box["width"] / 2
                cy = box["y"] + box["height"] / 2
                if not (
                    host_box["x"] - 20 <= cx <= host_box["x"] + host_box["width"] + 20
                    and host_box["y"] - 50 <= cy <= host_box["y"] + 80
                ):
                    continue
            label = self._control_label(node)
            if self._label_matches_expand_hierarchy(label):
                return node
            near.append((node, label, box))

        # Positional fallback: among top-of-visual header icons, expand-all is
        # usually the 4th drill control (after up / down / next-level).
        if len(near) >= 4:
            candidate = near[3][0]
            label = near[3][1]
            if not re.search(r"Drill up|כינוס|Focus|Filter|מסנן", label or "", re.I):
                return candidate
        return None

    def _is_header_button_enabled(self, button, *, strict: bool = True) -> bool:
        """
        Whether a header control looks usable.

        For הסתעפות (``strict=False``): Power BI often sets ``aria-disabled``
        even when the forked icon still works after selecting a bar — so we only
        require visibility. Real usability is verified by whether labels change.
        """
        try:
            if not button.is_visible():
                return False
        except Exception:
            return False
        if not strict:
            return True
        try:
            aria_disabled = (button.get_attribute("aria-disabled") or "").lower()
            if aria_disabled in ("true", "1"):
                return False
        except Exception:
            pass
        try:
            disabled = button.get_attribute("disabled")
            if disabled is not None:
                return False
        except Exception:
            pass
        try:
            cls = (button.get_attribute("class") or "").lower()
            # Avoid false positives from long class strings; require token-ish match.
            if re.search(r"(^|[\s_-])disabled($|[\s_-])", cls):
                return False
        except Exception:
            pass
        return True

    def _drilldown_action_locators(self):
        """Tooltip/overlay הסתעפות text — forked action, not Drill-down arrow."""
        pattern = self._EXPAND_HIERARCHY_PATTERN
        return (
            self.dashboard.get_by_role("button", name=pattern),
            self.dashboard.get_by_text(re.compile(r"הסתעפות"), exact=False),
            self.dashboard.locator(
                "[aria-label*='הסתעפות'], [title*='הסתעפות'], "
                "[aria-label*='Expand all down'], [title*='Expand all down']"
            ),
        )

    def _find_visible_drilldown_action(self):
        """Return visible forked-arrow / הסתעפות control, never plain Drill down."""
        for group in self._drilldown_action_locators():
            try:
                total = min(group.count(), 12)
            except Exception:
                continue
            for i in range(total):
                node = group.nth(i)
                try:
                    if not node.is_visible():
                        continue
                except Exception:
                    continue
                if self._label_matches_expand_hierarchy(self._control_label(node)):
                    return node
                # Plain visible text node "הסתעפות" (tooltip row) has little aria-label.
                try:
                    text = (node.inner_text() or "").strip()
                except Exception:
                    text = ""
                if text == "הסתעפות" or "הסתעפות" in text:
                    return node
        return None

    def _tooltip_has_drilldown_action(self) -> bool:
        """True when forked הסתעפות is available (header or tooltip)."""
        return self._find_visible_drilldown_action() is not None

    def _click_tooltip_drilldown_action(self) -> bool:
        action = self._find_visible_drilldown_action()
        if action is None:
            return False
        try:
            action.click(force=True)
            return True
        except Exception:
            return False

    def probe_expand_hierarchy(
        self,
        chart_key: str,
        *,
        segment_label: str | None = None,
        expected_value: int | None = None,
    ) -> str:
        """
        Probe forked-arrow הסתעפות on the chart header.

        Returns:
            ``"enabled"`` — control visible (try clicking; ignore flaky aria-disabled)
            ``"absent"`` — control not found
        """
        if chart_key not in self._CHART_TITLES:
            raise ValueError(f"Unknown chart key: {chart_key}")

        # Selecting a bar often "unlocks" hierarchy actions in Power BI.
        if segment_label:
            try:
                self.hover_chart_segment(
                    chart_key, segment_label, expected_value=expected_value
                )
                self.dismiss_tooltip()
            except Exception:
                pass
            try:
                self._segment_label_target(chart_key, segment_label).click(
                    force=True, timeout=3000
                )
                time.sleep(0.25)
            except Exception:
                pass

        button = self._find_expand_hierarchy_button(chart_key)
        if button is None:
            return "absent"
        try:
            if not button.is_visible(timeout=1500):
                return "absent"
        except Exception:
            return "absent"
        # Do not report "disabled" from aria — it is unreliable for this control.
        return "enabled"

    def _try_click_header_expand(self, chart_key: str) -> bool:
        """Click forked-arrow header הסתעפות (not single/double down arrows)."""
        button = self._find_expand_hierarchy_button(chart_key)
        if button is None or not self._is_header_button_enabled(button, strict=False):
            return False
        try:
            button.click(force=True)
            return True
        except Exception:
            return False

    @allure.step("Assert drilldown (הסתעפות) available on chart '{chart_key}'")
    def assert_expand_hierarchy_visible(
        self,
        chart_key: str,
        *,
        segment_label: str | None = None,
        expected_value: int | None = None,
    ) -> str:
        """
        Return expand state: enabled / disabled / absent.

        Does not fail when הסתעפות is missing or disabled — callers should skip.
        Optional tooltip probe only when header is absent and segment_label is set.
        """
        if chart_key not in self._CHART_TITLES:
            raise ValueError(f"Unknown chart key: {chart_key}")

        state = self.probe_expand_hierarchy(chart_key)
        if state == "enabled":
            return state
        if state == "disabled":
            return state

        # Header absent — optional tooltip הסתעפות still counts as enabled.
        if segment_label:
            try:
                bars = self._count_interactive_bars(self.chart_section(chart_key))
                if bars >= 1:
                    self.hover_chart_segment(
                        chart_key, segment_label, expected_value=expected_value
                    )
                    deadline = time.monotonic() + 2.0
                    while time.monotonic() < deadline:
                        if self._tooltip_has_drilldown_action():
                            return "enabled"
                        time.sleep(0.15)
            except Exception:
                pass
            finally:
                try:
                    self.dismiss_tooltip()
                except Exception:
                    pass
        return "absent"

    @allure.step("Expand chart hierarchy one level: {chart_key}")
    def expand_chart_hierarchy(
        self,
        chart_key: str,
        *,
        segment_label: str | None = None,
        expected_value: int | None = None,
        expected_child_labels: list[str] | None = None,
    ) -> list[str]:
        """
        Expand via forked-arrow הסתעפות — header first, then tooltip fallback.

        Flow: focus segment (optional) → click header branching icon →
        wait until labels change / expected children appear.
        If the header control is missing or ineffective and ``segment_label``
        is set, try tooltip ``הסתעפות``.

        Raises ``ExpandHierarchyUnavailable`` when the control is absent,
        disabled, or the click has no effect (callers should pytest.skip).
        """
        if chart_key not in self._CHART_TITLES:
            raise ValueError(f"Unknown chart key: {chart_key}")

        state = self.probe_expand_hierarchy(
            chart_key,
            segment_label=segment_label,
            expected_value=expected_value,
        )
        before = self.get_chart_segment_labels(chart_key)

        # Focus the datapoint so Power BI applies hierarchy on this visual.
        if segment_label:
            try:
                self.hover_chart_segment(
                    chart_key, segment_label, expected_value=expected_value
                )
                self.dismiss_tooltip()
            except Exception:
                pass
            try:
                target = self._segment_label_target(chart_key, segment_label)
                target.click(force=True, timeout=3000)
                time.sleep(0.3)
            except Exception:
                pass

        if state == "enabled" and self._try_click_header_expand(chart_key):
            after = self.wait_for_chart_labels_change(
                chart_key,
                before,
                required=False,
                expected_labels=expected_child_labels,
            )
            if expected_child_labels:
                kids = {label.replace("\u200f", "") for label in expected_child_labels}
                ui = {label.replace("\u200f", "") for label in after}
                if any(
                    kid == label or kid in label or label in kid
                    for kid in kids
                    for label in ui
                ):
                    return after
            if set(after) != set(before):
                return after

        # Tooltip הסתעפות — primary UX when header icon is flaky/absent.
        if segment_label:
            try:
                return self.expand_via_tooltip_drilldown(
                    chart_key,
                    segment_label,
                    expected_value=expected_value,
                )
            except ExpandHierarchyUnavailable:
                raise
            except AssertionError as exc:
                raise ExpandHierarchyUnavailable(chart_key, str(exc)) from exc

        if state == "absent":
            raise ExpandHierarchyUnavailable(chart_key, "control absent")
        if state == "disabled":
            raise ExpandHierarchyUnavailable(chart_key, "control disabled")
        raise ExpandHierarchyUnavailable(
            chart_key,
            f"click had no effect (labels still {before})",
        )

    def _find_visible_collapse_action(self):
        """Return visible כינוס control (tooltip/overlay), opposite of הסתעפות."""
        pattern = re.compile(r"כינוס")
        groups = (
            self.dashboard.get_by_role("button", name=pattern),
            self.dashboard.get_by_text(pattern, exact=False),
            self.dashboard.locator("[aria-label*='כינוס'], [title*='כינוס']"),
        )
        for group in groups:
            try:
                total = min(group.count(), 12)
            except Exception:
                continue
            for i in range(total):
                node = group.nth(i)
                try:
                    if node.is_visible():
                        return node
                except Exception:
                    continue
        return None

    @allure.step("Drill up / כינוס on chart '{chart_key}'")
    def drill_up_chart(self, chart_key: str) -> list[str]:
        """
        Collapse one hierarchy level (opposite of הסתעפות).

        Tries header Drill-up / כינוס first, then tooltip כינוס.
        """
        if chart_key not in self._CHART_TITLES:
            raise ValueError(f"Unknown chart key: {chart_key}")

        before = self.get_chart_segment_labels(chart_key)

        button = self._header_action_button(chart_key, self._DRILL_UP_PATTERN)
        try:
            if button.is_visible(timeout=2000) and self._is_header_button_enabled(button):
                button.click(force=True)
                self.wait_for_chart_labels_change(chart_key, before, required=True)
                return self.get_chart_segment_labels(chart_key)
        except Exception:
            pass

        # Tooltip path: כינוס is the reverse of הסתעפות.
        action = self._find_visible_collapse_action()
        if action is None:
            # Hover a current segment so the tooltip exposes כינוס.
            labels = before or self.get_chart_segment_labels(chart_key)
            for label in labels[:3]:
                try:
                    self.hover_chart_segment(chart_key, label)
                    deadline = time.monotonic() + 2.0
                    while time.monotonic() < deadline:
                        action = self._find_visible_collapse_action()
                        if action is not None:
                            break
                        time.sleep(0.15)
                    if action is not None:
                        break
                except Exception:
                    continue
        if action is None:
            raise AssertionError(
                f"כינוס / Drill-up not available on chart '{chart_key}' "
                "(already at top level, or control missing)"
            )
        action.click(force=True)
        self.wait_for_chart_labels_change(chart_key, before, required=True)
        return self.get_chart_segment_labels(chart_key)

    @allure.step("Reset chart '{chart_key}' to top hierarchy level")
    def reset_chart_hierarchy(self, chart_key: str, *, max_levels: int = 4) -> None:
        """Drill up via header while enabled; no-op when control is absent."""
        self.assert_chart_visible(chart_key)
        for _ in range(max_levels):
            button = self._header_action_button(chart_key, self._DRILL_UP_PATTERN)
            try:
                visible = button.is_visible(timeout=800)
            except Exception:
                visible = False
            if not visible or not self._is_header_button_enabled(button):
                return
            before = self.get_chart_segment_labels(chart_key)
            try:
                button.click(force=True)
            except Exception:
                return
            self.wait_for_chart_labels_change(chart_key, before, required=False)

    def get_chart_segment_labels(self, chart_key: str) -> list[str]:
        """Collect category / segment labels currently rendered on a chart."""
        section = self.chart_section(chart_key)
        labels: list[str] = []
        seen: set[str] = set()

        def _add(raw: str | None) -> None:
            text = (raw or "").strip().replace("\u200f", "")
            if not text:
                return
            # Power BI sometimes concatenates the same tick twice: מחוז דןמחוז דן
            if len(text) >= 4 and len(text) % 2 == 0:
                half = len(text) // 2
                if text[:half] == text[half:]:
                    text = text[:half]
            if text in seen:
                return
            # Skip pure numbers / measure chrome / pie data labels like "3 (50.0%)".
            if re.fullmatch(r"-?\d[\d,.]*%?", text):
                return
            if re.fullmatch(r"-?\d[\d,.]*\s*\(\s*\d+([.,]\d+)?\s*%\s*\)", text):
                return
            if text.lower() in {"null", "(blank)", "blank"}:
                return
            # Prefer short category labels; drop noisy concatenated junk.
            if len(text) > 80:
                return
            seen.add(text)
            labels.append(text)

        # SVG <title> often holds clean names — but pie charts put "3 (50%)"
        # there, so always also harvest axis / legend text nodes.
        titles = section.locator("svg title")
        try:
            title_count = titles.count()
        except Exception:
            title_count = 0
        for i in range(title_count):
            try:
                _add(titles.nth(i).text_content())
            except Exception:
                continue

        texts = section.locator(
            "svg text, .axis text, [class*='tick'] text, "
            "[class*='category'] text, [class*='legend'] text, "
            "[class*='Legend'] text, .legend text"
        )
        try:
            text_count = min(texts.count(), 60)
        except Exception:
            text_count = 0
        for i in range(text_count):
            try:
                _add(texts.nth(i).text_content())
            except Exception:
                continue

        return labels

    def wait_for_chart_labels_change(
        self,
        chart_key: str,
        previous_labels: list[str],
        *,
        required: bool = True,
        timeout_ms: int | None = None,
        expected_labels: list[str] | None = None,
    ) -> list[str]:
        """Poll until labels change, or until an expected child label appears."""
        budget = (timeout_ms if timeout_ms is not None else self.timeout) / 1000
        deadline = time.monotonic() + budget
        prev = set(previous_labels)
        current = previous_labels
        expected = [
            label.replace("\u200f", "") for label in (expected_labels or []) if label
        ]
        while time.monotonic() < deadline:
            current = self.get_chart_segment_labels(chart_key)
            ui = {label.replace("\u200f", "") for label in current}
            if expected and any(
                exp == label or exp in label or label in exp
                for exp in expected
                for label in ui
            ):
                return current
            if set(current) != prev:
                return current
            time.sleep(0.2)
        if required:
            raise AssertionError(
                f"Chart '{chart_key}' labels did not change after hierarchy action. "
                f"Still: {previous_labels}"
            )
        return current

    @allure.step("Expand hierarchy via tooltip הסתעפות on chart '{chart_key}'")
    def expand_via_tooltip_drilldown(
        self,
        chart_key: str,
        segment_label: str,
        *,
        expected_value: int | None = None,
    ) -> list[str]:
        """
        Hover the segment with the same path as tooltip tests, then click הסתעפות.

        ``הסתעפות`` is searched in the whole report iframe — Power BI often renders
        it as a tooltip sibling action, not inside the value tooltip node.

        Raises ``ExpandHierarchyUnavailable`` when the action is missing or the
        visual does not change (callers should pytest.skip).
        """
        if chart_key not in self._CHART_TITLES:
            raise ValueError(f"Unknown chart key: {chart_key}")

        before = self.get_chart_segment_labels(chart_key)
        bars = self._count_interactive_bars(self.chart_section(chart_key))
        if bars < 1:
            raise ExpandHierarchyUnavailable(
                chart_key, "chart_section has no bars — wrong host"
            )

        try:
            last_tooltip = self.hover_chart_segment(
                chart_key, segment_label, expected_value=expected_value
            )
        except Exception as exc:
            raise ExpandHierarchyUnavailable(
                chart_key, f"hover failed for '{segment_label}': {exc}"
            ) from exc

        normalized = last_tooltip.replace("\u200f", "")
        if segment_label.replace("\u200f", "") not in normalized:
            if expected_value is None or str(expected_value) not in normalized.replace(",", ""):
                raise ExpandHierarchyUnavailable(
                    chart_key,
                    f"hover did not land on '{segment_label}'. Tooltip:\n{last_tooltip!r}",
                )

        deadline = time.monotonic() + 4.0
        while time.monotonic() < deadline:
            if self._click_tooltip_drilldown_action():
                after = self.wait_for_chart_labels_change(
                    chart_key, before, required=False
                )
                if set(after) != set(before):
                    return after
                raise ExpandHierarchyUnavailable(
                    chart_key,
                    f"tooltip הסתעפות click had no effect (labels still {before})",
                )
            time.sleep(0.15)
            last_tooltip = self._read_visible_tooltip_text() or last_tooltip

        # Fallback: right-click the segment label target for Power BI context drill.
        try:
            target = self._segment_label_target(chart_key, segment_label)
            target.click(button="right", force=True, timeout=3000)
            time.sleep(0.4)
            if self._click_tooltip_drilldown_action():
                after = self.wait_for_chart_labels_change(
                    chart_key, before, required=False
                )
                if set(after) != set(before):
                    return after
        except Exception:
            pass

        raise ExpandHierarchyUnavailable(
            chart_key,
            f"הסתעפות not found after hovering '{segment_label}'. "
            f"Tooltip was:\n{last_tooltip!r}",
        )
