import os
from flask import Flask, request, jsonify, render_template
from pinecone import Pinecone, ServerlessSpec
from langchain_pinecone import Pinecone as PineconeVectorStore
from langchain_ollama import ChatOllama
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.schema import HumanMessage, SystemMessage
from ingest import ingest_links

app = Flask(__name__)

# Config
index_name = os.getenv("PINECONE_INDEX", "llama")
pinecone_api_key = os.getenv("PINECONE_API_KEY")
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-mpnet-base-v2")

# Pinecone setup
vectorstore = None
if pinecone_api_key:
    pc = Pinecone(api_key=pinecone_api_key)
    if index_name not in [ix.name for ix in pc.list_indexes()]:
        pc.create_index(name=index_name, dimension=768, metric="cosine", 
                       spec=ServerlessSpec(cloud="aws", region="us-west-2"))
    vectorstore = PineconeVectorStore(index_name=index_name, embedding=embeddings)

# LLM setup - ultra-fast with professional output
llm = ChatOllama(
    model="llama3.2:1b",  # Lightweight 1B model for stability
    temperature=0.2,      # Lower for consistency
    num_ctx=512,          # Small context for stability
    num_predict=100,      # Shorter responses for speed
    top_p=0.7,           # Conservative settings
    top_k=15,            # Conservative settings
    num_thread=1,        # Single thread to avoid conflicts
    num_gpu=0            # Disable GPU completely
)

# Cache
cache = {}

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    query = data.get("message", "").strip()
    
    if not query:
        return jsonify({"error": "Empty message"}), 400

    # Check cache
    if query.lower() in cache:
        return jsonify({"answer": cache[query.lower()], "sources": []})

    # Get context - ultra-fast processing
    docs = []
    if vectorstore:
        try:
            docs = vectorstore.similarity_search(query, k=2)  # Reduced for speed
        except:
            docs = []

    # Only keep essential instant responses for greetings
    if query.lower().strip() in {"hi", "hello", "hey", "good morning", "good evening", "good afternoon"}:
        if not hasattr(chat, 'greeted'):
            chat.greeted = True
            intro = ("Hello! I'm SybrantBot, your assistant for Sybrant's data solutions. "
                    "I can help with data management, AI processing, and analytics services. "
                    "How may I assist you?")
            return jsonify({"answer": intro, "sources": []})
        else:
            return jsonify({"answer": "Hello again! How can I help you?", "sources": []})

    # Process context - minimal processing for speed
    context = ""
    if docs:
        context = "\n".join([d.page_content[:300] for d in docs[:2]])  # Shorter snippets

    # Generate response - professional and customer-focused
    messages = [
        SystemMessage(content="""You are SybrantBot, the official AI assistant for Sybrant Technologies. You are an expert in data solutions and business intelligence.

COMPANY INFORMATION:
- Sybrant Technologies is a leading data solutions provider
- Founded to help businesses optimize their data processes
- Specializes in AI-powered data management and analytics

CORE SERVICES (Always mention these when relevant):
1. Data Management & Integration - End-to-end data solutions without overhead
2. AI-Powered Financial Data Processing - Automated financial data extraction
3. Intelligent Invoice Processing - AI-driven invoice automation
4. Advanced Lead Generation - AI-powered lead identification and qualification
5. Business Intelligence & Analytics - Data-driven insights and decision-making
6. Regulatory Compliance & Reporting - GDPR and regulatory compliance services

CONTACT INFORMATION (Always provide when asked):
- Phone: +91-44-2445-3822 (India) / +1-949-620-1643 (US)
- Email: connect@sybrant.com
- LinkedIn: https://www.linkedin.com/company/sybrant-technologies

OFFICE LOCATIONS (Always provide both when asked about location):
- India: 22/2, Sardar Patel Road, Adyar, Chennai - 600020, India
- United States: 5, Corporate Park, Suite 140, Irvine, CA 92606

RESPONSE GUIDELINES:
- Always be professional, helpful, and customer-focused
- Provide detailed, accurate information about Sybrant's services
- If asked about unrelated topics, politely redirect to Sybrant's services
- Always encourage next steps like demos, consultations, or contact
- Use clean, professional text without special characters or bullet points
- Never say you cannot provide business information (office locations, contact details, services)
- Always be specific about Sybrant's offerings and capabilities
- End responses with engagement questions when appropriate

TONE: Professional, knowledgeable, and customer-focused. Always represent Sybrant as a trusted data solutions partner."""),
        HumanMessage(content=f"Context: {context}\n\nQuestion: {query}")
    ]
    
    # Generate response with error handling
    try:
        response = llm.invoke(messages)
        answer = getattr(response, "content", str(response))
    except Exception as e:
        print(f"LLM Error: {e}")
        # Fallback to simple response
        answer = "I'm experiencing technical difficulties. Please try again or contact us directly at +91-44-2445-3822."
    
    # Clean and enhance response for professionalism
    answer = answer.strip()
    
    # Remove unwanted formatting characters
    answer = answer.replace('*', '').replace('_', '').replace('`', '')
    
    # Clean up multiple spaces and line breaks
    import re
    answer = re.sub(r'\s+', ' ', answer)
    
    if not answer:
        answer = "We don't have that information. Please contact us for more details."
    elif len(answer) < 30:
        answer = f"Sybrant provides comprehensive data solutions and AI services. {answer}"
    
    # Ensure professional tone
    if not answer.endswith('.') and not answer.endswith('!') and not answer.endswith('?'):
        answer += "."
    
    # Cache response
    cache[query.lower()] = answer
    
    return jsonify({"answer": answer, "sources": [d.metadata for d in docs]})

@app.route("/ingest", methods=["POST"])
def ingest():
    if not vectorstore:
        return jsonify({"error": "Pinecone not configured"}), 400
    
    try:
        with open("essential_links.txt", "r") as f:
            links = [line.strip() for line in f if line.strip()]
        
        count = ingest_links(links, index_name, pinecone_api_key)
        return jsonify({"ingested": count, "links": len(links)})
    except Exception as e:
        return jsonify({"error": str(e)}), 400

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)