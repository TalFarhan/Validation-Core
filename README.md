# Validation Core — בדיקות דשבורד שליטה בניוד

מסגרת pytest + Playwright שמאמתת את דשבורד הצי (Power BI בפורטל) מול מחסן SQL Server:  
KPI, פילטרים, טאבים, טבלה, גרפים ואינווריאנטים עסקיים.

מיועד לצוותי **Validation / QA**, **BI**, ו**Data** — מקור האמת לכיסוי: [`docs/COVERAGE_CATALOG.md`](docs/COVERAGE_CATALOG.md).

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

אחרי כל הרצה נוצרים תחת `test-results/` (gitignored):

| פלט | נתיב | למי שימושי |
|-----|------|------------|
| HTML | `test-results/report.html` | מפתחים / QA |
| CSV בעברית (שלבים UI+SQL) | `test-results/run-reports/run_*.csv` | BI / ניתוח כשלים |
| Allure raw | `test-results/allure-results/` | `allure serve test-results/allure-results` |
| צילומי מסך + Playwright trace | `test-results/screenshots/`, traces ב-Allure | דיבוג כשל |

ה-CSV הוא הדוח העסקי העיקרי: פעולה, שאילתה, פלט, סטטוס עבר/נכשל.  
ב-Allure מצורף `validation-steps.csv` לכל טסט (שלבים של אותה בדיקה). נתיב ה-CSV המלא של הריצה נרשם ב-`environment.properties` בתוך `allure-results`.

### Allure (מקומי)

הפלאגין `allure-pytest` רץ אוטומטית (`--alluredir` ב-`pytest.ini`). אחרי הרצה:

```powershell
# התקנת Allure CLI (פעם אחת) — Scoop / Chocolatey / הורדה מ-GitHub
# scoop install allure
# או: choco install allure-commandline

allure serve test-results/allure-results
```

בדוח תראו:

1. **Behaviors** — Epic `Fleet Dashboard Validation` ← Features (KPI / Filters / Charts / …)
2. **Steps** — ניווט, פילטרים, שאילתות DB, hover על גרפים
3. **Attachments** — צילום מסך + Playwright trace בכישלון, ו-CSV של שלבי הוולידציה

קטלוג התגיות: `reports/allure_catalog.py`.

> **CI:** עדיין לא מוטמע. אחרי שהדוח המקומי יציב — `allure generate` + שמירת HTML כ-Artifact.

---

## מבנה הפרויקט

```
config/settings.py          # הגדרות מ-.env
db/                         # לקוח SQL לקריאה בלבד
pages/fleet_dashboard/      # Page Object של הדשבורד
tests/ui/                   # sanity / smoke
tests/e2e/                  # רגרסיה UI↔DB
tests/helpers/              # assert משותפים
data/filters.json           # ערכי פילטר לדוגמה
data/filter_matrix.json     # תרחישי מטריצה
reports/test_run_report.py  # כתיבת CSV לריצה
reports/allure_catalog.py   # Epic / Feature labels ל-Allure
docs/COVERAGE_CATALOG.md    # קטלוג KPI ↔ DB ↔ טסטים
```

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

- Pipeline (GitHub Actions / Azure DevOps) עם `allure generate` + העלאת HTML + CSV
- אסטרטגיית auth לא-אינטראקטיבית מוסכמת
- יעד פרסום קבוע לדוחות (SharePoint / blob / pages)

---

## פתרון תקלות נפוצות

| תסמין | בדיקה |
|--------|--------|
| כשל חיבור ל-DB | ODBC 17 מותקן? `DB_SERVER` / הרשאות Windows ל-SQL? |
| KPI `allocated` / `withdrawn` לא תואמים UI | ודא שיובאו FACT דרך `python db.py`; בדוק פילטרים (Unit/Category/Source חלים גם על FACT) |
| Timeout על iframe / KPI | הגדל `DEFAULT_TIMEOUT`; ודא שהסשן ב-`auth_state.json` עדיין תקף |
| ערכי פילטר לא נמצאים | עדכן `data/filters.json` לפי הנתונים בסביבה |
| SubUnit לא מופיע | בחר קודם `district` מתאים (cascading) |

---

## רישיון / מקור

ריפו: Validation-Core — בדיקות אימות לדשבורד הצי מול מחסן הנתונים.
