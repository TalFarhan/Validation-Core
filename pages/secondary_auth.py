"""Shared secondary-auth (ArcGIS entry) flow for gated portal reports.

A few portal reports — Mass Events, Life-Saving Guidelines, Maya System and
Public Shelters — show an extra ArcGIS Online sign-in step AFTER the catalog
click and BEFORE the report becomes ready. The manual flow is:

    1. A dialog "היכנס אל ArcGIS Online" appears → click אישור (OK).
    2. A new tab opens: "היכנס ל-ענף אגמים - מפעל המידע של פיקוד העורף".
    3. "בחר סוג חשבון" → choose "Agamimp Users / משתמשי @agamimp.net".
    4. Choose the account (Tal.Farhan@agamimp.net) → type the password.
    5. Click "אין לי אפשרות להתחבר" → then "שלח הודעת טקסט למספר הטלפון …".
    6. Enter the SMS one-time code.

This module drives that flow. It lives in ``pages/secondary_auth.py``, outside
``core/``, so Layer 0 stays report-agnostic. The four page objects call
``bypass_secondary_auth`` from their ``_bypass_secondary_auth`` override.

Design notes:
- Every screen is OPTIONAL. Each step is guarded by a short visibility probe so
  a report that is already authenticated (reused session / saved auth_state)
  or one that does not actually gate passes straight through as a no-op.
- Secrets are never stored in the repo. The account email/password come from
  the ``AGAMIM_SECONDARY_EMAIL`` / ``AGAMIM_SECONDARY_PASSWORD`` environment
  variables when present; otherwise the run pauses for manual entry.
- The SMS one-time code cannot be automated: after "send text message" the run
  pauses for the engineer to type the code and resume.
- Selectors are intentionally broad (role + text + attribute fallbacks) and may
  be tightened after a live run reveals the exact DOM.
"""

from __future__ import annotations

import os
import re
import time

from playwright.sync_api import Page

from browser_session import ensure_single_tab, is_auth_url
from config.settings import settings

DEFAULT_ACCOUNT_EMAIL = "Tal.Farhan@agamimp.net"
ACCOUNT_TYPE_LABEL = "משתמשי @agamimp.net"

_ARCGIS_MARKER = re.compile(r"ArcGIS", re.IGNORECASE)
_AGAMIM_SIGNIN_MARKER = re.compile(r"ענף אגמים|בחר סוג חשבון")
_CONFIRM_TEXT = re.compile(r"^\s*(אישור|המשך|OK|Continue)\s*$", re.IGNORECASE)
_SEND_SMS_TEXT = re.compile(r"שלח הודעת טקסט|הודעת טקסט|text message", re.IGNORECASE)
_CANT_SIGNIN_TEXT = re.compile(r"אין לי אפשרות להתחבר|לא ניתן להתחבר|another way|can.?t")

# The extra screens either appear within a couple of seconds of the catalog
# click, or they do not appear at all. Keep probes short so no-op paths stay fast.
_PROBE_MS = 4000
_STEP_MS = 8000


def _env_email() -> str:
    return (os.getenv("AGAMIM_SECONDARY_EMAIL") or DEFAULT_ACCOUNT_EMAIL).strip()


def _env_password() -> str | None:
    value = os.getenv("AGAMIM_SECONDARY_PASSWORD")
    return value.strip() if value and value.strip() else None


def _visible(locator, timeout_ms: int) -> bool:
    try:
        return locator.first.is_visible(timeout=timeout_ms)
    except Exception:
        return False


def _manual_ok() -> bool:
    """True when we may hand off to a human (headed + manual-login run)."""
    return settings.MANUAL_LOGIN and not settings.HEADLESS


def _agamim_auth_tab(context, fallback: Page) -> Page:
    """Return the most recently opened ArcGIS/agamim/Microsoft sign-in tab."""
    for candidate in reversed(context.pages):
        try:
            if candidate.is_closed() or candidate is fallback:
                continue
            url = (candidate.url or "").lower()
            if is_auth_url(url) or "agamim" in url or "arcgis" in url:
                return candidate
        except Exception:
            continue
    return fallback


def bypass_secondary_auth(page: Page) -> None:
    """Drive the ArcGIS secondary-auth screens if they appear; else no-op.

    ``page`` is the shared portal tab (the report page object's ``self.page``).
    Safe to call on every navigation: it returns immediately when no ArcGIS
    sign-in prompt is present.
    """
    context = page.context

    if not _visible(page.get_by_text(_ARCGIS_MARKER), _PROBE_MS):
        # No ArcGIS prompt on this tab → nothing to bypass.
        return

    work = _confirm_arcgis_dialog(page) or _agamim_auth_tab(context, page)
    try:
        work.bring_to_front()
    except Exception:
        pass

    _choose_account_type(work)
    _choose_account(work)
    _enter_password(work)
    _choose_sms_verification(work)
    _complete_otp(work, page)

    ensure_single_tab(context, page)
    try:
        page.bring_to_front()
    except Exception:
        pass


def _confirm_arcgis_dialog(page: Page) -> Page | None:
    """Click OK on the 'Sign in to ArcGIS Online' dialog; return the new tab."""
    confirm = (
        page.get_by_role("button", name=_CONFIRM_TEXT)
        .or_(page.get_by_role("link", name=_CONFIRM_TEXT))
        .first
    )
    if not _visible(confirm, _STEP_MS):
        return None

    print("\n[secondary-auth] דיאלוג ArcGIS זוהה — לוחצים 'אישור'...\n")
    new_tab: Page | None = None
    try:
        with page.context.expect_page(timeout=15000) as popup_info:
            confirm.click()
        new_tab = popup_info.value
        try:
            new_tab.wait_for_load_state("domcontentloaded", timeout=30000)
        except Exception:
            pass
        print(f"\n[secondary-auth] נפתחה כרטיסיית כניסה: {new_tab.url}\n")
    except Exception:
        # No popup fired — sign-in likely continues on the same tab.
        pass
    return new_tab


def _choose_account_type(page: Page) -> None:
    """On 'בחר סוג חשבון', choose the '@agamimp.net' account type."""
    if not _visible(page.get_by_text(_AGAMIM_SIGNIN_MARKER), _STEP_MS):
        return
    option = (
        page.get_by_role("button", name=re.compile(re.escape(ACCOUNT_TYPE_LABEL)))
        .or_(page.get_by_role("link", name=re.compile(re.escape(ACCOUNT_TYPE_LABEL))))
        .or_(page.get_by_text(re.compile(re.escape(ACCOUNT_TYPE_LABEL))))
        .first
    )
    if _visible(option, _STEP_MS):
        print(f"\n[secondary-auth] בוחרים סוג חשבון: '{ACCOUNT_TYPE_LABEL}'...\n")
        option.click()


def _choose_account(page: Page) -> None:
    """Pick the saved account tile, or type the email into the account field."""
    email = _env_email()
    tile = page.get_by_text(re.compile(re.escape(email), re.IGNORECASE)).first
    if _visible(tile, _STEP_MS):
        print(f"\n[secondary-auth] בוחרים חשבון: {email}\n")
        tile.click()
        return

    email_input = (
        page.get_by_role("textbox", name=re.compile(r"email|דוא|חשבון|מש", re.IGNORECASE))
        .or_(page.locator("input[type='email']"))
        .or_(page.locator("input[name='loginfmt']"))
        .first
    )
    if _visible(email_input, _STEP_MS):
        print(f"\n[secondary-auth] מקלידים חשבון: {email}\n")
        email_input.fill(email)
        _click_next(page)


def _enter_password(page: Page) -> None:
    """Fill the password from env when available, else pause for manual entry."""
    password_input = (
        page.locator("input[type='password']")
        .or_(page.get_by_role("textbox", name=re.compile(r"password|סיסמ", re.IGNORECASE)))
        .first
    )
    if not _visible(password_input, _STEP_MS):
        return

    password = _env_password()
    if password:
        print("\n[secondary-auth] מקלידים סיסמה מתוך משתנה סביבה...\n")
        password_input.fill(password)
        _click_next(page)
        return

    if _manual_ok():
        print(
            "\n[secondary-auth] הקלידי את הסיסמה ידנית בחלון ArcGIS ואז המשיכי (Resume).\n"
            "  (אפשר להימנע מהשהיה ע\"י הגדרת AGAMIM_SECONDARY_PASSWORD.)\n"
        )
        try:
            page.pause()
        except Exception:
            pass
        return

    raise AssertionError(
        "Secondary-auth password screen reached but AGAMIM_SECONDARY_PASSWORD is "
        "not set and MANUAL_LOGIN/headed mode is off. Set the env var or run "
        "headed with MANUAL_LOGIN=true."
    )


def _choose_sms_verification(page: Page) -> None:
    """Click 'אין לי אפשרות להתחבר', then 'שלח הודעת טקסט...' (SMS OTP)."""
    cant = (
        page.get_by_role("button", name=_CANT_SIGNIN_TEXT)
        .or_(page.get_by_role("link", name=_CANT_SIGNIN_TEXT))
        .or_(page.get_by_text(_CANT_SIGNIN_TEXT))
        .first
    )
    if _visible(cant, _STEP_MS):
        print("\n[secondary-auth] לוחצים 'אין לי אפשרות להתחבר'...\n")
        cant.click()

    send_sms = (
        page.get_by_role("button", name=_SEND_SMS_TEXT)
        .or_(page.get_by_role("link", name=_SEND_SMS_TEXT))
        .or_(page.get_by_text(_SEND_SMS_TEXT))
        .first
    )
    if _visible(send_sms, _STEP_MS):
        print("\n[secondary-auth] לוחצים 'שלח הודעת טקסט' לקבלת קוד חד-פעמי...\n")
        send_sms.click()


def _complete_otp(auth_tab: Page, main_page: Page) -> None:
    """Wait for the SMS code to be entered manually and the auth tab to close."""
    otp_input = (
        auth_tab.locator("input[type='tel']")
        .or_(auth_tab.get_by_role("textbox", name=re.compile(r"code|קוד|otp", re.IGNORECASE)))
        .or_(auth_tab.locator("input[name*='otc' i]"))
        .first
    )
    if not _visible(otp_input, _STEP_MS):
        return

    if _manual_ok():
        print(
            "\n[secondary-auth] הזיני את הקוד שהתקבל ב-SMS בחלון ArcGIS ואז המשיכי "
            "(Resume). הכניסה תישמר להרצות הבאות.\n"
        )
        try:
            auth_tab.pause()
        except Exception:
            pass
    else:
        raise AssertionError(
            "Secondary-auth SMS one-time code screen reached but the run is not "
            "headed/manual, so the code cannot be entered. Run headed with "
            "MANUAL_LOGIN=true to complete the SMS step."
        )

    _wait_for_auth_tab_to_close(auth_tab, main_page)


def _wait_for_auth_tab_to_close(auth_tab: Page, main_page: Page, timeout_ms: int = 120000) -> None:
    """Block until the ArcGIS auth tab closes (login done) or a timeout hits."""
    if auth_tab is main_page:
        return
    deadline = time.monotonic() + timeout_ms / 1000
    while time.monotonic() < deadline:
        try:
            if auth_tab.is_closed():
                return
        except Exception:
            return
        time.sleep(0.5)


def _click_next(page: Page) -> None:
    nxt = (
        page.get_by_role("button", name=re.compile(r"^\s*(הבא|כניסה|התחבר|Next|Sign in)\s*$", re.IGNORECASE))
        .or_(page.locator("input[type='submit']"))
        .first
    )
    if _visible(nxt, _STEP_MS):
        nxt.click()
