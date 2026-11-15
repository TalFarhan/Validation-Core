import re
import time
from collections.abc import Callable
from typing import TypeVar

from playwright.sync_api import Locator, Page, expect

from config.settings import settings
from core.errors import LoadTimeoutError

T = TypeVar("T")


class BasePage:
    ACTIVE_TAB_CLASS = re.compile(r"(selected|active)")

    def __init__(self, page: Page):
        self.page = page
        self.timeout = settings.DEFAULT_TIMEOUT

    @staticmethod
    def _read_kpi_value(kpi_locator: Locator) -> int:
        text = kpi_locator.locator("p").last.text_content() or ""
        return int(text.strip().replace(",", ""))

    def _timeout_steps(self, total_ms: int | None = None) -> list[int]:
        """
        Build progressive wait budgets that sum to at most ``total_ms``.

        Example with DEFAULT_TIMEOUT=60000 and steps 3s/8s/20s:
        ``[3000, 8000, 20000, 29000]`` — success often returns in the first slice;
        only persistent failures burn the full budget, and optional ``recover``
        runs between slices.
        """
        budget = total_ms if total_ms is not None else self.timeout
        budget = max(1, int(budget))
        configured = settings.TIMEOUT_STEPS_MS or (3000, 8000, 20000)
        steps: list[int] = []
        remaining = budget
        for chunk in configured:
            if remaining <= 0:
                break
            take = min(int(chunk), remaining)
            steps.append(take)
            remaining -= take
        if remaining > 0:
            steps.append(remaining)
        return steps or [budget]

    def retry_with_backoff(
        self,
        attempt: Callable[[int], T],
        *,
        description: str,
        timeout_ms: int | None = None,
        recover: Callable[[], None] | None = None,
    ) -> T:
        """
        Run ``attempt(step_timeout_ms)`` with increasing budgets.

        On failure, optionally call ``recover()`` then retry with a larger budget.
        """
        last_error: BaseException | None = None
        steps = self._timeout_steps(timeout_ms)
        for index, step_ms in enumerate(steps):
            try:
                return attempt(step_ms)
            except Exception as exc:  # noqa: BLE001 — retry across backoff steps
                last_error = exc
                if index >= len(steps) - 1:
                    break
                if recover is not None:
                    try:
                        recover()
                    except Exception:
                        pass
        assert last_error is not None
        raise LoadTimeoutError(
            description, steps_ms=steps, cause=last_error
        ) from last_error

    def wait_for_visible(
        self,
        locator: Locator,
        *,
        timeout_ms: int | None = None,
        recover: Callable[[], None] | None = None,
        description: str | None = None,
    ) -> None:
        label = description or "element to be visible"

        def _attempt(step_ms: int) -> None:
            expect(locator).to_be_visible(timeout=step_ms)

        self.retry_with_backoff(
            _attempt,
            description=label,
            timeout_ms=timeout_ms,
            recover=recover,
        )

    def wait_for_kpi_update(
        self,
        kpi_locator: Locator,
        previous_value: int,
        *,
        required: bool = True,
        timeout_ms: int | None = None,
    ) -> None:
        # required=False means "change is optional" — do not burn DEFAULT_TIMEOUT
        # waiting for a value that may never change (e.g. clear when already clear).
        if timeout_ms is None:
            timeout_ms = (
                self.timeout if required else settings.KPI_OPTIONAL_WAIT_MS
            )
        deadline = time.monotonic() + timeout_ms / 1000
        while time.monotonic() < deadline:
            if self._read_kpi_value(kpi_locator) != previous_value:
                return
            time.sleep(0.15)

        if required:
            current = self._read_kpi_value(kpi_locator)
            raise LoadTimeoutError(
                f"KPI update (was {previous_value}, still {current})",
                steps_ms=[timeout_ms],
            )

    def assert_tab_active(self, tab_locator: Locator) -> None:
        expect(tab_locator).to_have_class(self.ACTIVE_TAB_CLASS, timeout=self.timeout)

    def assert_tab_inactive(self, tab_locator: Locator) -> None:
        expect(tab_locator).not_to_have_class(self.ACTIVE_TAB_CLASS, timeout=self.timeout)
