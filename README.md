# Validation Core — בדיקות דשבורד שליטה בניוד

מסגרת pytest + Playwright שמאמתת את דשבורד הצי (Power BI בפורטל) מול מחסן SQL Server:  
KPI, פילטרים, טאבים, טבלה, גרפים ואינווריאנטים עסקיים.

מיועד לצוותי **Validation / QA**, **BI**, ו**Data**.  
היכרות מדורגת (מושגים, ספריות, בדיקות גנריות מול YAML, ארכיטקטורה ודשבורדים): [`docs/PROJECT_GUIDE.md`](docs/PROJECT_GUIDE.md).  
מקור האמת לכיסוי הצי: [`docs/COVERAGE_CATALOG.md`](docs/COVERAGE_CATALOG.md).

---

## דרישות מקדימות

| רכיב | הערה |
|------|------|
| Python 3.11+ | מומלץ venv |
| Windows + ODBC Driver 17 for SQL Server | החיבור הוא `Trusted_Connection` (זהות Windows) |
| גישה ל-SQL Server / Express | טבלאות `[DIM].[Vehicle]`, `[FACT].[SigningReturnVehicle]`, `[FACT].[VehicleFlow]` |
| גישה לפורטל הדשבורד | SSO / MFA לפי הארגון |
| Chromium ל-Playwright | מותקן בשלב ההתקנה |

---

## התקנה מהירה

```powershell
cd Validation-Core-main
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
playwright install chromium

copy .env.example .env
# ערוך את .env: שרת DB, שמות DB/טבלה, כתובות פורטל
```

פרטי משתני סביבה: [`.env.example`](.env.example) ו-`config/settings.py`.

---

## התחברות (Auth)

1. ודא ש-`MANUAL_LOGIN=true` ב-`.env` בהרצה הראשונה.
2. הרץ טסט קצר (למשל sanity) — ייפתח דפדפן; התחבר לפורטל.
3. הסשן נשמר ל-`auth_state.json` (gitignored) ומשמש בהרצות הבאות.
4. להרצה לא-אינטראקטיבית (לאחר שיש קובץ סשן תקף): `MANUAL_LOGIN=false`.

> **CI / צוות:** נדרשת הסכמה על service account או חידוש מבוקר של `auth_state.json`.  
> כיום אין pipeline — ראו סעיף "הטמעה בצוות".

---

## הרצת טסטים

```powershell
# Smoke מהיר (טעינה + UX פילטרים)
pytest -m sanity

# רגרסיה מלאה (KPI / פילטרים / טבלאות / גרפים / אינווריאנטים)
pytest -m regression

# רק בדיקות מול DB
pytest -m data

# הכל
pytest
```

Markers מוגדרים ב-`pytest.ini`: `sanity`, `data`, `regression`.

---

## דוחות וארטיפקטים

אחרי כל הרצה נוצרים תחת `result/` (gitignored). ReportPortal אינו כותב לתיקייה הזו.

| פלט | נתיב | למי שימושי |
|-----|------|------------|
| HTML | `result/html-reports/report_*.html` | מפתחים / QA |
| CSV בעברית (שלבים UI+SQL) | `result/run-reports/run_*.csv` | BI / ניתוח כשלים |
| צילומי מסך + Playwright trace | `result/screenshots/`, `result/traces/` | דיבוג כשל |

ה-CSV הוא הדוח העסקי העיקרי לכל בדיקה: שם, סטטוס, תאריך התחלה, תאריך סיום, משך בשניות, פעולה, שאילתה, פלט, עבר/נכשל.  
ב-ReportPortal (עם `--reportportal`) מופיעים סיכום תזמון + אותו קובץ CSV כקובץ מצורף.

---

## מבנה הפרויקט

```
config/settings.py          # הגדרות מ-.env
core/portal/                # Layer 0 — ReportShell (SSO, קטלוג, iframe, timeouts, last-refresh)
core/components/            # Layer 2 — קוראי ויזואל גנריים (slicer, KPI, gauge, chart)
db/connection.py            # מפעל חיבור גנרי
db/clients/                 # SQL לקריאה בלבד, קובץ לכל דוח
pages/<report>/             # Page Object של כל דוח (צי: pages/fleet_dashboard/)
pages/secondary_auth.py     # התחברות ArcGIS משותפת, מחוץ ל-core
tests/ui/                   # sanity / smoke
tests/e2e/                  # רגרסיה UI↔DB
tests/helpers/              # מנוע parity ופתיחת דשבורד בלבד
data/fleet/                 # Layer 3 — קטלוג ומטריצת פילטרים של הצי
data/alerts/                # Layer 3 — חוזה מידות של התרעות
reports/test_run_report.py  # כתיבת CSV לריצה
docs/COVERAGE_CATALOG.md    # קטלוג KPI ↔ DB ↔ טסטים
.specify/memory/constitution.md  # עקרונות שכבות, אי-דליפת דומיין, חוזה הטסטים
```

### שכבות (Layered Portal)

| שכבה | מיקום | מה מותר |
|------|--------|---------|
| Layer 0 | `core/portal/` (`ReportShell`) | התחברות/SSO, חיפוש קטלוג, המתנה ל-iframe, timeout לטעינת ויזואל, בדיקת עדכניות אחרונה |
| Layer 1 / Domain | `pages/<report>/` | אובייקטי עמוד. צי: `pages/fleet_dashboard/` |
| Layer 2 | `core/components/` | קוראים גנריים ל-slicer, KPI, gauge ו-chart |
| Layer 3 | `data/<report>/` | `data/fleet/filters.json`, `data/fleet/filter_matrix.json`, `data/alerts/alerts_contract.yaml` |
| Warehouse | `db/connection.py`, `db/clients/<report>.py` | מפעל חיבור גנרי; SQL של דוח נשאר לקריאה בלבד |
| Helpers | `tests/helpers/` | מנוע parity ופתיחת דשבורד בלבד |

`ReportShell` ו-`Slicer` חייבים להישאר גנריים: אסור שידלוף אליהם לוגיקה של דשבורד ספציפי.
אחרי שינוי ב-Layer 0 או Layer 2, `pytest` על `tests/ui/fleet_dashboard/` חייב לעבור ב-100%.
עקרונות מלאים: [`.specify/memory/constitution.md`](.specify/memory/constitution.md).

---

## הטמעה בצוות (BI / פיתוח)

### לפני שינוי בדשבורד

1. פתחו את [`docs/COVERAGE_CATALOG.md`](docs/COVERAGE_CATALOG.md).
2. זהו את ה-KPI / פילטר / גרף שמשתנה.
3. עדכנו Page Object / שאילתות DB לפי הצ'קליסט בקטלוג.
4. הריצו `pytest -m sanity` ואז `pytest -m regression`.
5. שמרו את ה-CSV מהריצה כראיה לאימות.

### בעלות (RACI מוצע)

| שינוי | BI | Data | Validation |
|-------|----|------|------------|
| כותרת ויזואל / slicer | R | C | A (עדכון selectors) |
| לוגיקת מידה / עמודת סטטוס | C | R | A (עדכון SQL + טסט) |
| טסט חדש / הרחבת מטריצה | C | C | R |

R = Responsible, A = Accountable לעדכון הריפו, C = Consulted.

### מה עדיין חסר להטמעה מלאה ב-CI

- Pipeline (GitHub Actions / Azure DevOps) עם העלאת HTML + CSV
- אסטרטגיית auth לא-אינטראקטיבית מוסכמת
- יעד פרסום קבוע לדוחות (SharePoint / blob / pages)

---

## פתרון תקלות נפוצות

| תסמין | בדיקה |
|--------|--------|
| כשל חיבור ל-DB | ODBC 17 מותקן? `DB_SERVER` / הרשאות Windows ל-SQL? |
| KPI `allocated` / `withdrawn` לא תואמים UI | ודא שיובאו FACT דרך `python db.py`; בדוק פילטרים (Unit/Category/Source חלים גם על FACT) |
| Timeout על iframe / KPI | הגדל `DEFAULT_TIMEOUT`; ודא שהסשן ב-`auth_state.json` עדיין תקף |
| ערכי פילטר לא נמצאים | עדכן `data/fleet/filters.json` לפי הנתונים בסביבה |
| SubUnit לא מופיע | בחר קודם `district` מתאים (cascading) |

---

## רישיון / מקור

ריפו: Validation-Core — בדיקות אימות לדשבורד הצי מול מחסן הנתונים.
