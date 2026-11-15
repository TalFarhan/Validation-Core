"""Generic Power BI KPI card reader (Layer 2).

Knows how to find a KPI card by its title text inside a report iframe, read the
displayed value, and normalize it for comparison. Does not know any report's
business KPI names. Domain pages / tests supply the (opaque) title string and,
when titles repeat under different sections, an optional opaque scope string.
"""

from __future__ import annotations

import re
from typing import Literal, TypedDict

from playwright.sync_api import FrameLocator, Locator, Page, expect

from config.settings import settings
from core.components.visual import classify_presence, count_data_marks, scope_host

# Invisible bidi marks Power BI injects around Hebrew/RTL values.
_BIDI_MARKS = ("\u200f", "\u200e", "\u202a", "\u202b", "\u202c")
# Whitespace to strip, including the non-breaking space used as a thousands sep.
_WHITESPACE = re.compile(r"[\s\u00a0]+")
# A numeric run embedded in a longer label (e.g. a group's aria-label that also
# carries the Hebrew title). Allows internal thousands separators / decimals /
# spaces so "1,234" or "1 234.5" is captured as one token.
_NUMBER_TOKEN = re.compile(r"-?\d[\d.,\u00a0\u202f ]*\d|-?\d")
# Compact number token for Gauge detection only: no ASCII space (so "0 1,337 3"
# is three tokens, not one). Used by bound-pair capture and compact Gauge shape.
_NUMBER_TOKEN_COMPACT = re.compile(r"-?\d[\d.,\u00a0\u202f]*\d|-?\d")
# Generic Power BI Gauge chrome ("minimum/maximum value") plus the scale number
# that follows it. Not a report metric title. English is case-insensitive.
_GAUGE_BOUND_PAIR = re.compile(
    r"(?:ערך\s+מינימלי|ערך\s+מקסימלי|Minimum\s+value|Maximum\s+value)\s*"
    r"(?:-?\d[\d.,\u00a0\u202f]*\d|-?\d)\.?",
    re.IGNORECASE,
)
# Same chrome as _GAUGE_BOUND_PAIR, but the label and the number are captured
# so a scale reader can keep minimum and maximum instead of discarding them.
_GAUGE_BOUND_CAPTURE = re.compile(
    r"(?P<label>ערך\s+מינימלי|ערך\s+מקסימלי|Minimum\s+value|Maximum\s+value)\s*"
    r"(?P<number>-?\d[\d.,\u00a0\u202f]*\d|-?\d)\.?",
    re.IGNORECASE,
)
# One numerator/denominator pair. Extra numbers disqualify this shape.
_SLASH_PAIR = re.compile(
    r"(?P<left>-?\d[\d.,\u00a0\u202f]*\d|-?\d)\s*/\s*"
    r"(?P<right>-?\d[\d.,\u00a0\u202f]*\d|-?\d)"
)


class GaugeScale(TypedDict):
    """Current figure plus optional bounds. Missing limits are None, not 0."""

    state: Literal["value", "empty"]
    value: int | float | None
    minimum: int | float | None
    maximum: int | float | None


def _strip_bidi(raw: str) -> str:
    """Remove the invisible RTL/LTR marks Power BI injects around values."""
    text = raw or ""
    for mark in _BIDI_MARKS:
        text = text.replace(mark, "")
    return text


def normalize_kpi_text(raw: str) -> str:
    """Return a clean, comparable value string from raw KPI card text.

    Strips invisible RTL/LTR marks, thousands separators (commas), and all
    whitespace (including the non-breaking space). Leaves digits, signs, and a
    decimal point intact so the result can be parsed as a number.
    """
    text = _strip_bidi(raw)
    text = text.replace(",", "")
    text = _WHITESPACE.sub("", text)
    return text.strip()


def extract_kpi_value_text(raw: str) -> str:
    """Pull the numeric value out of a mixed label (e.g. a group's aria-label).

    Group visuals expose the value on a child ``img`` whose ``aria-label`` often
    bundles the Hebrew title together with the number. Strip the bidi marks, then
    return the longest numeric run found (KPIs carry a single value). Gauge
    labels that embed min/max chrome are reduced to the current value first.
    Falls back to the stripped text when no number is present so the caller can
    surface a meaningful parse error.
    """
    cleaned = _strip_bidi(raw).strip()
    if _GAUGE_BOUND_PAIR.search(cleaned):
        cleaned = _GAUGE_BOUND_PAIR.sub("", cleaned).strip()
    else:
        compact = _NUMBER_TOKEN_COMPACT.findall(cleaned)
        if len(compact) == 3:
            return compact[-1].strip()
    matches = _NUMBER_TOKEN.findall(cleaned)
    if not matches:
        return cleaned
    return max((match.strip() for match in matches), key=len)


def _parse_normalized_token(token: str | None) -> int | float | None:
    """Parse one numeric token. None stays None. 0 is a real number."""
    if token is None:
        return None
    clean = normalize_kpi_text(token)
    if not clean:
        return None
    try:
        number = float(clean)
    except ValueError:
        return None
    if number.is_integer():
        return int(number)
    return number


def _longest_number_token(text: str) -> str | None:
    """Longest numeric run in ``text``, or None when the text has no digits."""
    matches = [match.strip() for match in _NUMBER_TOKEN.findall(text)]
    if not matches:
        return None
    return max(matches, key=len)


def _is_minimum_label(label: str) -> bool:
    """True for generic minimum chrome. Maximum chrome does not match this."""
    return re.search(r"מינימלי|minimum", label, re.IGNORECASE) is not None


def _scale(
    value: int | float | None,
    minimum: int | float | None = None,
    maximum: int | float | None = None,
) -> GaugeScale:
    """Build a scale. A parsed value, including 0, is state ``value``."""
    state: Literal["value", "empty"] = "value" if value is not None else "empty"
    return {
        "state": state,
        "value": value,
        "minimum": minimum,
        "maximum": maximum,
    }


def extract_gauge_scale(raw: str) -> GaugeScale:
    """Parse a gauge or ratio label into value, minimum, and maximum.

    Shapes, first match wins: labeled min/max chrome, exactly three compact
    numbers (minimum, maximum, current), one slash pair (value / maximum),
    then a single figure. A denominator is ``maximum``. Absent limits are
    None. This does not change ``extract_kpi_value_text``.
    """
    cleaned = _strip_bidi(raw).strip()
    bounds = list(_GAUGE_BOUND_CAPTURE.finditer(cleaned))
    if bounds:
        minimum: int | float | None = None
        maximum: int | float | None = None
        for match in bounds:
            number = _parse_normalized_token(match.group("number"))
            if _is_minimum_label(match.group("label")):
                minimum = number
            else:
                maximum = number
        remainder = _GAUGE_BOUND_CAPTURE.sub(" ", cleaned)
        value = _parse_normalized_token(_longest_number_token(remainder))
        return _scale(value, minimum, maximum)

    compact = [token.strip() for token in _NUMBER_TOKEN_COMPACT.findall(cleaned)]
    if len(compact) == 3:
        return _scale(
            _parse_normalized_token(compact[2]),
            _parse_normalized_token(compact[0]),
            _parse_normalized_token(compact[1]),
        )

    pairs = list(_SLASH_PAIR.finditer(cleaned))
    if len(pairs) == 1 and len(compact) == 2:
        pair = pairs[0]
        return _scale(
            _parse_normalized_token(pair.group("left")),
            None,
            _parse_normalized_token(pair.group("right")),
        )

    token = _longest_number_token(cleaned)
    if token is None:
        return _scale(None)
    return _scale(_parse_normalized_token(token))


def _to_number(clean: str) -> int | float:
    """Parse a normalized KPI string into int (when integral) or float."""
    if not clean:
        raise ValueError("Empty KPI value cannot be parsed as a number")
    number = float(clean)
    if number.is_integer():
        return int(number)
    return number


class KPI:
    """Composed by a caller with the report iframe. Titles and scopes are opaque to core."""

    def __init__(
        self,
        page: Page,
        frame: FrameLocator,
        timeout_ms: int | None = None,
    ) -> None:
        self._page = page
        self._frame = frame
        self._timeout = (
            timeout_ms if timeout_ms is not None else settings.DEFAULT_TIMEOUT
        )

    def _scope_host(self, scope: str | None) -> FrameLocator | Locator:
        """Return the search root for a title lookup.

        Delegates to ``scope_host``. Blank scope uses the iframe. A matching
        group is that group. Otherwise the host is the visible visual
        containers. Never ``locator("*")``.
        """
        return scope_host(self._frame, scope)

    def _resolve_card(
        self, title: str, scope: str | None = None
    ) -> tuple[Locator, str]:
        """Return the KPI locator and its kind ("button" or "group").

        Power BI renders KPI visuals either as role="button" cards or as
        role="group" visuals (a heading plus a data image). Prefer the button;
        fall back to the group when no button carries the title. When scope is
        set, both queries run inside the scoped host, not the full iframe.
        """
        host = self._scope_host(scope)
        pattern = re.compile(re.escape(title))
        button = host.get_by_role("button", name=pattern).first
        if button.count() > 0:
            return button, "button"
        group = host.get_by_role("group", name=pattern).first
        return group, "group"

    def card(self, title: str, scope: str | None = None) -> Locator:
        """Locate a KPI card by its title text (button card, or group fallback)."""
        return self._resolve_card(title, scope)[0]

    def _read_group_value(self, card: Locator) -> str:
        """Extract the value text from a role="group" KPI visual.

        The number lives on the group's inner ``img`` (usually its ``aria-label``,
        sometimes its ``title``); fall back to the group's own text. The returned
        text may still bundle the title, so pull the numeric token out of it.
        """
        img = card.locator("img").first
        raw = ""
        if img.count() > 0:
            for attr in ("aria-label", "title"):
                value = img.get_attribute(attr, timeout=self._timeout)
                if value:
                    raw = value
                    break
        if not raw:
            raw = card.text_content(timeout=self._timeout) or ""
        return extract_kpi_value_text(raw)

    def read_text(self, title: str, scope: str | None = None) -> str:
        """Raw, un-normalized value text from the card's value node."""
        card, kind = self._resolve_card(title, scope)
        expect(card).to_be_visible(timeout=self._timeout)
        if kind == "group":
            return self._read_group_value(card)
        # Power BI KPI cards render the value in the last <p> of the card.
        value_node = card.locator("p").last
        return value_node.text_content(timeout=self._timeout) or ""

    def value(self, title: str, scope: str | None = None) -> str:
        """Normalized string value (commas, whitespace, and bidi marks stripped)."""
        return normalize_kpi_text(self.read_text(title, scope))

    def number(self, title: str, scope: str | None = None) -> int | float:
        """Normalized numeric value (int when integral, else float)."""
        return _to_number(self.value(title, scope))

    def _read_raw(self, title: str, scope: str | None = None) -> tuple[str, Locator]:
        """Return the unparsed label and the resolved card.

        Group visuals prefer the inner image aria-label, then its title, then
        the group's own text. Button cards use the last paragraph. The current
        value is not extracted here, so gauge limits stay in the string.
        """
        card, kind = self._resolve_card(title, scope)
        expect(card).to_be_visible(timeout=self._timeout)
        if kind == "group":
            img = card.locator("img").first
            raw = ""
            if img.count() > 0:
                for attr in ("aria-label", "title"):
                    value = img.get_attribute(attr, timeout=self._timeout)
                    if value:
                        raw = value
                        break
            if not raw:
                raw = card.text_content(timeout=self._timeout) or ""
            return raw, card
        value_node = card.locator("p").last
        return value_node.text_content(timeout=self._timeout) or "", card

    def scale(self, title: str, scope: str | None = None) -> GaugeScale:
        """Current value plus optional minimum and maximum.

        ``number`` is unchanged. A missing figure is not stored as 0. When the
        label has no number, data marks inside the card decide value versus empty.
        """
        raw, card = self._read_raw(title, scope)
        parsed = extract_gauge_scale(raw)
        if parsed["value"] is not None:
            return parsed
        state = classify_presence([None], count_data_marks(card))
        return {
            "state": state,
            "value": None,
            "minimum": parsed["minimum"],
            "maximum": parsed["maximum"],
        }
