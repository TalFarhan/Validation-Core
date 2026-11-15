# Implementation Plan: Hosen Status Screen 1 YAML Sanity

**Branch**: `feature/reportportal-integration` (spec directory `050-hosen-screen1-sanity`) | **Date**: 2026-11-12 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/050-hosen-screen1-sanity/spec.md`

**Note**: This plan is filled by `/speckit-plan`. The formal `tasks.md` is produced by `/speckit-tasks`.
`.specify/feature.json` is repointed to this directory. Planning does not switch the git checkout
(`feature/reportportal-integration`). Spec documents under `specs/049-hasbara-ui-validation/` are not edited.

## Summary

Add a Screen 1 reader on the existing Hosen Status page and a golden-YAML sanity test for the
landing screen of תמ"צ חוסן.

`HosenStatusPage` already opens the report (`DASHBOARD_SEARCH_TERM = תמ"צ חוסן`), waits until
`תמ"צ ארצי - דיווחי קה"א יקל"ר` is visible, and overrides the freshness caption to `מועד רענון`.
This slice adds `read_screen_1_metrics()` and compares it to `data/hosen/db_sanity.yaml`
(`hosen_dashboard.screen_1_landing`). The smoke test stays a one-line `verify_freshness()` call.
There is no SQL client and no new comparison engine.

1. **Filters** — Compose Layer 2 `Slicer` with Hebrew role names that live on the page. Read each
   selected label from `Slicer.control(id)` text. Do not click the slicer. YAML `active_filters`
   is a subset: every listed id matches; extra slicers are ignored.
2. **KPIs** — Read `הערכת קה״א - ממוצע ארצי` and the category cards in that assessment through
   Layer 2 `KPI`. Each card returns `title`, `percentage` (the display string, including `%`),
   and `trend` (`up`, `down`, or `flat`) from a non-canvas arrow on that card.
3. **Resilience table** — Collect `ציון חוסן` with `collect_virtualized_rows`. The page callback
   returns `authority`, `score`, and `status` (`green` or `yellow`) from the row or cell
   background. Extra authorities are ignored.
4. **Survey status** — Page locators read the top-left submitted count, total count, and missing
   authority names. Those locators stay on the page.
5. **Compare** — Private helpers in `tests/sanity/hosen_status_dashboard/test_screen1_sanity.py`
   walk the golden block. YAML integers match grouped or plain digits. YAML strings match
   display text. A visible anchor plus an empty reader fails. A missing anchor skips that block.

## Technical Context

**Language/Version**: Python 3.11+

**Primary Dependencies**: `pytest`, `PyYAML`, Playwright through `bind_dashboard`. Layer 2
`Slicer`, `KPI`, and `collect_virtualized_rows`. No new package.

**Storage**: New golden record `data/hosen/db_sanity.yaml`. No warehouse query and no
`db/clients/hosen.py` in this slice.

**Testing**: `pytest tests/sanity/hosen_status_dashboard/test_screen1_sanity.py`. Hosen smoke
`pytest tests/ui/hosen_status_dashboard/test_dashboard_smoke.py` must still pass. Fleet smoke is
not a gate: Layer 0, Layer 2, and the fleet page are not edited.

**Target Platform**: Windows workstation; Chromium against the organizational Power BI portal.

**Project Type**: Internal validation framework. Domain page `pages/hosen_status/page.py`.
Golden YAML `data/hosen/db_sanity.yaml`. Sanity test `tests/sanity/hosen_status_dashboard/`.

**Performance Goals**: N/A. One catalog open and one landing-screen read per test.

**Constraints**:

- Do not edit `core/portal` or `core/components`. `Slicer.control`, `KPI.card` / `KPI.read_text`,
  and `collect_virtualized_rows` already cover this screen. A trend method and a selected-text
  method are conveniences, not missing universal readers (see research.md).
- Do not edit `data/hasbara/`, `data/credit/`, `data/alerts/`, or those reports' pages and tests.
- Do not import Hasbara, Credit, or Alerts page modules or their sanity helpers.
- Do not add `tests/helpers/` comparison code. The subset walk stays private in the Hosen test.
- Hebrew titles, slicer role names, and survey phrases live in `pages/hosen_status/page.py` or
  in the YAML. They do not move into `core/`.
- Numbers live only in the YAML. The page and the test do not embed `7`, `12`, or `55%`.
- No `sleep`, no `wait_for_timeout`, no network-idle wait, no canvas bitmap sampling.
- `navigate` and `verify_freshness` stay as they are. Root `conftest.py` does not import this page.
- Comments and new Python identifiers stay English. Hebrew is limited to locator constants and YAML values.

**Scale/Scope**:

| Path | Change | Purpose |
|------|--------|---------|
| `pages/hosen_status/page.py` | EDIT | `read_screen_1_metrics()` and the four section readers |
| `data/hosen/db_sanity.yaml` | NEW | `hosen_dashboard.screen_1_landing` golden block |
| `tests/sanity/hosen_status_dashboard/__init__.py` | NEW | Package marker |
| `tests/sanity/hosen_status_dashboard/conftest.py` | NEW | `hosen_status_dashboard` fixture |
| `tests/sanity/hosen_status_dashboard/test_screen1_sanity.py` | NEW | Subset compare against the golden block |
| `tests/ui/hosen_status_dashboard/test_dashboard_smoke.py` | UNCHANGED | `verify_freshness()` smoke |
| `tests/ui/hosen_status_dashboard/conftest.py` | UNCHANGED | Smoke fixture name stays `dashboard` |
| `docs/COVERAGE_CATALOG.md` | EDIT | Hosen YAML block ↔ reader ↔ test rows |
| `core/` | NONE | Existing readers are sufficient |
| hasbara / credit / alerts | NONE | Off-limits |

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Layered portal (I)**: PASS. `HosenStatusPage` already subclasses `ReportShell`. Login, catalog
  search, iframe wait, visual-load timeout, and last-refresh stay in Layer 0. The ready locator
  stays on the domain page. This slice does not add a tab switch.
- **Zero domain leakage (II, NON-NEGOTIABLE)**: PASS. Hebrew titles, slicer role names, the
  resilience title, and the survey phrases stay on `pages/hosen_status/page.py` and in
  `data/hosen/db_sanity.yaml`. `core/` is not edited. Root `conftest.py` does not import the page.
- **Existing tests are the contract (III, NON-NEGOTIABLE)**: PASS. `read_screen_1_metrics` is
  additive. Smoke `verify_freshness` stays. Fleet smoke is not the gate because Layer 0, Layer 2,
  and the fleet navigation surface are not edited. The Hosen smoke module is the navigation gate
  for this page and must stay green.
- **Page object discipline (IV)**: PASS. The sanity test calls the page object. Locators live on
  `HosenStatusPage`. The test body loads YAML and compares.
- **Warehouse as source of truth (V)**: PASS for this slice. The user scoped the work to golden
  YAML, which this repository already keeps in `tests/sanity/` (Hasbara, Credit). No business SQL
  is added to Layer 0 or to a new client. A later warehouse slice would use an existing parity
  helper only after a real client exists; that work is out of scope here.
- **Observability (VI)**: PASS. The new test is a normal pytest sanity test. Existing CSV,
  screenshot, and trace hooks on the shared session stay in place. This slice does not remove them.
- **Extract shared behavior only (VII)**: PASS. The page composes `Slicer`, `KPI`, and
  `collect_virtualized_rows`. Trend classification, color-to-status mapping, survey text, and
  filter role names stay on the domain page. No new generic API is added.

## Project Structure

### Documentation (this feature)

```text
specs/050-hosen-screen1-sanity/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── hosen-screen1-sanity.md
└── tasks.md              # /speckit-tasks — not created here
```

### Source Code (repository root)

```text
pages/hosen_status/page.py                         # HosenStatusPage + Screen 1 readers
data/hosen/db_sanity.yaml                          # hosen_dashboard.screen_1_landing
tests/sanity/hosen_status_dashboard/               # fixture + subset compare
tests/ui/hosen_status_dashboard/                   # existing smoke, unchanged
core/components/slicer.py                          # used, not edited
core/components/kpi.py                             # used, not edited
core/components/virtual_grid.py                    # used, not edited
```

**Structure Decision**: Validation Core layout. Domain behavior stays on
`pages/hosen_status/page.py`. The golden file stays under `data/hosen/`. The sanity module
stays under `tests/sanity/hosen_status_dashboard/`. Layer 2 is called and not modified.

## Phase 0 — Research

Unknowns from the technical context are resolved in [research.md](./research.md). None remain
marked NEEDS CLARIFICATION.

Decisions locked there:

- Selected slicer text is `Slicer.control(id).inner_text()` on the page. `Slicer` is not extended.
- Percentage text comes from the card `KPI` already resolves. `KPI.read_text` is used when it
  still contains `%`. When the group path returns digits only, the page keeps the `%` token from
  that same card's text. `extract_kpi_value_text` is not changed.
- Trend and resilience color are page-level classifications of non-canvas DOM. Canvas sampling
  is a failure, not a fallback scraper.
- Golden literals are copied once from the live landing screen into the YAML during implementation.
- Subset comparison is private to the Hosen test module.

## Phase 1 — Design

- Data shapes: [data-model.md](./data-model.md)
- Page and test contract: [contracts/hosen-screen1-sanity.md](./contracts/hosen-screen1-sanity.md)
- How to run the slice: [quickstart.md](./quickstart.md)
- Agent context: `.cursor/rules/specify-rules.mdc` points at this plan.

### `read_screen_1_metrics`

Returns one dict. Each section reader waits until its anchor is visible, bounded by
`self.timeout`, then reads. The method does not sleep and does not wait for network idle.

```text
{
  "survey_status": {"submitted": "<digits>", "total": "<digits>", "missing_authorities": ["..."]},
  "kpis": {
    "national_average": {"title": "...", "percentage": "55%", "trend": "up"},
    "categories": [{"title": "...", "percentage": "40%", "trend": "down"}]
  },
  "resilience_scores": [{"authority": "...", "score": "<digits or text>", "status": "green"}],
  "active_filters": {"district": "מחוז דרום", "sub_district": "נפת לכיש"}
}
```

The test, not the page, coerces YAML integers. The page returns display text for counts, scores,
percentages, labels, and the trend/status words.

### Filters

`SlicerDefinition` rows live on the page. `id` matches the YAML key (`district`,
`sub_district`, plus any further id the live right-hand rail actually shows). `role_name` is the
Hebrew accessible name copied from the live combobox during implementation. `kind` is `dropdown`.

The reader calls `control(id)`, expects the control visible, and returns the selected label with
the role name and bidi marks removed. `הכל`, when that is the selected label, is compared as a
string. It is not clicked.

### KPIs

National title constant: `הערכת קה״א - ממוצע ארצי`. Implementation confirms the quote character
against the accessible name (`״` versus `"`) and stores the live spelling in the page constant
and in the YAML `title`.

`KPI` is constructed with the report iframe. `KPI.card(title)` locates the card. Percentage:

- Button cards: `KPI.read_text` (last paragraph). Keep the `%`.
- Group cards: if `read_text` dropped the percent sign, read the card text from the same locator
  and keep the token that contains `%`.

Trend, on that same card locator, in this order: an element whose accessible name says up, down,
or flat; otherwise the arrow node's computed `fill` or `color`. Green → `up`, red → `down`,
yellow → `flat`. The search skips `canvas`. If the only signal is a canvas, `trend` is `""`.

Category cards are the other button or group cards inside the visual that contains the national
title. The reader returns every such card. The test matches golden categories by `title`.

### Resilience table

Anchor: visible text `ציון חוסן`. The grid passed to `collect_virtualized_rows` is the table or
grid inside that visual. `row_id` is the authority name. `read_visible` reads the authority text,
the score text, and `getComputedStyle` background color of the row or the score cell. Mapping:

- Green-dominant background → `green`
- Yellow (high red and green, low blue) → `yellow`
- Anything else → the raw `rgb(...)` string, so a golden `green` or `yellow` fails

The callback does not read pixels from `canvas`.

### Survey status

Anchor: the top-left block that shows the submitted/total pair. The page locators extract the two
counts and the list of missing authority names. The returned counts are digit strings. The test
applies the integer rule. Missing names are exact strings. Golden names must all appear.

### Sanity test

`conftest.py`:

```python
from pages.hosen_status.page import HosenStatusPage
from tests.helpers.dashboard_fixture import bind_dashboard

hosen_status_dashboard = bind_dashboard(HosenStatusPage, "hosen_status_dashboard")
```

`test_hosen_screen1_matches_golden` loads `hosen_dashboard.screen_1_landing` and compares it to
`page.read_screen_1_metrics()`:

- Dict: every golden key is present. Extra UI keys are ignored. An empty actual dict fails when
  the golden dict has keys and the section anchor is visible.
- List of rows (`resilience_scores`, `kpis.categories`, `missing_authorities`): match on
  `authority`, `title`, or the name string. Extra UI entries are ignored. An empty actual list
  fails when the golden list is non-empty and the anchor is visible.
- `int`: strip bidi marks, commas, spaces, and no-break spaces, then compare the integer.
- `str`: strip bidi marks and outer whitespace, then compare exactly.
- Anchor absent: `pytest.skip` that block only. The other blocks still run. If every anchor is
  absent, the test skips.

### Golden file

Create `data/hosen/db_sanity.yaml` during implementation by reading the open landing screen once
and writing those literals under the schema in data-model.md. Do not invent counts. Do not copy
values from Hasbara, Credit, or Alerts files.

### Coverage catalog

Add a short Hosen section to `docs/COVERAGE_CATALOG.md` mapping each `screen_1_landing` block to
`read_screen_1_metrics` and `test_hosen_screen1_matches_golden`. State that the source is the YAML
file, not SQL.

## Constitution Check (post-design)

Re-checked after data-model.md and the contract. The design still passes.

- No `core/` edit. Filter text, trend, and row color stay on the domain page (II, VII).
- No new shared compare module. The subset walk is private to the Hosen test (VII).
- No SQL in Layer 0. Sanity YAML is the source of truth named by the spec (V).
- Smoke `verify_freshness` is unchanged (III, IV).
- Complexity Tracking is empty. No principle is waived.

## Complexity Tracking

No constitution violations. This table is intentionally empty.
