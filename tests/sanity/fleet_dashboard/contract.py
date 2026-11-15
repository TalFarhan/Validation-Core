"""Pure checks for the fleet golden record."""

from __future__ import annotations

import re
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

import yaml

_GOLDEN_RECORD = (
    Path(__file__).resolve().parents[3] / "data" / "fleet" / "db_sanity_all.yaml"
)

_REQUIRED_SECTIONS = (
    "summary",
    "units_breakdown",
    "pull_source_breakdown",
    "vehicle_categories",
    "credit_reasons_summary",
    "credited_vehicles_details",
)

_SUMMARY_KEYS = (
    "total_vehicles_in_use",
    "total_vehicles_received",
    "vehicles_transferred",
    "vehicles_credited",
)

_BREAKDOWNS = (
    ("units_breakdown", "total_vehicles_in_use"),
    ("pull_source_breakdown", "total_vehicles_in_use"),
    ("credit_reasons_summary", "vehicles_credited"),
)

_LEDGER_TEXT_FIELDS = (
    "סיבת זיכוי",
    "תאריך זיכוי",
    "מקור משיכה",
    "יחידה",
    "יחידת משנה",
)

_CREDIT_DATE = re.compile(
    r"^(0[1-9]|[12][0-9]|3[01])/(0[1-9]|1[0-2])/\d{4}$"
)
_RATE_TOKEN = re.compile(r"(\d+(?:\.\d+)?)%")


def load_sanity_record(path: Path | None = None) -> dict:
    """Load the fleet golden record and require its top-level sections."""
    target = _GOLDEN_RECORD if path is None else path
    with target.open(encoding="utf-8") as handle:
        record = yaml.safe_load(handle)
    if not isinstance(record, dict):
        raise AssertionError(
            _mismatch("golden", "record", record, "mapping")
        )
    for key in _REQUIRED_SECTIONS:
        if key not in record:
            raise AssertionError(f"missing {key}")
    return record


def assert_summary(record: dict) -> None:
    """Require the four counters and keep in-use at or below received."""
    summary = record["summary"]
    if not isinstance(summary, dict):
        raise AssertionError(_mismatch("summary", "summary", summary, "mapping"))
    values: dict[str, int] = {}
    for key in _SUMMARY_KEYS:
        if key not in summary:
            raise AssertionError(_mismatch("summary", key, None, "present"))
        values[key] = _require_count("summary", key, summary[key])
    in_use = values["total_vehicles_in_use"]
    received = values["total_vehicles_received"]
    if in_use > received:
        raise AssertionError(
            _mismatch("summary", "total_vehicles_in_use", in_use, f"<= {received}")
        )


def assert_breakdowns(record: dict) -> None:
    """Sum each breakdown to its summary counter. Transferred has no sum."""
    summary = record["summary"]
    for section, summary_key in _BREAKDOWNS:
        mapping = record[section]
        if not isinstance(mapping, dict):
            raise AssertionError(_mismatch(section, section, mapping, "mapping"))
        total = 0
        for key, value in mapping.items():
            total += _require_count(section, str(key), value)
        expected = summary[summary_key]
        if total != expected:
            raise AssertionError(
                f"{section}: sum={total} expected {summary_key}={expected}"
            )


def assert_category_rates(record: dict) -> None:
    """Check each stored rate against actual / standard, and sum the actuals."""
    rows = record["vehicle_categories"]
    if not isinstance(rows, list):
        raise AssertionError(
            _mismatch("vehicle_categories", "rows", rows, "list")
        )
    actual_total = 0
    seen: set[str] = set()
    for row in rows:
        if not isinstance(row, dict):
            raise AssertionError(
                _mismatch("vehicle_categories", "row", row, "mapping")
            )
        category = row.get("category")
        if not isinstance(category, str) or not category.strip():
            raise AssertionError(
                _mismatch("vehicle_categories", "category", category, "non-empty string")
            )
        if category in seen:
            raise AssertionError(
                _mismatch("vehicle_categories", category, category, "unique category")
            )
        seen.add(category)
        actual = _require_count("vehicle_categories", category, row.get("actual"))
        standard = row.get("standard")
        if isinstance(standard, bool) or not isinstance(standard, int) or standard < 1:
            raise AssertionError(
                _mismatch(
                    "vehicle_categories",
                    category,
                    standard,
                    "standard int >= 1",
                )
            )
        computed = _computed_rate(actual, standard)
        stored = _stored_rate(row.get("rate"), category)
        if stored != computed:
            raise AssertionError(
                "vehicle_categories."
                f"{category}: rate={row.get('rate')!r} computed={computed!r} "
                f"(actual={actual}, standard={standard})"
            )
        actual_total += actual
    received = record["summary"]["total_vehicles_received"]
    if actual_total != received:
        raise AssertionError(
            "vehicle_categories: "
            f"sum={actual_total} expected total_vehicles_received={received}"
        )


def assert_ledger(record: dict) -> None:
    """Require a complete credited-vehicle row for every credited vehicle."""
    rows = record["credited_vehicles_details"]
    reasons = record["credit_reasons_summary"]
    credited = record["summary"]["vehicles_credited"]
    if not isinstance(rows, list):
        raise AssertionError(
            _mismatch("credited_vehicles_details", "rows", rows, "list")
        )
    if not isinstance(reasons, dict):
        raise AssertionError(
            _mismatch("credit_reasons_summary", "reasons", reasons, "mapping")
        )
    if len(rows) != credited:
        raise AssertionError(
            _mismatch("credited_vehicles_details", "len", len(rows), credited)
        )
    seen_vehicles: set[int] = set()
    reason_counts: dict[str, int] = {}
    for index, row in enumerate(rows):
        vehicle = _vehicle_number(row, index)
        if vehicle in seen_vehicles:
            raise AssertionError(
                _mismatch(
                    "credited_vehicles_details",
                    str(vehicle),
                    vehicle,
                    "unique vehicle number",
                )
            )
        seen_vehicles.add(vehicle)
        for field in _LEDGER_TEXT_FIELDS:
            _require_text(row, vehicle, field)
        credit_date = row["תאריך זיכוי"]
        if _CREDIT_DATE.fullmatch(credit_date.strip()) is None:
            raise AssertionError(
                _mismatch(
                    "credited_vehicles_details",
                    str(vehicle),
                    credit_date,
                    "DD/MM/YYYY",
                )
            )
        reason = row["סיבת זיכוי"].strip()
        if reason not in reasons:
            raise AssertionError(
                _mismatch(
                    "credited_vehicles_details",
                    str(vehicle),
                    reason,
                    "key of credit_reasons_summary",
                )
            )
        reason_counts[reason] = reason_counts.get(reason, 0) + 1
    if reason_counts != {str(key): int(value) for key, value in reasons.items()}:
        raise AssertionError(
            _mismatch(
                "credited_vehicles_details",
                "סיבת זיכוי",
                reason_counts,
                reasons,
            )
        )


def _mismatch(section: str, key: str, actual: object, expected: object) -> str:
    return f"{section}.{key}: actual={actual!r} expected={expected!r}"


def _require_count(section: str, key: str, value: object) -> int:
    """Reject bools. YAML ints are the only accepted counts."""
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise AssertionError(_mismatch(section, key, value, "int >= 0"))
    return value


def _computed_rate(actual: int, standard: int) -> str:
    ratio = (Decimal(actual) / Decimal(standard)) * Decimal(100)
    quantized = ratio.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return f"{quantized}%"


def _stored_rate(raw: object, category: str) -> str:
    """Read the leading percent and ignore a trailing citation suffix."""
    if not isinstance(raw, str):
        raise AssertionError(
            _mismatch("vehicle_categories", category, raw, "percent string")
        )
    match = _RATE_TOKEN.search(raw)
    if match is None:
        raise AssertionError(
            _mismatch("vehicle_categories", category, raw, "percent string")
        )
    return f"{match.group(1)}%"


def _vehicle_number(row: object, index: int) -> int:
    label = f"row {index}"
    if not isinstance(row, dict) or "מספר רכב" not in row:
        raise AssertionError(f"credited_vehicles_details.{label}: missing מספר רכב")
    vehicle = row["מספר רכב"]
    if isinstance(vehicle, bool) or not isinstance(vehicle, int):
        raise AssertionError(
            _mismatch("credited_vehicles_details", label, vehicle, "int")
        )
    return vehicle


def _require_text(row: dict, vehicle: int, field: str) -> None:
    if field not in row:
        raise AssertionError(
            f"credited_vehicles_details.{vehicle}: missing {field}"
        )
    value = row[field]
    if not isinstance(value, str) or not value.strip():
        raise AssertionError(
            f"credited_vehicles_details.{vehicle}: missing {field}"
        )
