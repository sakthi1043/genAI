import os
import json
import re
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import SystemMessage, HumanMessage

from backend.vector_tools import search_local_knowledge
from backend.hybrid_rag import hybrid_search
from backend.flight_data import get_flights
from backend.accommodation_tools import search_accommodations, search_attractions, search_food_restaurants, search_travel_tips
from backend.memory import get_session

load_dotenv(dotenv_path="backend/.env")

llm = ChatGroq(
    model_name="llama-3.1-8b-instant",
    groq_api_key=os.getenv("GROQ_API_KEY")   ,
    temperature=0,
    max_retries=3,          # Automatically pauses and retries on 429 Rate Limit errors!
    timeout=30.00
)

tools = [
    search_local_knowledge, 
    hybrid_search, 
    get_flights,
    search_accommodations,
    search_attractions,
    search_food_restaurants,
    search_travel_tips
]

agent = create_react_agent(llm, tools)

def run_agent(user_input: str, session_id="default"):
    session = get_session(session_id)

    system_prompt = """
You are Wandr, a highly detailed and conversational AI travel planner for India.

Your role:

Create detailed day-by-day itineraries with specific rec      ommendations
Answer follow-up questions about existing itineraries
Modify plans based on user preferences and budget constraints
Provide real place names, costs, and practical travel advice

CRITICAL GROUNDING RULES (ANTI-HALLUCINATION):

You MUST only use information that is explicitly available from the retrieval system (RAG), provided context, or widely known, verifiable facts.
If specific data (hotel names, prices, timings, transport options, etc.) is NOT available in retrieved data, DO NOT fabricate it.
Instead, do one of the following:
Use a generic but truthful placeholder such as:
"Mid-range hotel in [area]"
"Local vegetarian restaurant near [place]"
OR clearly mark the value as:
null (for JSON fields)
or "Not available from data"
Never guess exact prices, ratings, durations, or availability.
Do not invent flight details, hotel ratings, or restaurant names.
If budget allocation is uncertain due to missing data, distribute conservatively and label assumptions clearly in "tips".

DATA USAGE PRIORITY:

Retrieved (RAG) data
User-provided inputs
General known facts (only if highly reliable and non-specific)

If a conflict occurs, prefer retrieved data over prior knowledge.

FORMATTING RULES FOR ITINERARIES:
You MUST return your itinerary as a valid JSON object. Do NOT include any text before or after the JSON.
Do NOT wrap it in markdown code blocks. Just return the raw JSON.

Use this exact JSON structure:

{
"tripDetails": {
"source": "City Name",
"destination": "City Name",
"days": 3,
"travelers": 2,
"totalBudget": 25000,
"dailyBudget": 4167,
"foodPreference": "vegetarian"
},
"flight": {
"airline": "IndiGo or null",
"price": 3500,
"duration": "2h 15m or null",
"departure": "YYYY-MM-DD or null"
},
"accommodation": {
"name": "Hotel Name or generic description",
"pricePerNight": 2000,
"rating": 4.2,
"location": "Area Name",
"amenities": "WiFi, AC, Breakfast or null"
},
"days": [
{
"dayNumber": 1,
"title": "Arrival and Exploration",
"activities": [
{
"timeSlot": "Morning",
"time": "8:00 AM - 12:00 PM",
"activity": "Check-in at hotel and visit local market",
"place": "Place Name",
"cost": 500,
"details": "Only include details supported by data; otherwise keep generic"
},
{
"timeSlot": "Afternoon",
"time": "12:00 PM - 5:00 PM",
"activity": "Lunch and sightseeing",
"place": "Restaurant Name or generic",
"meal": "Lunch at [name] - cuisine type or generic",
"cost": 800,
"details": "Description based only on available info"
},
{
"timeSlot": "Evening",
"time": "5:00 PM - 10:00 PM",
"activity": "Dinner and leisure",
"place": "Restaurant Name or generic",
"meal": "Dinner at [name] - cuisine type or generic",
"cost": 600,
"details": "Description"
}
],
"dailyTotal": 1900
}
],
"budget": {
"flights": 7000,
"accommodation": 6000,
"food": 5000,
"activities": 4500,
"transport": 1500,
"buffer": 1000,
"total": 25000
},
"tips": [
"Only include verified advice",
"If assumptions are made, explicitly state them",
"Mention when data was unavailable and generalized"
]
}

STRICT RULES:

ALL cost values must be NUMBERS (not strings)
DO NOT fabricate:
hotel ratings
exact restaurant names
transport durations
flight details
If unknown, use:
null (for numbers/structured fields)
"Not available from data" (for strings)
Budget must still add up correctly
Daily totals must match activity costs
No emojis
Output ONLY JSON

FOLLOW-UP RESPONSES:

Be conversational and transparent
Clearly state when information is missing =
Offer safe alternatives without guessing specifics
Do NOT fabricate details

CORE PRINCIPLE:
If you are not sure, do not guess. Prefer partial accuracy over complete hallucination.

"""

    # Only add system prompt once at the start of a new session
    if not session or (len(session) == 0):
        session.append(SystemMessage(content=system_prompt))
    
    # Add the user's new message
    session.append(HumanMessage(content=user_input))

    # Invoke the agent with the full conversation history
    response = agent.invoke({"messages": session})

    # Extract the final response and store it in session
    final = response["messages"][-1].content
    session.append(response["messages"][-1])

    return final


def parse_itinerary_json(text):
    """Try to extract and parse JSON from the LLM response."""
    # Try direct JSON parse first
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    
    # Try to find JSON in markdown code blocks
    code_block = re.search(r'```(?:json)?\s*\n?(.*?)\n?```', text, re.DOTALL)
    if code_block:
        try:
            return json.loads(code_block.group(1))
        except json.JSONDecodeError:
            pass
    
    # Try to find JSON object in the text
    brace_match = re.search(r'\{.*\}', text, re.DOTALL)
    if brace_match:
        try:
            return json.loads(brace_match.group())
        except json.JSONDecodeError:
            pass
    
    return None


def generate_itinerary(source, destination, budget, days, food, travelers):
    budget_val = int(float(str(budget).replace(',', '')))

    per_person_per_day = budget_val // (days * travelers) if travelers > 0 else 0

    query = f"""
Generate a complete {days}-day travel itinerary from {source} to {destination}.

IMPORTANT INSTRUCTIONS:

1. First, search for flights from {source} to {destination} using get_flights tool,if no flight found say no flight found do not create your flight
2. Use search_accommodations to find suitable hotels, if no hotel found say no hotel found do not create your hotel
3. Use search_attractions to find activities and places, if no attractions found say no attractions found do not create your attractions
4. Use search_food_restaurants to find dining options for {food} preference, if no food found say no food found do not create your food
5. Use search_travel_tips for location insights, if no travel tips found say no travel tips found do not create your travel tips
6. Return the result as a valid JSON object following the exact structure in your system prompt
7. If the prompt is irrelevant means you should say out of domain.
8. If you dont know the location or destination  do not provide any other information. givew location not found in db

Trip Details:
- Source: {source}
- Destination: {destination}
- Total Budget: {budget_val} INR ({travelers} traveler(s))
- Duration: {days} days
- Food Preference: {food}
- Per person per day budget: {per_person_per_day} INR

COST ALLOCATION (Total: {budget_val} INR):
- Flights: ~{int(budget_val * 0.25)} INR (25%)
- Accommodation: ~{int(budget_val * 0.30)} INR (30%)
- Food: ~{int(budget_val * 0.25)} INR (25%)
- Activities & Local Transport: ~{int(budget_val * 0.15)} INR (15%)
- Buffer: ~{int(budget_val * 0.05)} INR (5%)

CRITICAL: 
- Return ONLY a valid JSON object, no extra text
- ALL cost values must be numbers, NOT strings
- Budget items must add up to approximately {budget_val} INR
- Do NOT use any emojis
- Use real place names and realistic costs

Generate the JSON itinerary now.
"""

    raw = run_agent(query)
    
    # Try to parse as JSON
    parsed = parse_itinerary_json(raw)
    
    if parsed:
        return {"format": "json", "data": parsed}
    else:
        # Fallback: return raw text
        return {"format": "text", "data": raw}