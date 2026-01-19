import streamlit as st
import os
from dotenv import load_dotenv
from src.crawler import load_url, clean_documents, chunk_documents
from src.embeddings import create_vector_store
from src.model import setup_qa_chain, ask_question

load_dotenv()

st.set_page_config(page_title="Humanli.ai Website Chatbot", page_icon="🤖")
st.title("Website-Based Chatbot")
st.markdown("Chat **only** with the content of a website.")

groq_api_key = os.getenv("GROQ_API_KEY")
if not groq_api_key:
    st.error(" GROQ_API_KEY not found. Please add it to .env file")
    st.stop()

with st.sidebar:
    st.header("Configuration")
    url = st.text_input("Website URL", placeholder="https://example.com")
    process = st.button("Index Website")

if "qa_chain" not in st.session_state:
    st.session_state.qa_chain = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if process and url:
    try:
        with st.spinner("Processing website..."):
            docs = load_url(url)
            if not docs:
                st.error("Failed to fetch the website. Please check the URL and try again.")
            else:
                cleaned = clean_documents(docs)
                if not cleaned:
                    st.error("No usable content found on the website.")
                else:
                    chunks = chunk_documents(cleaned)
                    vectorstore = create_vector_store(chunks)
                    st.session_state.qa_chain = setup_qa_chain(vectorstore, groq_api_key)
                    st.session_state.chat_history = []
                    st.success("Website indexed successfully!")
    except Exception as e:
        st.error(f"Error processing website: {str(e)}")

if st.session_state.qa_chain:
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
    question = st.chat_input("Ask a question about the website")
    if question:
        st.session_state.chat_history.append({"role": "user", "content": question})
        with st.chat_message("assistant"):
            answer = ask_question(st.session_state.qa_chain, question)
            st.markdown(answer)
            st.session_state.chat_history.append({"role": "assistant", "content": answer})
