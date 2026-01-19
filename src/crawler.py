import os
import re
from bs4 import BeautifulSoup
from langchain_community.document_loaders import WebBaseLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

def load_url(url: str):
    if not os.environ.get("USER_AGENT"):
        os.environ["USER_AGENT"] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    docs = WebBaseLoader(url).load()
    if not docs:
        raise RuntimeError("No content fetched from URL")
    return docs

def clean_html(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")

    for tag in soup(["script", "style"]):
        tag.decompose()

    text = soup.get_text(separator="\n")
    text = re.sub(r"\n\s*\n+", "\n\n", text)
    return text.strip()

def clean_documents(documents: list) -> list:
    cleaned = []
    for doc in documents:
        text = clean_html(doc.page_content)
        if text:
            cleaned.append(
                Document(
                    page_content=text,
                    metadata=doc.metadata
                )
            )
    return cleaned

def chunk_documents(documents: list, chunk_size: int = 800, chunk_overlap: int = 150) -> list:
    return RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap
    ).split_documents(documents)
