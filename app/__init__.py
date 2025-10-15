import os
import re
import logging
from datetime import datetime

from flask import Flask, request, jsonify, render_template
from flask_mail import Mail
from pymongo import MongoClient
from langchain.schema import HumanMessage, SystemMessage

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

from .config import init_app_config
from .services.ingest import ingest_links
from .services.mail_set import configure_mail, send_appointment_confirmation


app = Flask(
    __name__,
    template_folder=os.path.join(os.path.dirname(__file__), '..', 'templates')
)
init_app_config(app)

# Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger("sybrantbot")

# Config
cloud_mode = app.config.get("CLOUD_MODE", False)
index_name = app.config.get("PINECONE_INDEX")
pinecone_api_key = app.config.get("PINECONE_API_KEY")

embeddings = None
if not cloud_mode:
    try:
        from langchain_community.embeddings import HuggingFaceEmbeddings
        embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-mpnet-base-v2",
            model_kwargs={'device': 'cpu'}
        )
    except Exception:
        embeddings = None

# Email configuration via helper
mail = configure_mail(app)

# MongoDB setup - configurable via environment variable and validated at startup
mongo_uri = app.config.get("MONGODB_URI", "")
db_available = False
appointments_collection = None
try:
    if not mongo_uri:
        raise RuntimeError("MONGODB_URI is not configured")
    mongo_client = MongoClient(mongo_uri, serverSelectionTimeoutMS=4000)
    mongo_client.admin.command("ping")
    db = mongo_client[app.config.get("MONGODB_DB")]
    appointments_collection = db[app.config.get("MONGODB_COLLECTION")]
    db_available = True
except Exception as e:
    logger.warning(f"MongoDB connection failed: {e}")
    db_available = False

# Pinecone setup (disabled in cloud mode)
vectorstore = None
if not cloud_mode and pinecone_api_key and embeddings is not None:
    try:
        from pinecone import Pinecone, ServerlessSpec
        from langchain_pinecone import Pinecone as PineconeVectorStore
        pc = Pinecone(api_key=pinecone_api_key)
        if index_name not in [ix.name for ix in pc.list_indexes()]:
            pc.create_index(
                name=index_name,
                dimension=768,
                metric="cosine",
                spec=ServerlessSpec(cloud=app.config.get("PINECONE_CLOUD"), region=app.config.get("PINECONE_REGION")),
            )
        vectorstore = PineconeVectorStore(index_name=index_name, embedding=embeddings)
    except Exception:
        vectorstore = None

# LLM setup - Groq for cloud, Ollama for local
llm = None
if cloud_mode:
    try:
        from langchain_groq import ChatGroq
        llm = ChatGroq(
            api_key=app.config.get("GROQ_API_KEY"),
            model_name=app.config.get("GROQ_MODEL", "llama-3.1-70b-versatile"),
            temperature=app.config.get("OLLAMA_TEMPERATURE"),
        )
    except Exception as _e:
        logger = logging.getLogger("sybrantbot")
        logger.error(f"Groq init failed: {_e}")
        llm = None
else:
    try:
        from langchain_ollama import ChatOllama
        llm = ChatOllama(
            model=app.config.get("OLLAMA_MODEL"),
            temperature=app.config.get("OLLAMA_TEMPERATURE"),
            num_ctx=app.config.get("OLLAMA_NUM_CTX"),
            num_predict=app.config.get("OLLAMA_NUM_PREDICT"),
            top_p=app.config.get("OLLAMA_TOP_P"),
            top_k=app.config.get("OLLAMA_TOP_K"),
            num_thread=app.config.get("OLLAMA_NUM_THREAD"),
            num_gpu=app.config.get("OLLAMA_NUM_GPU"),
        )
    except Exception as _e:
        logger = logging.getLogger("sybrantbot")
        logger.error(f"Ollama init failed: {_e}")
        llm = None

# Cache and session storage
cache = {}
appointment_sessions = {}


def handle_appointment_booking(query, session_id):
    """Handle appointment booking conversation flow"""
    session_data = appointment_sessions[session_id]["data"]
    
    if ',' in query:
        parts = [p.strip() for p in query.split(',')]
        for part in parts:
            if '@' in part and not session_data.get("email"):
                session_data["email"] = part
            elif re.search(r'\d{7,}', part) and not session_data.get("phone"):
                session_data["phone"] = part
            elif any(word in part.lower() for word in ["consultation", "meeting", "help", "service"]) and not session_data.get("subject"):
                session_data["subject"] = part
            elif not session_data.get("name") and not '@' in part and not re.search(r'\d{7,}', part):
                session_data["name"] = part.title()
    else:
        if '@' in query and not session_data.get("email"):
            session_data["email"] = query
        elif re.search(r'\d{7,}', query) and not session_data.get("phone"):
            session_data["phone"] = query
        elif not session_data.get("name") and not '@' in query and not re.search(r'\d{7,}', query):
            session_data["name"] = query.title()
        elif not session_data.get("subject"):
            session_data["subject"] = query
    
    missing_fields = []
    if not session_data.get("name"):
        missing_fields.append("name")
    if not session_data.get("email"):
        missing_fields.append("email")
    if not session_data.get("phone"):
        missing_fields.append("phone")
    if not session_data.get("subject"):
        missing_fields.append("subject")
    
    if missing_fields:
        field_name = missing_fields[0]
        
        if field_name == "name":
            response = f"What's your full name?"
        elif field_name == "email":
            if session_data.get('name'):
                response = f"Thank you, {session_data.get('name')}! What's your email address?"
            else:
                response = f"What's your email address?"
        elif field_name == "phone":
            if session_data.get('name'):
                response = f"Perfect! What's your phone number?"
            else:
                response = f"What's your phone number?"
        elif field_name == "subject":
            if session_data.get('name'):
                response = f"Excellent! What's the subject or reason for the appointment?"
            else:
                response = f"What's the subject or reason for the appointment?"
    else:
        try:
            if not db_available or appointments_collection is None:
                raise RuntimeError("Database is not available")
            appointment_doc = {
                'name': session_data["name"],
                'email': session_data["email"],
                'phone': session_data["phone"],
                'subject': session_data["subject"],
                'message': session_data.get("message", ""),
                'status': 'confirmed',
                'created_at': datetime.now(),
                'session_id': session_id
            }
            result = appointments_collection.insert_one(appointment_doc)
            appointment_id = str(result.inserted_id)
            
            appointment_sessions[session_id]["booking"] = False
            appointment_sessions[session_id]["data"] = {}
            
            email_sent = False
            try:
                email_sent = send_appointment_confirmation(
                    mail=mail,
                    app=app,
                    to_email=session_data['email'],
                    name=session_data['name'],
                    phone=session_data['phone'],
                    subject=session_data['subject'],
                    appointment_id=appointment_id,
                )
            except Exception as email_error:
                logger.error(f"Email sending error: {email_error}")
                email_sent = False
            
            response = (f"✅ Appointment booked successfully!\n\n"
                       f"Appointment ID: #{appointment_id}\n"
                       f"Name: {session_data['name']}\n"
                       f"Email: {session_data['email']}\n"
                       f"Phone: {session_data['phone']}\n"
                       f"Subject: {session_data['subject']}\n\n"
                       f"{'Confirmation email sent!' if email_sent else 'Email sending failed, but appointment is booked.'}\n\n"
                       f"Our team will contact you within 24 hours. Is there anything else I can help you with?")
            
        except Exception as e:
            logger.error(f"Database error: {e}")
            response = (
                "❌ Sorry, we couldn't save your appointment right now. "
                "Our system is experiencing a database issue. Please try again later "
                "or contact us directly at +91-44-2445-3822."
            )
    
    return jsonify({"answer": response, "sources": []})


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/admin")
def admin():
    return render_template("appointments.html")


@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    query = data.get("message", "").strip()
    session_id = data.get("session_id", "default")

    if not query:
        return jsonify({"error": "Empty message"}), 400

    if query.lower() in cache:
        return jsonify({"answer": cache[query.lower()], "sources": []})

    if session_id not in appointment_sessions:
        appointment_sessions[session_id] = {"booking": False, "data": {}}

    if any(keyword in query.lower() for keyword in [
        "book appointment",
        "book a meeting",
        "schedule appointment",
        "appointment",
    ]):
        appointment_sessions[session_id]["booking"] = True
        appointment_sessions[session_id]["data"] = {}

        response = (
            "I'd be happy to help you book an appointment with Sybrant Technologies! 📅\n\n"
            "Let me collect your information step by step.\n\n"
            "What's your full name?"
        )

        return jsonify({"answer": response, "sources": []})

    if appointment_sessions[session_id]["booking"]:
        return handle_appointment_booking(query, session_id)

    docs = []
    if vectorstore:
        try:
            docs = vectorstore.similarity_search(query, k=2)
        except Exception:
            docs = []

    if query.lower().strip() in {"hi", "hello", "hey", "good morning", "good evening", "good afternoon"}:
        if not hasattr(chat, "greeted"):
            chat.greeted = True
            intro = (
                "Hello! I'm SybrantBot, your assistant for Sybrant's data solutions. "
                "I can help with data management, AI processing, and analytics services. "
                "You can also type 'book appointment' to schedule a consultation. "
                "How may I assist you?"
            )
            return jsonify({"answer": intro, "sources": []})
        else:
            return jsonify({"answer": "Hello again! How can I help you?", "sources": []})

    context = ""
    if docs:
        context = "\n".join([d.page_content[:300] for d in docs[:2]])

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
- If someone wants to book an appointment, guide them to type "book appointment"

TONE: Professional, knowledgeable, and customer-focused. Always represent Sybrant as a trusted data solutions partner."""),
        HumanMessage(content=f"Context: {context}\n\nQuestion: {query}")
    ]

    try:
        if llm is None:
            raise RuntimeError("LLM not initialized")
        response = llm.invoke(messages)
        answer = getattr(response, "content", str(response))
    except Exception as e:
        logger.error(f"LLM Error: {e}")
        answer = "I'm experiencing technical difficulties. Please try again or contact us directly at +91-44-2445-3822."

    answer = answer.strip()
    answer = answer.replace('*', '').replace('_', '').replace('`', '')
    import re as _re
    answer = _re.sub(r'\s+', ' ', answer)

    if not answer:
        answer = "We don't have that information. Please contact us for more details."
    elif len(answer) < 30:
        answer = f"Sybrant provides comprehensive data solutions and AI services. {answer}"

    if not answer.endswith('.') and not answer.endswith('!') and not answer.endswith('?'):
        answer += "."

    cache[query.lower()] = answer

    return jsonify({"answer": answer, "sources": [d.metadata for d in docs]})


@app.route("/appointments", methods=["GET"])
def view_appointments():
    try:
        if not db_available or appointments_collection is None:
            return jsonify({"success": False, "error": "Database not available"}), 503
        appointments = list(appointments_collection.find({}, {'_id': 1, 'name': 1, 'email': 1, 'phone': 1, 'subject': 1, 'status': 1, 'created_at': 1}))
        for appointment in appointments:
            appointment['_id'] = str(appointment['_id'])
            appointment['created_at'] = appointment['created_at'].strftime('%Y-%m-%d %H:%M:%S')
        return jsonify({
            "success": True,
            "count": len(appointments),
            "appointments": appointments
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/appointments/<appointment_id>", methods=["GET"])
def view_appointment(appointment_id):
    try:
        if not db_available or appointments_collection is None:
            return jsonify({"success": False, "error": "Database not available"}), 503
        from bson import ObjectId
        appointment = appointments_collection.find_one({'_id': ObjectId(appointment_id)})
        if not appointment:
            return jsonify({"success": False, "error": "Appointment not found"}), 404
        appointment['_id'] = str(appointment['_id'])
        appointment['created_at'] = appointment['created_at'].strftime('%Y-%m-%d %H:%M:%S')
        return jsonify({
            "success": True,
            "appointment": appointment
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# Dev server helper
def run_dev():
    app.run(host="0.0.0.0", port=5000, debug=app.config.get("DEBUG"))


