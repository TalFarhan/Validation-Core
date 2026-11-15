# Data Model: Fleet DB Sanity and Validation Tests

**Feature**: 039-fleet-db-sanity | **Date**: 2026-10-29

No new stored tables. The golden file already exists. The only edit is removing `[cite: 1]` from the four rate lines so each `rate` is a quoted percent string.

## Golden document

`data/fleet/db_sanity_all.yaml`. Top-level keys are required. The checker fails with the missing key's name.

### Summary

| Field | Type | Rule |
|-------|------|------|
| `total_vehicles_in_use` | int ≥ 0 | Card `in_use`. Equals the sum of `units_breakdown` and the sum of `pull_source_breakdown`. |
| `total_vehicles_received` | int ≥ 0 | Card `total`. Equals the sum of `vehicle_categories[].actual`. Greater than or equal to in use. |
| `vehicles_transferred` | int ≥ 0 | Card `allocated`. No breakdown is summed to this field. |
| `vehicles_credited` | int ≥ 0 | Card `withdrawn`. Equals the sum of `credit_reasons_summary` and the length of the ledger. |

Not a rule: `total_vehicles_received = total_vehicles_in_use + vehicles_credited + vehicles_transferred`.

### Units breakdown

Mapping of unit name → in-use count. Every value is an int ≥ 0. The sum equals `total_vehicles_in_use`. Names are data, not code.

On the current file the sum is 358 (`מחוז צפון` 71, `מחוז ירושלים והמרכז` 57, `מפקע"ר` 52, `מחוז חיפה` 48, `מפקדת יערה` 48, `מחוז דרום` 44, `מחוז דן` 38).

UI chart key: `unit`.

### Pull-source breakdown

Mapping of pull source → in-use count. Every value is an int ≥ 0. The sum equals `total_vehicles_in_use`.

On the current file the sum is 358 (`אורגני` 263, `יר"ם` 68, `שכור` 23, `מרכז הובלה` 4).

UI chart key: `source`.

These keys describe vehicles in use. They are not a catalog for ledger pull sources.

### Vehicle category

List of rows.

| Field | Type | Rule |
|-------|------|------|
| `category` | non-empty string | Unique in the list. UI looks for this label on chart key `category`. |
| `actual` | int ≥ 0 | Sum across rows equals `total_vehicles_received`. |
| `standard` | int ≥ 1 | Staffing standard. A zero fails the row and does not divide. |
| `rate` | string | Numeric value equals `actual / standard × 100`, half-up to two decimal places, rendered with a trailing `%`. |

Computed rates on the current file:

| Category | Actual | Standard | Rate |
|----------|--------|----------|------|
| אוטובוס | 3 | 525 | 0.57% |
| אמבולנס | 11 | 65 | 16.92% |
| אמצעי הובלה | 139 | 406 | 34.24% |
| רכב קל | 210 | 1955 | 10.74% |

The category chart is checked for `actual` only. `standard` and `rate` stay file checks.

### Credit-reason summary

Mapping of credit reason → credited count. Every value is an int ≥ 0. The sum equals `vehicles_credited`.

On the current file the sum is 6 (`אחר` 3, `פקודת רידוד פיקודית` 3).

UI chart key: `withdrawal`.

### Credited vehicle row

List of rows. Length equals `vehicles_credited`. Grouping by `סיבת זיכוי` equals `credit_reasons_summary`.

| Field | Type | Rule |
|-------|------|------|
| `סיבת זיכוי` | non-empty string | Must be a key of `credit_reasons_summary`. |
| `תאריך זיכוי` | string `DD/MM/YYYY` | Day 01–31, month 01–12, four-digit year. |
| `מקור משיכה` | non-empty string | Not required to be a key of `pull_source_breakdown`. |
| `יחידה` | non-empty string | Not required to be a key of `units_breakdown`. |
| `יחידת משנה` | non-empty string | Present and non-blank. |
| `מספר רכב` | int | Unique in the ledger. |

The current file has six rows and six distinct vehicle numbers: `83304602`, `238161`, `36778301`, `123123`, `1111111`, `89071202`.

UI: tab `withdrawn`, search by `מספר רכב`. The visible row text must contain the other five fields after label normalization.

## Label normalization (UI compare only)

Fold `״` and `"` to `"`, strip, and collapse whitespace. File-to-file checks do not fold.

## Validation rules

1. Load uses `yaml.safe_load` and UTF-8 from a path under the repository `data/fleet/` directory.
2. A missing top-level section, a missing ledger field, a duplicate vehicle number, a non-positive standard, or a sum mismatch fails.
3. Messages include the section, the key or vehicle number, the actual value, and the expected value.
4. UI tests clear filters and search before reading. They do not pass a district, source, or category into `apply_filters`.
5. An empty chart read skips that UI test only.
6. `core/` does not parse this file.

## State transitions

```text
structural test
    → load_sanity_record()
    → assert_summary / assert_breakdowns / assert_category_rates / assert_ledger
    → fail with section, key, actual, expected

UI test
    → load_sanity_record()
    → reset_dashboard_filters()
    → read one surface (KPI role, one chart key, or withdrawn-tab search)
    → compare to the loaded section
    → skip only when that chart exposes no golden label
```
