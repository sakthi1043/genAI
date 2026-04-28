# app.py

import os
import json
import logging
from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_groq import ChatGroq

# ================= CONFIG =================
DATA_PATH = "data"
DB_PATH = "./vector_db/travel_data"

# ================= FASTAPI =================
app = FastAPI()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

# ================= LOAD FILES =================
def load_documents():
    docs = []
    for file in os.listdir(DATA_PATH):
        path = os.path.join(DATA_PATH, file)

        if file.endswith(".pdf"):
            loader = PyPDFLoader(path)
        elif file.endswith(".txt"):
            loader = TextLoader(path)
        else:
            continue

        docs.extend(loader.load())

    return docs

# ================= CREATE DB =================
def create_db():
    docs = load_documents()

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=100
    )

    chunks = splitter.split_documents(docs)

    embedding = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )

    db = Chroma.from_documents(
        documents=chunks,
        embedding=embedding,
        persist_directory=DB_PATH
    )

    db.persist()
    return db

# ================= LOAD DB =================
def load_db():
    embedding = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )

    return Chroma(
        persist_directory=DB_PATH,
        embedding_function=embedding
    )

# ================= DOMAIN CHECK =================
def is_out_of_domain(docs, destination):
    combined = " ".join([d.page_content.lower() for d in docs])
    return destination.lower() not in combined

# ================= CORE FUNCTION =================
def generate_itinerary(source, destination, budget, days, food, travelers):
    db = load_db()
    retriever = db.as_retriever(search_kwargs={"k": 4})

    query = f"{destination} travel plan"
    docs = retriever.invoke(query)

    # 🚨 STRICT RULE
    if len(docs) == 0 or is_out_of_domain(docs, destination):
        return {"error": "out of domain"}

    context = "\n\n".join([d.page_content for d in docs])

    llm = ChatGroq(
        groq_api_key=GROQ_API_KEY,
        model_name="llama3-70b-8192",
        temperature=0
    )

    prompt = f"""
Generate a complete {days}-day travel itinerary from {source} to {destination}.

IMPORTANT RULES:
- Use ONLY the given context
- Do NOT assume anything
- If destination not found → return:
{{ "error": "out of domain" }}

- Output ONLY JSON

CONTEXT:
{context}

Trip Details:
- Source: {source}
- Destination: {destination}
- Total Budget: {budget} INR ({travelers} traveler(s))
- Duration: {days} days
- Food Preference: {food}
- Per person per day budget: {int(budget)//int(travelers)//int(days)} INR

OUTPUT FORMAT:
{{
  "trip_plan": [
    {{
      "day": 1,
      "activities": [],
      "food": [],
      "stay": "",
      "transport": ""
    }}
  ]
}}
"""

    response = llm.invoke(prompt)

    try:
        return json.loads(response.content)
    except:
        return {"error": "invalid response from model"}

# ================= API =================
@app.post("/generate")
def generate(data: TravelRequest):
    try:
        logger.info(f"{data.source} -> {data.destination}")

        result = generate_itinerary(
            data.source,
            data.destination,
            data.budget,
            data.days,
            data.food,
            data.travelers,
        )

        return {"plan": result}

    except Exception as e:
        logger.error(str(e), exc_info=True)
        return {"plan": {"error": str(e)}, "error": True}

# ================= STARTUP =================
@app.on_event("startup")
def startup():
    if not os.path.exists(DB_PATH):
        logger.info("Creating vector DB...")
        create_db()
    else:
        logger.info("Vector DB already exists")