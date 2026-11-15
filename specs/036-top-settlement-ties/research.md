# Research: Top Settlement Tie Assertion

## Decision 1 — Change the ranking test, not the filtered-card test

**Decision**: Edit `test_screen_1_top_settlements` only. Leave `test_screen_1_filtered_metrics` as the two range-card asserts.

**Rationale**: The user allowed either the filtered-metrics test or the top-settlements assertion. The filtered test does not read the ranking chart. Putting the tie split there would mix card checks with settlement checks and would let a ranking failure hide inside the card test. The ranking function already loads the golden range and the UI map.

**Alternatives considered**: Rewriting `test_screen_1_filtered_metrics` to assert settlements. Rejected because that function's contract is the two range cards.

## Decision 2 — Partition the golden map at 32

**Decision**: Stable entries are `top_10_settlements.values` items whose count is greater than or equal to 32. The current file yields six names: ראשון לציון 39, תל אביב-יפו 36, רמת השרון 35, נתניה 34, ראש העין 32, רמלה 32. The test computes that set from the file. It does not hard-code the names.

**Rationale**: Those six counts were stable across live loads. The user asked for that cutoff. Reading the cutoff from the golden values keeps the YAML as the source and satisfies the request not to edit it.

**Alternatives considered**: Hard-coding the six Hebrew names in the test. Rejected because a golden count change would then require a second edit, and the user forbade editing the YAML rather than forbade reading it.

## Decision 3 — Four remaining UI rows must each equal the golden tie value

**Decision**: After removing the stable names, the UI map must contain exactly four rows. Each count must equal the single golden value that is below 32. In the current file that value is 31. Names in those four rows are ignored.

**Rationale**: Live loads showed a full top 10 whose tail was always 31, with names such as קריית תעופה, כפר חב"ד, זיתן, אחיעזר, יגל, צפרייה, and חיפה swapping in and out. Requiring the golden tie names (יגל, גינתון, צפרייה, חיפה) fails whenever the chart picks a different subset. Requiring length 4 and count 31 still fails a short read, an extra row, or a count other than the tie.

**Alternatives considered**:

- Keep requiring every golden name and allow extra UI names. That is the current assertion, and it fails on the shuffle.
- Skip the test when a golden tie name is missing. That would hide a real count mismatch and would no longer check that four rows sit at 31.
- Sort both maps and compare only the multiset of counts. That would ignore a missing stable name if some other settlement happened to carry the same count.

## Decision 4 — Do not change the page reader

**Decision**: `read_top_10_settlements()` stays as implemented for feature 035. It already scrolls the chart and returns `{name: count}`.

**Rationale**: The shuffle is in the visual's tie break, not in a missed row. The last full reads returned ten names. This slice only changes how the test judges that map.

**Alternatives considered**: Sorting the chart through a different visual or a data table. Rejected because the user asked for a resilient assertion, not a new reader, and the page file is out of scope.

## Decision 5 — Empty map still skips

**Decision**: `if not actual: pytest.skip("Missing Page Object reader for top_10_settlements")` stays. A non-empty map that fails the stable or tie checks is a failure, not a skip.

**Rationale**: Feature 035 uses that skip when the reader cannot pair labels. A shuffled tie is a paired map and must be asserted.
