Adrian, here's the implementation roadmap I'd suggest, broken into phases you can ship incrementally:

---

**DONE Phase 0 — Scaffolding** *(do once, unblocks everything else)*
- Init repo structure per `DIRECTORY_STRUCTURE.md` (all folders + empty `__init__.py`s)
- `requirements.txt` with pinned versions: `streamlit`, `supabase`, `google-generativeai`, `requests`, `python-dotenv`
- `utils/config.py` loading env vars
- `.env` template (gitignored), `.gitignore` updated
- Supabase project created + all 6 tables defined with correct schema

---

**DONE Phase 1 — Database layer** *(foundation everything else calls)*
- `models/schemas.py` — dataclasses for `Food`, `Meal`, `LoggedEntry`, `WeightLog`, `Goals`
- `services/db.py` — full CRUD for all 6 tables
- No UI yet, test this directly in a scratch script

---

**DONE Phase 2 — Goals & Daily Summary** *(easiest pages, validates DB layer)*
- `pages/5_Goals_Settings.py` — form to set calorie/macro targets, saves to `goals` table
- `services/calculations.py` — macro math (sum logged entries for a date, compare to goals)
- `pages/3_Daily_Summary.py` — pulls today's logged entries, renders progress bars vs goals

---

**DONE Phase 3 — Manual food logging** *(core loop without any AI)*
- `pages/1_Log_Food.py` — manual entry tab: name + cal/protein/carbs/fats form, saves to `foods` + `logged_entries`
- Searchable food library (pull existing `foods` rows, let user re-log without re-entering)
- This gives you a fully working tracker before touching any AI

---

**DONE Phase 4 — Weight tracking** *(isolated, no dependencies)*
- Unique `weight_logs.date`; `upsert_weight_log` overwrites same day; `delete_weight_log`
- `pages/4_Weight_Tracker.py` — date + lbs form, latest/delta metric, line chart, delete list

---

**Phase 5 — Vision food detection** *(first AI integration)*
- `services/nutrition_api.py` — USDA FoodData Central search + lookup
- `services/estimator.py` — Gemini fallback when USDA misses, flags result as `estimated`
- `services/vision.py` — Gemini vision call, structured output (list of detected food names)
- Wire into `pages/1_Log_Food.py` as a "Photo" tab: capture → detect → USDA lookup (or fallback) → user confirms weights → log

---

**Phase 6 — OCR label scanning**
- `services/ocr.py` — Gemini vision call with a label-reading prompt, parses nutrition facts
- `pages/2_Scan_Label.py` — capture label photo → OCR → save as `source: ocr` food entry

---

**Phase 7 — Polish + deploy**
- Error states, loading spinners, edit/reject flow for detected foods
- Deploy to Streamlit Community Cloud from GitHub