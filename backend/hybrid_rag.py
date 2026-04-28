import wikipedia
from langchain_core.tools import tool
from backend.vector_tools import search_local_knowledge

@tool
def hybrid_search(query: str) -> str:
    """
    Combine vector database and Wikipedia search results.
    """
    try:
        wiki = wikipedia.summary(query, sentences=3)
    except:
        wiki = "No Wikipedia data found."

    local = search_local_knowledge.invoke(query)

    return f"""
=== LOCAL DATA ===
{local}

=== WIKIPEDIA ===
{wiki}
"""