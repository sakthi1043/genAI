from langchain_core.tools import tool
from backend.vector_tools import db, embeddings

@tool
def search_accommodations(destination: str, budget_range: str) -> str:
    """
    Search for specific hotels and accommodations in a destination with prices.
    Budget ranges: budget (₹1000-3000), mid (₹3000-8000), luxury (₹8000+)
    Returns specific hotel names, ratings, amenities and estimated costs.
    """
    query = f"hotels accommodations stays {destination} {budget_range} price cost INR"
    results = db.similarity_search(query, k=8)
    
    accommodations = "\n".join([doc.page_content for doc in results])
    
    if not accommodations.strip():
        return f"Standard {budget_range} accommodations in {destination}:\n- No specific data found. Recommend searching for star hotels."
    
    return f"Accommodations in {destination} ({budget_range}):\n{accommodations}"


@tool
def search_attractions(destination: str, interest: str = "all") -> str:
    """
    Search for specific attractions, places, and activities in a destination.
    Interest types: temples, museums, parks, restaurants, shopping, adventure, cultural, historical
    Returns specific place names, types, and recommended visit times.
    """
    query = f"attractions places {interest} {destination} visit explore things to do"
    results = db.similarity_search(query, k=10)
    
    attractions = "\n".join([doc.page_content for doc in results])
    
    if not attractions.strip():
        return f"Popular attractions in {destination}: No specific data available."
    
    return f"Attractions in {destination}:\n{attractions}"


@tool
def search_food_restaurants(destination: str, cuisine: str) -> str:
    """
    Search for specific restaurants and food options in a destination.
    Cuisine types: vegetarian, non-vegetarian, local, international
    Returns specific restaurant names, cuisines, estimated costs and ratings.
    """
    query = f"restaurants food {cuisine} {destination} dining eat cost price"
    results = db.similarity_search(query, k=8)
    
    restaurants = "\n".join([doc.page_content for doc in results])
    
    if not restaurants.strip():
        return f"Food options in {destination} ({cuisine}): No specific data found."
    
    return f"Restaurants in {destination} ({cuisine}):\n{restaurants}"


@tool
def search_travel_tips(destination: str) -> str:
    """
    Search for travel tips, weather, best time to visit, and practical information
    about a destination. Returns costs, climate, and recommendations.
    """
    query = f"{destination} travel tips weather climate best time to visit cost budget"
    results = db.similarity_search(query, k=6)
    
    tips = "\n".join([doc.page_content for doc in results])
    
    if not tips.strip():
        return f"Travel info for {destination}: Check weather before visiting."
    
    return f"Travel Tips for {destination}:\n{tips}"
