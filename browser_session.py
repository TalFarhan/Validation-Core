"""Browser tab helpers.

Important: Microsoft SSO login MUST be allowed to open a popup/tab.
Forcing everything into one tab breaks 'התחברות' into an endless loop.
"""

from __future__ import annotations

from playwright.sync_api import BrowserContext, Page

_AUTH_URL_HINTS = (
    "login.microsoftonline.com",
    "login.live.com",
    "login.windows.net",
    "microsoftonline.com",
    "msauth",
    "oauth",
)

# Only force same-tab for normal portal links — NOT for Microsoft login.
_SAME_TAB_INIT_SCRIPT = """
(() => {
  const isAuthUrl = (url) => {
    if (typeof url !== "string") return false;
    const u = url.toLowerCase();
    return (
      u.includes("login.microsoftonline.com") ||
      u.includes("login.live.com") ||
      u.includes("login.windows.net") ||
      u.includes("microsoftonline.com") ||
      u.includes("oauth")
    );
  };
  const nativeOpen = window.open.bind(window);
  window.open = function (url, name, features) {
    if (isAuthUrl(String(url || ""))) {
      return nativeOpen(url, name, features);
    }
    if (typeof url === "string" && url && url !== "about:blank") {
      window.location.href = url;
      return window;
    }
    return nativeOpen(url, name, features);
  };
  document.addEventListener(
    "click",
    (event) => {
      const anchor = event.target && event.target.closest
        ? event.target.closest("a[target='_blank']")
        : null;
      if (!anchor) return;
      const href = anchor.href || "";
      if (isAuthUrl(href)) return; // keep popup behavior for SSO
      anchor.setAttribute("target", "_self");
    },
    true
  );
})();
"""


def is_auth_url(url: str) -> bool:
    lower = (url or "").lower()
    return any(hint in lower for hint in _AUTH_URL_HINTS)


def install_single_tab_policy(context: BrowserContext, main_page: Page) -> None:
    """
    Keep portal navigation on one tab, but NEVER kill Microsoft SSO popups.
    """
    context.add_init_script(_SAME_TAB_INIT_SCRIPT)
    try:
        main_page.add_init_script(_SAME_TAB_INIT_SCRIPT)
        main_page.evaluate(_SAME_TAB_INIT_SCRIPT)
    except Exception:
        pass

    def _on_new_page(new_page: Page) -> None:
        if new_page == main_page:
            return
        try:
            new_page.wait_for_load_state("domcontentloaded", timeout=20000)
        except Exception:
            pass

        url = ""
        try:
            url = new_page.url or ""
        except Exception:
            url = ""

        # Critical: let Microsoft login finish in its own window/tab.
        if is_auth_url(url) or url in {"", "about:blank"}:
            print(
                f"\n[browser] Auth popup/tab detected ({url or 'loading'}) — "
                "leaving it open for SSO.\n"
            )
            return

        print(
            f"\n[browser] Extra portal tab ({url}) — "
            "closing it and continuing on the main tab.\n"
        )
        try:
            new_page.close()
        except Exception:
            pass
        if url and url not in {"", "about:blank"}:
            try:
                if main_page.url != url:
                    main_page.bring_to_front()
                    main_page.goto(url, wait_until="domcontentloaded")
            except Exception:
                pass

    context.on("page", _on_new_page)


def ensure_single_tab(context: BrowserContext, main_page: Page) -> Page:
    """Close non-auth extra tabs. Never close Microsoft SSO tabs."""
    for page in list(context.pages):
        if page is main_page:
            continue
        try:
            if page.is_closed():
                continue
            url = page.url or ""
            if is_auth_url(url) or url in {"", "about:blank"}:
                continue
            print(f"\n[browser] Closing extra portal tab: {url}\n")
            page.close()
        except Exception:
            pass
    try:
        main_page.bring_to_front()
    except Exception:
        pass
    return main_page


def wait_for_auth_popups_to_finish(context: BrowserContext, *, timeout_ms: int = 120000) -> None:
    """Wait until Microsoft login tabs/popups are gone."""
    import time

    deadline = time.monotonic() + timeout_ms / 1000
    while time.monotonic() < deadline:
        auth_pages = []
        for page in list(context.pages):
            try:
                if page.is_closed():
                    continue
                if is_auth_url(page.url or ""):
                    auth_pages.append(page)
            except Exception:
                continue
        if not auth_pages:
            return
        time.sleep(0.5)


def save_auth_state(context: BrowserContext) -> None:
    """Persist cookies and localStorage so the next pytest run stays logged in."""
    from pathlib import Path

    from config.settings import settings

    path = Path(settings.AUTH_FILE)
    try:
        context.storage_state(path=str(path))
        print(f"\n[auth] Session saved → {path.resolve()}\n")
    except Exception as exc:
        print(f"\n[auth] WARNING: could not save session: {exc}\n")
