# Contract: Screen 2 Page-Switch Hook

No `core/` contract changes. `_report_ready_locator` is not a writable contract in this slice.
See `screen2-ready-and-quotes.md` for the ready phrase, the date wait, and quote folding.

## Page switch

### `AlertsPopulationPage.before_report_ready_check(self) -> None` — CHANGED

- **Current**: returns when the district chart title is visible via `_iframe_phrase_locator`.
  Otherwise clicks `.nth(attempts % count)` on the page-rail chrome named `ניווט בין עמודים`
  or `Page navigation`, with `click(force=True, no_wait_after=True)`. Returns during a
  12-second cooldown. Returns for the rest of the page object's life once
  `_page_switch_attempts >= 3`, even when `מרחק מהגבול` is absent.
- **After**:
  1. If `_report_ready_locator()` is visible (short check, about 500 ms), return.
  2. Otherwise resolve the page-navigation visual on `self._report_frame()` by accessible name
     `ניווט בין עמודים` or `Page navigation` (`navigation`, `group`, or label). Do not search
     `self.page`.
  3. Inside that visual, take the first visible exact match of `PAGE_TITLE`
     (`ניתוח התרעות`) on `button`, `tab`, `link`, `option`, or exact text. If none match, take
     the first visible rail control from the Hebrew/English link, button, and label union.
  4. `click(force=True)` on that node. Do not pass `no_wait_after=True`.
  5. `page.wait_for_timeout(400)`. Do not call `networkidle`.
  6. Check `_report_ready_locator()` again. If it is visible, return.
  7. Repeat steps 3–6 while the anchor is absent, for at most about 8 seconds in this call,
     then return.
- **Not a stop**: three clicks, `_page_switch_attempts`, and the 12-second cooldown. Those
  fields must not suppress a later call while `מרחק מהגבול` is absent. The district chart
  title is not the success probe.
- **Not the target**: an unscoped `ניתוח התרעות` node (global header, Screen 1 title
  `ניתוח התרעות | תמונת מצב ב [Filter]`, side navigation).
- **Unchanged locator**: `_SCREEN2_READY_ANCHOR` stays `מרחק מהגבול`. `_report_ready_locator`
  stays `self._report_frame().get_by_text(self._SCREEN2_READY_ANCHOR).filter(visible=True).first`.
  The hook does not rebuild that phrase and does not call `_iframe_phrase_locator` for it.
- **Host behavior** (not edited): `ReportShell.navigate` calls this hook on each ready poll,
  then waits until `_report_ready_locator()` is visible. Failure is still `LoadTimeoutError`.
  Timeout is still `self.timeout` (`120_000` on `AlertsPopulationPage`). The hook does not
  raise that error and does not loop for the full timeout, because `_dashboard_ready` and
  `reload_and_measure_ready_ms` call it on short polls.
- **Guarantee**: while Screen 1 is showing, the hook keeps clicking the inner Screen 2 tab
  across calls until `מרחק מהגבול` is visible or `navigate` reaches its timeout. A report
  that is already on Screen 2 returns without a click storm.
- **Comments**: English, inside the function.

## Invariants

- No locator is added in the test module.
- `core/` is not edited.
- `_report_ready_locator`, `set_date_range`, `read_hour_daily_avg`, and Show-as-a-table
  teardown are not edited.
- `_assert_golden_keys` and the golden YAML are not edited.
- Comments inside edited functions are English.
