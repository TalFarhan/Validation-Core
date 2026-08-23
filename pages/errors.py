"""Typed failures so reports can distinguish load timeouts from data bugs."""


class ExpandHierarchyUnavailable(AssertionError):
    """הסתעפות missing, disabled, or click did not change the visual."""

    def __init__(self, chart_key: str, reason: str):
        super().__init__(
            f"הסתעפות unavailable on chart '{chart_key}': {reason}"
        )
        self.chart_key = chart_key
        self.reason = reason


class LoadTimeoutError(AssertionError):
    """UI did not become ready within the progressive wait budget."""

    def __init__(
        self,
        description: str,
        *,
        steps_ms: list[int],
        cause: BaseException | None = None,
    ):
        total = sum(steps_ms)
        message = (
            f"[LOAD_TIMEOUT] {description} — לא הופיע בזמן "
            f"(תקציב={total}ms, צעדים={steps_ms}ms). "
            f"זה כשל טעינה/המתנה, לא בהכרח באג נתונים."
        )
        super().__init__(message)
        self.description = description
        self.steps_ms = steps_ms
        self.cause = cause
