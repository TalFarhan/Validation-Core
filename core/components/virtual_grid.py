"""Report-agnostic reader for a virtualized Power BI grid (Layer 2).

The caller supplies the visible-row extractor and the row id. This module
does not know which report it is reading.
"""

from __future__ import annotations

import time
from collections.abc import Callable, Mapping, Sequence

from playwright.sync_api import Error, Locator

_SCROLL_JS = """(el, mode) => {
    const horizontal = mode === 'x' || mode === 'x-start';
    const extraOf = (node) => horizontal
        ? node.scrollWidth - node.clientWidth
        : node.scrollHeight - node.clientHeight;
    const overflowScrolls = (node) => {
        const style = window.getComputedStyle(node);
        const overflow = horizontal ? style.overflowX : style.overflowY;
        return overflow === 'auto' || overflow === 'scroll' || overflow === 'overlay';
    };
    const largest = (list, requireOverflow) => {
        let best = null;
        let room = 0;
        for (const node of list) {
            if (!node) continue;
            const gap = extraOf(node);
            if (gap <= 1) continue;
            if (requireOverflow && !overflowScrolls(node)) continue;
            if (gap > room) {
                best = node;
                room = gap;
            }
        }
        return best;
    };
    const family = [];
    const push = (node) => {
        if (node && family.indexOf(node) === -1) family.push(node);
    };
    const host = el.parentElement || el;
    push(host);
    host.querySelectorAll('*').forEach(push);
    let best = largest(family, true) || largest(family, false);
    if (!best) {
        let parent = host.parentElement;
        for (let depth = 0; depth < 12 && parent && !best; depth += 1) {
            if (extraOf(parent) > 1 && overflowScrolls(parent)) best = parent;
            parent = parent.parentElement;
        }
    }
    if (!best) return false;
    if (mode === 'top') {
        best.scrollTop = 0;
        return true;
    }
    if (mode === 'x-start') {
        for (const node of family) {
            if (extraOf(node) > 1) node.scrollLeft = 0;
        }
        return true;
    }
    if (mode === 'x') {
        const ordered = family
            .filter((node) => extraOf(node) > 1)
            .sort((a, b) => extraOf(a) - extraOf(b));
        for (const node of ordered) {
            const before = node.scrollLeft;
            const step = Math.max(60, Math.floor(node.clientWidth * 0.45));
            node.scrollLeft = before - step;
            if (node.scrollLeft !== before) return true;
            node.scrollLeft = before + step;
            if (node.scrollLeft !== before) return true;
        }
        return false;
    }
    const before = best.scrollTop;
    best.scrollTop = Math.min(before + best.clientHeight, best.scrollHeight);
    return best.scrollTop !== before;
}"""


def _scroll(grid: Locator, mode: str) -> bool:
    """Move the grid's scroll container to the top, or down by its height."""
    try:
        return bool(grid.evaluate(_SCROLL_JS, mode))
    except Error:
        return False


def _store(
    found: dict[str, dict[str, str]],
    rows: Sequence[Mapping[str, str]],
    row_id: Callable[[Mapping[str, str]], str],
) -> int:
    """Insert the first row for each new non-empty id. Return how many were added."""
    added = 0
    for row in rows:
        key = row_id(row)
        text = "" if key is None else str(key)
        if not text:
            continue
        incoming = {
            str(name): "" if value is None else str(value) for name, value in row.items()
        }
        current = found.get(text)
        if current is None:
            found[text] = incoming
            added += 1
            continue
        # A later viewport can fill cells that were blank on the first paint.
        for name, value in incoming.items():
            if value.strip() and not current.get(name, "").strip():
                current[name] = value
                added += 1
    return added


def _wait_for_paint(grid: Locator) -> None:
    """Let the virtualizer paint the next viewport. Not a fixed sleep."""
    try:
        grid.evaluate(
            "() => new Promise((resolve) => requestAnimationFrame(() => requestAnimationFrame(resolve)))"
        )
    except Error:
        return


def collect_virtualized_rows(
    grid: Locator,
    read_visible: Callable[[Locator], Sequence[Mapping[str, str]]],
    row_id: Callable[[Mapping[str, str]], str],
    *,
    timeout_ms: int,
) -> list[dict[str, str]]:
    """Read every viewport of ``grid``, deduped by ``row_id``.

    Starts at the top of the scroll container. Each pass stores the visible
    rows, then moves ``scrollTop`` forward by the container height. After a
    move, wait for animation frames until a new id appears. Stop when the
    scroll does not move, when those frames show no new id, or when
    ``timeout_ms`` elapses.
    """
    found: dict[str, dict[str, str]] = {}
    deadline = time.monotonic() + max(timeout_ms, 0) / 1000

    def absorb() -> int:
        try:
            rows = read_visible(grid)
        except Error:
            return 0
        return _store(found, rows, row_id)

    def sweep_horizontal() -> int:
        """Read every horizontal page at the current vertical position."""
        gained = 0
        _scroll(grid, "x-start")
        _wait_for_paint(grid)
        gained += absorb()
        for _ in range(8):
            if time.monotonic() >= deadline or not _scroll(grid, "x"):
                break
            revealed = False
            paint_deadline = min(deadline, time.monotonic() + 1.0)
            while time.monotonic() < paint_deadline:
                _wait_for_paint(grid)
                added = absorb()
                if added:
                    gained += added
                    revealed = True
                    break
            if not revealed:
                break
        return gained

    _scroll(grid, "top")
    _wait_for_paint(grid)
    sweep_horizontal()
    while time.monotonic() < deadline:
        if not _scroll(grid, "page"):
            break
        if sweep_horizontal() == 0:
            break
    return list(found.values())
