# Calorie Tracker

A personal calorie and macro tracker that replaces paid apps (Cal AI, MyFitnessPal, etc.) with a self-hosted Streamlit app backed by Supabase and Gemini.

## Features

- **Photo logging** — photograph a mixed dish; Gemini 3.6 Flash estimates calories and macros per component, scaled to your measured or size-described portion
- **Nutrition label OCR** — photograph a packaged food label; Gemini 3.1 Flash-Lite extracts structured nutrition data
- **Manual logging** — enter name + nutrition data once, reuse from the library on later days
- **Daily summary** — calories and macros vs. targets with progress bars; delete individual log entries
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

1. Clone the repo and install dependencies:

```bash
pip install -r requirements.txt
```

2. Copy `.env.example` to `.env` and fill in your keys:

```
SUPABASE_URL=...
SUPABASE_KEY=...
GEMINI_API_KEY=...
```

3. Run locally:

```bash
streamlit run app.py
```

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
