"""Generic Power BI report shell: portal SSO, catalog, iframe, load timeouts."""

import re
import time
from datetime import datetime, timedelta

import allure
from playwright.sync_api import Locator, Page, expect

from browser_session import ensure_single_tab, wait_for_auth_popups_to_finish
from config.settings import settings
from pages.base_page import BasePage
from pages.errors import LoadTimeoutError
from reports.test_run_report import get_current_report


_LAST_REFRESH_PHRASE = "הדשבורד עודכן לאחרונה ב:"
_LAST_REFRESH_DATETIME_TOKEN = re.compile(
    r"(\d{1,4}[./-]\d{1,2}[./-]\d{1,4}"
    r"(?:\s+\d{1,2}:\d{2}(?::\d{2})?(?:\s*[AaPp][Mm])?)?)"
)
_LAST_REFRESH_FORMATS = (
    "%d/%m/%Y %H:%M:%S",
    "%d/%m/%Y %H:%M",
    "%d/%m/%Y %I:%M:%S %p",
    "%d/%m/%Y %I:%M %p",
    "%m/%d/%Y %H:%M:%S",
    "%m/%d/%Y %H:%M",
    "%m/%d/%Y %I:%M:%S %p",
    "%m/%d/%Y %I:%M %p",
    "%d.%m.%Y %H:%M:%S",
    "%d.%m.%Y %H:%M",
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%dT%H:%M:%S",
    "%d/%m/%Y",
    "%m/%d/%Y",
    "%Y-%m-%d",
)


def _parse_last_refresh_datetime(raw: str) -> datetime | None:
    """Parse a last-refresh timestamp from captured caption text."""
    candidate = re.sub(r"\s+", " ", (raw or "").strip())
    if not candidate:
        return None
    token_match = _LAST_REFRESH_DATETIME_TOKEN.search(candidate)
    snippets = [candidate]
    if token_match:
        snippets.insert(0, token_match.group(1))
    for snippet in snippets:
        text = snippet.strip(" .,-;")
        for fmt in _LAST_REFRESH_FORMATS:
            try:
                return datetime.strptime(text, fmt)
            except ValueError:
                continue
    return None


class ReportShell(BasePage):
    """Layer 0 host. Domain pages override ready-state and post-navigate hooks."""

    def __init__(self, page: Page):
        super().__init__(page)
        self.url = ""

    LAST_REFRESH_PHRASE: str = _LAST_REFRESH_PHRASE

    def _report_ready_locator(self) -> Locator:
        raise NotImplementedError(
            "Domain page must override _report_ready_locator() "
            "with the visual that means this report is loaded."
        )

    def _last_refresh_phrase(self) -> str:
        """Freshness caption prefix to search for in the report iframe.

        Layer 0 default is the generic Power BI chrome phrase. Domain pages
        whose dashboards use a different caption override ``LAST_REFRESH_PHRASE``
        (or this method) so freshness lookup targets the right text.
        """
        return getattr(self, "LAST_REFRESH_PHRASE", None) or _LAST_REFRESH_PHRASE

    def _last_refresh_pattern(self) -> re.Pattern:
        """Regex capturing the timestamp that follows the freshness phrase."""
        return re.compile(re.escape(self._last_refresh_phrase()) + r"\s*(.+)")

    def after_navigate(self) -> None:
        return

    def _bypass_secondary_auth(self) -> None:
        """Domain hook: dismiss a secondary auth/entry screen shown after the
        catalog click, before the report ready visual is awaited.

        Some reports gate behind an extra authentication/entry step that only
        appears once the product is opened from the catalog. Layer 0 stays
        report-agnostic: the default is a no-op, and domain pages override this
        to dismiss their specific screen. Called from ``navigate()`` after the
        report is opened and before the ready-locator wait begins.
        """
        return

    def before_report_ready_check(self) -> None:
        """Domain hook: dismiss overlays that block the ready visual.

        Called immediately before each ready-locator visibility check.
        Default is a no-op so fleet behavior is unchanged.
        """
        return

    def _iframe_phrase_locator(self, phrase: str) -> Locator:
        """Locate a phrase in the report iframe by text or accessible name.

        Power BI KPI/card titles are often images or buttons (aria-label /
        alt), not text nodes, so ``get_by_text`` alone misses them.
        Role ``name`` is passed as a plain string (substring match) — a
        compiled regex is double-escaped by Playwright and fails to match.
        """
        frame = self._report_frame()
        return (
            frame.get_by_text(phrase, exact=False)
            .or_(frame.get_by_role("button", name=phrase))
            .or_(frame.get_by_role("img", name=phrase))
            .or_(frame.get_by_role("heading", name=phrase))
            .or_(frame.get_by_role("group", name=phrase))
            .or_(frame.get_by_label(phrase))
            .or_(frame.get_by_alt_text(phrase, exact=False))
            .or_(
                frame.locator(
                    f"[aria-label*='{phrase}'], [title*='{phrase}'], [alt*='{phrase}']"
                )
            )
            .first
        )

    def _catalog_search_term(self) -> str:
        """Catalog product name: page-owned term, else settings default."""
        return getattr(self, "DASHBOARD_SEARCH_TERM", None) or settings.DASHBOARD_SEARCH_TERM

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

    def _report_frame(self):
        """FrameLocator for the hosted Power BI report (same iframe as wait)."""
        frame = self._dashboard_iframe().content_frame
        if frame is not None:
            return frame
        try:
            if self.page.locator("main iframe").count() > 0:
                return self.page.frame_locator("main iframe")
        except Exception:
            pass
        return self.page.frame_locator("iframe")

    def _last_refresh_caption_text(self) -> str:
        """Visible last-refresh caption text inside the report iframe."""
        phrase = self._last_refresh_phrase()
        frame = self._report_frame()
        caption = frame.get_by_text(re.compile(re.escape(phrase))).first
        try:
            expect(caption).to_be_visible(timeout=self.timeout)
        except AssertionError as exc:
            raise AssertionError(
                "Last-refresh caption "
                f"{phrase!r} was not found in the report iframe. "
                f"{self._page_debug_summary()}"
            ) from exc

        chunks: list[str] = []
        try:
            chunks.append(caption.inner_text(timeout=self.timeout) or "")
        except Exception:
            pass
        try:
            chunks.append(caption.locator("xpath=..").inner_text(timeout=3000) or "")
        except Exception:
            pass
        try:
            chunks.append(frame.locator("body").inner_text(timeout=3000) or "")
        except Exception:
            pass
        return "\n".join(chunk for chunk in chunks if chunk)

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
        """True for Microsoft IdP or the public landing with 'התחברות'."""
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
        """True when the portal shows a transient profile/user fetch failure."""
        try:
            body = self.page.locator("body").inner_text(timeout=2000) or ""
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

    def _open_all_products_catalog(self) -> None:
        """Open catalog: click the configured all-products control, else catalog URL."""
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

    def _catalog_result_locator(self, term: str) -> Locator:
        """Locate a catalog product card/link/button by its name text."""
        return (
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

    def _catalog_shows_no_products(self) -> bool:
        """True when the catalog result area reports an empty result set."""
        try:
            return (
                self.page.get_by_text(re.compile(r"אין מוצרים להצגה|אין מידע"))
                .first.is_visible(timeout=1000)
            )
        except Exception:
            return False

    def _switch_catalog_to_archive(self) -> bool:
        """Switch the catalog segmented control to its 'ארכיון' (archive) tab.

        Some products are not listed under the default 'קטלוג' tab; they live
        under 'ארכיון'. Generic catalog behavior — no report-specific text.
        """
        archive = (
            self.page.get_by_role("radio", name=re.compile(r"^\s*ארכיון\s*$"))
            .or_(self.page.get_by_role("option", name=re.compile(r"^\s*ארכיון\s*$")))
            .or_(self.page.get_by_role("tab", name=re.compile(r"^\s*ארכיון\s*$")))
            .or_(self.page.get_by_text(re.compile(r"^\s*ארכיון\s*$")))
            .first
        )
        try:
            if archive.is_visible(timeout=1500):
                print("\n[nav] אין תוצאות ב'קטלוג' — עוברים ללשונית 'ארכיון'...\n")
                archive.click()
                return True
        except Exception:
            pass
        return False

    def _open_dashboard_via_portal_search(self) -> None:
        self._open_all_products_catalog()

        term = self._catalog_search_term()
        print(f"\n[nav] מחפשים '{term}' בקטלוג...\n")
        search = self._portal_search_box()
        search.wait_for(state="visible", timeout=self.timeout)
        search.click()
        search.fill(term)
        search.press("Enter")

        result = self._catalog_result_locator(term)
        try:
            expect(result).to_be_visible(timeout=self.timeout)
        except AssertionError:
            # Product may live under the catalog 'ארכיון' (archive) tab rather
            # than the default 'קטלוג' tab. Retry the search there once.
            if not (self._catalog_shows_no_products() and self._switch_catalog_to_archive()):
                raise
            search = self._portal_search_box()
            try:
                if search.count() > 0:
                    search.click()
                    search.fill(term)
                    search.press("Enter")
            except Exception:
                pass
            result = self._catalog_result_locator(term)
            expect(result).to_be_visible(timeout=self.timeout)
        result.click()
        ensure_single_tab(self.page.context, self.page)

        if not self._wait_for_dashboard_iframe():
            raise AssertionError(
                f"Opened portal search for '{term}' but report iframe did not load. "
                f"{self._page_debug_summary()}."
            )

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
                ensure_single_tab(self.page.context, self.page)
                return True
            time.sleep(0.5)

        print(
            "\n[auth] אחרי לחיצה אחת על 'התחברות' עדיין במסך כניסה. "
            "לא לוחצים שוב אוטומטית.\n"
        )
        return False

    def _ensure_authenticated(self) -> None:
        """Enter portal: one SSO click; pause only if still stuck (no click loop)."""
        if self._dashboard_ready() or not self._is_login_page():
            return

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

    def _dashboard_ready(self) -> bool:
        """True when the report iframe and domain ready visual are present."""
        if not self._wait_for_dashboard_iframe(timeout=3000):
            return False
        self.before_report_ready_check()
        try:
            expect(self._report_ready_locator()).to_be_visible(timeout=5000)
            return True
        except AssertionError:
            return False

    def _report_ready(self) -> bool:
        """Alias for ``_dashboard_ready`` (iframe + domain ready locator)."""
        return self._dashboard_ready()

    @allure.step("Navigate to report")
    def navigate(self, *, force_reload: bool = False) -> None:
        if not force_reload and self._dashboard_ready():
            via = "reuse_open"
            ensure_single_tab(self.page.context, self.page)
            self.after_navigate()
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
        self._bypass_secondary_auth()
        ready = self._report_ready_locator()
        ready_deadline = time.monotonic() + self.timeout / 1000
        while time.monotonic() < ready_deadline:
            self.before_report_ready_check()
            try:
                if ready.is_visible(timeout=1500):
                    break
            except Exception:
                pass
            self.page.wait_for_timeout(400)
        try:
            expect(ready).to_be_visible(timeout=self.timeout)
        except AssertionError as exc:
            raise LoadTimeoutError(
                "report ready visual",
                steps_ms=[self.timeout],
                cause=exc,
            ) from exc
        self.after_navigate()
        try:
            self.page.context.storage_state(path=settings.AUTH_FILE)
        except Exception:
            pass
        report = get_current_report()
        if report is not None:
            report.log_ui(
                f"Navigated to dashboard via {via}: {self.page.url} "
                f"(search_term={self._catalog_search_term()!r})"
            )

    @allure.step("Reload report and measure time until ready")
    def reload_and_measure_ready_ms(self) -> int:
        """
        Hard-reload the already-authenticated report and return elapsed ms
        until the domain ready visual is visible (interactive load signal).

        Uses short polls so wait timeouts do not inflate the measured duration.
        """
        start = time.perf_counter()
        self.page.reload(wait_until="domcontentloaded")
        wait_budget_ms = max(self.timeout, settings.DASHBOARD_LOAD_SLA_MS) + 30_000
        deadline = time.monotonic() + wait_budget_ms / 1000
        ready = self._report_ready_locator()
        while time.monotonic() < deadline:
            try:
                iframe_ok = self._wait_for_dashboard_iframe(timeout=400)
                if iframe_ok:
                    self.before_report_ready_check()
                if iframe_ok and ready.is_visible(timeout=400):
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
            "report ready visual after reload",
            steps_ms=[elapsed_ms],
        )

    @allure.step("Verify report last-refresh freshness")
    def verify_freshness(self, max_hours: int = 24) -> None:
        """Assert the report last-refresh caption is within ``max_hours``.

        Locates the freshness caption (``self._last_refresh_phrase()``) inside
        the report iframe (text/regex, not dashboard-specific CSS), parses the
        timestamp, and asserts ``datetime.now() - parsed <= max_hours``.
        """
        if not self._wait_for_dashboard_iframe():
            raise AssertionError(
                "Report iframe was not visible before last-refresh check. "
                f"{self._page_debug_summary()}"
            )

        phrase = self._last_refresh_phrase()
        captured = self._last_refresh_caption_text()
        match = self._last_refresh_pattern().search(captured)
        remainder = match.group(1).strip() if match else captured
        parsed = _parse_last_refresh_datetime(remainder)
        if parsed is None and remainder != captured:
            # Timestamp may sit outside the phrase's own line (separate node);
            # fall back to scanning the full captured caption text.
            parsed = _parse_last_refresh_datetime(captured)
            remainder = captured if parsed is not None else remainder
        if parsed is None:
            raise AssertionError(
                "Last-refresh timestamp could not be parsed from caption "
                f"{phrase!r}. Captured text: {captured!r}"
            )

        extracted_date_string = remainder.splitlines()[0].strip()
        now = datetime.now()
        age = now - parsed
        limit = timedelta(hours=max_hours)
        with allure.step(f"Dashboard last updated at: {extracted_date_string}"):
            assert age <= limit, (
                f"Report last-refresh is older than {max_hours} hours: "
                f"parsed={parsed.isoformat()}, age={age}, now={now.isoformat()}."
            )
