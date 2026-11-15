"""Shared generic Power BI visual helpers (Layer 2).

Scope host, empty-versus-zero classification, data-mark counting, and the
title currently shown on a visual. Titles and scopes passed in by callers
stay opaque. This module does not know report names or metric titles.
"""

from __future__ import annotations

import re
from collections.abc import Sequence
from typing import Literal

from playwright.sync_api import FrameLocator, Locator

# Invisible bidi marks Power BI injects around Hebrew/RTL text.
_BIDI_MARKS = ("\u200f", "\u200e", "\u202a", "\u202b", "\u202c")
# Plot glyphs. Title text and axis hairlines are not marks.
_DATA_MARKS = (
    "svg.plotArea rect, svg .plotArea rect, .plotArea rect, "
    ".bar, .column, svg rect[aria-label], svg path[aria-label], "
    "svg circle[aria-label], [class*='bar'], [class*='dataPoint']"
)
_VISUAL_TITLE = ".visualTitle, [class*='visualTitle'], [class*='visual-title']"
# Generic Power BI visual chrome. Not a report title or a visual id.
_VISUAL_CONTAINERS = (
    ".visualContainerHost, .visual-container-host, "
    "[class*='visualContainerHost'], "
    ".visualContainer, .visual-container, "
    ".visual-container-component, "
    "[class*='visualContainer'], [class*='visual-container']"
)


def _strip_bidi(raw: str) -> str:
    """Remove the invisible RTL/LTR marks Power BI injects around text."""
    text = raw or ""
    for mark in _BIDI_MARKS:
        text = text.replace(mark, "")
    return text


def _visible_canvas(frame: FrameLocator) -> Locator:
    """Visible Power BI visual containers on the active report page.

    Hidden pages drop out through Playwright's visibility check. The locator
    is not filtered by a scope string.
    """
    return frame.locator(_VISUAL_CONTAINERS).filter(visible=True)


def scope_host(frame: FrameLocator, scope: str | None) -> FrameLocator | Locator:
    """Return the search root for a visual lookup.

    None or whitespace uses the full report iframe. A non-empty scope uses a
    role=group whose accessible name matches. A text node that merely contains
    the scope is not a section. When no named group matches, the host is the
    visible visual containers, so hidden pages stay out of the search. Never filter ``*`` — that ancestor is the report root.
    ``count()`` decides the tier and does not wait the action timeout.
    """
    if scope is None or not str(scope).strip():
        return frame
    pattern = re.compile(re.escape(str(scope).strip()))
    named = frame.get_by_role("group", name=pattern)
    if named.count() > 0:
        return named.first
    return _visible_canvas(frame)


def classify_presence(
    numbers: Sequence[int | float | None],
    mark_count: int,
) -> Literal["value", "empty"]:
    """Distinguish a rendered reading, including 0, from a blank visual.

    A present 0 is ``value``. ``None`` means absent and is not a zero. Marks
    with no readable number are still ``value`` so callers do not substitute 0.
    """
    if any(number is not None for number in numbers):
        return "value"
    if mark_count > 0:
        return "value"
    return "empty"


def count_data_marks(container: Locator) -> int:
    """Count plot glyphs inside a visual. Title text is not a mark."""
    marks = container.locator(_DATA_MARKS)
    try:
        total = min(marks.count(), 40)
    except Exception:
        return 0
    found = 0
    for index in range(total):
        node = marks.nth(index)
        try:
            box = node.bounding_box(timeout=300)
        except Exception:
            continue
        if box is None or box["width"] < 2 or box["height"] < 2:
            continue
        # Axis hairlines are chrome, not data.
        if box["width"] > 400 and box["height"] < 4:
            continue
        if box["height"] > 400 and box["width"] < 4:
            continue
        found += 1
    return found


def _first_text(locator: Locator) -> str:
    """Text of the first match, or an empty string when the node is absent."""
    try:
        if locator.count() == 0:
            return ""
        text = locator.first.text_content(timeout=1000) or ""
    except Exception:
        return ""
    return _strip_bidi(text).strip()


def displayed_title_text(container: Locator) -> str:
    """Full title currently shown on a visual container.

    First non-empty source wins: heading, visual-title node, then the
    container's accessible name. Bidi marks are stripped. The lookup anchor
    is not removed from the result.
    """
    heading = _first_text(container.get_by_role("heading"))
    if heading:
        return heading
    title_node = _first_text(container.locator(_VISUAL_TITLE))
    if title_node:
        return title_node
    try:
        aria = container.get_attribute("aria-label") or ""
    except Exception:
        aria = ""
    aria = _strip_bidi(aria).strip()
    if aria:
        return aria
    try:
        labelled = container.evaluate(
            """el => {
                const by = el.getAttribute('aria-labelledby');
                if (!by) return '';
                return by.split(/\\s+/).map(id => {
                    const node = el.ownerDocument.getElementById(id);
                    return node ? (node.textContent || '') : '';
                }).join(' ').trim();
            }"""
        )
    except Exception:
        labelled = ""
    return _strip_bidi(labelled or "").strip()
