import os
import re
from bs4 import BeautifulSoup
from langchain_community.document_loaders import WebBaseLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

def load_url(url: str):
    if not os.environ.get('USER_AGENT'):
        os.environ['USER_AGENT'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    try:
        docs = WebBaseLoader(url).load()
        if not docs:
            raise ValueError(f"No content found at URL: {url}")
        return docs
    except Exception as e:
        raise RuntimeError(f"Failed to fetch URL '{url}': {str(e)}")

def clean_html(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["header", "footer", "nav", "aside", "script", "style"]):
        tag.decompose()
    text = soup.get_text(separator="\n")
    text = re.sub(r"\n\s*\n+", "\n\n", text)
    return text.strip()

def clean_documents(documents: list) -> list:
    cleaned, seen = [], set()
    for doc in documents:
        text = clean_html(doc.page_content)
        if text and text not in seen:
            seen.add(text)
            cleaned.append(Document(
                page_content=text,
                metadata={
                    "source": doc.metadata.get("source", ""),
                    "title": doc.metadata.get("title", "Unknown")
                }
            ))
    return cleaned
def chunk_documents(documents: list, chunk_size: int = 1000, chunk_overlap: int = 200) -> list:
    return RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap
    ).split_documents(documents)
