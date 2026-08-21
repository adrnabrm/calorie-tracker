# Calorie Tracker

A personal calorie and macro tracker that replaces paid apps (Cal AI, MyFitnessPal, etc.) with a self-hosted Streamlit app backed by Supabase and Gemini.

## Features

- **Photo logging** — photograph a mixed dish; Gemini 3.6 Flash estimates calories and macros per component, scaled to your measured or size-described portion
- **Nutrition label OCR** — photograph a packaged food label; Gemini 3.1 Flash-Lite extracts structured nutrition data. Save to library or save and log 1 serving in one step
- **Manual logging** — enter name + nutrition data once, reuse from the library on later days. Supports g, oz, or serving as the unit — pick serving for single-serving items (bag of chips, piece of fruit) without needing to know the gram weight
- **Recipes** — compose named meals from library foods; log a recipe as a single entry; supports multiple servings per batch
- **Daily summary** — calories and macros vs. targets with progress bars; each log entry shows the full macro breakdown (p/c/f); edit or delete individual entries
- **Past-date logging** — log food to any past date, not just today
- **Library management** — edit a food's name, serving size, and macros in place; live macro preview as you adjust the amount before logging
- **Weight tracking** — log weight in lbs, see delta vs. previous entry, view a line chart over time
- **Goals** — set calorie/macro targets per date; daily summary always uses the latest applicable goal

## Stack

| Layer | Choice |
|---|---|
| App | Streamlit |
| Database | Supabase (Postgres) |
| Photo estimate | Gemini 3.6 Flash (thinking `medium`) |
| OCR | Gemini 3.1 Flash-Lite |
| Hosting | Streamlit Community Cloud |

## Setup

> **Note:** This app is wired to a personal Supabase instance and is not intended for public use. The database, credentials, and schema are private — there is no setup path for other users.

## Project Structure

```
calorie-tracker/
├── app.py                  # Entry point; st.navigation
├── pages/
│   ├── 1_Log_Food.py       # Vision + manual logging
│   ├── 2_Scan_Label.py     # OCR label workflow
│   ├── 3_Daily_Summary.py  # Today's totals vs goals (default page)
│   ├── 4_Weight_Tracker.py # Weight log + chart
│   └── 5_Goals_Settings.py # Calorie/macro targets
├── services/               # Business logic (no UI)
│   ├── db.py               # Supabase CRUD
│   ├── gemini.py           # Shared Gemini client
│   ├── vision.py           # Photo estimate
│   ├── ocr.py              # Label OCR
│   └── calculations.py     # Macro math
├── models/
│   └── schemas.py          # Pydantic models
└── utils/
    └── config.py           # Env var loading
```
