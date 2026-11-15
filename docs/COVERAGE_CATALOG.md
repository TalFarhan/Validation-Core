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
- טיפוסים: `tests/ui/fleet_dashboard/dashboard_validation.py` → `KPI_TYPES`
- הגדרות טבלאות: `DB_TABLE`, `DB_WITHDRAWN_TABLE`, `DB_ALLOCATED_TABLE`

---

## 2. פילטרים (Slicers)

| מפתח בקוד | תפקיד ב-UI (role name) | עמודת DB | ערכי דוגמה (`data/fleet/filters.json`) |
|-----------|-------------------------|----------|-----------------------------------|
| `district` | Unit | `Unit` | מחוז דן / דרום / צפון |
| `sub_unit` | SubUnit | `SubUnit` | מחוז הדרום 6003, מחוז דן 789, … |
| `category` | VehicleCategory | `VehicleCategory` | משאית |
| `source` | VehicleSource | `VehicleSource` | יר"ם, מרכז הובלה |

מטריצת תרחישים: `data/fleet/filter_matrix.json`.

שכבות: **איך** לסנן (dropdown / checkbox / search / clear-all) נמצא ב-Layer 2
(`core/components/slicer.py`). **מה** לבחור (כינויים ותוויות) נשאר ב-`data/fleet/filters.json`.
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
- DB: `tests/ui/fleet_dashboard/dashboard_validation.py` → `CHART_DB_BREAKDOWNS`, `assert_chart_tooltips_match_db_sample`, `assert_chart_labels_match_db_sample`
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
- [ ] Slicer חדש / שינוי שם → `_SLICER_LISTBOXES` + `data/fleet/filters.json` + מטריצה
- [ ] טבלת FACT חדשה ל-KPI → `DB_WITHDRAWN_TABLE` / `DB_ALLOCATED_TABLE` + קטלוג
- [ ] שינוי עמודת סיבת זיכוי / `TransferReason` → עדכון `count_by_withdrawal_reason` + טולטיפ/תוויות withdrawal
- [ ] הרצת `pytest -m sanity` ואז `pytest -m regression` לפני מסירה
- [ ] צירוף CSV מ-`result/run-reports/` לתיעוד הריצה

---

## 8. דשבורד התרעות — DB Parity (מנוע גנרי)

מנוע declarative: כל מידה בחוזה YAML (`name` יציב בלי ביטוי טווח התאריכים, `visual`, `compare` אופציונלי, `scope` אופציונלי, `category_id`, `sql_query`).
UI נקרא דרך Layer 2 (`KPI.number` / `KPI.read_text` / `KPI.scale` / `Chart.read`) ובמפה דרך `classify_presence`. DB דרך runner עם bind של `:start_date`, `:end_date`, ו-`:category_id` כשהמידה מגדירה אותו.
כל אחד מהמזהים `1`, `2`, `10` נבדק בנפרד. בכרטיסי זמן לפי סוג איום המיפוי מאושר: `1` ירי רקטות וטילים (Rockets), `2` חדירת מחבלים (Terrorists), `10` חדירת כלי טיס עוין (UAV). שש מידות הקטגוריה הקיימות נשארות בלי `label`.

| מידה (עוגן ב-UI) | visual | category_id | מקור / SQL | טסט |
|-------------------|--------|-------------|------------|------|
| אזורי התרעה תחת ירי | kpi | `1`, `2`, `10` (כל אחד במידה נפרדת) | `[FACT].[AlertsRedWeb]`, `COUNT(DISTINCT [WarningZoneName])`, `AlertDate >= :start_date AND < :end_date`, `CategoryID = :category_id` | `tests/ui/alerts_analysis_dashboard/test_db_parity.py` |
| אוכלוסייה מותרעת | kpi | `1`, `2`, `10` (כל אחד במידה נפרדת) | אותו חלון; `ISNULL(SUM(MAX(LesserWarningAreaPopulation) per LesserWarningAreaID), 0)` | `tests/ui/alerts_analysis_dashboard/test_db_parity.py` |
| מד (gauge) | gauge | — | אין כותרת ואין שאילתת מכנה מאושרות עדיין | — |
| עשרת היישובים עם כמות ההתרעות הגבוהה ביותר | chart | — | stub `SETTLEMENTS_CHART_SQL` (`SELECT 'placeholder'`, שתי עמודות). לא שאילתת מחסן מאושרת | `tests/ui/alerts_analysis_dashboard/test_db_parity.py` |
| מפת התרעות ביישובים | map | — | stub `MAP_PRESENCE_SQL` (`SELECT 'placeholder'`). נוכחות: `value` כולל 0, `empty` רק בלי מספר ובלי סימנים | `tests/ui/alerts_analysis_dashboard/test_db_parity.py` |
| סיכון לפי מדיניות התגוננות ברגע | kpi (text) | — | stub `POLICY_STATUS_SQL` (`SELECT 'placeholder'`). השוואת טקסט, לא מספר | `tests/ui/alerts_analysis_dashboard/test_db_parity.py` |
| היום / אתמול / סה"כ בטווח שנבחר | kpi | scope `ירי רקטות וטילים`, `category_id` `1` | stub `THREAT_KPI_STUB_SQL` (`SELECT 0`). לא שאילתת מחסן מאושרת | `tests/ui/alerts_analysis_dashboard/test_db_parity.py` |
| היום / אתמול / סה"כ בטווח שנבחר | kpi | scope `חדירת מחבלים`, `category_id` `2` | stub `THREAT_KPI_STUB_SQL` (`SELECT 0`). לא שאילתת מחסן מאושרת | `tests/ui/alerts_analysis_dashboard/test_db_parity.py` |
| היום / אתמול / סה"כ בטווח שנבחר | kpi | scope `חדירת כלי טיס עוין`, `category_id` `10` | stub `THREAT_KPI_STUB_SQL` (`SELECT 0`). לא שאילתת מחסן מאושרת | `tests/ui/alerts_analysis_dashboard/test_db_parity.py` |
| היום / אתמול / סה"כ בטווח שנבחר | kpi | scope `אוכלוסייה מותרעת`, בלי `category_id` | stub `POPULATION_KPI_STUB_SQL` (`SELECT 0`). לא שאילתת מחסן מאושרת | `tests/ui/alerts_analysis_dashboard/test_db_parity.py` |
| היום / אתמול / סה"כ בטווח שנבחר | kpi | scope `אזורי התרעה תחת ירי`, בלי `category_id` | stub `AREA_KPI_STUB_SQL` (`SELECT 0`). לא שאילתת מחסן מאושרת | `tests/ui/alerts_analysis_dashboard/test_db_parity.py` |
| עשרת הישובים עם כמות ההתרעות הגבוהה ביותר ביממה הנוכחית והקודמת | chart | — | stub `PERIOD_COMPARISON_CHART_SQL` (שתי עמודות, `WHERE 1 = 0`, בלי `:start_date` ובלי `AlertDate`). הכותרת סטטית ואינה עוקבת אחרי סלייסר הזמן | `tests/ui/alerts_analysis_dashboard/test_db_parity.py` |
| עמוד אוכלוסייה: התרעות לפי מחוז, התרעות לפי תאריך, גרף התרעות וגם ממוצע לפי שעה, אוכלוסייה מותרעת לפי יישוב (סדרות מותרעת / לא מותרעת) | chart | scope `ניתוח התרעות` | stub `POPULATION_PAGE_CHART_STUB_SQL`. לא שאילתת מחסן. זהויות UI בלבד | `tests/ui/alerts_analysis_dashboard/test_population_invariants.py` |
| סה"כ אוכלוסייה / אוכלוסייה מותרעת / אוכלוסייה לא ממוגנת | kpi | scope `ניתוח התרעות` | stub `POPULATION_PAGE_KPI_STUB_SQL` (`SELECT 0`). לא שאילתת מחסן. `test_db_parity.py` מוציא את ה-scope הזה | `tests/ui/alerts_analysis_dashboard/test_population_invariants.py` |

מיפוי בקוד:

- UI גנרי: `core/components/kpi.py` (`KPI.number`, `KPI.read_text`, `KPI.scale`), `core/components/chart.py` (`Chart.read`), `core/components/visual.py` (`classify_presence`) — ללא כותרות דומיין
- מנוע: `tests/helpers/db_parity_engine.py` → `validate_dashboard_generic`
- חוזה מידות: `data/alerts/alerts_contract.yaml`
- DB runner: `db/clients/alerts.py` → `AlertsDBRunner.scalar` / `rows` / `cell` (SQLAlchemy `text()` binds)
- דף / סלייסר טווח תאריכים: `pages/alerts_analysis/page.py` → `AlertsAnalysisPage.select_date_range`
- עמוד אוכלוסייה: `pages/alerts_analysis/population_page.py` → `AlertsPopulationPage`
- הגדרה: `DB_ALERTS_NAME` ב-`config/settings.py`; Marker: `db_parity` ב-`pytest.ini`

חלון 30 יום מחושב ב-Python (`end = now`, `start = now - 30d`, חצי-פתוח `[start, end)`) ומועבר כפרמטרים —
ללא string-formatting של תאריכים ב-SQL. בחירת הסלייסר נשארת בטסט, לא בשם המידה.

---

## 9. דשבורד צריכת אשראי — UI Sanity (רשומת זהב)

בדיקות מול `data/credit/db_sanity_purim2026.yaml` (snapshot פורים 2026). אין לקוח מחסן ואין `db/clients/credit.py` בslice הזה. המקור הוא קובץ הזהב, לא SQL.

| מפתח ב-YAML | שיטה בדף | טסט |
|-------------|----------|------|
| `kpi_metrics` | `CreditConsumptionPage.read_kpi_metrics()` | `test_kpi_metrics_match_golden` |
| `daily_trends_by_toggle` | `set_metric` / `set_visualization` + `read_daily_trends()` (Show as a table) | `test_daily_trends_match_golden` |
| `expenses_by_authority_millions` | `read_expenses_by_authority()` (Show as a table) | `test_expenses_by_authority_match_golden` |
| `daily_alerts` | `read_daily_alerts()` | `test_daily_alerts_match_golden` |
| `export_table_data` | `open_export_page()` + `read_export_table()` | `test_export_table_match_golden` |
| `active_filters` (`time_range` / `period` = פורים 2026) | `apply_filters()` | כל בדיקות הסניטי לפני הקריאה |

מיפוי בקוד:

- דף: `pages/credit_consumption/credit_consumption_page.py` (`CreditConsumptionPage`)
- ייצוא לעשן: `pages/credit_consumption/page.py`
- מתקן: `tests/sanity/credit_consumption_dashboard/conftest.py`
- טסטים: `tests/sanity/credit_consumption_dashboard/test_data_validation.py`
- Layer 2 מורכב: `KPI`, `Slicer` (כותרות ו-role names נשארות בדף)

---

## 10. דשבורד פניות הסברה — UI Sanity (רשומת זהב)

בדיקות מול `data/hasbara/db_sanity.yaml` (אוקטובר 2026). אין לקוח מחסן ואין `db/clients/hasbara.py`. המקור הוא קובץ הזהב, לא SQL. `apply_date_range` לוחץ פעם אחת על מתג סרגל הסינון `כלל התאריכים` או `יום נוכחי` כששדות תאריך ההתחלה והסיום מוסתרים או נעולים, ואז ממלא את `dashboard_info.date_range`. גריד מפורט וטבלת "הצג כטבלה" נגללים דרך `collect_virtualized_rows`. לקובץ הזהב אין השוואת `last_updated`.

| מפתח ב-YAML | שיטה בדף | טסט |
|-------------|----------|------|
| `dashboard_info.date_range`, `active_filters` | `apply_date_range` / `read_slicer_text` | `test_hasbara_screen1_filters_match_golden` עד `test_hasbara_screen4_filters_match_golden` |
| `kpi_metrics` | `PublicInquiriesPage.read_kpi_metrics()` | `test_hasbara_screen1_kpi_match_golden` |
| `charts` | `read_screen1_charts()` (`VisualTable`) | `test_hasbara_screen1_charts_match_golden` |
| `investigation_table_data` | `open_screen("screen_2")` + `read_investigation_rows()` | `test_hasbara_screen2_investigation_rows_match_golden` |
| `surveys_summary` | `read_satisfaction()` | `test_hasbara_screen3_surveys_match_golden` |
| `message_reception`, `service_reception`, `leading_contact_channels`, `platforms_breakdown` | `select_satisfaction_tab` + `read_satisfaction()` | `test_hasbara_screen3_distributions_match_golden` |
| `feedback_investigation_table_data` | `open_screen("screen_4")` + `read_feedback_rows()` | `test_hasbara_screen4_feedback_rows_match_golden` |

מיפוי בקוד:

- דף: `pages/public_inquiries/page.py` (`PublicInquiriesPage`)
- מתקן: `tests/sanity/public_inquiries_dashboard/conftest.py`
- טסטים: `tests/sanity/public_inquiries_dashboard/test_data_validation.py`
- עשן טריות (לא חלק מהרשומה): `tests/ui/public_inquiries_dashboard/test_dashboard_smoke.py`
- Layer 2 מורכב: `KPI`, `Slicer`, `VisualTable`, `core/components/virtual_grid.py` (כותרות נשארות בדף)

---

## 11. דשבורד תמ״צ חוסן — UI Sanity (מסך נחיתה)

בדיקות מול `data/hosen/db_sanity.yaml`. אין לקוח מחסן ואין `db/clients/hosen.py`. המקור הוא קובץ הזהב, לא SQL. מסך 1 הוא המסך שנפתח בלי מעבר טאב. עשן הטריות נשאר `verify_freshness()`.

| מפתח ב-YAML | שיטה בדף | טסט |
|-------------|----------|------|
| `survey_status` | `HosenStatusPage.read_screen_1_metrics()` | `test_hosen_screen1_matches_golden` |
| `kpis` | `read_screen_1_metrics()` (`KPI` כשהכותרת על הכרטיס, אחרת מסמך הוויזואל) | `test_hosen_screen1_matches_golden` |
| `resilience_scores` | `read_screen_1_metrics()` (`collect_virtualized_rows` על `ציון חוסן`) | `test_hosen_screen1_matches_golden` |
| `active_filters` | `read_screen_1_metrics()` (`Slicer.control`) | `test_hosen_screen1_matches_golden` |

מיפוי בקוד:

- דף: `pages/hosen_status/page.py` (`HosenStatusPage`)
- מתקן: `tests/sanity/hosen_status_dashboard/conftest.py`
- טסט: `tests/sanity/hosen_status_dashboard/test_screen1_sanity.py`
- עשן טריות: `tests/ui/hosen_status_dashboard/test_dashboard_smoke.py`
