# Humanli.ai - Website-Based Chatbot

## Overview
This is an AI-powered chatbot designed to chat exclusively with website content. It accepts a website URL, crawls and extracts its content, creates embeddings, and allows users to ask questions strictly related to that content. Built for the Humanli.ai AI/ML Engineer Assignment.

## Architecture

### System Components
```
User Query
    ↓
Streamlit UI (app.py)
    ├── URL Input & Validation
    ├── Website Crawling (src/crawler.py)
    ├── Embeddings Generation (src/embeddings.py)
    └── Question Answering (src/model.py)
    ↓
Answer (Grounded in Website Content)
```

### Technology Stack
- **Frontend**: [Streamlit](https://streamlit.io/) - Clean, interactive user interface
- **Orchestration**: [LangChain](https://www.langchain.com/) - RAG pipeline management
- **LLM**: **Groq API** (OpenAI GPT-compatible models)
  - **Why Groq?**: Fast inference, free tier available, reliable API, easy integration with LangChain
- **Vector Database**: [ChromaDB](https://www.trychroma.com/)
  - **Why ChromaDB?**: 
    - Lightweight and runs locally (no external infrastructure)
    - Persistent storage to avoid recreating embeddings
    - Built-in similarity search
    - Perfect for RAG applications
- **Embeddings**: `HuggingFace Embeddings` (sentence-transformers/all-MiniLM-L6-v2)
  - **Why HuggingFace?**: Fast, open-source, semantic understanding, no API calls needed
- **Web Crawling**: LangChain's `WebBaseLoader` + BeautifulSoup
  - **Why?**: Simple HTML extraction, proper error handling, USER_AGENT support

## Features
1. **URL Input & Validation**: Robust crawling with proper USER_AGENT headers to prevent rejection
2. **Content Cleaning**: Removes headers, footers, navigation, ads, and duplicate content
3. **RAG Pipeline**: Retrieves semantically similar chunks for accurate answers
4. **Strict Anchoring**: Answers only from website content - no external knowledge
5. **Session Memory**: Maintains conversation context across multiple queries
6. **Error Handling**: Comprehensive error messages for network issues, invalid URLs, empty content

## How It Works

### Step 1: Website Crawling
- User provides URL
- `WebBaseLoader` fetches HTML content
- BeautifulSoup parses and cleans HTML
- Removes structural elements (nav, footer, ads, scripts)
- Deduplicates content

### Step 2: Text Processing
- Content split into semantic chunks (1000 tokens, 200 token overlap)
- Metadata preserved: source URL, page title
- Chunks ready for embedding

### Step 3: Embedding Generation
- Each chunk converted to vector using HuggingFace model
- Embeddings stored persistently in ChromaDB
- Embeddings reused for future queries (no recreation)

### Step 4: Question Answering
- User query converted to embedding
- Similarity search finds top-k relevant chunks
- LLM receives context + conversation history
- Prompt template ensures grounded responses
- If answer not in content, returns: "The answer is not available on the provided website."

## Project Structure
```
Sybrant_Chatbot/
├── app.py                 # Main Streamlit application
├── src/
│   ├── __init__.py
│   ├── crawler.py         # Website crawling & content extraction
│   ├── embeddings.py      # Embeddings & vector storage
│   └── model.py           # LLM integration & QA logic
├── chroma_db/             # Persistent vector database
├── requirements.txt       # Python dependencies
├── .env                   # Environment variables (not in repo)
├── .env.example          # Environment template
├── README.md             # This file
└── ASSIGNMENT_CHECKLIST.md # Requirement verification
```

## Setup & Run Instructions

### Prerequisites
- Python 3.9+ (or use Conda)
- Groq API Key (free tier available at https://console.groq.com)
- ~2GB disk space for vector database

### Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd Sybrant_Chatbot
   ```

2. **Create a virtual environment** (recommended):
   ```bash
   conda create -n resume_ai python=3.11
   conda activate resume_ai
   ```
   
   Or with venv:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up Environment Variables**:
   Create a `.env` file in the root directory:
   ```bash
   cp .env.example .env
   ```
   
   Then edit `.env` and add your Groq API Key:
   ```
   GROQ_API_KEY=your_groq_api_key_here
   ```
   
   Get your key from: https://console.groq.com/keys

### Running the Application
```bash
streamlit run app.py
```

The app will open in your browser at `http://localhost:8501`

### Usage Example
1. Enter your Groq API Key (or set in `.env`)
2. Enter a website URL: `https://docs.python.org/3/`
3. Click "Index Website"
4. Ask questions like: "What is Python?"
5. View answers grounded in the website content

## Configuration & Customization

### Adjusting Chunk Parameters
Edit `src/crawler.py` - `chunk_documents()` function:
```python
def chunk_documents(documents, chunk_size=1000, chunk_overlap=200):
    # Adjust chunk_size and chunk_overlap as needed
    # Larger chunks = more context, slower retrieval
    # Smaller chunks = faster retrieval, less context
```

### Changing Embedding Model
Edit `src/embeddings.py`:
```python
return HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"  # Change this
)
```

### Changing Vector Database
If you want to use FAISS, Qdrant, or Weaviate instead of ChromaDB, modify `src/embeddings.py` to use the appropriate LangChain integration.

## Assumptions & Limitations

### Assumptions
- Websites serve standard HTML (not heavy JavaScript-rendered content)
- URLs are publicly accessible
- Content is in text format (primarily)
- Session memory resets on page refresh (as intended)

### Limitations
- **JavaScript-heavy sites**: `WebBaseLoader` doesn't execute JavaScript. For sites like SPAs, consider using Playwright/Selenium
- **Large websites**: Crawling time scales with content size
- **Memory**: Conversation history is in-session only (no persistence across sessions)
- **Languages**: Embeddings model optimized for English

### Future Improvements
- [ ] Add Playwright for JavaScript-rendered content
- [ ] Implement persistent conversation database
- [ ] Add multi-language support
- [ ] Support for PDFs and other document types
- [ ] Streaming responses for better UX
- [ ] Advanced filtering (date ranges, categories)
- [ ] Caching layer for frequently asked questions
- [ ] Web UI for vector database management

## Testing

### Manual Testing
```bash
# Test URL crawling
python -c "from src.crawler import load_url; docs = load_url('https://example.com'); print(f'Loaded {len(docs)} documents')"

# Test embeddings
python -c "from src.embeddings import load_embeddings; emb = load_embeddings(); print('Embeddings loaded successfully')"
```

### Running the Application
```bash
streamlit run app.py
# Try different websites and questions
```

## Important Notes
- ✅ Answers strictly grounded in website content only
- ✅ No external knowledge or hallucinations
- ✅ No hardcoded answers
- ✅ Modular, clean code architecture
- ✅ Comprehensive error handling

## Troubleshooting

### Issue: "The answer is not available on the provided website."
- This is expected if the information truly isn't on the site
- Try rephrasing your question
- Check if the website was indexed successfully

### Issue: Failed to fetch URL
- Check if URL is valid and publicly accessible
- Some websites block automated crawlers
- Try a different website

### Issue: Slow response
- First query is slower (loading model)
- Subsequent queries are faster
- Large websites take longer to index

## Requirements & Assignment Verification

See `ASSIGNMENT_CHECKLIST.md` for detailed verification that all Humanli.ai assignment requirements are met:
- ✅ All core requirements implemented
- ✅ All deliverables provided
- ✅ Production-ready code quality

## License
This project is for educational purposes as part of the Humanli.ai assignment.

## Contact & Support
For questions or issues, please refer to the assignment guidelines and code documentation.

