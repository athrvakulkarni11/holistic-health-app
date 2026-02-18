# Holistic Health AI Platform — How It Works

## What Is This?

An AI-powered web app that analyzes blood test results and gives personalized health advice. Users can:

1. **Enter biomarker values** in a form and get an instant analysis
2. **Upload a lab report** (PDF, CSV, DOCX, etc.) — the AI reads it and analyzes it
3. **Chat with an AI health assistant** for any health question

---

## How the Code Is Organized

```
healthcare/
├── main.py                  ← Starts the server
├── app/
│   ├── config.py            ← API keys & settings
│   ├── models.py            ← Input/output data shapes
│   ├── api.py               ← All API endpoints
│   ├── analytics_engine.py  ← Core analysis logic (the brain)
│   ├── chat_engine.py       ← AI chatbot
│   ├── file_processor.py    ← Reads uploaded files
│   ├── knowledge_base.py    ← Medical reference data
│   └── web_search.py        ← Searches the web for health info
├── knowledge_base/
│   └── biomarker_references.json  ← Curated biomarker data
├── static/                  ← Frontend (HTML/CSS/JS)
└── uploads/                 ← Uploaded files go here
```

---

## What Each File Does

| File | One-Line Summary |
|---|---|
| `main.py` | Starts the FastAPI server, serves the frontend and API |
| `config.py` | Loads API keys (`GROQ_API_KEY`, `SERPAPI_KEY`) from `.env` |
| `models.py` | Defines what data the API expects and returns (using Pydantic) |
| `api.py` | Defines all the URL endpoints — routes requests to the right engine |
| `analytics_engine.py` | Takes biomarker values → classifies them → calculates health score → calls the AI for a full report |
| `chat_engine.py` | Manages chat sessions, enriches messages with context, calls the AI |
| `file_processor.py` | Extracts text from uploaded files (PDF, DOCX, CSV, etc.) and uses the AI to find biomarker values in the text |
| `knowledge_base.py` | Searches a local JSON file of curated medical info about each biomarker |
| `web_search.py` | Uses SerpAPI (Google Search) to find current medical research online |

---

## The Main Flow: Biomarker Analysis

When a user submits biomarker values (either manually or from an uploaded file):

```
1. CLASSIFY  →  Compare each value against normal ranges (gender-specific)
                 Mark each as "low", "normal", or "high"

2. SCORE     →  Calculate a health score from 0–100 (higher = healthier)
                 Break it down by category (blood, metabolic, lipids, etc.)

3. RESEARCH  →  Look up abnormal markers in the knowledge base (local JSON)
                 Search the web for the most abnormal markers (SerpAPI)

4. ANALYZE   →  Send everything to the Groq AI (Llama 3.3 70B model)
                 AI returns: summary, findings, risks, diet tips,
                 supplements with dosages, and follow-up test suggestions

5. RESPOND   →  Send the full result back to the frontend
```

---

## Health Score

- **100** = perfect, all markers normal
- **85+** = excellent
- **70–84** = good
- **50–69** = moderate
- **30–49** = needs attention
- **Below 30** = high risk

The score accounts for how many markers are abnormal, how far off they are, and which category they belong to (metabolic and cardiovascular issues weigh more heavily).

---

## Supported Biomarkers (14 total)

**Blood Health:** Hemoglobin, RBC Count
**Nutritional:** Ferritin, Vitamin B12, Vitamin D
**Metabolic:** Fasting Glucose, HbA1c
**Lipids:** Total Cholesterol, LDL, HDL, Triglycerides
**Inflammation:** hs-CRP
**Hormonal:** TSH
**Liver:** SGPT/ALT

---

## External Services Used

- **Groq API** — AI language model for analysis and chat (Llama 3.3 70B)
- **SerpAPI** — Google Search for real-time medical information

Both require API keys set in the `.env` file.

---

## How to Run

```bash
pip install -r requirements.txt
# Add GROQ_API_KEY and SERPAPI_KEY to .env
python main.py
# Open http://localhost:8050
```
