from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_core.tools import tool

CHROMA_PATH = "./vector_db/travel_data"

embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
db = Chroma(persist_directory=CHROMA_PATH, embedding_function=embeddings)

@tool
def search_local_knowledge(query: str) -> str:
    """
    Search local vector database for travel-related information.
    """
    results = db.similarity_search(query, k=5)
    return "\n\n".join([doc.page_content for doc in results])