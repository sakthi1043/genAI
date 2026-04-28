import os
import pandas as pd
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

INPUT_DIRECTORY = "data/static_rag"
CHROMA_PATH = "./vector_db/travel_data"

embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

def ingest_all_csvs():
    db = Chroma(persist_directory=CHROMA_PATH, embedding_function=embeddings)

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50
    )

    for file in os.listdir(INPUT_DIRECTORY):
        if file.endswith(".csv"):
            path = os.path.join(INPUT_DIRECTORY, file)
            df = pd.read_csv(path)

            df = df.dropna(how="all").fillna("Unknown").drop_duplicates()

            documents = []
            for _, row in df.iterrows():
                content = " | ".join([f"{k}: {v}" for k, v in row.items()])
                documents.append(Document(page_content=content, metadata={"source": file}))

            chunks = splitter.split_documents(documents)
            db.add_documents(chunks)

    print("Data ingested into Vector DB")

if __name__ == "__main__":
    ingest_all_csvs()