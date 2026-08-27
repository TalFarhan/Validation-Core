# קטלוג כיסוי — דשבורד שליטה בניוד

מסמך זה מקשר בין **כלל עסקי / KPI** לבין **עמודת DB**, **טקסט ב-UI**, ו**טסט**.  
כשמשנים מידה ב-Power BI, slicer, או לוגיקת מחסן — לעדכן כאן ואת הטסטים הרלוונטיים.

**בעלות מוצעת**

| שכבה | אחראי | מעדכן בשינוי |
|------|--------|---------------|
| מידות DAX / ויזואלים / כותרות בעברית | צוות BI | `pages/fleet_dashboard/main_dashboard_page.py` + קטלוג זה |
| עמודות / סטטוסים במחסן (`IsActive`, טבלאות FACT) | Data / Warehouse | `db/client.py` + קטלוג זה |
| טסטים, הרצה, דוחות | Validation / QA | `tests/**` |

---

## 1. הגדרות KPI (מקור האמת)

| מפתח | כותרת ב-UI | מקור DB | כלל | הערות |
|------|------------|---------|-----|--------|
| `total` | סה"כ רכבים שנקלטו | `[DIM].[Vehicle]` | `Environment = מבצעי` | ללא סינון `IsActive` |
| `in_use` | סה"כ רכבים בשימוש | `[DIM].[Vehicle]` | `IsActive = 1` + `Environment` | |
| `withdrawn` | רכבים שזוכו | `[FACT].[SigningReturnVehicle]` | `Environment` + אותם סלייסרים כמו DIM | Category דרך `VehicleID` ב-DIM |
| `allocated` | רכבים שווסתו | `[FACT].[VehicleFlow]` | `Environment` + אותם סלייסרים כמו DIM | Category דרך `VehicleID` ב-DIM |

**פילטרים משותפים (לכל ארבעת ה-KPI):**  
`Environment`, ובאופן אופציונלי `Unit` / `SubUnit` / `VehicleCategory` / `VehicleSource`.

ב-FACT אין להסתמך על `Unit` / `VehicleSource` שעל שורת ה-FACT עצמה —  
ב-Power BI הסלייסרים יושבים על DIM ומסננים את כרטיסי זוכו/שווסתו דרך קשר `VehicleID`.  
לכן ב-`db/client.py` סינון FACT נעשה כך:  
`FACT.Environment` + `VehicleID IN (SELECT … FROM DIM WHERE Unit/SubUnit/Category/Source …)`.

> **מקור האמת:** התנהגות כרטיסי ה-KPI ב-Power BI (כולל cross-filter מסלייסרים דרך DIM).  
> אם BI משנים את הקשרים במודל — לעדכן כאן ואת `db/client.py` יחד.

מיפוי בקוד:

- UI: `pages/fleet_dashboard/main_dashboard_page.py` → `_KPI_TITLES`
- DB: `db/client.py` → `_table_for` / `_DIM_STATUS_FILTERS`
- טיפוסים: `tests/helpers/dashboard_validation.py` → `KPI_TYPES`
- הגדרות טבלאות: `DB_TABLE`, `DB_WITHDRAWN_TABLE`, `DB_ALLOCATED_TABLE`

---

## 2. פילטרים (Slicers)

| מפתח בקוד | תפקיד ב-UI (role name) | עמודת DB | ערכי דוגמה (`data/filters.json`) |
|-----------|-------------------------|----------|-----------------------------------|
| `district` | Unit | `Unit` | מחוז דן / דרום / צפון |
| `sub_unit` | SubUnit | `SubUnit` | מחוז הדרום 6003, מחוז דן 789, … |
| `category` | VehicleCategory | `VehicleCategory` | משאית |
| `source` | VehicleSource | `VehicleSource` | יר"ם, מרכז הובלה |

מטריצת תרחישים: `data/filter_matrix.json`.

שכבות: **איך** לסנן (dropdown / checkbox / search / clear-all) נמצא ב-Layer 2
(`core/components/slicer.py`). **מה** לבחור (כינויים ותוויות) נשאר ב-`data/filters.json`.
חוזה מלא: [`specs/002-generic-slicer/architecture.md`](../specs/002-generic-slicer/architecture.md)
(Slicer definitions / value catalog / scenario matrix).

---

## 3. טאבים וטבלה

| טאב ב-UI | מפתח | KPI מקושר |
|----------|------|-----------|
| כל הרכבים | `all` | `total` |
| בשימוש | `in_use` | `in_use` |
| שווסתו | `allocated` | `allocated` |
| שזוכו | `withdrawn` | `withdrawn` |

חיפוש רכב: Text Search Slicer → לפי **מספר רכב** (`VehicleID`) בלבד (התאמת contains).  
הטסט בוחר ID ייחודי תחת contains כדי לא ליפול על ערכים קצרים כמו `111111`.

---

## 4. גרפים (Charts)

| מפתח | כותרת ב-UI | בדיקה נוכחית |
|------|------------|---------------|
| `source` | פילוח מקור משיכת רכבים בשימוש | נראות + תוויות↔DB + **טולטיפ** ערך מול `count_by_source`; **אין הסתעפות** |
| `unit` | פילוח רכבים בשימוש ביחידות | נראות + תוויות↔DB + **טולטיפ** + **הסתעפות** (הדר / טולטיפ) Unit→SubUnit מול `count_by_sub_unit` |
| `category` | פילוח קטגוריות רכב | נראות + distinct DB; **לא** תוויות/טולטיפ↔`VehicleCategory` (ויזואל: אוטובוס/רכב קל/… ≠ טנדר/משאית/…) |
| `withdrawal` | פילוח סיבות לזיכוי רכב | נראות + distinct DB + **טולטיפ** ערך מול `TransferReason` (סריקת hover — על הפרוסות מופיע "3 (50%)" בלי שם) |

מיפוי בקוד:

- UI: `MainDashboardPage` → `_CHART_TITLES`, `hover_chart` / `get_tooltip_text` / `parse_tooltip_entries`
- DB: `tests/helpers/dashboard_validation.py` → `CHART_DB_BREAKDOWNS`, `assert_chart_tooltips_match_db_sample`, `assert_chart_labels_match_db_sample`
- טסטים: `tests/e2e/test_chart_tooltips.py`, `tests/e2e/test_chart_validation.py`
- הסתעפות: `expand_chart_hierarchy` / `expand_via_tooltip_drilldown` / `drill_up_chart` / `count_by_sub_unit` → `tests/e2e/test_chart_drilldown.py`

> **הסתעפות / כינוס (זוג הפוך):**  
> - **הסתעפות** = ירידה ברמה (Unit → SubUnit). אייקון חצים מחוברים / טולטיפ.  
> - **כינוס** = חזרה למעלה (SubUnit → Unit). ההפך מהסתעפות.  
> לא החץ הבודד למטה (Drill down) ולא החץ הכפול. ל-`source` אין הסתעפות.  
> אם הכפתור חסר או disabled — הטסטים עושים `skip` (לא fail).

---

## 5. אינווריאנטים עסקיים

| כלל | היכן נבדק |
|-----|-----------|
| `in_use ≤ total` (שניהם מ-DIM) | UI + DB — `test_data_invariants.py` |
| `withdrawn` = ספירה מ-`FACT.SigningReturnVehicle` | DB — `test_db_withdrawn_comes_from_fact_table` |
| `allocated` = ספירה מ-`FACT.VehicleFlow` | DB — `test_db_allocated_comes_from_fact_table` |
| סכום פילוח מקור = `in_use` | DB — `test_db_source_breakdown_sums_to_in_use` |
| סכום פילוח יחידה = `in_use` | DB — `test_db_unit_breakdown_sums_to_in_use` |
| סכום פילוח תת־יחידה = `in_use` (אותו scope) | DB — `test_unit_drilldown_children_sum_to_parent` |
| סכום פילוח קטגוריה = `total` | DB — `test_db_category_breakdown_sums_to_total` |
| סכום פילוח סיבות זיכוי = `withdrawn` | DB — `test_db_withdrawal_reason_breakdown_sums_to_withdrawn` |
| שורות טבלה בטאבי FACT | אם KPI>0 והגריד ריק — `skip` (bookmark לא משקף FACT) |
| לחיצה על שורה בטבלה → cross-filter | UI — `test_table_row_click_cross_filters_dashboard` |

> `in_use + withdrawn = total` **לא** תקף יותר — `withdrawn` מגיע מטבלת FACT נפרדת.

---

## 6. מיפוי טסטים

| אזור | קובץ | Markers | מה מכוסה |
|------|------|---------|----------|
| Smoke טעינה | `tests/ui/fleet_dashboard/test_dashboard_smoke.py` | `sanity` | **SLA טעינה ≤5s** (`DASHBOARD_LOAD_SLA_MS`), KPI≥0, iframe, slicers, charts, table |
| UX פילטרים | `tests/ui/fleet_dashboard/test_dashboard_filters.py` | `sanity` | צמצום מונים, cascading SubUnit, clear |
| KPI vs DB | `tests/e2e/test_kpi_validation.py` | `data`, `regression` | baseline + מחוז + פילטר משולב |
| מטריצת פילטרים | `tests/e2e/test_filter_matrix.py` | `data`, `regression` | single/combined מתוך JSON |
| טאבים / טבלה / חיפוש | `tests/e2e/test_table_validation.py` | `data`, `regression` | KPI↔DB, שורות↔KPI, search, **לחיצת שורה→cross-filter** |
| גרפים | `tests/e2e/test_chart_validation.py` | `data`, `regression` | נראות + תוויות↔DB (source/unit); category/withdrawal = נראות + distinct |
| טולטיפ גרפים | `tests/e2e/test_chart_tooltips.py` | `sanity`, `data`, `regression` | הופעה/סגירה + ערך מול DB (source/unit/withdrawal) |
| הסתעפות גרפים | `tests/e2e/test_chart_drilldown.py` | `sanity`, `data`, `regression` | הדר + **טולטיפ הסתעפות**; Unit→SubUnit מול DB; פילטרים |
| אינווריאנטים | `tests/e2e/test_data_invariants.py` | `data`, `regression` | כללי עקביות |
| קצוות | `tests/e2e/test_edge_cases.py` | `data`, `regression` | zero-count, clear, refresh, FACT KPIs |

---

## 7. צ'קליסט שינוי דשבורד (BI)

- [ ] שינוי כותרת KPI / גרף / טאב → עדכון `_KPI_TITLES` / `_CHART_TITLES` / `_tab(...)` + שורה בקטלוג
- [ ] שינוי מבנה טולטיפ Power BI / כותרת שדה בטולטיפ → עדכון `hover_chart` / `parse_tooltip_entries` / helpers
- [ ] שינוי היררכיית גרף / כפתורי הסתעפות → עדכון `expand_chart_hierarchy` / `count_by_sub_unit` / `test_chart_drilldown.py`
- [ ] שינוי לוגיקת מידה (DAX) → עדכון `_table_for` / `_DIM_STATUS_FILTERS` ב-`db/client.py` + טסט אינווריאנט אם צריך
- [ ] Slicer חדש / שינוי שם → `_SLICER_LISTBOXES` + `data/filters.json` + מטריצה
- [ ] טבלת FACT חדשה ל-KPI → `DB_WITHDRAWN_TABLE` / `DB_ALLOCATED_TABLE` + קטלוג
- [ ] שינוי עמודת סיבת זיכוי / `TransferReason` → עדכון `count_by_withdrawal_reason` + טולטיפ/תוויות withdrawal
- [ ] הרצת `pytest -m sanity` ואז `pytest -m regression` לפני מסירה
- [ ] צירוף CSV מ-`results/run-reports/` לתיעוד הריצה
