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

**DONE Phase 5 — OCR label scanning** *(first AI integration)*
- `models/schemas.py` — `NutritionLabel` Pydantic model (serving + macros, no name)
- `services/ocr.py` — Gemini Interactions structured output via `NutritionLabel.model_json_schema()` / `model_validate_json`
- `pages/2_Scan_Label.py` — camera or upload → Read label → confirm (user types name) → `foods` with `source: ocr`

---

**DONE Phase 6 — Vision mixed-dish estimate**
- `models/schemas.py` — `FoodEstimate` / `EstimateComponent` (`is_food`, grams/macros bounds, validator)
- `services/gemini.py` — `model` + `thinking_level` per call; OCR default `gemini-3.1-flash-lite`; parse/API fail → `GeminiError`
- `services/vision.py` — photo + grams or Small/Typical/Large + notes → 3.6 Flash (`medium`); rescale to weighed grams
- `pages/1_Log_Food.py` From photo: Estimate spinner → edit/discard → log as `estimated` (per 100g food + today's entry). Library and Daily Summary tag `(estimated)`
- Not in this phase: USDA lookup, per-ingredient weighing

---

**Phase 7 — Polish + deploy**
- Error states, loading spinners
- Deploy to Streamlit Community Cloud from GitHub