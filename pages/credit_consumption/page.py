"""Credit Consumption report — Layer 0 binding plus info-page popup dismiss."""

import re

from playwright.sync_api import Page

from config.settings import settings
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


class CreditConsumptionPage(ReportShell):
    DASHBOARD_SEARCH_TERM = "צריכת אשראי"

    def __init__(self, page: Page):
        super().__init__(page)
        self.url = settings.LOGIN_URL or settings.DASHBOARD_URL

    def _report_ready_locator(self):
        return self._iframe_phrase_locator("ממוצע הוצאות לקנייה בשגרה")

    def before_report_ready_check(self) -> None:
        self._close_info_popup(wait_ms=200)

    def after_navigate(self) -> None:
        for _ in range(2):
            if not self._info_popup_visible(wait_ms=800):
                return
            self._close_info_popup(wait_ms=800)
            self.page.wait_for_timeout(400)

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
