"""Generic Power BI slicer operator (Layer 2).

Knows how to talk to dropdowns, checkboxes, search fields, and clear-all.
Does not know any report's business filter names. Domain pages supply
``SlicerDefinition`` rows and a settle hook.
"""

from __future__ import annotations

import re
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Literal, NoReturn

from playwright.sync_api import FrameLocator, Locator, Page, expect

from config.settings import settings
from reports.test_run_report import get_current_report

SlicerKind = Literal["dropdown", "checkbox", "search"]
SlicerHost = Literal["report", "visual_sandbox"]
SettleKind = Literal[
    "before_select",
    "after_select",
    "before_clear",
    "after_clear",
    "after_search",
]

_CLEAR_ALL_NAME = re.compile(
    r"נקה את כל|Clear all slicers|Clear all filters",
    re.I,
)


@dataclass(frozen=True)
class SlicerDefinition:
    """How one control on *this* report is operated. Values are opaque to core."""

    id: str
    role_name: str
    kind: SlicerKind
    cascade_rank: int | None = None
    host: SlicerHost = "report"


class Slicer:
    """Composed by a domain page. Definitions and settle come from the caller."""

    def __init__(
        self,
        page: Page,
        frame: FrameLocator,
        definitions: Sequence[SlicerDefinition] = (),
        settle: Callable[..., bool | None] | None = None,
        clear_all_control: Locator | None = None,
        timeout_ms: int | None = None,
    ) -> None:
        self._page = page
        self._frame = frame
        self._definitions = tuple(definitions)
        self._by_id = {item.id: item for item in self._definitions}
        self._settle = settle if settle is not None else (lambda *_a, **_k: None)
        self._timeout = (
            timeout_ms if timeout_ms is not None else settings.DEFAULT_TIMEOUT
        )
        self.clear_all_control = clear_all_control or self._frame.get_by_role(
            "button",
            name=_CLEAR_ALL_NAME,
        )

    def _definition(self, slicer_id: str) -> SlicerDefinition:
        try:
            return self._by_id[slicer_id]
        except KeyError as exc:
            known = ", ".join(sorted(self._by_id)) or "(none)"
            raise KeyError(
                f"Unknown slicer id {slicer_id!r}. Known: {known}"
            ) from exc

    def _call_settle(self, kind: SettleKind, **kwargs) -> bool:
        return bool(self._settle(kind, **kwargs))

    def _not_wired(self, method: str) -> NoReturn:
        raise NotImplementedError(
            f"Slicer.{method} is not wired yet (later Strangler Fig step)."
        )

    def control(self, slicer_id: str) -> Locator:
        definition = self._definition(slicer_id)
        if definition.kind == "search":
            self._not_wired("control(search)")
        return self._frame.get_by_role(
            "combobox", name=definition.role_name, exact=True
        )

    def option_by_role(self, option_name: str, role_name: str) -> Locator:
        return self._frame.get_by_role(
            "listbox", name=role_name, exact=True
        ).get_by_role("option", name=option_name, exact=True)

    def close_open(self) -> None:
        self._page.keyboard.press("Escape")
        self._page.keyboard.press("Escape")

    def _dropdown_shows_selection(
        self, dropdown: Locator, option_name: str
    ) -> bool:
        try:
            text = (dropdown.inner_text() or "").replace("\u200f", "")
            return option_name in text
        except Exception:
            return False

    def select(self, slicer_id: str, value: str) -> None:
        definition = self._definition(slicer_id)
        if definition.kind != "dropdown":
            raise ValueError(
                f"Slicer.select expects kind='dropdown', got {definition.kind!r} "
                f"for id {slicer_id!r}"
            )

        dropdown = self.control(slicer_id)
        changed = False
        for attempt in range(2):
            self.close_open()
            self._call_settle("before_select")
            dropdown.click(force=True)
            option = self.option_by_role(value, definition.role_name)
            expect(option).to_be_visible(timeout=self._timeout)
            option.scroll_into_view_if_needed()
            option.click(force=True)
            changed = self._call_settle("after_select")
            selected = self._dropdown_shows_selection(dropdown, value)
            if selected or changed or attempt == 1:
                break

        report = get_current_report()
        if report is not None:
            report.log_filter(definition.role_name, value)

    def select_many(self, slicer_id: str, values: Sequence[str]) -> None:
        self._not_wired("select_many")

    def search(self, slicer_id: str, query: str) -> None:
        self._not_wired("search")

    def clear_search(self, slicer_id: str) -> None:
        self._not_wired("clear_search")

    def clear_all(self) -> None:
        self._call_settle("before_clear")
        self.clear_all_control.click()
        self._call_settle(
            "after_clear",
            required=False,
            timeout_ms=self._timeout,
        )
