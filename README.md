# ✈️ Travel Itinerary Planner — AI-Powered

A full-stack travel planning application that generates **specific, realistic day-by-day itineraries** using RAG (Retrieval-Augmented Generation) with a Groq-hosted LLM. The backend validates source/destination against a vector database, estimates flight costs, allocates budgets across all trip components, and falls back to LLM world knowledge when RAG data is sparse.

---

## 🎯 Features

| Feature | Details |
|---|---|
| **Itinerary Generation** | Day-by-day plan with real place names, hotels, restaurants, and activities |
| **RAG + World Knowledge** | Tries vector DB first; falls back to LLM knowledge automatically per component |
| **Smart Budget Allocation** | Splits budget: Stay 40%, Food 25%, Activities 20%, Transport 15% |
| **Flight Cost Lookup** | Real Sky-Scrapper API → realistic simulated fallback (domestic / neighbour / international) |
| **Budget Awareness** | Flight cost subtracted first; remaining "ground budget" drives all allocations |
| **Input Validation** | Source and destination checked against DB; budget validated with minimum thresholds |
| **JSON Repair** | 3-tier repair strategy for truncated LLM responses |
| **Chat Refinement** | Follow-up questions via `/chat` endpoint with session memory |

---

## 🏗️ Project Structure

```
genAI/
├── backend/
│   ├── test2.py              # Main FastAPI app — all backend logic
│   ├── flight_data.py        # Flight lookup (RapidAPI) + realistic simulator
│   ├── static_rag/           # Travel data CSV files
│   │   ├── Expanded_Destinations.csv
│   │   ├── India_Tourism_2025_Processed.csv
│   │   ├── Tourist_Destinations.csv
│   │   └── Worldwide_Travel_Cities_Dataset__Ratings_and_Climate_.csv
│   ├── vectordb/             # ChromaDB persistent vector store (auto-created)
│   ├── requirements.txt
│   └── .env                  # API keys
│
└── frontend/
    └── src/
        └── App.jsx           # React UI — form, itinerary display, chat
```

---

## 💻 Tech Stack

### Backend
| Component | Technology |
|---|---|
| Web framework | **FastAPI** |
| LLM | **Groq** — `llama-3.3-70b-versatile` (temperature 0, max_tokens 2048) |
| Embeddings | **HuggingFace** — `sentence-transformers/all-MiniLM-L6-v2` |
| Vector DB | **ChromaDB** (persistent, local) |
| RAG orchestration | **LangChain** (`langchain_chroma`, `langchain_groq`, `langchain_huggingface`) |
| Flight data | **Sky-Scrapper RapidAPI** + built-in simulated fallback |
| Data processing | **Pandas** |

### Frontend
| Component | Technology |
|---|---|
| Framework | **React 19 + Vite** |
| HTTP client | **Axios** |
| Styling | Vanilla CSS (inline styles in `App.jsx`) |

---

## 🚀 Getting Started

### Prerequisites
- Python 3.10+
- Node.js 18+ and npm
- [Groq API key](https://console.groq.com/keys)

### Backend Setup

```bash
# 1. Navigate to backend
cd backend

# 2. Create and activate virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Create .env file
echo GROQ_API_KEY=your_key_here > .env
# Optional: add RAPID_API_KEY=your_rapidapi_key for real flight data

# 5. Start the server
uvicorn test2:app --reload
```

Backend runs at `http://localhost:8000`.

The vector DB (`vectordb/`) is built automatically on the first `POST /init-db` call. You can also trigger it via the UI or curl:

```bash
curl -X POST http://localhost:8000/init-db
```

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at `http://localhost:5173`.

---

## 📡 API Reference

### `POST /init-db`
Builds the ChromaDB vector store from the CSVs in `static_rag/`. Call once before generating itineraries. Safe to call again to rebuild.

**Response:**
```json
{ "status": "success", "documents": 1248 }
```

---

### `POST /generate`
Generates a complete travel itinerary.

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

**Response:**
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
        {
          "airline": "IndiGo",
          "price_per_person_inr": 4200,
          "total_price_inr": 8400,
          "duration": "1h 20m"
        }
      ]
    },
    "trip_plan": [
      {
        "day": 1,
        "theme": "Old Goa Heritage",
        "activities": [
          { "time": "Morning",   "activity": "Visit Basilica of Bom Jesus", "cost_inr": 0 },
          { "time": "Afternoon", "activity": "Se Cathedral & Goa Museum",   "cost_inr": 50 },
          { "time": "Evening",   "activity": "Sunset at Fort Aguada",       "cost_inr": 0 }
        ],
        "food": [
          { "meal": "Breakfast", "description": "Poie bread & chai at Café Bhonsle", "cost_inr": 120 },
          { "meal": "Lunch",     "description": "Goan Fish Curry at Ritz Classic",   "cost_inr": 350 },
          { "meal": "Dinner",    "description": "Prawn balchão at Viva Panjim",      "cost_inr": 600 }
        ],
        "stay": {
          "name": "Old Quarter Inn",
          "type": "Budget",
          "cost_per_night_inr": 1400
        },
        "transport": {
          "mode": "Hired scooter rental",
          "cost_inr": 400
        },
        "day_total_inr": 2920
      }
    ],
    "tips": [
      "Visit beaches early morning to avoid crowds",
      "Carry cash — many shacks don't accept cards",
      "Oct–Feb is the best time; avoid monsoon (Jun–Sep)"
    ]
  },
  "error": false
}
```

---

### `POST /chat`
Ask follow-up questions about an existing itinerary.

**Request:**
```json
{
  "message": "Can you suggest budget accommodation in Goa?",
  "session_id": "abc123"
}
```

**Response:**
```json
{
  "response": "For budget stays in Goa under ₹1,500/night, consider...",
  "error": false
}
```

---

## 🔄 Request Processing Pipeline

```
User Input (source, destination, budget, days, food, travelers)
         │
         ▼
① Source validation  ── not in DB → error "Source not found in our database"
         │
         ▼
② Flight cost lookup
    ├─ RapidAPI (if RAPID_API_KEY set)
    └─ Simulated fallback:
         Domestic India     → ₹3,500–₹9,500  | IndiGo, SpiceJet, Vistara...
         Neighbour country  → ₹12,000–₹35,000 | SriLankan, Maldivian...
         International      → ₹45,000–₹1,20,000 | Emirates, Qatar, Air France...
         │
         ▼
③ Budget validation (on ground budget = total − flight cost)
    ├─ Domestic minimum: ₹500/person/day
    └─ International minimum: ₹3,000/person/day
         │
         ▼
④ Budget allocation (from ground budget only)
    ├─ Stay:        40%
    ├─ Food:        25%
    ├─ Activities:  20%
    └─ Transport:   15%
         │
         ▼
⑤ Destination validation ── not in DB → error "Destination not found"
         │
         ▼
⑥ RAG retrieval (ChromaDB, k=6)
    ├─ Full destination document passed as context
    └─ Cost hints extracted per component (accommodation, food, transport, activities)
         │
         ▼
⑦ LLM generation (llama-3.3-70b-versatile via Groq)
    ├─ Uses RAG data for cost ranges
    ├─ Uses world knowledge for specific names (hotels, restaurants, landmarks)
    └─ JSON schema pre-seeded with correct budget values
         │
         ▼
⑧ JSON extraction + repair (3-tier)
    ├─ Tier 1: Parse raw response
    ├─ Tier 2: Repair truncated JSON (close open braces/brackets/strings)
    └─ Tier 3: Truncate to last complete `}`
         │
         ▼
⑨ Travel info injected into result (always valid — never passed through LLM)
         │
         ▼
Response returned to frontend
```

---

## 📊 Data Sources (CSVs in `static_rag/`)

| File | Contents |
|---|---|
| `Expanded_Destinations.csv` | Indian destinations — name, state, type, popularity, best time |
| `India_Tourism_2025_Processed.csv` | State-level tourism revenue, visitor counts, visit purposes |
| `Tourist_Destinations.csv` | International destinations — country, cost/day (USD), season, rating |
| `Worldwide_Travel_Cities_Dataset_*.csv` | Global city scores — culture, adventure, nature, beaches, nightlife, cuisine |

Each CSV row is enriched into a single **LangChain `Document`** that combines all available fields, then embedded and stored in ChromaDB.

---

## 🐛 Troubleshooting

| Problem | Fix |
|---|---|
| `Vector DB not initialised` | `POST http://localhost:8000/init-db` |
| `Source/Destination not found` | Only cities present in the CSV data are validated; try common city names |
| `Budget too low` | Domestic: ₹500/person/day minimum after flights; International: ₹3,000/person/day |
| `LLM returned empty response` | Retry; or check `GROQ_API_KEY` in `.env` |
| `Failed to parse AI response` | LLM output was too large; reduce `days` or try again |
| Real flights not showing | Set `RAPID_API_KEY` in `.env`; simulated data is used as fallback |

---

## 🔑 Environment Variables

```env
# backend/.env

GROQ_API_KEY=gsk_...          # Required — Groq LLM inference
RAPID_API_KEY=...             # Optional — real flight data via Sky-Scrapper
```

---

## 📝 Notes

- The vector DB persists in `backend/vectordb/`. Delete this folder and re-call `/init-db` to rebuild from updated CSVs.
- LLM timeout is set to **60 seconds** (`LLM_TIMEOUT` in `test2.py`). Increase for slow connections.
- The LLM is instructed to use **real, specific names** for hotels, restaurants, and landmarks. Quality improves when the destination is well-represented in the CSV data.

---

## 📄 License

Open source — MIT License.

---

**Last Updated**: April 28, 2026
