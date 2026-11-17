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
            node.removeAttribute('data-vc-xdir');
            if (extraOf(node) > 1) node.scrollLeft = 0;
        }
        return true;
    }
    if (mode === 'x') {
        const ordered = family
            .filter((node) => extraOf(node) > 1 && overflowScrolls(node))
            .sort((a, b) => extraOf(b) - extraOf(a));
        if (best && ordered.indexOf(best) > 0) {
            ordered.splice(ordered.indexOf(best), 1);
            ordered.unshift(best);
        }
        for (const node of ordered) {
            const before = node.scrollLeft;
            const step = Math.max(80, Math.floor(node.clientWidth * 0.55));
            const stored = Number(node.getAttribute('data-vc-xdir') || '0');
            const deltas = stored === 0 ? [step, -step] : [stored * step];
            for (const delta of deltas) {
                node.scrollLeft = before + delta;
                if (node.scrollLeft !== before) {
                    const sign = Math.sign(node.scrollLeft - before) || Math.sign(delta);
                    node.setAttribute('data-vc-xdir', String(sign));
                    return true;
                }
            }
        }
        return false;
    }
    const tryVertical = (node) => {
        if (!node) return false;
        const before = node.scrollTop;
        const gap = node.scrollHeight - node.clientHeight;
        if (gap <= 1) return false;
        node.scrollTop = Math.min(before + node.clientHeight, node.scrollHeight);
        return node.scrollTop !== before;
    };
    if (tryVertical(best)) return true;
    const ordered = family
        .filter((node) => node !== best && extraOf(node) > 1)
        .sort((a, b) => extraOf(b) - extraOf(a));
    for (const node of ordered) {
        if (tryVertical(node)) return true;
    }
    return false;
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
    move, wait for animation frames and store whatever is painted. Stop when
    ``scrollTop`` cannot increase, or when ``timeout_ms`` elapses. A viewport
    that adds no new row id does not end the walk while ``scrollTop`` still moves.
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
        """Read every horizontal page. Stop only when scrollLeft stops moving."""
        gained = 0
        _scroll(grid, "x-start")
        _wait_for_paint(grid)
        gained += absorb()
        for _ in range(30):
            if time.monotonic() >= deadline or not _scroll(grid, "x"):
                break
            _wait_for_paint(grid)
            gained += absorb()
        return gained

    _scroll(grid, "top")
    _wait_for_paint(grid)
    sweep_horizontal()
    while time.monotonic() < deadline:
        if not _scroll(grid, "page"):
            break
        sweep_horizontal()
    return list(found.values())
