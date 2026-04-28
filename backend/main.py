from fastapi import FastAPI
from pydantic import BaseModel
from backend.agent import generate_itinerary, run_agent
from backend.memory import get_session_info, list_sessions
from fastapi.middleware.cors import CORSMiddleware
import logging

app = FastAPI()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Allow React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class TravelRequest(BaseModel):
    source: str
    destination: str
    budget: int
    days: int
    food: str
    travelers: int

class ChatMessage(BaseModel):
    message: str
    session_id: str = "default"

@app.post("/generate")
def generate(data: TravelRequest):
    """Generate a travel itinerary based on user preferences"""
    try:
        logger.info(f"Generating itinerary: {data.source} -> {data.destination}")
        result = generate_itinerary(
            data.source,
            data.destination,
            str(data.budget),
            data.days,
            data.food,
            data.travelers,
        )
        # result is now a dict with "format" and "data" keys
        return {"plan": result}
    except Exception as e:
        logger.error(f"Error generating itinerary: {str(e)}", exc_info=True)
        return {"plan": {"format": "text", "data": f"Error generating itinerary: {str(e)}"}, "error": True}

@app.post("/chat")
def chat(msg: ChatMessage):
    """Handle follow-up questions and chat interactions while maintaining conversation history"""
    try:
        logger.info(f"Chat message on session {msg.session_id}: {msg.message[:100]}")
        result = run_agent(msg.message, session_id=msg.session_id)
        logger.info(f"Chat response generated for session {msg.session_id}")
        return {"response": result}
    except Exception as e:
        logger.error(f"Error in chat for session {msg.session_id}: {str(e)}", exc_info=True)
        return {"response": f"Error processing your question: {str(e)}", "error": True}

@app.get("/session/{session_id}")
def get_session_status(session_id: str):
    """Debug endpoint to check session status"""
    try:
        info = get_session_info(session_id)
        if info:
            return {"session_id": session_id, "info": info}
        else:
            return {"session_id": session_id, "status": "not_found"}
    except Exception as e:
        logger.error(f"Error getting session info: {str(e)}")
        return {"error": str(e)}

@app.get("/sessions")
def get_all_sessions():
    """Debug endpoint to list all active sessions"""
    try:
        sessions = list_sessions()
        return {"sessions": sessions, "total": len(sessions)}
    except Exception as e:
        logger.error(f"Error listing sessions: {str(e)}")
        return {"error": str(e)}