# **Project Spec: Personal Calorie & Macro Tracker**

# **Problem & Purpose**

Calorie tracking takes significant time due to manual lookup and re-entry of packaged foods. Existing apps hide vision-based logging and OCR nutrition label scanning behind paywalls. This project builds a personal version to avoid recurring subscription costs.

## **Success Criteria**

* Able to track daily calorie intake and compare against a manually-set target (for weight loss)  
* Able to track macronutrients (protein, carbs, fats) against manually-set targets  
* Total implementation cost (API usage, hosting, etc.) stays below the cost of comparable subscriptions (reference range: \~$10–$20/month, \~$50–$80/year, based on apps like Cal AI, MyFitnessPal, MacroFactor, Cronometer)

## **Users**

* Single user (you) — tracks personal daily intake, macros, and weight progress over time

## **Scope**

**In scope (v1):**

* Calorie/macro logging via vision (photo of food), manual entry, and nutrition label OCR  
* Reusable food and meal library  
* Manual weight logging with graph over time  
* Manual goal input (calorie/macro targets)

**Out of scope (v1):**

* Social features  
* Meal planning  
* Multi-user support  
* Barcode scanning (potential future enhancement — noted as generally more reliable than OCR for packaged foods with existing database entries, since it avoids OCR misreads, but OCR covers a wider range of products including homemade/foreign items)

## **Core Features**

### **1\. Calorie/Macro Tracking**

Three logging workflows, all feeding into a shared, reusable food/meal database:

**Vision Workflow**

* User takes a picture of food  
* LLM API detects what food items are present  
* App checks if each detected food exists in the local DB  
  * If not found, retrieves nutrition data from a nutrition API and stores it  
* User inputs the weight of each individual food item in the meal  
* App calculates calories/macros based on weight \+ nutrition data  
* **Fallback:** if the nutrition API fails for a given ingredient, LLM estimates its nutrition data. Estimated entries are **flagged** (e.g. "estimated" vs "verified") and remain visually/data distinct from API-sourced entries

**Manual Workflow**

* User logs a food or meal once with name \+ nutrition data (calories, protein, carbs, fats)  
* Saved entries are searchable/reusable for future logging (e.g. log "morning smoothie" once, reuse on later days)

**Nutrition Label OCR**

* User photographs a nutrition label on packaged food  
* OCR extracts nutrition data and saves it using the same reusable structure as the Manual Workflow  
* Saved OCR-derived foods are searchable later, same as manually logged foods

  ### **2\. Weight Tracking**

* 100% manual entry (user weighs themselves, then logs the value — picture optional/personal habit, not an app requirement)  
* Historical data displayed as a graph over time  
* No goal-setting tied to weight (logging \+ graph only)

## **Data Model (entities, tech-agnostic)**

* **Food** — an individual item with nutrition data (calories, protein, carbs, fats). Source-tagged as `manual`, `vision`, `ocr`, or `estimated` (flag for fallback cases)  
* **Meal** — two types:  
  * *Composed Meal*: built from existing Food entities (e.g. "chicken \+ rice \+ broccoli")  
  * *Simple Meal*: a single logged item with its own nutrition totals, no ingredient breakdown (e.g. "restaurant burger — 800 cal / 40g protein" with no sub-items)  
* **LoggedEntry** — a record of a Food or Meal consumed on a specific date/time, referencing the source Food/Meal  
* **WeightLog** — a date-stamped weight entry  
* **Goals** — manually input calorie/macro targets (no calculation logic needed for v1)

## **Constraints**

* Minimize ongoing API costs (vision LLM calls, nutrition API calls, OCR) to stay under the reference subscription cost range noted in Success Criteria

## **Assumptions & Risks**

1. Nutrition API — recommend USDA FoodData Central (free) as primary, decided at spec level  
2. Vision correction — user can edit or reject detected items before proceeding  
3. Connectivity — always-connected assumption is fine for v1