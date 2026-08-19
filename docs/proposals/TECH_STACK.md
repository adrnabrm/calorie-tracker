## **Finalized Tech Stack**

**Frontend \+ Backend (combined):** Streamlit

* Single Python app, no separate API layer needed for single-user scale  
* Built-in `st.camera_input` for photo capture (food photos \+ OCR labels)  
* All logic (calling Gemini, calling Supabase, calculations) lives directly in the Streamlit app

**Database:** Supabase (Postgres)

* Tables: `foods`, `meals`, `meal_ingredients` (join table for composed meals), `logged_entries`, `weight_logs`, `goals`  
* Accessed via `supabase-py` client from within the Streamlit app

**LLM (two models, both google-genai Interactions API):**

* **OCR:** Gemini 3.1 Flash-Lite — read a printed nutrition label into structured fields  
* **Photo estimate:** Gemini 3.6 Flash, thinking `medium` — mixed-dish calories/macros from a photo + food weight + optional notes. This call only; do not use Flash-Lite here  

Personal-scale usage is a few meals a day. 3.6 Flash is pennies/month, not a subscription.

**Hosting:** Streamlit Community Cloud

* Free, deploys directly from a GitHub repo, purpose-built for exactly this kind of app

**Language:** Python end-to-end — no JS required anywhere in this stack.

---

### **Stack summary**

| Layer | Choice | Cost |
| ----- | ----- | ----- |
| App (frontend+logic) | Streamlit | Free |
| Database | Supabase | Free tier |
| OCR | Gemini 3.1 Flash-Lite | Free tier |
| Photo estimate | Gemini 3.6 Flash | Pennies/month at personal scale |
| Hosting | Streamlit Community Cloud | Free |

Total projected cost stays under the Success Criteria subscription range (~$10–$20/month). No USDA in the vision path.