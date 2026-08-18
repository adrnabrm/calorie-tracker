# Architecture

## Stack

| Layer | Choice |
|---|---|
| App (frontend + logic) | Streamlit |
| Database | Supabase (Postgres) |
| Vision / LLM | Gemini 3.1 Flash-Lite (google-genai, Interactions API) |
| Nutrition data | USDA FoodData Central |
| Hosting | Streamlit Community Cloud |

## Directory Layout

```
calorie-tracker/
├── app.py                    # Streamlit entry point / home page
├── requirements.txt
├── .env                      # API keys — gitignored
├── .env.example              # Template for env vars
│
├── pages/
│   ├── 1_Log_Food.py         # Vision + manual food logging
│   ├── 2_Scan_Label.py       # OCR nutrition label workflow
│   ├── 3_Daily_Summary.py    # Today's calories/macros vs goals
│   ├── 4_Weight_Tracker.py   # Weight logging + graph
│   └── 5_Goals_Settings.py   # Calorie/macro target input
│
├── services/                 # All business logic, no UI code
│   ├── db.py                 # Supabase client + CRUD
│   ├── vision.py             # Gemini: food detection from photo
│   ├── ocr.py                # Gemini: nutrition label reading
│   ├── nutrition_api.py      # USDA FoodData Central lookups
│   ├── estimator.py          # Gemini fallback when USDA fails (flags as "estimated")
│   └── calculations.py       # Macro/calorie math
│
├── models/
│   └── schemas.py            # Dataclasses mirroring Supabase tables
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
1. User photos food → `vision.py` sends to Gemini → list of food names
2. Each name looked up via `nutrition_api.py` (USDA)
3. On USDA miss → `estimator.py` (Gemini fallback, source = `estimated`)
4. User confirms weights → `calculations.py` computes totals → `db.py` writes `logged_entries`

### Daily summary
1. `pages/3_Daily_Summary.py` loads today's entries once (`get_entries_for_date` joins `foods(name)`) and `calculations.macros_from_entries` sums them vs goals
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
1. User photos nutrition label → `ocr.py` sends to Gemini → parsed nutrition facts
2. Saved as `foods` entry (source = `ocr`), then logged via `logged_entries`

## Implementation Phases

| Phase | Scope |
|---|---|
| 0 | Scaffolding — repo structure, requirements, env, stubs |
| 1 | Database layer — `db.py` CRUD + schema |
| 2 | Goals & Daily Summary pages |
| 3 | Manual food logging |
| 4 | Weight tracking |
| 5 | Vision food detection (Gemini + USDA) |
| 6 | OCR label scanning |
| 7 | Polish + Streamlit Community Cloud deploy |
