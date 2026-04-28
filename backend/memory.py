"""
Session memory management for maintaining conversation history.
"""
from datetime import datetime

session_store = {}


def get_session(session_id: str):
    """
    Get or create a session for a given session_id.
    Sessions persist across multiple API calls to maintain conversation history.
    """
    if session_id not in session_store:
        session_store[session_id] = {
            "messages": [],
            "created_at": datetime.now().isoformat(),
            "last_accessed": datetime.now().isoformat(),
            "turn_count": 0
        }
    
    # Update last access time
    session_store[session_id]["last_accessed"] = datetime.now().isoformat()
    session_store[session_id]["turn_count"] += 1
    
    return session_store[session_id]["messages"]


def clear_session(session_id: str):
    """Clear all messages from a session."""
    if session_id in session_store:
        session_store[session_id]["messages"] = []


def delete_session(session_id: str):
    """Delete an entire session."""
    if session_id in session_store:
        del session_store[session_id]


def get_session_info(session_id: str):
    """Get metadata about a session."""
    if session_id in session_store:
        info = session_store[session_id].copy()
        info["message_count"] = len(info["messages"])
        return info
    return None


def list_sessions():
    """List all active sessions with their metadata."""
    sessions_summary = {}
    for session_id, session_data in session_store.items():
        sessions_summary[session_id] = {
            "messages": len(session_data["messages"]),
            "created_at": session_data["created_at"],
            "last_accessed": session_data["last_accessed"],
            "turns": session_data["turn_count"]
        }
    return sessions_summary
