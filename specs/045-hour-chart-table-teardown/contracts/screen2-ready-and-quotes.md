# Contract: Unique Screen 2 Ready Anchor, Filtered-Data Wait, and Golden Key Quotes

No `core/` contract changes. Golden YAML is not a writable contract in this slice.

## Ready locator

### `AlertsPopulationPage._report_ready_locator(self) -> Locator` — CHANGED

- **Current**: exact Screen 2 document title `ניתוח התרעות | ניתוח התרעות` via
  `_SCREEN2_READY_TITLE`, as exact text, exact heading, and exact label on the report frame.
  That title contains `ניתוח התרעות`, which is also on Screen 1.
- **After**: visible text `מרחק מהגבול` (the Screen 2 distance filter), held by
  `_SCREEN2_READY_ANCHOR`. Built only as:

  `self._report_frame().get_by_text(self._SCREEN2_READY_ANCHOR).filter(visible=True).first`

  `_SCREEN2_READY_TITLE` is removed. No call to `_iframe_phrase_locator`. No search of
  `self.page`.
- **Not used**: `PAGE_TITLE`, `ניתוח התרעות`, Screen 2 title `ניתוח התרעות | ניתוח התרעות`,
  Screen 1 title `ניתוח התרעות | תמונת מצב ב [Filter]`, `סה"כ אוכלוסייה`, `סה"כ בטווח שנבחר`,
  `אוכלוסייה לא ממוגנת`, `אוכלוסייה מותרעת`, or any other metric card.
- **Unchanged constants**: `PAGE_TITLE` remains `ניתוח התרעות` for metric and chart scope.
  `TOTAL_CARD` remains `סה"כ אוכלוסייה`. `UNPROTECTED_CARD` remains `אוכלוסייה לא ממוגנת` for
  `read_card("unprotected")`.
- **Value independence**: the selected distance is not read. Any value still shows the label.
- **Hook**: `before_report_ready_check` is specified in `page-switch-hook.md`. It calls this
  locator to see whether Screen 2 is open. It does not change this method.
- **Host behavior** (not edited): `ReportShell.navigate` and `reload_and_measure_ready_ms` wait
  until this locator is visible. Failure is still `LoadTimeoutError`. Timeout is still the page
  `self.timeout` (`120_000` on `AlertsPopulationPage`). `_iframe_phrase_locator` in
  `core/portal/page.py` is not edited.
- **Guarantee**: rashut/yeshuv fixture setup passes the ready wait only when `מרחק מהגבול` is
  visible. Screen 1's header, navigation, and title do not satisfy the wait. The ready phrase is
  not parsed as a number.
- **Comments**: English, inside the function.

## Date-filter settle

### `AlertsPopulationPage.set_date_range(self, start_date: str, end_date: str) -> None` — UNCHANGED (preserve)

Already implemented. This anchor revision does not edit the method.

- **Signature**: unchanged.
- **After** (already in the method):
  1. `set_between_dates(start_date, end_date)`.
  2. `expect` the warned card `אוכלוסייה מותרעת` to be visible (`timeout=self.timeout`).
  3. `expect.poll` (or an equivalent `expect` retry) until `read_card("warned")` is neither blank
     nor `0` / `0.0`. Blank text is the `ValueError` raised by the KPI number parser and counts
     as not ready.
  4. Return on the first other number.
- **Not used**: `page.wait_for_load_state("networkidle")`. A stable `read_card("total")` does not
  end the wait.
- **Failure**: the `expect` timeout (`self.timeout`) if the warned card stays blank or `0`.
  Callers do not read charts in that case.
- **Guarantee**: for the golden range, the method returns only after the warned card has left the
  default zero state. The golden value of that card is `9474`.
- **Comments**: English, inside the function.

## Key comparison

### `_assert_golden_keys(actual: dict, expected: dict, normalize=None) -> None` — UNCHANGED (preserve)

File: `tests/sanity/alerts_analysis_dashboard/test_data_validation.py`. Already implements the fold.
Do not add a second normalizer.

- Actual keys pass through `normalize` when it is provided, otherwise `str(key)`.
- Both that name and each expected key then use `replace('"', "'")`.
- Extra UI keys are ignored. Values compare with `==`.
- **Guarantee**: `חטמ"ר צפונית - 7643` (UI) and `חטמ'ר צפונית - 7643` (golden nafa sum and
  daily avg) match. A key that differs by more than `"` versus `'` still fails. Values are not
  rewritten. Date normalization still runs first for `test_alerts_by_date_matches_db`.
- **Out of fold**: Hebrew geresh (U+05F3) and gershayim (U+05F4). YAML bytes are not changed.

## Invariants

- No locator is added in the test module.
- `core/` is not edited.
- Comments inside edited functions are English.
