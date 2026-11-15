# Phase 0 Research: Population Chart Scope

**Feature**: 022-population-chart-scope | **Date**: 2026-10-15

No `NEEDS CLARIFICATION` markers remain.

## Decision 1 — Narrow the dates and hour reads on the page

**Decision**: For `DATES_CHART` and `HOUR_CHART` only, `chart_total` builds a locator and calls
`Chart._parse` on it. District, settlement, and any other title still call `Chart.read`.

**Rationale**: A live dates-chart read on 2026-10-14 returned district names (`מחוז צפון` and the
other districts), command names, city names (`ירושלים`, `תל אביב-יפו`, `חיפה`, `ראשון לציון`,
`פתח תקווה`, `אשדוד`, `נתניה`, `אשקלון`, `בני ברק`), scale captions (`0אלף`), and hour ticks
(`00:00` through `16:00`). It returned no date labels. Night mode filled city cells that were
empty in the other two readings, so the sums were `2329401 + 2348962` against an untoggled
`2329400`. The page title scope is not a bounding group, so `scope_host` returns the visible
canvas, and `Chart._container` then takes the outer `visualContainerHost`.

**Alternatives considered**:

- *Skip labels that contain no digit*: rejected. The run that did this dropped every numeric cell.
  The real categories in that wide read also had no digit requirement that separated cities from
  the numbers the test needs.
- *Skip cells above a size cutoff*: rejected. That would hide population numbers and still sum
  district rows that are not the dates chart.
- *Change `Chart._container` in `core/`*: rejected. The request forbids a `core/` edit, and the
  outer-host order is what other reports already use.

## Decision 2 — Nearest container that has the title, a number, and no sibling chart title

**Decision**: Start at the title text node in the report frame. Walk ancestor nodes whose class
contains `visualContainer` or `visual-container`, nearest first. Keep the first ancestor that
has at least one numeric token and whose text does not also contain a different title from
`DISTRICT_CHART`, `HOUR_CHART`, `DATES_CHART`, and `SETTLEMENT_CHART`. The title being read is
allowed. `visualContainerHost` is eligible only when a closer box failed those two checks.

**Rationale**: An earlier core experiment that stopped at the innermost `visualContainer` and
skipped the host made the dates chart empty: the title's closest box was a header with no
numbers. Walking outward until numbers appear, and stopping when another chart title appears,
avoids both the empty header and the page-wide host.

**Alternatives considered**:

- *Always the innermost `visualContainer`*: rejected. That read was empty.
- *Always the outer host*: rejected. That is the current spill.

## Decision 3 — Sixty seconds on this page, and a visible card before clear

**Decision**: `AlertsPopulationPage.__init__` sets `self.timeout = 60_000` before it constructs
`KPI` and `Chart`. `before_report_ready_check` returns as soon as the district chart is visible.
It clicks the page switcher only when that control is visible and the district chart is not.
`clear_filters` waits until the total population card is visible, then calls clear.

**Rationale**: `test_clear_restores_population_snapshot` failed in setup with
`LoadTimeoutError` at 30 seconds on the report-ready visual. `navigate` uses `self.timeout` for
that wait. Setting it on the population page lengthens that wait without editing `ReportShell`.
Clicking the page switcher before it exists burned the same budget. The clear click needs the
card on screen so a slow paint does not start the filter change early.

**Alternatives considered**:

- *Raise `settings.DEFAULT_TIMEOUT`*: rejected. That changes every report.
- *Edit the ready loop in `core/portal/page.py`*: rejected. Layer 0 stays as it is.

## Decision 4 — What "no core diff" means

**Decision**: The implementation edits `pages/alerts_analysis/population_page.py` only. It does
not stage, revert, or reformat anything under `core/`. Earlier uncommitted core edits from
feature 020 stay in the working tree. This slice adds no core change.

**Rationale**: The request says the numeric filter and the Sum click succeeded, and it forbids a
`core/` edit for the spill.

**Alternatives considered**:

- *Revert `core/` so `git diff core/` is empty against HEAD*: rejected. That removes the canvas
  host the card tests use.
