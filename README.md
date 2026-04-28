# Travel Planner AI Assistant

An intelligent travel planning application that generates personalized itineraries with specific recommendations for accommodations, attractions, restaurants, and flights. This project combines AI-powered planning with a knowledge base of travel data to provide comprehensive travel suggestions.

## 🎯 Features

- **AI-Powered Itinerary Generation**: Creates detailed day-by-day travel plans with specific times and activities
- **Smart Budget Management**: Allocates daily budgets across activities, food, accommodation, and transportation
- **Specific Recommendations**: Provides real place names, restaurant recommendations, and hotel options with ratings and prices
- **Multi-Source Information**: Integrates vector databases, Wikipedia, and specialized travel data
- **Flight Search**: Real-time flight information and pricing
- **Accommodation Search**: Find hotels with amenities, ratings, and costs
- **Attraction Discovery**: Get specific attractions based on interests
- **Restaurant Recommendations**: Cuisine and cost-aware dining suggestions
- **Travel Tips**: Weather, climate, and practical travel advice
- **Chat-Based Refinement**: Ask follow-up questions to refine your itinerary
- **Session Management**: Maintains conversation history for personalized recommendations

## 🏗️ Project Structure

```
.
├── backend/                          # FastAPI backend service
│   ├── main.py                      # FastAPI application entry point
│   ├── agent.py                     # AI agent with LangGraph integration
│   ├── accommodation_tools.py       # Search tools for hotels, attractions, restaurants, tips
│   ├── flight_data.py               # Flight search functionality
│   ├── hybrid_rag.py                # Combined vector DB + Wikipedia search
│   ├── vector_tools.py              # Chroma vector database queries
│   ├── memory.py                    # Session management and conversation history
│   ├── ingest.py                    # Data ingestion pipeline
│   ├── requirements.txt             # Python dependencies
│   ├── .env                         # Environment variables (API keys)
│   └── data/
│       └── static_rag/              # Travel data CSV files
│           ├── Expanded_Destinations.csv
│           ├── India_Tourism_2025_Processed.csv
│           ├── Tourist_Destinations.csv
│           ├── trending_topics_2026_synthetic.csv
│           └── Worldwide Travel Cities Dataset (Ratings and Climate).csv
│
├── frontend/                         # React + Vite frontend application
│   ├── src/
│   │   ├── App.jsx                  # Main application component with chat interface
│   │   ├── api.js                   # API client for backend communication
│   │   ├── main.jsx                 # React entry point
│   │   ├── components/
│   │   │   └── Form.jsx             # Travel request form component
│   │   └── styles files
│   ├── package.json                 # Node.js dependencies
│   ├── vite.config.js              # Vite configuration
│   └── index.html
│
└── vector_db/                        # Chroma vector database storage
    └── travel_data/
        └── chroma.sqlite3           # Persistent vector embeddings

```

## 💻 Tech Stack

### Backend
- **FastAPI**: Modern Python web framework for building APIs
- **LangChain**: LLM orchestration and tool integration
- **LangGraph**: Agentic workflow framework for multi-step reasoning
- **Groq API**: High-speed LLM inference (GPT-OSS-120B model)
- **Chroma**: Vector database for semantic search and RAG
- **Sentence Transformers**: Embedding generation for text similarity
- **Pandas & NumPy**: Data processing and analysis
- **Wikipedia API**: External knowledge source
- **DuckDuckGo Search**: Web search integration

### Frontend
- **React 19**: Modern UI framework
- **Vite**: Fast build tool and development server
- **Axios**: HTTP client for API requests
- **ESLint**: Code quality and linting

### Infrastructure
- **CORS Middleware**: Cross-origin resource sharing setup for frontend-backend communication
- **Pydantic**: Data validation using Python type hints

## 🚀 Getting Started

### Prerequisites
- Python 3.8+
- Node.js 16+ and npm
- Groq API key ([Get one here](https://console.groq.com/keys))
- Git

### Backend Setup

1. **Navigate to backend directory**
   ```bash
   cd backend
   ```

2. **Create Python virtual environment**
   ```bash
   python -m venv venv
   source venv/Scripts/activate  # Windows
   # or
   source venv/bin/activate      # macOS/Linux
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   Create a `.env` file in the `backend/` directory:
   ```env
   GROQ_API_KEY=your_groq_api_key_here
   ```

5. **Initialize vector database (first run only)**
   ```bash
   python backend/ingest.py
   ```
   This processes CSV data and creates vector embeddings in the Chroma database.

6. **Start backend server**
   ```bash
   uvicorn backend.main:app --reload --port 8000
   ```
   Backend will be available at `http://localhost:8000`

### Frontend Setup

1. **Navigate to frontend directory**
   ```bash
   cd frontend
   ```

2. **Install dependencies**
   ```bash
   npm install
   ```

3. **Start development server**
   ```bash
   npm run dev
   ```
   Frontend will be available at `http://localhost:5173`

## 📡 API Reference

### POST `/generate`
Generate a travel itinerary based on user preferences.

**Request Body:**
```json
{
  "source": "Mumbai",
  "destination": "Goa",
  "budget": 50000,
  "days": 5,
  "food": "vegetarian",
  "travelers": 2
}
```

**Parameters:**
- `source` (string): Starting city
- `destination` (string): Target city
- `budget` (integer): Total budget in rupees
- `days` (integer): Number of days for the trip
- `food` (string): Food preference (e.g., "vegetarian", "non-vegetarian", "vegan")
- `travelers` (integer): Number of travelers

**Response:**
```json
{
  "plan": "Day 1:\n  Morning: Arrive at Goa...\n  [detailed itinerary with specific places, prices, and times]"
}
```

### POST `/chat`
Send follow-up questions about an existing itinerary or get refinements.

**Request Body:**
```json
{
  "message": "Can you suggest cheaper restaurants?",
  "session_id": "default"
}
```

**Parameters:**
- `message` (string): Chat message or question
- `session_id` (string): Session identifier for maintaining context (default: "default")

**Response:**
```json
{
  "response": "Based on your budget constraints, here are some budget-friendly options...",
  "error": false
}
```

## 🔧 Core Components

### Agent (`agent.py`)
- Uses LangGraph's ReAct agent pattern for step-by-step reasoning
- Integrates multiple tools for gathering travel information
- Maintains conversation context using session management
- Uses Groq's optimized LLM for fast response generation

### Search Tools (`accommodation_tools.py`)
- **search_accommodations()**: Finds hotels with amenities and pricing
- **search_attractions()**: Discovers attractions by type and interest
- **search_food_restaurants()**: Recommends restaurants with cuisine and cost info
- **search_travel_tips()**: Provides weather, climate, and practical travel advice

### Vector Database (`vector_tools.py`)
- Semantic search over travel knowledge base
- Integration with Chroma for fast similarity queries
- Powered by Sentence Transformers embeddings

### Hybrid Search (`hybrid_rag.py`)
- Combines local vector database results with Wikipedia information
- Provides comprehensive travel context and facts

### Memory Management (`memory.py`)
- Session-based conversation history
- Maintains context across multiple queries
- Enables personalized follow-up responses

## 📊 Data Sources

The project includes several CSV datasets for travel information:
- **India_Tourism_2025_Processed.csv**: Indian destination data
- **Expanded_Destinations.csv**: Extended destination information
- **Tourist_Destinations.csv**: Popular tourist spots
- **Worldwide Travel Cities Dataset**: Global city ratings and climate data
- **trending_topics_2026_synthetic.csv**: Trending travel topics

## 🎨 User Interface

The frontend provides:
- **Travel Request Form**: Easy form to specify trip preferences
- **Quick Trip Suggestions**: Pre-configured popular routes
- **Chat Interface**: Conversational refinement of itineraries
- **Typing Indicators**: Visual feedback during processing
- **Responsive Design**: Works on desktop and mobile devices

## 🔄 Workflow

1. User fills out travel form with source, destination, budget, duration, preferences
2. Frontend sends request to `/generate` endpoint
3. Backend agent processes request:
   - Searches vector database for destination information
   - Queries accommodation, attraction, and restaurant data
   - Retrieves flight information
   - Generates detailed day-by-day itinerary with budget breakdown
4. Frontend displays itinerary with typing animation
5. User can ask follow-up questions via chat interface
6. Agent refines recommendations based on conversation history

## 💡 Tips for Best Results

- Be specific with preferences (vegetarian, adventure sports, luxury, budget, etc.)
- Longer trips (5+ days) allow for better multi-city recommendations
- Mention traveler count for accurate per-person budget allocation
- Use follow-up chat to refine specific days or activities
- Ask for alternatives if you need budget options

## 🐛 Troubleshooting

**Backend won't start:**
- Ensure GROQ_API_KEY is set in `.env`
- Check if port 8000 is available
- Verify all Python dependencies are installed

**Vector database errors:**
- Run `python backend/ingest.py` to regenerate embeddings
- Check if `vector_db/` directory exists and is writable

**Frontend connection issues:**
- Verify backend is running on `http://localhost:8000`
- Check browser console for CORS errors
- Ensure `.env` is properly configured

**Poor itinerary quality:**
- Try different keywords in follow-up questions
- Ask for specific activity types or interests
- Request budget breakdowns for detailed cost analysis

## 📝 Future Enhancements

- Real-time API integration for flight bookings
- Hotel reservation integration
- Weather API integration for accurate forecasts
- Multi-language support
- Social sharing of itineraries
- User accounts and saved trips
- Mobile app (React Native)
- Advanced filtering options (carbon footprint, accessibility)

## 📄 License

This project is open source and available under the MIT License.

## 👨‍💼 Author

Created as a Mini Project showcasing AI-powered travel planning with LangChain, LangGraph, and modern GenAI capabilities.

---

**Last Updated**: April 28, 2026
