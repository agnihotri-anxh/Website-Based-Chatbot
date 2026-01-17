import streamlit as st
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma

PERSIST_DIRECTORY = "./chroma_db"

@st.cache_resource
def load_embeddings() -> HuggingFaceEmbeddings:
    try:
        return HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    except Exception as e:
        raise RuntimeError(f"Failed to load embeddings model: {str(e)}")

embeddings = load_embeddings()

def create_vector_store(chunks: list) -> Chroma:
    if not chunks:
        raise ValueError("No document chunks provided for vector store creation")
    try:
        return Chroma.from_documents(
            documents=chunks,
            embedding=embeddings,
            persist_directory=PERSIST_DIRECTORY
        )
    except Exception as e:
        raise RuntimeError(f"Failed to create vector store: {str(e)}")
