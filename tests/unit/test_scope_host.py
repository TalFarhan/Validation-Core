"""Unit tests for scope host resolution (Layer 2). No browser."""

import re
from pathlib import Path


class FakeLocator:
    """Records filter calls. ``first`` is this locator, matching a resolved node."""

    def __init__(
        self,
        count: int,
        label: str,
        *,
        text_count: int = 0,
        bounding_count: int = 0,
    ):
        self._count = count
        self.label = label
        self._text_count = text_count
        self._bounding_count = bounding_count
        self.filter_kwargs = None

    def count(self) -> int:
        return self._count

    @property
    def first(self):
        return self

    def filter(self, **kwargs):
        if "has_text" in kwargs:
            return FakeLocator(
                self._text_count,
                "containing",
                bounding_count=self._bounding_count,
            )
        if "has" in kwargs:
            return FakeLocator(self._bounding_count, "bounding")
        child = FakeLocator(self._count, "visible-canvas")
        child.filter_kwargs = kwargs
        return child

    def locator(self, selector):
        parent = FakeLocator(self._count, "canvas-parent")
        parent.filter_kwargs = self.filter_kwargs
        return parent


class FakeFrame:
    """Records role and locator queries used by ``scope_host``."""

    def __init__(
        self,
        named_count: int = 0,
        containing_count: int = 0,
        bounding_count: int | None = None,
    ):
        self.named_count = named_count
        self.containing_count = containing_count
        self.bounding_count = (
            containing_count if bounding_count is None else bounding_count
        )
        self.role_calls = []
        self.locator_selectors = []

    def get_by_role(self, role, name=None):
        self.role_calls.append((role, name))
        if name is not None:
            return FakeLocator(self.named_count, "named")
        return FakeLocator(
            0,
            "groups",
            text_count=self.containing_count,
            bounding_count=self.bounding_count,
        )

    def locator(self, selector):
        self.locator_selectors.append(selector)
        return FakeLocator(1, "containers")


def test_blank_scope_returns_the_frame():
    from core.components.visual import scope_host

    frame = FakeFrame(named_count=1, containing_count=1)
    assert scope_host(frame, None) is frame
    assert scope_host(frame, "   ") is frame
    assert frame.role_calls == []
    assert frame.locator_selectors == []


def test_named_group_wins_and_skips_the_canvas():
    from core.components.visual import scope_host

    frame = FakeFrame(named_count=1, containing_count=2)
    result = scope_host(frame, "Section A")
    assert result.label == "named"
    assert frame.locator_selectors == []


def test_unnamed_text_uses_the_visible_canvas():
    from core.components.visual import scope_host

    frame = FakeFrame(named_count=0, containing_count=2)
    result = scope_host(frame, "Section A")
    assert result.label == "visible-canvas"
    assert result.filter_kwargs == {"visible": True}


def test_text_only_group_uses_the_visible_canvas():
    from core.components.visual import scope_host

    frame = FakeFrame(named_count=0, containing_count=1, bounding_count=0)
    result = scope_host(frame, "Section A")
    assert result.label == "visible-canvas"
    assert result.filter_kwargs == {"visible": True}


def test_unresolved_scope_uses_the_visible_canvas():
    from core.components.visual import scope_host

    frame = FakeFrame(named_count=0, containing_count=0)
    result = scope_host(frame, "Section A")
    assert result.label == "visible-canvas"
    assert frame.locator_selectors
    selector = frame.locator_selectors[0]
    assert "visualContainer" in selector
    assert "visual-container-component" in selector
    assert result.filter_kwargs == {"visible": True}
    assert "has_state" not in result.filter_kwargs
    assert "has_text" not in result.filter_kwargs


def test_visual_module_has_no_hebrew():
    source = (
        Path(__file__).resolve().parents[2] / "core" / "components" / "visual.py"
    ).read_text(encoding="utf-8")
    assert re.search(r"[\u0590-\u05FF]", source) is None
