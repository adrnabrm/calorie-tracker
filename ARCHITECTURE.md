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

- `foods` — `id, name, calories, protein, carbs, fats, source: manual|vision|ocr|estimated`
- `meals` — `id, name, type: composed|simple`
- `meal_ingredients` — `meal_id, food_id, weight_grams` (join table for composed meals)
- `logged_entries` — `id, date, food_id?, meal_id?, weight_grams, calories, protein, carbs, fats`
- `weight_logs` — `id, date, weight`
- `goals` — `calorie_target, protein_target, carbs_target, fats_target`

## Data Flow

### Vision workflow
1. User photos food → `vision.py` sends to Gemini → list of food names
2. Each name looked up via `nutrition_api.py` (USDA)
3. On USDA miss → `estimator.py` (Gemini fallback, source = `estimated`)
4. User confirms weights → `calculations.py` computes totals → `db.py` writes `logged_entries`

### Daily summary
1. `db.get_entries_for_date` + `db.get_goals`
2. `calculations.macros_for_date` sums calories/macros and compares to targets (remaining + %)

### Manual workflow
1. User enters food name + nutrition data → saved to `foods` (source = `manual`)
2. Reusable: searchable from `foods` table for future log entries

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
