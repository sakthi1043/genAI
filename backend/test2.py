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

from langchain_core.documents import Document
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_groq import ChatGroq

# ================= CONFIG =================
DATA_PATH = "static_rag"
DB_PATH = "vectordb"

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
            model_name="openai/gpt-oss-20b",
            temperature=0,
            request_timeout=LLM_TIMEOUT,
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
def extract_json(text: str):
    text = text.strip()
    fenced = re.search(r"```(?:json)?\s*([\s\S]+?)\s*```", text)
    if fenced:
        text = fenced.group(1).strip()
    # Find the first { ... } block as a fallback
    match = re.search(r"\{[\s\S]+\}", text)
    if match:
        text = match.group(0)
    return json.loads(text)


# ================= GENERATE =================
def _sync_generate(source, destination, budget, days, food, travelers):
    db  = state["db"]
    llm = state["llm"]

    if db is None:
        return {"error": "Vector DB not initialised. POST to /init-db first."}
    if llm is None:
        return {"error": "LLM not loaded. Check server startup logs."}

    # Retrieve with multiple targeted queries and merge results
    retriever = db.as_retriever(search_kwargs={"k": 8})
    docs = retriever.invoke(destination)

    if not docs or is_out_of_domain(docs, destination):
        logger.warning(f"'{destination}' not found in DB.")
        return {"error": f"Destination '{destination}' not found in our database."}

    # Build clean context — deduplicate and focus on destination match
    seen = set()
    context_parts = []
    for d in docs:
        content = d.page_content.strip()
        if content not in seen:
            seen.add(content)
            context_parts.append(content)

    context = "\n\n---\n\n".join(context_parts)

    per_day_per_person = budget // max(travelers, 1) // max(days, 1)

    prompt = f"""You are a travel planner. Generate a {days}-day itinerary from {source} to {destination}.

=== TRAVELER DETAILS ===
- Travelers: {travelers}
- Total Budget: ₹{budget:,} INR
- Per person per day budget: ₹{per_day_per_person:,} INR
- Food preference: {food}
- Duration: {days} days

=== DESTINATION DATA (USE THIS ONLY — DO NOT INVENT) ===
{context}

=== YOUR TASK ===
Using ONLY the data above, generate a realistic day-by-day itinerary.
- Activities must come from the "Suggested Activities" or "Type" fields in the data
- Food options must match the food preference "{food}" and reference local cuisine from the data
- Stay must reference accommodation options mentioned in the data with a realistic cost within ₹{per_day_per_person:,}/person/day
- Transport must reference transport options mentioned in the data
- Each day must be distinct — do not repeat the same activity

OUTPUT: Return ONLY a valid JSON object. No markdown. No explanation. No extra text.

{{
  "destination": "{destination}",
  "duration_days": {days},
  "total_budget_inr": {budget},
  "travelers": {travelers},
  "trip_plan": [
    {{
      "day": 1,
      "theme": "short theme for the day",
      "activities": [
        {{"time": "Morning", "activity": "specific activity from data", "cost_inr": 0}},
        {{"time": "Afternoon", "activity": "specific activity from data", "cost_inr": 0}},
        {{"time": "Evening", "activity": "specific activity from data", "cost_inr": 0}}
      ],
      "food": [
        {{"meal": "Breakfast", "description": "{food} option at local eatery", "cost_inr": 0}},
        {{"meal": "Lunch", "description": "{food} dish from local cuisine", "cost_inr": 0}},
        {{"meal": "Dinner", "description": "{food} dinner at restaurant", "cost_inr": 0}}
      ],
      "stay": {{"name": "accommodation from data", "type": "Budget/Mid-range/Luxury", "cost_per_night_inr": 0}},
      "transport": {{"mode": "transport from data", "cost_inr": 0}},
      "day_total_inr": 0
    }}
  ],
  "tips": ["tip based on best time to visit from data", "tip about local cuisine", "tip about transport"]
}}"""

    response = llm.invoke(prompt)
    logger.info(f"LLM raw response (first 300 chars): {response.content[:300]}")

    try:
        result = extract_json(response.content)
        return result
    except (json.JSONDecodeError, ValueError) as e:
        logger.error(f"JSON parse error: {e}\nFull response: {response.content}")
        return {"error": "Failed to parse LLM response as JSON", "raw": response.content}


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