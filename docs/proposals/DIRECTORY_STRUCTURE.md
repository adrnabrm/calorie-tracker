Here's a proposed project structure based on the finalized stack. This is a **layout proposal only** — no code yet, just organizing responsibilities into files so it's easy to build incrementally.

calorie-tracker/  
├── app.py                      \# Main Streamlit entry point / navigation  
├── requirements.txt            \# streamlit, supabase, google-generativeai, requests, etc.  
├── .env                        \# API keys (Supabase, Gemini, USDA) — gitignored  
├── .gitignore  
│  
├── pages/                      \# Streamlit multi-page app structure  
│   ├── 1\_Log\_Food.py            \# Vision workflow \+ manual workflow entry point  
│   ├── 2\_Scan\_Label.py          \# OCR nutrition label workflow  
│   ├── 3\_Daily\_Summary.py       \# Today's calories/macros vs goals  
│   ├── 4\_Weight\_Tracker.py      \# Weight logging \+ graph  
│   └── 5\_Goals\_Settings.py      \# Manual calorie/macro goal input  
│  
├── services/                   \# Core logic, no UI code here  
│   ├── \_\_init\_\_.py  
│   ├── db.py                    \# Supabase client \+ CRUD functions (foods, meals, logs, weight)  
│   ├── vision.py                 \# Gemini calls: food detection from photo  
│   ├── ocr.py                    \# Gemini calls: nutrition label reading  
│   ├── nutrition\_api.py          \# USDA FoodData Central lookups  
│   ├── estimator.py              \# LLM fallback estimation when nutrition API fails  
│   └── calculations.py           \# Calorie/macro math, weight-based aggregation  
│  
├── models/                     \# Data structures (optional but clean)  
│   ├── \_\_init\_\_.py  
│   └── schemas.py               \# Python dataclasses/TypedDicts mirroring Supabase tables  
│  
└── utils/  
    ├── \_\_init\_\_.py  
    └── config.py                 \# Loads env vars, API keys, constants

### **Rationale for key decisions**

* **`pages/` folder** — Streamlit's built-in multi-page app convention (numbered files become sidebar nav automatically), matches your 5 core features naturally as separate pages  
* **`services/` separated from `pages/`** — keeps API calls and business logic out of UI code, so Streamlit files stay focused on layout/display, not logic (easier to test/debug independently, and honors your "surgical, minimal changes" preference later — you'll know exactly which file to touch for a given bug)  
* **`ocr.py` separate from `vision.py`** — even though both call Gemini, they're distinct workflows (label OCR vs. food photo detection) with different prompts/parsing, so keeping them separate avoids one bloated file  
* **`estimator.py` separate from `nutrition_api.py`** — this is your fallback path (LLM estimates when USDA lookup fails), worth isolating since it's conceptually different from a real API call and needs the "estimated" flag logic

### **Table structure (for `db.py` / Supabase)**

Matches the data model from your spec:

* `foods` (id, name, calories, protein, carbs, fats, source: manual/vision/ocr/estimated)  
* `meals` (id, name, type: composed/simple)  
* `meal_ingredients` (meal\_id, food\_id, weight\_grams) — join table for composed meals  
* `logged_entries` (id, date, food\_id OR meal\_id, weight\_grams, calculated totals)  
* `weight_logs` (id, date, weight)  
* `goals` (calorie\_target, protein\_target, carbs\_target, fats\_target)

---

Does this structure look right, or do you want changes before we start writing actual files (e.g. different page grouping, want `models/` dropped since it might be overkill for a single-user app)?
