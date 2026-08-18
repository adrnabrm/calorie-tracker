## **Finalized Tech Stack**

**Frontend \+ Backend (combined):** Streamlit

* Single Python app, no separate API layer needed for single-user scale  
* Built-in `st.camera_input` for photo capture (food photos \+ OCR labels)  
* All logic (calling Gemini, calling Supabase, calculations) lives directly in the Streamlit app

**Database:** Supabase (Postgres)

* Tables: `foods`, `meals`, `meal_ingredients` (join table for composed meals), `logged_entries`, `weight_logs`, `goals`  
* Accessed via `supabase-py` client from within the Streamlit app

**LLM (vision \+ estimation fallback):** Gemini 3.1 Flash-Lite

* Free tier covers personal-scale usage  
* Used for: food detection from photos, nutrition estimation fallback, OCR reading of nutrition labels (Gemini handles vision \+ text extraction in one call)

**Nutrition API:** USDA FoodData Central

* Free, no rate limit issues at personal scale  
* Primary source for ingredient-level nutrition lookups

**Hosting:** Streamlit Community Cloud

* Free, deploys directly from a GitHub repo, purpose-built for exactly this kind of app

**Language:** Python end-to-end — no JS required anywhere in this stack.

---

### **Stack summary**

| Layer | Choice | Cost |
| ----- | ----- | ----- |
| App (frontend+logic) | Streamlit | Free |
| Database | Supabase | Free tier |
| Vision/LLM | Gemini 3.1 Flash-Lite | Free tier |
| Nutrition data | USDA FoodData Central | Free |
| Hosting | Streamlit Community Cloud | Free |

Total projected cost: **$0/month** at your usage scale, which beats every subscription comparison from your Success Criteria.