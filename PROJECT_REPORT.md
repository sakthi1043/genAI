# AI-Powered Travel Itinerary Planner
### Mini Project Report — Generative AI

---

## 1. Project Overview

**Project Title:** AI-Powered Travel Itinerary Planner  
**Technology Domain:** Generative AI, Retrieval-Augmented Generation (RAG), Full-Stack Web Development  
**Submitted By:** [Your Name]  
**Institution:** [Your Institution]  
**Date:** April 2026

---

## 2. Abstract

This project presents an intelligent travel planning web application that generates detailed, personalized day-by-day travel itineraries using a combination of Retrieval-Augmented Generation (RAG) and a Large Language Model (LLM). The system retrieves structured destination data from a local vector database (ChromaDB), validates inputs, computes realistic flight costs, allocates budgets intelligently across trip components, and generates specific, actionable itineraries. When RAG data is insufficient, the system seamlessly falls back to the LLM's world knowledge. A React-based frontend provides an intuitive interface for planning and chat-based refinement.

---

## 3. Problem Statement

Existing travel planning tools either produce generic, template-based itineraries or require expensive real-time API subscriptions. Travelers face challenges in:

- Getting destination-specific, realistic recommendations within a defined budget
- Understanding how to split a travel budget across flights, accommodation, food, and activities
- Quickly generating personalized plans that account for food preferences, trip duration, and number of travelers

This project addresses these gaps by combining structured travel data with AI generation, ensuring both accuracy and personalization.

---

## 4. Objectives

1. Build a full-stack AI application with a FastAPI backend and React frontend
2. Implement RAG using ChromaDB to ground LLM responses in real destination data
3. Validate user inputs (source city, destination, budget) before generation
4. Compute realistic flight cost estimates with domestic/international differentiation
5. Allocate the post-flight "ground budget" intelligently across accommodation, food, activities, and transport
6. Produce specific, named recommendations (real hotels, restaurants, landmarks) — not generic placeholders
7. Handle LLM failures gracefully with JSON repair and fallback mechanisms

---

## 5. System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     React Frontend                       │
│   Travel Form → Itinerary Display → Chat Interface       │
└──────────────────────┬──────────────────────────────────┘
                       │ HTTP (POST /generate, /chat)
┌──────────────────────▼──────────────────────────────────┐
│                  FastAPI Backend (test2.py)               │
│                                                          │
│  ① Input Validation (Source & Destination in DB?)        │
│  ② Flight Cost Lookup (RapidAPI → Simulated Fallback)    │
│  ③ Budget Validation (post-flight ground budget check)   │
│  ④ Budget Allocation (Stay/Food/Activities/Transport)    │
│  ⑤ RAG Retrieval (ChromaDB vector search)               │
│  ⑥ LLM Generation (Groq — llama-3.3-70b-versatile)     │
│  ⑦ JSON Extraction & Repair (3-tier strategy)           │
│  ⑧ Response Assembly (travel + trip_plan injected)      │
└──────────────────────┬──────────────────────────────────┘
          ┌────────────┴────────────┐
          ▼                        ▼
   ChromaDB (local)          Groq Cloud API
   (destination docs)        (LLM inference)
```

---

## 6. Technology Stack

### 6.1 Backend

| Component | Technology | Purpose |
|---|---|---|
| Web Framework | FastAPI | REST API, async request handling |
| LLM | Groq — `llama-3.3-70b-versatile` | Itinerary generation |
| Embeddings | HuggingFace `all-MiniLM-L6-v2` | Semantic text encoding |
| Vector DB | ChromaDB | RAG — destination document retrieval |
| RAG Framework | LangChain | Document retrieval and LLM integration |
| Flight Data | Sky-Scrapper (RapidAPI) + custom simulator | Flight cost estimation |
| Data Processing | Pandas | CSV data ingestion and enrichment |
| Validation | Pydantic | Request model validation |
| Runtime | Python 3.10+, Uvicorn | ASGI server |

### 6.2 Frontend

| Component | Technology |
|---|---|
| UI Framework | React 19 + Vite |
| HTTP Client | Axios |
| Styling | Vanilla CSS (inline) |

### 6.3 Data Sources (CSV files in `static_rag/`)

| File | Contents |
|---|---|
| `Expanded_Destinations.csv` | Indian destinations — name, state, type, popularity, best time |
| `India_Tourism_2025_Processed.csv` | State-level tourism revenue, visitor counts |
| `Tourist_Destinations.csv` | International destinations — daily cost (USD), season, rating |
| `Worldwide_Travel_Cities_Dataset_*.csv` | Global city scores — culture, adventure, nature, cuisine, nightlife |

---

## 7. Key Modules

### 7.1 `test2.py` — Backend Core

**`build_destination_documents()`**  
Reads all four CSVs and produces one rich `LangChain Document` per destination. Indian destinations are cross-joined with state-level tourism stats for richer context. International destinations include USD/day costs converted to INR.

**`_sync_init_db()`**  
Embeds all documents using `all-MiniLM-L6-v2` and stores them in ChromaDB at `backend/vectordb/`.

**`is_out_of_domain()`**  
Checks whether retrieved documents actually contain keywords matching the queried destination, preventing irrelevant results from passing validation.

**`extract_json()` + `_repair_truncated_json()`**  
Three-tier JSON extraction:
1. Parse raw LLM output directly
2. Repair truncated output by closing open braces/brackets character-by-character
3. Truncate to last complete `}` as a last resort

**`budget_validate()`**  
Computes per-person-per-day cost from the remaining ground budget and checks it against minimum thresholds:
- Domestic India: ₹500/person/day
- International: ₹3,000/person/day

**`budget_allocate()`**  
Splits the ground budget using industry-standard travel ratios:

| Component | Allocation |
|---|---|
| Accommodation | 40% |
| Food | 25% |
| Activities | 20% |
| Transport | 15% |

**`_sync_generate()`**  
Main generation pipeline — coordinates all steps from flight lookup through LLM invocation and JSON injection.

---

### 7.2 `flight_data.py` — Flight Cost Estimation

Detects route type and applies appropriate airlines, price ranges, and durations:

| Route Type | Detection | Airlines | Price Range | Duration |
|---|---|---|---|---|
| **Domestic** | Both cities in Indian cities list | IndiGo, Air India, SpiceJet, Vistara, Akasa Air | ₹3,500–₹9,500 | 1h–3h 20m |
| **Neighbour** | Dest is Sri Lanka / Nepal / Bhutan / Maldives | SriLankan Airlines, Himalaya Airlines, Maldivian | ₹12,000–₹35,000 | 1h 30m–5h |
| **International** | All other destinations | Emirates, Qatar Airways, Air France, Lufthansa, British Airways, Turkish Airlines | ₹45,000–₹1,20,000 | 7h–15h |

The real Sky-Scrapper RapidAPI is attempted first when `RAPID_API_KEY` is configured; the simulator is an automatic fallback.

---

## 8. Request Processing Pipeline

```
User Input
    │
    ▼
① Source city → checked in ChromaDB
    │ Not found → "Source not found in our database"
    ▼
② Flight cost computed (cheapest option selected)
    │ Flight ≥ total budget → "Budget insufficient for flight"
    ▼
③ Ground Budget = Total Budget − Flight Cost
    │
    ▼
④ Budget validation on ground budget
    │ Too low → detailed error with minimum required
    ▼
⑤ Budget allocation (Stay/Food/Activities/Transport)
    │
    ▼
⑥ Destination → checked in ChromaDB
    │ Not found → "Destination not found in our database"
    ▼
⑦ Full destination documents retrieved (k=6)
    Cost hints extracted per component
    │
    ▼
⑧ LLM prompt built with:
    - Traveler details
    - Budget allocation (pre-computed values)
    - RAG destination context
    - Specificity rules (real hotel names, real landmarks, real dishes)
    │
    ▼
⑨ Groq LLM generates JSON itinerary
    │
    ▼
⑩ JSON extraction + repair (3-tier)
    │
    ▼
⑪ Travel info injected (never passed through LLM — always valid JSON)
    │
    ▼
Response → Frontend
```

---

## 9. API Endpoints

### `POST /init-db`
Builds ChromaDB from CSVs. Must be called once before generating itineraries.

```json
Response: { "status": "success", "documents": 1248 }
```

### `POST /generate`

**Request:**
```json
{
  "source": "Mumbai",
  "destination": "Goa",
  "budget": 25000,
  "days": 3,
  "food": "non-vegetarian",
  "travelers": 2
}
```

**Response (abbreviated):**
```json
{
  "plan": {
    "destination": "Goa",
    "duration_days": 3,
    "total_budget_inr": 25000,
    "travelers": 2,
    "travel": {
      "from": "Mumbai",
      "to": "Goa",
      "options": [
        { "airline": "IndiGo", "price_per_person_inr": 4200,
          "total_price_inr": 8400, "duration": "1h 20m" }
      ]
    },
    "trip_plan": [
      {
        "day": 1,
        "theme": "Old Goa Heritage",
        "activities": [
          { "time": "Morning", "activity": "Visit Basilica of Bom Jesus", "cost_inr": 0 }
        ],
        "food": [
          { "meal": "Lunch", "description": "Goan Fish Curry at Ritz Classic", "cost_inr": 350 }
        ],
        "stay": { "name": "Old Quarter Inn", "type": "Budget", "cost_per_night_inr": 1400 },
        "transport": { "mode": "Hired scooter rental", "cost_inr": 400 },
        "day_total_inr": 2920
      }
    ],
    "tips": ["Visit beaches early morning", "Carry cash for shacks", "Oct–Feb is best season"]
  },
  "error": false
}
```

### `POST /chat`
Follow-up questions with session memory.

```json
Request:  { "message": "Suggest cheaper hotels", "session_id": "abc123" }
Response: { "response": "For budget stays under ₹1,500/night...", "error": false }
```

---

## 10. Input Validations

| Validation | Condition | Error Message |
|---|---|---|
| Source in database | Source keywords not in ChromaDB | "Source 'X' not found in our database" |
| Destination in database | Destination keywords not in ChromaDB | "Destination 'X' not found in our database" |
| Flight affordability | Flight cost ≥ total budget | "Budget ₹X insufficient to cover flight (₹Y)" |
| Ground budget (domestic) | < ₹500/person/day after flights | "Budget too low — minimum ₹500/person/day" |
| Ground budget (international) | < ₹3,000/person/day after flights | "Budget too low — minimum ₹3,000/person/day" |
| Empty LLM response | Model returns nothing | "AI returned an empty response. Try again." |
| LLM refusal | Response contains refusal phrases, no `{` | "AI declined this request: ..." |

---

## 11. Frontend Components (`App.jsx`)

| Component | Description |
|---|---|
| `TravelForm` | Input form — source, destination, budget, days, food, travelers |
| `ItineraryDisplay` | Renders the full itinerary with stat cards |
| `TravelCard` | Shows flight options with Best Price badge |
| `DayCard` | Expandable day card — activities, meals, stay, transport |
| `StatCard` | Summary stat tile (destination, duration, travelers, budget) |
| `FlightCard` | Legacy single-flight display |
| Chat input | Follow-up question bar with session_id |

---

## 12. Setup Instructions

### Prerequisites
- Python 3.10+, Node.js 18+
- Groq API key → [console.groq.com/keys](https://console.groq.com/keys)

### Backend
```bash
cd backend
python -m venv venv
venv\Scripts\activate          # Windows
pip install -r requirements.txt

# Create .env
echo GROQ_API_KEY=your_key > .env

# Start server
uvicorn test2:app --reload
# → http://localhost:8000

# Init vector DB (first time only)
curl -X POST http://localhost:8000/init-db
```

### Frontend
```bash
cd frontend
npm install
npm run dev
# → http://localhost:5173
```

---

## 13. Environment Variables

| Variable | Required | Purpose |
|---|---|---|
| `GROQ_API_KEY` | ✅ Yes | Groq LLM inference |
| `RAPID_API_KEY` | ⬜ Optional | Real flight data via Sky-Scrapper API |

---

## 14. Challenges & Solutions

| Challenge | Solution Implemented |
|---|---|
| LLM truncating JSON output | 3-tier JSON repair — structural closure, brace tracking, last-`}` fallback |
| Generic activity/hotel names | Prompt specificity rules enforce real landmark and hotel names |
| Python dict syntax in JSON output | Travel options injected server-side after parsing — never passed through LLM |
| International vs domestic flight pricing | Route type classifier with three price tiers and appropriate airline lists |
| Budget making no sense after flights | Flight cost subtracted first; allocations applied only to ground budget |
| Irrelevant RAG results | `is_out_of_domain()` keyword check rejects off-topic documents |

---

## 15. Future Enhancements

- Real-time hotel booking integration (MakeMyTrip / Booking.com API)
- Accurate weather forecast per destination and travel dates
- User accounts and saved/shared itineraries
- Multi-city trip support
- Carbon footprint estimation per transport mode
- React Native mobile application

---

## 16. Conclusion

This project demonstrates the practical application of Generative AI and RAG techniques in the travel domain. By combining a structured vector knowledge base with a powerful open-source LLM, the system generates accurate, budget-aware, and specific travel itineraries. The layered validation pipeline ensures only feasible trips are planned, while the 3-tier JSON repair mechanism makes the system robust against LLM output variability. The clear separation between RAG data (for costs and context) and LLM world knowledge (for specific names) produces itineraries that are both grounded and detailed.

---

*Document prepared for Mini Project evaluation — April 2026*
