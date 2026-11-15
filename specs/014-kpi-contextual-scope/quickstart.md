# Quickstart: Verifying KPI Contextual Scope

**Feature**: 014-kpi-contextual-scope | **Date**: 2026-10-12

Confirm that `scope=None` is unchanged and that a non-empty `scope` narrows the title search.

## Prerequisites

- Repo checked out; Python 3.11+ venv with `pip install -r requirements.txt`.
- No new dependencies.

## 1. Extract regression (no browser)

```powershell
python -m pytest tests/unit/test_kpi_normalize.py -v
```

Expected: all cases pass. Scope does not touch extract/normalize (including Gauge rows from 013).

## 2. Caller compatibility

`tests/helpers/db_parity_engine.py` must still call `KPI.number(name)` with one argument.

```powershell
rg "kpi\.number\(" tests/helpers/db_parity_engine.py
```

## 3. Regression gate (Constitution III)

```powershell
python -m pytest tests/ui/fleet_dashboard/
```

Expected: 100% pass (portal / `.env` required). Unique fleet titles use the default global path.

## 4. Manual / later e2e (duplicate titles)

From a domain page or REPL, after the report iframe is ready:

```python
kpi.number("היום", scope="Section A")  # opaque strings supplied by the caller
kpi.number("היום", scope="Section B")
```

The two calls MUST resolve different cards. Do not put those section strings into `core/`.

## What "done" looks like

- Unit extract suite green.
- Parity engine unmodified.
- `card` / `read_text` / `value` / `number` accept optional `scope`.
- Fleet smoke green (or `--collect-only` if portal is unavailable).

## Where to look

- Implementation: `core/components/kpi.py` (`_scope_host`, `_resolve_card`).
- Contract: `specs/014-kpi-contextual-scope/contracts/kpi-component.md`.
