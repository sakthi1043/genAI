import os
import re
import json
import logging
import asyncio
import pandas as pd
from contextlib import asynccontextmanager
from concurrent.futures import ThreadPoolExecutor

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from langchain_core.documents import Document
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_groq import ChatGroq
from flight_data import get_flights, get_simulated_flights

# ================= CONFIG =================
DATA_PATH = "static_rag"
DB_PATH = "vectordb"
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
LLM_TIMEOUT = 60
EXECUTOR = ThreadPoolExecutor(max_workers=4)

# ================= LOGGING =================
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logging.getLogger("httpx").setLevel(logging.WARNING)

# ================= GLOBAL STATE =================
state = {"embedding": None, "db": None, "llm": None}

# ================= LIFESPAN =================
@asynccontextmanager
async def lifespan(app: FastAPI):
    loop = asyncio.get_event_loop()

    def load_models():
        logger.info("Loading embedding model...")
        state["embedding"] = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )
        logger.info("Loading LLM...")
        state["llm"] = ChatGroq(
            groq_api_key=GROQ_API_KEY,
            model_name="llama-3.3-70b-versatile",
            temperature=0,
            request_timeout=LLM_TIMEOUT,
            max_tokens=2048,
        )
        logger.info("Models loaded.")

    await loop.run_in_executor(EXECUTOR, load_models)

    if os.path.exists(DB_PATH) and state["embedding"]:
        def load_existing_db():
            state["db"] = Chroma(
                persist_directory=DB_PATH,
                embedding_function=state["embedding"]
            )
            logger.info("Existing vector DB loaded.")
        await loop.run_in_executor(EXECUTOR, load_existing_db)

    yield
    logger.info("Shutting down.")


# ================= APP =================
app = FastAPI(lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ================= REQUEST MODEL =================
class TravelRequest(BaseModel):
    source: str
    destination: str
    budget: int
    days: int
    food: str
    travelers: int


# ===================================================================
# KEY FIX: Build rich, joined documents per destination from all CSVs
# ===================================================================
def build_destination_documents() -> list[Document]:
    """
    Instead of dumping raw CSV rows as flat text, we join all CSVs
    by destination/state name and produce one rich document per
    destination. This gives the LLM structured, meaningful context.
    """
    docs = []

    # --- Load all CSVs ---
    expanded_path    = os.path.join(DATA_PATH, "Expanded_Destinations.csv")
    india_path       = os.path.join(DATA_PATH, "India_Tourism_2025_Processed.csv")
    tourist_path     = os.path.join(DATA_PATH, "Tourist_Destinations.csv")
    worldwide_path   = os.path.join(DATA_PATH, "Worldwide_Travel_Cities_Dataset__Ratings_and_Climate_.csv")

    expanded   = pd.read_csv(expanded_path)   if os.path.exists(expanded_path)   else pd.DataFrame()
    india      = pd.read_csv(india_path)      if os.path.exists(india_path)       else pd.DataFrame()
    tourist    = pd.read_csv(tourist_path)    if os.path.exists(tourist_path)     else pd.DataFrame()
    worldwide  = pd.read_csv(worldwide_path)  if os.path.exists(worldwide_path)   else pd.DataFrame()

    # ---- 1. Indian destinations from Expanded_Destinations + India_Tourism ----
    if not expanded.empty:
        for _, row in expanded.iterrows():
            name  = str(row.get("Name", "")).strip()
            state_name = str(row.get("State", "")).strip()
            dtype = str(row.get("Type", "")).strip()
            pop   = row.get("Popularity", "N/A")
            best  = str(row.get("BestTimeToVisit", "")).strip()

            # Pull tourism revenue & visitor stats for the matching state
            tourism_info = ""
            if not india.empty:
                state_data = india[india["State"].str.lower() == state_name.lower()]
                if not state_data.empty:
                    avg_rev  = state_data["Tourism Revenue (INR Crore)"].mean()
                    total_v  = state_data["Total Tourists"].mean()
                    purposes = state_data["Purpose of Visit"].unique().tolist()
                    rev_per  = state_data["Revenue_Per_Tourist_INR"].mean()
                    tourism_info = (
                        f"State Tourism Stats ({state_name}): "
                        f"Avg monthly revenue ₹{avg_rev:.1f} Cr, "
                        f"Avg monthly visitors {int(total_v):,}, "
                        f"Revenue per tourist ₹{rev_per:.0f}, "
                        f"Popular visit purposes: {', '.join(purposes)}."
                    )

            text = (
                f"Destination: {name}\n"
                f"Location: {state_name}, India\n"
                f"Type: {dtype}\n"
                f"Popularity Score: {pop:.2f}/10\n"
                f"Best Time to Visit: {best}\n"
                f"{tourism_info}\n"
                f"Suggested Activities: Sightseeing at {name}, local market visits, "
                f"cultural experiences typical of {dtype.lower()} destinations in {state_name}.\n"
                f"Food: Local cuisine of {state_name} — street food, regional specialties.\n"
                f"Transport: Trains, buses, and taxis commonly used within {state_name}.\n"
                f"Accommodation: Budget guesthouses (~₹800-1500/night), "
                f"mid-range hotels (~₹1500-3500/night), "
                f"luxury hotels (~₹5000+/night) available near {name}."
            )
            docs.append(Document(
                page_content=text,
                metadata={"destination": name, "state": state_name, "country": "India", "type": dtype}
            ))

    # ---- 2. International destinations from Tourist_Destinations ----
    if not tourist.empty:
        for _, row in tourist.iterrows():
            name     = str(row.get("Destination Name", "")).strip()
            country  = str(row.get("Country", "")).strip()
            continent= str(row.get("Continent", "")).strip()
            dtype    = str(row.get("Type", "")).strip()
            cost_usd = row.get("Avg Cost (USD/day)", "N/A")
            season   = str(row.get("Best Season", "")).strip()
            rating   = row.get("Avg Rating", "N/A")
            visitors = row.get("Annual Visitors (M)", "N/A")
            unesco   = str(row.get("UNESCO Site", "No")).strip()

            cost_inr = f"~₹{int(float(cost_usd) * 84):,}/day" if cost_usd != "N/A" else "N/A"

            text = (
                f"Destination: {name}\n"
                f"Location: {country}, {continent}\n"
                f"Type: {dtype}\n"
                f"Average Cost: ${cost_usd}/day per person ({cost_inr})\n"
                f"Best Season: {season}\n"
                f"Rating: {rating}/5\n"
                f"Annual Visitors: {visitors} million\n"
                f"UNESCO World Heritage Site: {unesco}\n"
                f"Suggested Activities: Explore local landmarks, cultural tours, "
                f"{dtype.lower()} activities typical of {country}.\n"
                f"Food: Local cuisine of {country} — restaurants range from budget to fine dining.\n"
                f"Transport: Local taxis, public transport, and guided tours available.\n"
                f"Accommodation: Hostels (~$20-40/night), mid-range hotels (~$60-120/night), "
                f"luxury hotels (~$150+/night) in {name}."
            )
            docs.append(Document(
                page_content=text,
                metadata={"destination": name, "country": country, "continent": continent, "type": dtype}
            ))

    # ---- 3. Worldwide city details ----
    if not worldwide.empty:
        for _, row in worldwide.iterrows():
            city    = str(row.get("city", "")).strip()
            country = str(row.get("country", "")).strip()
            region  = str(row.get("region", "")).strip()
            desc    = str(row.get("short_description", "")).strip()
            budget  = str(row.get("budget_level", "")).strip()
            dur     = str(row.get("ideal_durations", "")).strip()

            # Build experience profile from numeric scores
            scores = {
                "Culture": row.get("culture", 0),
                "Adventure": row.get("adventure", 0),
                "Nature": row.get("nature", 0),
                "Beaches": row.get("beaches", 0),
                "Nightlife": row.get("nightlife", 0),
                "Cuisine": row.get("cuisine", 0),
                "Wellness": row.get("wellness", 0),
                "Urban": row.get("urban", 0),
                "Seclusion": row.get("seclusion", 0),
            }
            top_experiences = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:3]
            exp_str = ", ".join([f"{k} ({v}/5)" for k, v in top_experiences])

            text = (
                f"City: {city}\n"
                f"Country: {country}, Region: {region}\n"
                f"Description: {desc}\n"
                f"Budget Level: {budget}\n"
                f"Ideal Trip Duration: {dur}\n"
                f"Top Experiences: {exp_str}\n"
                f"Activities: Explore {city}'s top attractions, local cuisine, and "
                f"experiences rated high in {exp_str.split(',')[0]}.\n"
                f"Food: {city} cuisine ranges from street food to fine dining.\n"
                f"Transport: Metro, taxis, and city buses widely available in {city}.\n"
                f"Accommodation: Budget to luxury options available across {city}."
            )
            docs.append(Document(
                page_content=text,
                metadata={"destination": city, "country": country, "region": region}
            ))

    logger.info(f"Built {len(docs)} destination documents.")
    return docs


# ================= CREATE DB =================
def _sync_init_db():
    embedding = state["embedding"]
    if embedding is None:
        return {"status": "error", "message": "Embedding model not loaded."}

    docs = build_destination_documents()
    if not docs:
        return {"status": "error", "message": "No destination data could be built from CSVs."}

    db = Chroma.from_documents(
        documents=docs,
        embedding=embedding,
        persist_directory=DB_PATH
    )
    state["db"] = db
    logger.info(f"DB created with {len(docs)} destination documents.")
    return {"status": "success", "documents": len(docs)}


# ================= DOMAIN CHECK =================
def is_out_of_domain(docs: list[Document], destination: str) -> bool:
    combined = " ".join([d.page_content.lower() for d in docs])
    words = [w for w in destination.lower().split() if len(w) > 2]
    return not any(word in combined for word in words)


# ================= JSON EXTRACTOR =================
def _repair_truncated_json(text: str) -> str:
    """
    Attempt to close any unclosed JSON structures produced by a truncated
    LLM response so that json.loads has a chance of succeeding.
    """
    # Track open structures
    stack = []          # 'obj' or 'arr'
    in_string = False
    escape_next = False

    for i, ch in enumerate(text):
        if escape_next:
            escape_next = False
            continue
        if ch == "\\" and in_string:
            escape_next = True
            continue
        if ch == '"':
            in_string = not in_string
            continue
        if in_string:
            continue
        if ch == '{':
            stack.append('obj')
        elif ch == '[':
            stack.append('arr')
        elif ch == '}' and stack and stack[-1] == 'obj':
            stack.pop()
        elif ch == ']' and stack and stack[-1] == 'arr':
            stack.pop()

    # If we are mid-string, close it
    closer = '"' if in_string else ''
    # Close every open structure in reverse order
    for frame in reversed(stack):
        closer += '}' if frame == 'obj' else ']'
    return text + closer


def extract_json(text: str):
    text = text.strip()
    # Unwrap ```json ... ``` fences
    fenced = re.search(r"```(?:json)?\s*([\s\S]+?)\s*```", text)
    if fenced:
        text = fenced.group(1).strip()
    # Find the outermost { ... } block
    match = re.search(r"\{[\s\S]+", text)   # intentionally no closing \}
    if match:
        text = match.group(0)

    # 1) Try parsing as-is
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # 2) Try repairing truncated JSON
    try:
        repaired = _repair_truncated_json(text)
        logger.warning("JSON was truncated; repaired and re-parsed successfully.")
        return json.loads(repaired)
    except json.JSONDecodeError:
        pass

    # 3) Last resort — find the last complete top-level } and cut there
    last_brace = text.rfind('}')
    if last_brace != -1:
        try:
            candidate = text[:last_brace + 1]
            result = json.loads(candidate)
            logger.warning("JSON repaired by truncating to last '}'.")
            return result
        except json.JSONDecodeError:
            pass

    raise ValueError("Could not parse or repair JSON from LLM response.")


# ================= BUDGET HELPERS =================

# Minimum per-person-per-day thresholds (INR)
_DOMESTIC_MIN_PER_PERSON_DAY  = 500    # very budget domestic India
_INTL_MIN_PER_PERSON_DAY      = 3_000  # budget international (flight not included)

# Known international country keywords (extend as needed)
_INTL_KEYWORDS = {
    "japan", "usa", "uk", "france", "germany", "italy", "spain", "australia",
    "singapore", "thailand", "bali", "dubai", "uae", "canada", "malaysia",
    "maldives", "switzerland", "new zealand", "south korea", "china",
    "indonesia", "vietnam", "sri lanka", "nepal", "bhutan", "egypt", "turkey",
}

def _is_international(destination: str) -> bool:
    d = destination.lower()
    return any(kw in d for kw in _INTL_KEYWORDS)


def budget_validate(destination: str, budget: int, days: int, travelers: int) -> dict | None:
    """
    Returns an error dict if budget is too low, else None.
    """
    per_person_per_day = budget / max(travelers, 1) / max(days, 1)
    is_intl = _is_international(destination)
    min_ppd = _INTL_MIN_PER_PERSON_DAY if is_intl else _DOMESTIC_MIN_PER_PERSON_DAY
    min_total = min_ppd * travelers * days

    if per_person_per_day < min_ppd:
        trip_type = "international" if is_intl else "domestic"
        return {
            "error": (
                f"Budget \u20b9{budget:,} is too low for a {days}-day {trip_type} trip "
                f"to {destination} for {travelers} traveler(s). "
                f"Minimum recommended budget is \u20b9{min_total:,} "
                f"(\u20b9{min_ppd:,}/person/day)."
            )
        }
    return None


def budget_allocate(budget: int, days: int, travelers: int) -> dict:
    """
    Split total budget across stay, food, activities, transport.
    Standard travel allocation:
      Stay        40 %
      Food        25 %
      Activities  20 %
      Transport   15 %
    Returns per-night / per-day / per-trip values.
    """
    stay_total       = int(budget * 0.40)
    food_total       = int(budget * 0.25)
    activity_total   = int(budget * 0.20)
    transport_total  = int(budget * 0.15)

    nights = max(days, 1)
    return {
        "stay_per_night_inr":      stay_total // nights,
        "food_per_day_inr":        food_total // max(days, 1),
        "activity_per_day_inr":    activity_total // max(days, 1),
        "transport_per_day_inr":   transport_total // max(days, 1),
        "stay_total_inr":          stay_total,
        "food_total_inr":          food_total,
        "activity_total_inr":      activity_total,
        "transport_total_inr":     transport_total,
    }


# ================= GENERATE =================
def _sync_generate(source, destination, budget, days, food, travelers):
    db  = state["db"]
    llm = state["llm"]

    if db is None:
        return {"error": "Vector DB not initialised. POST to /init-db first."}
    if llm is None:
        return {"error": "LLM not loaded. Check server startup logs."}

    # ---- 1. Get flight cost first (needed for budget validation) ----
    try:
        flight_raw = get_simulated_flights(source, destination)
        import os
        if os.getenv("RAPID_API_KEY"):
            try:
                flight_raw = get_flights.invoke({"source": source, "destination": destination})
            except Exception as fe:
                logger.warning(f"Real flight API failed, using simulated: {fe}")
    except Exception as e:
        logger.warning(f"Flight lookup failed entirely: {e}")
        flight_raw = f"FLIGHTS FROM {source.upper()} TO {destination.upper()}\nEstimated cost: \u20b93,500 \u2013 \u20b98,500 per person"

    # Parse flight text into a structured dict
    travel_info = {"from": source, "to": destination, "options": []}
    for line in flight_raw.splitlines():
        line = line.strip()
        if line.startswith("Option"):
            parts = [p.strip() for p in line.split("|")]
            if len(parts) >= 3:
                airline    = parts[0].split(":", 1)[-1].strip()
                price_str  = parts[1].replace("\u20b9", "").replace(",", "").strip()
                try:
                    price_inr = int(price_str)
                except ValueError:
                    price_inr = 0
                duration = parts[2].replace("Duration:", "").strip()
                travel_info["options"].append({
                    "airline": airline,
                    "price_per_person_inr": price_inr,
                    "total_price_inr": price_inr * travelers,
                    "duration": duration,
                })

    if travel_info["options"]:
        cheapest        = min(travel_info["options"], key=lambda x: x["price_per_person_inr"])
        travel_cost_inr = cheapest["total_price_inr"]
        travel_note     = (
            f"{source} \u2192 {destination}: {cheapest['airline']}, "
            f"\u20b9{cheapest['price_per_person_inr']:,}/person, "
            f"Duration: {cheapest['duration']}"
        )
    else:
        travel_cost_inr = 0
        travel_note     = f"Estimate travel cost from {source} to {destination} separately."

    logger.info(f"Travel info: {travel_note}")

    # ---- 2. Budget validation against remaining (ground) budget ----
    if travel_cost_inr >= budget:
        return {
            "error": (
                f"Your budget \u20b9{budget:,} is insufficient to cover even the flight. "
                f"Cheapest flight ({cheapest['airline']}) costs "
                f"\u20b9{cheapest['price_per_person_inr']:,}/person "
                f"(\u20b9{travel_cost_inr:,} total for {travelers} traveler(s)). "
                f"Please increase your budget."
            )
        }

    ground_budget = budget - travel_cost_inr   # what's left after flights
    budget_error  = budget_validate(destination, ground_budget, days, travelers)
    if budget_error:
        # Enrich the error to mention flight cost ate into budget
        base_msg = budget_error["error"]
        return {
            "error": (
                f"{base_msg} "
                f"Note: \u20b9{travel_cost_inr:,} of your budget is used for flights "
                f"({cheapest['airline'] if travel_info['options'] else 'flights'}), "
                f"leaving \u20b9{ground_budget:,} for the trip."
            )
        }

    # ---- 3. Allocate from ground budget (stay + food + activities + transport) ----
    alloc              = budget_allocate(ground_budget, days, travelers)
    per_day_per_person = ground_budget // max(travelers, 1) // max(days, 1)

    logger.info(
        f"Budget split — total:\u20b9{budget:,} flight:\u20b9{travel_cost_inr:,} "
        f"ground:\u20b9{ground_budget:,} ({per_day_per_person:,}/person/day)"
    )



    # ---- 3. RAG retrieval ----
    retriever = db.as_retriever(search_kwargs={"k": 6})

    # Check source city exists in DB
    source_docs = retriever.invoke(source)
    if not source_docs or is_out_of_domain(source_docs, source):
        logger.warning(f"Source '{source}' not found in DB.")
        return {"error": f"Source '{source}' not found in our database. Please enter a valid departure city."}

    # Check destination exists in DB
    docs = retriever.invoke(destination)
    if not docs or is_out_of_domain(docs, destination):
        logger.warning(f"'{destination}' not found in DB.")
        return {"error": f"Destination '{destination}' not found in our database."}

    # ---- 4. Build full destination context from retrieved docs ----
    seen_docs: set = set()
    full_context_parts = []
    for doc in docs:
        content = doc.page_content.strip()
        if content not in seen_docs:
            seen_docs.add(content)
            full_context_parts.append(content)
    full_context = "\n\n---\n\n".join(full_context_parts)

    # ---- 5. Extract cost hints from context ----
    def _extract_lines(doc_list: list, keyword: str) -> str:
        seen: set = set()
        results = []
        for doc in doc_list:
            for line in doc.page_content.splitlines():
                s = line.strip()
                if keyword.lower() in s.lower() and s not in seen:
                    seen.add(s)
                    results.append(s)
        return "\n".join(results)

    accom_hint    = _extract_lines(docs, "accommodation") or "Use world-knowledge hotel costs."
    food_hint     = _extract_lines(docs, "food")          or "Use world-knowledge food costs."
    transport_hint= _extract_lines(docs, "transport")     or "Use world-knowledge transport costs."
    activity_hint = _extract_lines(docs, "activit")       or "Use world-knowledge for activities."

    logger.info(f"Full context built: {len(full_context_parts)} docs for {destination}")

    rag_section = f"""=== DESTINATION REFERENCE DATA ===
{full_context}

=== COST HINTS FROM DATABASE ===
Accommodation: {accom_hint}
Food: {food_hint}
Transport: {transport_hint}
Activities: {activity_hint}"""

    prompt = f"""You are an expert travel planner with deep knowledge of {destination}.
Generate a detailed, SPECIFIC {days}-day itinerary from {source} to {destination}.

=== TRAVELER DETAILS ===
- Travelers: {travelers}
- Total Budget: \u20b9{budget:,} INR
- Per person per day: \u20b9{per_day_per_person:,} INR
- Food preference: {food}
- Duration: {days} days

=== APPROVED BUDGET ALLOCATION ===
- Stay:       \u20b9{alloc['stay_per_night_inr']:,}/night  (total \u20b9{alloc['stay_total_inr']:,})
- Food:       \u20b9{alloc['food_per_day_inr']:,}/day     (total \u20b9{alloc['food_total_inr']:,})
- Activities: \u20b9{alloc['activity_per_day_inr']:,}/day  (total \u20b9{alloc['activity_total_inr']:,})
- Transport:  \u20b9{alloc['transport_per_day_inr']:,}/day (total \u20b9{alloc['transport_total_inr']:,})

{rag_section}

=== YOUR TASK ===
Create a SPECIFIC, REALISTIC itinerary using the reference data above.
If the database has details, use them. Where the database is generic, use your world knowledge.

STRICT SPECIFICITY RULES — every field must be REAL and SPECIFIC:

ACTIVITIES (MUST be specific real places):
- Use actual landmark names: e.g. "Visit Calangute Beach", "Explore Basilica of Bom Jesus", NOT "Beach Visit"
- Use real tourist spots, museums, markets, temples with their actual names
- Each day MUST have a completely different theme and 3 distinct activities
- Use the cost hint from database; if 0, estimate a realistic cost from world knowledge

FOOD (MUST be specific dishes and real eateries):
- Use real local dish names: e.g. "Goan Fish Curry at Ritz Classic", NOT "local lunch"
- Breakfast, Lunch, Dinner must each be a specific {food} dish with a real restaurant name
- Match "{food}" preference throughout
- Use database food cost hints; if missing, estimate from world knowledge

STAY (MUST be a real hotel name):
- Use an ACTUAL hotel/resort/guesthouse name that fits \u20b9{alloc['stay_per_night_inr']:,}/night budget
- Include hotel type (Budget/Mid-range/Luxury) based on the budget
- Use database accommodation cost hints to set cost_per_night_inr
- Keep the SAME hotel for all days (realistic for a short trip) unless budget changes

TRANSPORT (MUST be specific):
- Use real transport options for {destination}: e.g. "Hired scooter rental", "Kadamba bus", NOT "local transport"
- Vary transport per day where realistic

GENERAL RULES:
- Keep ALL string values under 60 characters
- cost_inr values MUST match the APPROVED BUDGET ALLOCATION — do not exceed them
- tips: EXACTLY 3 strings, each a SPECIFIC practical tip for {destination} (best time, must-eat, etc.)
- Each of the {days} days MUST have a unique theme

OUTPUT: Return ONLY a valid, COMPLETE JSON object. No markdown, no explanation.
Every opening brace/bracket MUST have a matching closing brace/bracket.

{{
  "destination": "{destination}",
  "duration_days": {days},
  "total_budget_inr": {budget},
  "travelers": {travelers},
  "trip_plan": [
    {{
      "day": 1,
      "theme": "SPECIFIC theme (e.g. Old Goa Heritage)",
      "activities": [
        {{"time": "Morning",   "activity": "SPECIFIC real place/activity", "cost_inr": {alloc['activity_per_day_inr'] // 3}}},
        {{"time": "Afternoon", "activity": "SPECIFIC real place/activity", "cost_inr": {alloc['activity_per_day_inr'] // 3}}},
        {{"time": "Evening",   "activity": "SPECIFIC real place/activity", "cost_inr": {alloc['activity_per_day_inr'] // 3}}}
      ],
      "food": [
        {{"meal": "Breakfast", "description": "SPECIFIC dish at REAL restaurant", "cost_inr": {alloc['food_per_day_inr'] // 4}}},
        {{"meal": "Lunch",     "description": "SPECIFIC dish at REAL restaurant", "cost_inr": {alloc['food_per_day_inr'] // 3}}},
        {{"meal": "Dinner",    "description": "SPECIFIC dish at REAL restaurant", "cost_inr": {alloc['food_per_day_inr'] // 3}}}
      ],
      "stay":      {{"name": "REAL hotel name", "type": "Budget/Mid-range/Luxury", "cost_per_night_inr": {alloc['stay_per_night_inr']}}},
      "transport": {{"mode": "SPECIFIC transport mode", "cost_inr": {alloc['transport_per_day_inr']}}},
      "day_total_inr": {per_day_per_person * travelers}
    }}
  ],
  "tips": ["SPECIFIC tip 1 for {destination}", "SPECIFIC tip 2", "SPECIFIC tip 3"]
}}"""

    response = llm.invoke(prompt)
    raw = response.content.strip() if response.content else ""
    logger.info(f"LLM raw response (first 300 chars): {raw[:300]}")

    # Guard 1: empty response
    if not raw:
        logger.error("LLM returned an empty response.")
        return {"error": "The AI returned an empty response. Please try again."}

    # Guard 2: refusal / apology (model declined to generate)
    REFUSAL_PHRASES = [
        "i'm sorry", "i am sorry", "i cannot", "i can't",
        "unable to", "not able to", "cannot generate", "can't generate",
        "unfortunately", "as an ai",
    ]
    raw_lower = raw.lower()
    if any(phrase in raw_lower for phrase in REFUSAL_PHRASES) and "{" not in raw:
        logger.error(f"LLM refused to generate itinerary: {raw[:200]}")
        return {"error": f"The AI declined this request: {raw[:200]}"}

    # Guard 3: response doesn't look like JSON at all
    if "{" not in raw:
        logger.error(f"LLM did not return JSON. Response: {raw[:200]}")
        return {"error": "The AI did not return a valid itinerary. Please try again."}

    try:
        result = extract_json(raw)
        # Inject the pre-computed travel info so it's always valid JSON
        result["travel"] = travel_info
        return result
    except (json.JSONDecodeError, ValueError) as e:
        logger.error(f"JSON parse error: {e}\nFull response: {raw}")
        return {"error": "Failed to parse the AI response. Please try again.", "raw": raw}


# ================= ROUTES =================

@app.get("/")
async def root():
    return {
        "status": "running",
        "db_loaded": state["db"] is not None,
        "llm_loaded": state["llm"] is not None,
        "embedding_loaded": state["embedding"] is not None,
        "message": "POST /init-db first, then POST /generate"
    }


@app.post("/init-db")
async def init_db():
    try:
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(EXECUTOR, _sync_init_db)
        return result
    except Exception as e:
        logger.exception("Error in /init-db")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/generate")
async def generate(data: TravelRequest):
    try:
        loop = asyncio.get_event_loop()
        result = await asyncio.wait_for(
            loop.run_in_executor(
                EXECUTOR,
                _sync_generate,
                data.source,
                data.destination,
                data.budget,
                data.days,
                data.food,
                data.travelers,
            ),
            timeout=LLM_TIMEOUT,
        )
        has_error = "error" in result
        return {"plan": result, "error": has_error}

    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="LLM timed out. Try again.")
    except Exception as e:
        logger.exception("Error in /generate")
        raise HTTPException(status_code=500, detail=str(e))