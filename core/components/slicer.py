"""Generic Power BI slicer operator (Layer 2).

Knows how to talk to dropdowns, checkboxes, search fields, and clear-all.
Does not know any report's business filter names. Domain pages supply
``SlicerDefinition`` rows and a settle hook; interaction methods are
wired in later Strangler steps.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Literal, NoReturn

from playwright.sync_api import FrameLocator, Locator, Page

SlicerKind = Literal["dropdown", "checkbox", "search"]
SlicerHost = Literal["report", "visual_sandbox"]
SettleKind = Literal["after_select", "after_clear", "after_search"]


@dataclass(frozen=True)
class SlicerDefinition:
    """How one control on *this* report is operated. Values are opaque to core."""

    id: str
    role_name: str
    kind: SlicerKind
    cascade_rank: int | None = None
    host: SlicerHost = "report"


class Slicer:
    """Composed by a domain page. Stub methods must not be called until US1+."""

    def __init__(
        self,
        page: Page,
        frame: FrameLocator,
        definitions: Sequence[SlicerDefinition] = (),
        settle: Callable[..., None] | None = None,
        clear_all_control: Locator | None = None,
    ) -> None:
        self._page = page
        self._frame = frame
        self._definitions = tuple(definitions)
        self._settle = settle if settle is not None else (lambda *_a, **_k: None)
        self.clear_all_control = clear_all_control

    def _not_wired(self, method: str) -> NoReturn:
        raise NotImplementedError(
            f"Slicer.{method} is a Layer 2 stub; the domain page still owns "
            "filter interaction until the Strangler Fig move."
        )

    def select(self, slicer_id: str, value: str) -> None:
        self._not_wired("select")

    def select_many(self, slicer_id: str, values: Sequence[str]) -> None:
        self._not_wired("select_many")

    def search(self, slicer_id: str, query: str) -> None:
        self._not_wired("search")

    def clear_search(self, slicer_id: str) -> None:
        self._not_wired("clear_search")

    def clear_all(self) -> None:
        self._not_wired("clear_all")

    def close_open(self) -> None:
        self._not_wired("close_open")

    def control(self, slicer_id: str) -> Locator:
        del slicer_id
        self._not_wired("control")

    def option_by_role(self, option_name: str, role_name: str) -> Locator:
        del option_name, role_name
        self._not_wired("option_by_role")
