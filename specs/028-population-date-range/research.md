# Phase 0 Research: Population Date Range for the Three-Chart Total

**Feature**: 028-population-date-range | **Date**: 2026-10-17

No `NEEDS CLARIFICATION` markers remain.

## Decision 1 — The gap is a filter window, and the assertion stays strict

**Decision**: Do not change the hour, dates, or district readers. Do not mark
`test_hour_date_and_district_sums_match` expected-fail. Set an explicit wide date
range before the three reads.

**Rationale**: On 2026-10-15 the dates menu table contained `1118` body rows and summed
to `140493`. `aria-rowcount` was `1119` (the header plus those rows). No `סה"כ` row was
skipped and no cell failed integer parsing. The hour chart was `141493`. A default date
slider can leave one visual on a shorter window than the others. An explicit range puts
all three on the same window. If they still differ, the strict assertion fails.

**Alternatives considered**:

- *Treat the `1000` as a parser defect*: rejected. The scrolled column was fully read.
- *Mark the test expected-fail*: rejected. The user ruled that out.

## Decision 2 — `set_date_range` uses the existing start and end fields

**Decision**: `set_date_range(start_date, end_date)` fills `תאריך התחלה` and
`תאריך סיום` through the same path as `set_between_dates`. It does not search for a
new "From" / "To" control. `set_between_dates` stays for callers that already pass a
narrower pair and do not need this settle wait.

**Rationale**: Those two accessible-name prefixes are already the population page's date
inputs. The clear-baseline test passes `01/09/2026` and `01/10/2026` through them.

**Alternatives considered**:

- *Add a second pair of locators*: rejected. The page already has this pair.
- *Edit `core/components/slicer.py`*: rejected. The labels are domain text, and this slice must not edit `core/`.

## Decision 3 — Day/month/year, from 1 January 2020 through today

**Decision**: The test passes `01/01/2020` and the current day formatted `DD/MM/YYYY`.
On 17 October 2026 that end value is `17/10/2026`. The test builds the end value from
the local date so the range stays wide after that day.

**Rationale**: The population page already accepts day/month/year strings. `01/01/2020`
is 1 January 2020 in that form. A month/day string such as `10/17/2026` is not the
page's format.

**Alternatives considered**:

- *Hard-code `17/10/2026` forever*: rejected. After that day the range would stop being "through today".
- *Use month/day/year because the example looks American*: rejected. The existing date calls on this page are day/month/year.

## Decision 4 — Wait for a repeated total-card read

**Decision**: After both fields are committed, poll `read_card("total")` until two
consecutive reads match, with the same deadline style as `clear_filters` (`self.timeout`
and a short pause between reads). The total card must be visible before that poll.

**Rationale**: Power BI refreshes the visuals after a slicer commit. `clear_filters`
already treats a repeated total-card value as the settled page. A network-idle wait is
not how this page detects that refresh.

**Alternatives considered**:

- *Return as soon as the fields are filled*: rejected. The charts can still show the previous window.
- *Wait only for the dates chart title*: rejected. The title is already on the page and does not prove the numbers moved.

## Decision 5 — Clear, then the range, then Sum, then one read each

**Decision**: `test_hour_date_and_district_sums_match` calls `clear_filters()`, then
`set_date_range(...)`, then `set_district_aggregation("sum")`, then reads the hour,
dates, and district totals once each. The assertion is
`hour_total == district_total == dates_total`.

**Rationale**: `clear_filters` removes slicer values, so a range applied earlier would
be lost. Sum is applied after the range so the district chart is in Sum mode on the
refreshed page. Reading the dates total once avoids opening the menu table twice.

**Alternatives considered**:

- *Set the range before `clear_filters`*: rejected. The clear would remove it.
- *Keep the two separate equality asserts and read the dates total twice*: rejected. The user asked for one strict three-way comparison, and the second dates read only repeats the table open.
