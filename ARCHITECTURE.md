# Architecture

## Stack

| Layer | Choice |
|---|---|
| App (frontend + logic) | Streamlit |
| Database | Supabase (Postgres) |
| Photo estimate | Gemini 3.6 Flash (thinking `medium`) |
| OCR | Gemini 3.1 Flash-Lite |
| Hosting | Streamlit Community Cloud |

## Directory Layout

```
calorie-tracker/
├── app.py                    # Streamlit entry point; st.navigation, Daily Summary is default
├── requirements.txt
├── .env                      # API keys — gitignored
├── .env.example              # Template for env vars
├── .streamlit/
│   ├── config.toml           # Dark navy theme; coral #FF8C42 for buttons, alerts, selections
│   └── secrets.toml          # gitignored
│
├── pages/
│   ├── 1_Log_Food.py         # Vision + manual food logging
│   ├── 2_Scan_Label.py       # OCR nutrition label workflow
│   ├── 3_Daily_Summary.py    # Today's calories/macros vs goals (home / default page)
│   ├── 4_Weight_Tracker.py   # Weight logging + graph
│   └── 5_Goals_Settings.py   # Calorie/macro target input
│
├── services/                 # All business logic, no UI code
│   ├── db.py                 # Supabase client + CRUD
│   ├── gemini.py             # Shared Gemini client + generate() (Pydantic structured output; model per call)
│   ├── vision.py             # Gemini 3.6 Flash: mixed-dish estimate from photo + weight or size + notes
│   ├── ocr.py                # Gemini 3.1 Flash-Lite: nutrition label reading
│   ├── nutrition_api.py      # Stub — USDA is not part of v1 vision
│   ├── estimator.py          # Stub — old USDA fallback; estimates live in vision.py
│   └── calculations.py       # Macro/calorie math
│
├── models/
│   └── schemas.py            # Dataclasses + NutritionLabel + vision estimate Pydantic models
│
└── utils/
    └── config.py             # Loads env vars / API keys
```

## Database Schema (Supabase)

- `foods` — `id, name, calories, protein, carbs, fats, serving_grams, serving_unit: g|oz, source: manual|vision|ocr|estimated`
- `meals` — `id, name, type: composed|simple`
- `meal_ingredients` — `meal_id, food_id, weight_grams` (join table for composed meals)
- `logged_entries` — `id, date, food_id?, meal_id?, weight_grams, weight_unit: g|oz, calories, protein, carbs, fats`
- `weight_logs` — `id, date` (unique), `weight` (lbs)
- `goals` — `calorie_target, protein_target, carbs_target, fats_target`

## Data Flow

### Vision workflow
For mixed dishes you did not cook (pho, a restaurant plate). Homemade food you already know goes through Manual, not this path. No per-ingredient USDA lookup.

1. On `pages/1_Log_Food.py` tabs (From library, New food, From photo): take or upload a photo, then either a **food-only** weight (bowl tared; g or oz) **or** Small / Typical / Large, plus an optional note (`extra noodles, ate half`)
2. **Estimate** (button only) → `vision.py` calls Gemini 3.6 Flash (thinking `medium`) with `FoodEstimate` JSON schema. API/JSON/validation failures raise `GeminiError` ("Gemini request failed. Try again.") and do not open confirm. `is_food=false` is a successful read of a non-food image ("No food in this photo.")
3. If the user weighed the food, component grams/macros are rescaled so grams sum to that weight. Confirm: edit name and component rows (`st.data_editor`); displayed totals are the sum of rows. Discard clears the estimate. Blank name does not write
4. **Log** always `insert_food` (`source=estimated`, `serving_grams=100`, macros per 100g from confirmed totals) then `logged_entries` for the confirmed grams. Library and Daily Summary tag these `(estimated)`

### Daily summary
1. `pages/3_Daily_Summary.py` loads today's entries once (`get_entries_for_date` joins `foods(name, source)`) and `calculations.macros_from_entries` sums them vs goals
2. Progress bars show calories/protein/carbs/fats vs targets (remaining + %)
3. Lists today's `logged_entries` (food name, amount in the unit it was logged, calories) via `get_entries_for_date`
4. Delete button on each row opens an Are you sure? dialog, then `delete_logged_entry` (removes the log, not the food library item)

### Manual workflow
1. User enters name, label serving size (g or oz), and nutrition per serving → `foods` (source = `manual`). Serving is stored as grams (`1 oz = 28.3495 g`) plus `serving_unit` for display
2. Amount eaten (g or oz) is converted to grams. `calculations.scale_macros` scales by `eaten_grams / serving_grams`
3. `db.py` writes `logged_entries` for today with `weight_unit`
4. Reusable: search `foods`, pick one, enter amount (unit defaults to that food's `serving_unit`), log again
5. Delete from library opens an Are you sure? dialog, then `delete_food` (clears `food_id` on existing logs so the row can be removed; log macros stay)

### Weight tracking
1. `pages/4_Weight_Tracker.py` form: date (default today) + weight in lbs → `upsert_weight_log` (one row per date; second save overwrites)
2. Latest log shown as a metric with delta vs the previous log (down is green)
3. Line chart of all `weight_logs` over time (`get_all_weight_logs`, ordered by date)
4. List newest-first; delete opens an Are you sure? dialog, then `delete_weight_log`

### OCR workflow
1. User photos or uploads a nutrition label on `pages/2_Scan_Label.py`
2. **Read label** → `ocr.py` calls `gemini.generate` (`gemini-3.1-flash-lite`, Interactions API) with `NutritionLabel` as the Pydantic JSON schema (`model_json_schema()` / `model_validate_json`). API/parse failures raise `GeminiError` (shown as "Gemini request failed"); a successful read with `found_label=false` is a different path
3. Schema is serving size/unit + per-serving calories/protein/carbs/fats and `found_label`. Name is not extracted
4. Confirm form: user types the name and can edit the numbers, then `insert_food` with source = `ocr`. Nothing is written to `logged_entries` (log later from Log Food)

## Implementation Phases

| Phase | Scope |
|---|---|
| 0 | Scaffolding — repo structure, requirements, env, stubs |
| 1 | Database layer — `db.py` CRUD + schema |
| 2 | Goals & Daily Summary pages |
| 3 | Manual food logging |
| 4 | Weight tracking |
| 5 | OCR label scanning |
| 6 | Vision mixed-dish estimate (photo + weight or size + notes → Gemini 3.6 Flash) |
| 7 | Polish + Streamlit Community Cloud deploy |
