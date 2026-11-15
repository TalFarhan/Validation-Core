# Phase 0 Research: Alerts DB Parity Upgrade

All items below were resolved against the current code (features 010 and 012–015). No
**NEEDS CLARIFICATION** remains.

## R1 — Where scope, gauge scale, and chart parsing already live

- **Decision**: Do not modify `core/components/`. Call the existing methods.
- **Rationale**: `KPI.number`, `KPI.scale`, and `Chart.read` already take `(title, scope=None)`.
  Blank scope is normalized inside `scope_host`. Title matching is `re.compile(re.escape(title))`
  with no anchors, so a stable prefix matches a title whose suffix changes with the slicer.
  `KPI.scale` returns `value`, `minimum`, `maximum`, and `state`. `Chart.read` returns
  `categories` (label + values), `series`, and `state`. Feature 015's gauge contract even said the
  parity engine still called `KPI.number(name)` and needed no change; this feature is that change,
  on the caller side.
- **Alternatives considered**: Extending `KPI` with an Alerts-specific gauge helper, or parsing
  chart text inside `db_parity_engine.py`. Rejected. Both would either leak domain rules into
  Layer 2 or duplicate feature 015.

## R2 — How the engine should choose a reader

- **Decision**: Add `visual` on each metric: `kpi` (default), `gauge`, or `chart`. R12 adds `map`.
- **Rationale**: One contract list can mix cards, gauges, and charts. Default `kpi` keeps a metric
  that only has `name` and `sql_query` on today's path. Inferring gauge from the presence of
  `maximum_sql` is easier to mis-set; an explicit kind fails closed in the loader.
- **Alternatives considered**: Separate YAML files per visual kind. Rejected. The test would have
  to know which file matches which reader, and category/date binds would be copied three times.

## R3 — Gauge checks

- **Decision**: For `visual: gauge`, call `KPI.scale(name, scope=scope)`. Compare `value` to
  `sql_query` and `maximum` to `maximum_sql`. Both compares always run. Fail the metric when
  `state` is `empty`, when `value` is `None`, or when `maximum` is `None`.
- **Rationale**: The request is to verify the actual value and the denominator against the
  database. `KPI.number` drops the maximum (feature 015: slash pairs are not returned by
  `number`). Two `ParityResult` rows (`check="value"` and `check="maximum"`) keep the existing
  "one assertion error listing every mismatch" behavior. `0` compares equal to `0`.
- **Alternatives considered**: A single tolerance on `value / maximum`. Rejected. The user asked
  for both numbers against the warehouse, not a ratio. Ignoring `minimum` is deliberate: the
  request names value and maximum only.

## R4 — Category ids for UAV, Rockets, and Terrorists

- **Decision**: The id set is the one already grouped in `alerts_contract.yaml`: `'1'`, `'2'`,
  `'10'`. Each parity query uses `CategoryID = :category_id` with one of those ids. The human
  label (UAV, Rockets, Terrorists) is an optional `label` field in the Alerts YAML. The engine
  does not read `label`. Implementation confirms which id matches which label from the report or
  warehouse and writes that only in the YAML. This plan does not assign a label to an id.
- **Rationale**: The repo contains the three ids and no mapping to those English names. Guessing
  the pairing would ship a wrong filter. The engine only needs an opaque string to bind.
- **Alternatives considered**: Hardcoding a dict in `db_parity_engine.py` or `core/`. Rejected
  (Constitution II, FR-008). Keeping `IN ('1', '2', '10')` and post-filtering in Python.
  Rejected. The request replaces the grouped query with per-category validation.

## R5 — Where `category_id` is accepted

- **Decision**: `AlertsDBRunner.scalar` and `rows` gain `category_id: str | None = None`. When it
  is not `None`, the params dict includes `"category_id": category_id`. The engine stringifies a
  YAML int (`1` → `"1"`) before the call, and omits the kwarg when the metric has no
  `category_id`. SQL text in the contract uses the named bind. No f-string and no `.format()`.
- **Rationale**: `scalar` today binds only `start_date` and `end_date` via `text()`. Adding one
  optional key matches that pattern. Stringifying avoids a type drift if the YAML leaves the id
  unquoted, because the current predicates compare to character literals. The engine must not
  import Alerts types; it just forwards a string.
- **Alternatives considered**: A generic `params: dict` blob on the runner. Rejected for this
  feature. The request names `category_id` on the Alerts client. Extra binds can wait until a
  second filter exists. Building `IN` from a list inside the runner. Rejected. That keeps the
  grouped query the user wants removed.

## R6 — Chart comparison

- **Decision**: Add `AlertsDBRunner.rows`, returning `list[tuple[str, int | float | None]]`
  (label, value) in query order. The engine calls `Chart.read(name, scope=scope)` and matches
  rows to `categories` by label. The compared cell is `values[series_index]` with default
  `series_index` 0. SQL NULL stays `None` (not `0`). Duplicate labels on either side fail.
  `state == "empty"` passes only when the query returns no rows.
- **Rationale**: Feature 015 stores a missing mark as `None` and a blank plot as `empty`.
  Matching by label survives a sort difference between the visual and the query. `scalar`'s
  NULL→0 behavior stays, because KPI queries already use `ISNULL` and the pilot depends on it.
  Chart grain is different: a NULL there means "no bar".
- **Alternatives considered**: Comparing chart category count only. Rejected. That would not use
  the parsed values. Requiring legend-name equality with a SQL column. Rejected. Series identity
  in Layer 2 is positional (`series_index`); names would force Hebrew series titles into the
  comparison key. The contract may still set `series_index` after the author sees `series` order.

## R7 — Decoupling date phrases from metric names

- **Decision**: `name` is the stable title anchor. For the two current metrics, drop the suffix
  ` בשלושים יום האחרונים`. The test keeps `dashboard.select_date_range("שלושים יום אחרונים")` and
  the half-open window (`end = now`, `start = end - 30 days`). The engine never appends slicer
  text to `name`. A later slicer option is a new test argument plus a new window, not a new
  metric name.
- **Rationale**: Playwright name regexes used by `KPI` and `Chart` are unanchored, so the shorter
  anchor still matches the longer accessible name. Putting the period in the contract is what
  forces a rename when the slicer changes. The slicer option and the window stay paired in the
  test, which is the domain layer.
- **Alternatives considered**: Teaching `KPI` a new "ignore suffix" mode. Rejected. The current
  matcher already does this, and Layer 2 is out of scope (FR-014). Parameterizing the title
  inside the engine with the slicer label. Rejected. That puts Hebrew date phrases back into the
  lookup path and couples the helper to one report's wording.

## R8 — One test call versus a category loop

- **Decision**: Prefer one `validate_dashboard_generic` call. Each metric carries its own `scope`
  and `category_id`, so all three categories can be on screen under the same date slicer. Add an
  Alerts page category slicer only if implementation finds a visual is absent until that control
  is set. The loop, if needed, lives in `test_db_parity.py` and selects through the page object
  before calling the engine on the metrics for that id.
- **Rationale**: The user asked for `scope` on lookups and `category_id` on SQL, not for a new
  slicer. Scope is the mechanism that separates repeated titles. A hidden visual is an
  implementation check, not a schema change.
- **Alternatives considered**: Always clicking three category slicer values. Rejected as the
  default. It adds a domain control the report may not use, and it duplicates work when sections
  are already visible.

## R9 — What the live contract must contain before the feature is done

- **Decision**: Rewrite the two existing measures so each of ids `1`, `2`, and `10` has its own
  metric (six KPI metrics, same SQL shape, bind instead of `IN`). Add gauge metrics (`sql_query`
  + `maximum_sql`) and chart metrics (`rows` SQL) for the Alerts visuals that actually show those
  categories. Titles and scopes are copied from the report into the YAML during implementation.
  Do not invent a title that is not on the report. If a category has no gauge or no chart, say
  so in the coverage catalog and still ship the engine path covered by unit tests.
- **Rationale**: No Alerts gauge title, chart title, or section scope is stored in the repo today.
  The schema and unit tests do not need those strings. The live test does. Inventing Hebrew titles
  in this plan would fail on the portal.
- **Alternatives considered**: Blocking the design until titles are scraped from a live session.
  Rejected. Locator strings are domain data; the interface is what this plan locks.

## R10 — Tests that do not need the portal

- **Decision**: `tests/unit/test_db_parity_engine.py` loads a temporary YAML and stubs `KPI` and
  `Chart` (or stubs the methods the engine calls) plus a fake runner that records binds. Cases:
  scope forwarded; blank scope becomes `None`; gauge value match with maximum mismatch fails;
  gauge `0` matches; chart labels match including `None`; unknown `visual` fails at load;
  `category_id` `1` is forwarded as `"1"`; a metric name is not rewritten with a date phrase.
- **Rationale**: The live `db_parity` test needs the portal and the warehouse. The dispatch rules
  are pure relative to Playwright. Fleet smoke stays the constitution gate and does not assert
  these rules.
- **Alternatives considered**: Only the live Alerts test. Rejected. A portal failure would hide a
  broken gauge or scope path.

## R11 — Comments

- **Decision**: New and edited comments in Python and in the YAML contract are English. Hebrew
  is allowed only as data (`name`, `scope`, slicer option, `label`).
- **Rationale**: Request rule and FR-013. The current engine and runner comments are already
  English. The coverage catalog is an existing Hebrew document; updating its table cells does not
  require translating the catalog. New sentences added there may stay in the catalog's language.

## R12 — Three remaining visuals and their title anchors

- **Decision**: Add three metrics to `alerts_contract.yaml`. Names are stable anchors from the
  Alerts report (screenshot of the failed `db_parity` run on 2026-10-13). The date-range slicer
  phrase is not part of `name`.

  | Metric | `visual` | `name` |
  |--------|----------|--------|
  | Top 10 settlements chart | `chart` | `עשרת היישובים עם כמות ההתרעות הגבוהה ביותר` |
  | Alerts map | `map` | `מפת התרעות ביישובים` |
  | Policy classification | `kpi` + `compare: text` | `סיכון לפי מדיניות התגוננות ברגע` |

  None of the three sets `category_id`. They are report-level visuals, not one of the per-id cards.
- **Rationale**: The live report title on the map is `מפת התרעות ביישובים` plus the slicer phrase.
  The ranking chart title is the settlements anchor plus `בשלושים יום האחרונים`. The policy bar
  caption is `סיכון לפי מדיניות התגוננות ברגע`. The highlighted segment on that bar is
  `פעילות הכרחית`; the other segments are `פעילות מצומצמת`, `פעילות חלקית`, and `פעילות מלאה`.
  The phrase `הכרחית / מצומצמת` is an example of the status text the reader must return, not the
  metric name and not an expected literal in the YAML.
- **Alternatives considered**: Leaving the chart and map out until warehouse SQL exists. Rejected.
  The contract would keep ignoring visuals that are on the report. Inventing `maximum_sql` for the
  gauges on the same page. Rejected. Those stay on the existing gauge path until a denominator
  query is confirmed.

## R13 — Settlements chart must match one visual

- **Decision**: Contract only the ranking chart (settlement label, alert count). A second chart on
  the same page compares the current period with the previous period and shares the prefix
  `עשרת היישובים עם כמות ההתרעות הגבוהה ביותר`. `Chart.read` uses an unanchored substring and
  `.first`. The ranking metric's `name` must match exactly one visual after the date slicer is
  applied. If the short anchor matches both, extend `name` with the shortest extra stable words
  from the ranking title that are not `שלושים יום אחרונים`. Do not put the slicer phrase into
  `name`. Do not add the period-comparison chart in this slice.
- **Rationale**: A shared prefix would silently read the wrong chart. The comparison chart's
  distinguishing words are part of its own title and are not the 30-day slicer option. They stay
  off this metric. Exact codepoints of that second title are confirmed on the visual at
  implementation and are not copied from a lossy screenshot transcription into this metric.
- **Alternatives considered**: Contracting both charts now. Rejected. The request names one top-10
  settlements chart. Using the date phrase as the distinguisher. Rejected by FR-009.

## R14 — Map presence, including true zero

- **Decision**: `visual: map` is legal. The engine locates the container with `scope_host` and the
  opaque title (group accessible name, then the visual-container ancestor of that title — the same
  generic chrome `Chart` already uses). It does not add a `Map` class and it does not edit
  `core/components/`. State is `classify_presence(numbers, count_data_marks(container))`.
  `numbers` is `[parsed]` when the container text yields a number, including 0, and `[None]`
  otherwise. `value` means present (marks, or a number including 0). `empty` means no number and
  no data marks. The check name is `presence`. UI value is the string `value` or `empty`.
- **Rationale**: Feature 015 defined true zero versus empty and said a map is classified by the
  caller that already holds the container. `classify_presence([0], 0)` is `value`.
  `classify_presence([None], 0)` is `empty`. Treating a blank map as numeric 0 would hide an empty
  visual. The current unit test uses `visual: map` as the illegal token; that test changes to a
  still-unknown kind such as `sankey`.
- **Alternatives considered**: Calling `Chart.read` on the map. Rejected. A map is not a
  category/value series, and a failed parse would look like an empty chart. Adding `Map` under
  `core/components/`. Rejected by FR-014 and feature 015.

## R15 — Policy status is a text KPI

- **Decision**: The policy metric stays `visual: kpi` and sets `compare: text`. The engine calls
  `KPI.read_text(name, scope=scope)`, strips bidi marks, collapses whitespace, and compares that
  string to one SQL cell. It does not call `KPI.number`. `compare` defaults to `number`. Any other
  `compare` value, or `compare: text` on a gauge, chart, or map, fails at load.
- **Rationale**: `KPI.number` parses a numeric token and raises or returns a legend digit on a
  status phrase. The public text reader already exists, so Layer 2 stays unchanged. The status
  words stay in the UI and, later, in the query result. The engine only checks string equality.
- **Alternatives considered**: A new `visual: status`. Rejected. The request says `visual: kpi`.
  Falling back from `KPI.number` after a parse error. Rejected. That hides the text path behind
  an exception.

## R16 — Stub SQL is executed, and database errors stay visible

- **Decision**: `db/clients/alerts.py` defines three constants. The contract `sql_query` for the
  matching metric is that exact string. No Hebrew and no category ids in the module.

  ```text
  SETTLEMENTS_CHART_SQL = "SELECT 'placeholder' AS category_label, CAST(NULL AS int) AS metric_value"
  MAP_PRESENCE_SQL = "SELECT 'placeholder'"
  POLICY_STATUS_SQL = "SELECT 'placeholder'"
  ```

  The chart stub returns two columns because `rows()` reads a label and a value. A one-column
  chart query would raise inside the runner before a comparison. Map and policy use a new
  `AlertsDBRunner.cell` that returns the first column unchanged: SQL NULL stays `None` (not `0`),
  a string stays a stripped string, a number uses the existing numeric coercion. `scalar` is
  unchanged (NULL → 0) so the existing KPI queries keep their meaning.

  Map expected state from `cell`: `None` → `empty`; numeric `0` → `value` (true zero); any other
  number → `value`; any other object, including the string `placeholder`, fails the check and is
  reported as the DB value. Policy compares the stripped UI string to the stripped cell. The
  literal `placeholder` does not match a status phrase, so a reachable server still fails the
  assertion.

  `text()` binds only names that appear in the statement. These stubs do not mention
  `:start_date` or `:category_id`, so those keys are not sent. Do not catch connection errors.
  Do not add `pytest.skip`, `pytest.importorskip`, or `pytest.mark.skip` to
  `test_alerts_db_parity_last_30_days`. The missing Alerts database remains a failing test.
- **Rationale**: The request keeps the connection error as the reminder that the warehouse is not
  available, and it asks for placeholder SQL that is still run. Skipping the test or swallowing
  the exception would delete that reminder. `scalar` cannot carry a status string or a SQL NULL
  that means "map is empty", because it coerces NULL to 0 and non-numeric text to a `ValueError`.
- **Alternatives considered**: Omitting `sql_query` until the real statement exists. Rejected.
  The loader requires `sql_query`, and a missing query would fail before the database is contacted.
  Pointing the new metrics at the existing zone-count SQL. Rejected. That would report a false
  business mismatch. Mocking the runner in the live test. Rejected. The live test is the reminder.
