"""Generic Power BI slicer operator (Layer 2).

Knows how to talk to dropdowns, checkboxes, search fields, and clear-all.
Does not know any report's business filter names. Domain pages supply
``SlicerDefinition`` rows and a settle hook.
"""

from __future__ import annotations

import re
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Literal

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
    "before_search",
    "after_search",
]

_CLEAR_ALL_NAME = re.compile(
    r"נקה את כל|Clear all slicers|Clear all filters",
    re.I,
)
_SEARCH_PLACEHOLDER = re.compile(r"חיפוש|Search", re.I)


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

    def control(self, slicer_id: str) -> Locator:
        definition = self._definition(slicer_id)
        name = definition.role_name
        if definition.kind == "search":
            field, _submit, _clear = self._search_parts(slicer_id)
            return field
        if definition.kind == "checkbox":
            # Open list (combobox) or always-visible checklist (listbox).
            return self._frame.get_by_role("combobox", name=name, exact=True).or_(
                self._frame.get_by_role("listbox", name=name, exact=True)
            )
        return self._frame.get_by_role("combobox", name=name, exact=True)

    def _search_parts(self, slicer_id: str) -> tuple[Locator, Locator, Locator]:
        definition = self._definition(slicer_id)
        if definition.kind != "search":
            raise ValueError(
                f"Search host requires kind='search', got {definition.kind!r}"
            )
        if definition.host == "visual_sandbox":
            host = self._frame.frame_locator("iframe.visual-sandbox")
        else:
            host = self._frame
        field = host.locator("input.input-field").or_(
            host.get_by_placeholder(_SEARCH_PLACEHOLDER)
        ).first
        submit = host.locator("button.input-button").first
        clear = host.locator("button.input-button").nth(1)
        return field, submit, clear

    def option_by_role(self, option_name: str, role_name: str) -> Locator:
        return self._frame.get_by_role(
            "listbox", name=role_name, exact=True
        ).get_by_role("option", name=option_name, exact=True)

    def _choice(self, option_name: str, role_name: str) -> Locator:
        listbox = self._frame.get_by_role("listbox", name=role_name, exact=True)
        return listbox.get_by_role("option", name=option_name, exact=True).or_(
            listbox.get_by_role("checkbox", name=option_name, exact=True)
        )

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
        definition = self._definition(slicer_id)
        if definition.kind != "checkbox":
            raise ValueError(
                f"Slicer.select_many expects kind='checkbox', got "
                f"{definition.kind!r} for id {slicer_id!r}"
            )
        if not values:
            return

        self.close_open()
        self._call_settle("before_select")
        self.control(slicer_id).click(force=True)
        for value in values:
            choice = self._choice(value, definition.role_name)
            expect(choice).to_be_visible(timeout=self._timeout)
            choice.scroll_into_view_if_needed()
            choice.click(force=True)
        self.close_open()
        self._call_settle("after_select")

        report = get_current_report()
        if report is not None:
            for value in values:
                report.log_filter(definition.role_name, value)

    def ordered_ids(self, slicer_ids: Sequence[str]) -> list[str]:
        """Stable sort: lower cascade_rank first; missing rank keeps original order."""
        indexed = list(enumerate(slicer_ids))

        def sort_key(item: tuple[int, str]) -> tuple[int, int]:
            position, slicer_id = item
            rank = self._definition(slicer_id).cascade_rank
            return (rank if rank is not None else 10**9, position)

        return [slicer_id for _position, slicer_id in sorted(indexed, key=sort_key)]

    def apply(self, selections: dict[str, str]) -> None:
        """Apply id→label map in cascade order. Ids are opaque to this layer."""
        for slicer_id in self.ordered_ids(list(selections.keys())):
            definition = self._definition(slicer_id)
            value = selections[slicer_id]
            if definition.kind == "dropdown":
                self.select(slicer_id, value)
            elif definition.kind == "checkbox":
                self.select_many(slicer_id, [value])
            elif definition.kind == "search":
                self.search(slicer_id, value)
            else:
                raise ValueError(f"Unsupported slicer kind {definition.kind!r}")

    def search(self, slicer_id: str, query: str) -> None:
        field, submit, _clear = self._search_parts(slicer_id)
        self._call_settle("before_search")
        expect(field).to_be_visible(timeout=self._timeout)
        field.click(force=True)
        field.fill(str(query))
        submit.click(force=True)
        self._call_settle("after_search", required=True)

    def clear_search(self, slicer_id: str) -> None:
        field, _submit, clear_btn = self._search_parts(slicer_id)
        try:
            current = (field.input_value(timeout=1000) or "").strip()
        except Exception:
            current = ""
        if not current and clear_btn.count() == 0:
            return
        self._call_settle("before_search")
        if clear_btn.count() > 0:
            clear_btn.click(force=True)
        else:
            field.click(force=True)
            field.fill("")
            field.press("Enter")
        self._call_settle("after_search", required=False)

    def clear_all(self, *, wait_full_timeout: bool = True) -> None:
        self._call_settle("before_clear")
        self.clear_all_control.click()
        if wait_full_timeout:
            self._call_settle(
                "after_clear",
                required=False,
                timeout_ms=self._timeout,
            )
        else:
            self._call_settle("after_clear", required=False)
