import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Iterable, List

import requests
from bs4 import BeautifulSoup
from langchain.docstore.document import Document
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_pinecone import Pinecone as PineconeVectorStore

from pinecone import Pinecone, ServerlessSpec


def fetch_text(url: str, timeout: int = 20) -> str:
    try:
        r = requests.get(url, timeout=timeout)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        for tag in soup(["script", "style", "noscript", "header", "footer", "nav"]):
            tag.extract()
        text = soup.get_text("\n")
        lines = [ln.strip() for ln in text.splitlines()]
        lines = [ln for ln in lines if ln]
        return "\n".join(lines)
    except Exception:
        return ""


def paragraph_chunk(text: str, chunk_size: int = 800, chunk_overlap: int = 120) -> List[str]:
    if not text:
        return []
    paragraphs = text.split("\n\n")
    chunks, buf, cur_len = [], [], 0
    for p in paragraphs:
        p = p.strip()
        if not p:
            continue
        if cur_len + len(p) + 1 > chunk_size and buf:
            chunk_text = "\n\n".join(buf)
            chunks.append(chunk_text)
            overlap_text = chunk_text[-chunk_overlap:]
            buf = [overlap_text, p]
            cur_len = len(overlap_text) + len(p) + 1
        else:
            buf.append(p)
            cur_len += len(p) + 1
    if buf:
        chunks.append("\n\n".join(buf))
    return chunks


def ensure_index(pc: Pinecone, index_name: str, dimension: int = 768, cloud: str = "aws", region: str = "us-west-2") -> None:
    if index_name not in [ix.name for ix in pc.list_indexes()]:
        pc.create_index(
            name=index_name,
            dimension=dimension,
            metric="cosine",
            spec=ServerlessSpec(cloud=cloud, region=region),
        )


def ingest_links(links: Iterable[str], index_name: str, pinecone_api_key: str, chunk_size: int = 800, chunk_overlap: int = 120, max_workers: int = 8) -> int:
    pc = Pinecone(api_key=pinecone_api_key)
    ensure_index(pc, index_name)

    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-mpnet-base-v2")

    vectorstore = PineconeVectorStore(index_name=index_name, embedding=embeddings)

    # Concurrent fetch
    texts = {}
    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        futures = {ex.submit(fetch_text, url): url for url in links}
        for fut in as_completed(futures):
            url = futures[fut]
            try:
                texts[url] = fut.result()
            except Exception:
                texts[url] = ""

    documents: List[Document] = []
    for url, txt in texts.items():
        for c in paragraph_chunk(txt, chunk_size=chunk_size, chunk_overlap=chunk_overlap):
            documents.append(Document(page_content=c, metadata={"url": url, "text": c}))

    if not documents:
        return 0

    vectorstore.add_documents(documents)

    return len(documents)


