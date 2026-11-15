# Phase 0 Research: Alerts Contract Coverage

All items below were resolved against the current code (features 014 and 016) and one local
SQLAlchemy check. No **NEEDS CLARIFICATION** remains.

## R1 — Where the new cards are read

- **Decision**: Do not modify `core/` or `tests/helpers/db_parity_engine.py`. Add YAML rows that
  the existing loader already accepts.
- **Rationale**: `KPI.number(name, scope=scope)` and `Chart.read(name, scope=scope)` already take
  an opaque scope. `_normalize_scope` passes a non-blank string through and treats blank as
  `None`. `_category_id` stringifies a set id and omits a missing one. `visual: kpi` calls
  `scalar`. `visual: chart` calls `rows`. Feature 014 added scope specifically because `היום`,
  `אתמול`, and `סה"כ בטווח שנבחר` repeat under different sections.
- **Alternatives considered**: A new engine field for "time bucket", or encoding the bucket in
  the metric name together with the section. Rejected. Scope plus the stable card title is the
  feature 014 contract, and a new field would be an unused engine change.

## R2 — Dynamic titles versus the static chart

- **Decision**: Threat scopes and the two group scopes are the stable bases from the request.
  Card `name` values are `היום`, `אתמול`, and `סה"כ בטווח שנבחר`. None of those strings includes
  `שלושים יום אחרונים`. The comparison chart `name` is the full sentence, including
  `ביממה הנוכחית והקודמת` and the spelling `ישובים`.
- **Rationale**: `scope_host` and the KPI title lookup compile `re.escape(text)` with no anchors,
  so a stable base still matches an accessible name that has gained a slicer suffix. The
  comparison chart does not follow the slicer, so stripping that phrase would point the metric
  at the wrong visual or at no visual. The ranking chart already in the file uses `יישובים`
  (two yods). The new title uses `ישובים` (one yod), so the two names do not substring-match.
  They must not be normalized to one spelling.
- **Alternatives considered**: Dropping `ביממה הנוכחית והקודמת` the way feature 016 dropped the
  slicer phrase from other titles. Rejected. That phrase is the chart's permanent title, not the
  slicer option. Using the two-yod spelling so the titles look consistent. Rejected. The request
  gives the exact full name.

## R3 — KPI versus gauge for population and warning area

- **Decision**: All fifteen new cards are `visual: kpi` with `sql_query` of `SELECT 0` and no
  `maximum_sql`.
- **Rationale**: The threat cards were specified as `visual: kpi`. The population and area cards
  were allowed as gauge or kpi. A gauge metric fails contract load unless `maximum_sql` is set,
  and feature 016 forbids inventing a denominator. `KPI.number` still returns the current figure
  for a card. A later confirmed scale can switch a row to `gauge` and add a real `maximum_sql`.
- **Alternatives considered**: `visual: gauge` with `maximum_sql: SELECT 0`. Rejected. That
  claims a scale check the warehouse has not confirmed, and a stub maximum of 0 would fail every
  real gauge for the wrong reason.

## R4 — Category ids and the rows that already exist

- **Decision**: Write `category_id` as the YAML strings `"1"`, `"2"`, and `"10"`. Optional
  `label` values are `Rockets`, `Terrorists`, and `UAV`. The six existing measures that use
  `name` `אוכלוסייה מותרעת` or `אזורי התרעה תחת ירי` with those ids stay, with their current
  warehouse SQL. The new general cards use those Hebrew strings as `scope`, not as `name`, and
  they omit `category_id`. The ranking chart, map, and policy status stay.
- **Rationale**: The user assigned id 1 to rockets, id 2 to terrorist infiltration, and id 10 to
  hostile aircraft. The engine already does `str(category_id)`, and the existing contract and
  unit test use quoted strings. The new general cards are not a second per-id split. Keeping the
  feature-016 rows preserves confirmed SQL. The engine ignores `label`.
- **Alternatives considered**: Replacing the six category measures with the time-bucket cards.
  Rejected. The request says to add the general entries, and those six queries are the confirmed
  warehouse predicates. Integer `category_id: 1` without quotes. Rejected for the file style;
  runtime behavior would still be `"1"`, but the contract would mix types.

## R5 — Stub SQL and date binds the chart does not use

- **Decision**: KPI stubs are the constant text `SELECT 0`. The chart stub is:

  ```text
  SELECT CAST(NULL AS nvarchar(200)) AS category_label, CAST(NULL AS int) AS metric_value WHERE 1 = 0
  ```

  That statement does not mention `:start_date`, `:end_date`, or `AlertDate`. The runner is not
  changed. It still passes the date dict into `text()`.
- **Rationale**: `rows()` raises `ValueError` on a blank label, so the stub must return no rows
  rather than one row of NULLs. `WHERE 1 = 0` is valid T-SQL and yields an empty two-column
  result. A local check on SQLAlchemy 2.0.51 (`sqlite://`, `text()` plus a params dict that
  contains `start_date` and `end_date` for a statement that does not use them) returned `[]`
  and did not raise. Future business SQL for this chart must keep ignoring the slicer window.
  The runner's extra keys are safe today, so this slice does not add a bind filter.
- **Alternatives considered**: `SELECT 'placeholder', NULL` like the ranking-chart stub.
  Rejected for this chart. A placeholder label is a row, and the request asks for an empty row
  set. Tautologies such as `AND :start_date = :start_date`. Rejected. That uses the date binds
  the business rule says this chart ignores. Catching a connect error around the new constants.
  Rejected. FR-009 requires the error to propagate.

## R6 — How a unit test can see duplicate titles

- **Decision**: Assert the new metrics as a set of `(name, scope, category_id or None, visual)`.
  Do not build `{name: metric}` for them. Keep the existing by-name lookup only for the three
  unique feature-016 visuals (ranking chart, map, policy).
- **Rationale**: `היום` will appear on five scopes. A name-keyed dict keeps one of them and drops
  the rest, which would make a green test that did not count the rows.
- **Alternatives considered**: Requiring `name` to be unique by prefixing the scope. Rejected.
  That fights the scoped-title design in R1.
