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

* Calorie/macro logging via photo estimate (mixed dishes), manual entry, and nutrition label OCR  
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

Three logging workflows, all feeding into a shared food/meal database. Vision is for mixed dishes you did not cook. Food you make yourself is Manual (you already know the recipe).

**Vision Workflow**

* User photographs a mixed dish (e.g. a bowl of pho), enters the **food-only** weight, and an optional note about what’s in it  
* Gemini 3.6 Flash estimates calories/macros for **that weighed portion**, with a component breakdown (grams must add up to the weight) and short reasoning  
* User edits or rejects the estimate before anything is saved  
* Logged as **estimated** (visually/data distinct from manual/OCR). Saving to the reusable library is opt-in — a restaurant bowl is a one-off by default  

**Manual Workflow**

* User logs a food or meal once with name \+ nutrition data (calories, protein, carbs, fats)  
* Saved entries are searchable/reusable for future logging (e.g. log a homemade smoothie once, reuse on later days)

**Nutrition Label OCR**

* User photographs a nutrition label on packaged food  
* OCR extracts nutrition data and saves it using the same reusable structure as the Manual Workflow  
* Saved OCR-derived foods are searchable later, same as manually logged foods

  ### **2\. Weight Tracking**

* 100% manual entry (user weighs themselves, then logs the value — picture optional/personal habit, not an app requirement)  
* Historical data displayed as a graph over time  
* No goal-setting tied to weight (logging \+ graph only)

## **Data Model (entities, tech-agnostic)**

* **Food** — an individual item with nutrition data (calories, protein, carbs, fats). Source-tagged as `manual`, `vision`, `ocr`, or `estimated` (photo estimates use `estimated`)  
* **Meal** — two types:  
  * *Composed Meal*: built from existing Food entities (e.g. "chicken \+ rice \+ broccoli")  
  * *Simple Meal*: a single logged item with its own nutrition totals, no ingredient breakdown (e.g. "restaurant burger — 800 cal / 40g protein" with no sub-items)  
* **LoggedEntry** — a record of a Food or Meal consumed on a specific date/time, referencing the source Food/Meal  
* **WeightLog** — a date-stamped weight entry  
* **Goals** — manually input calorie/macro targets (no calculation logic needed for v1)

## **Constraints**

* Minimize ongoing API costs (estimate + OCR Gemini calls) to stay under the reference subscription cost range noted in Success Criteria

## **Assumptions & Risks**

1. Photo estimates are guesses anchored to a scale. 20–40% error is expected; they stay flagged `estimated`  
2. Weight must be food-only (tare the bowl). Skip the weight and the estimate is not usable  
3. User can edit or reject the estimate before logging  
4. Connectivity — always-connected assumption is fine for v1