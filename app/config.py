import os

class BaseConfig:
    SECRET_KEY = os.getenv("SECRET_KEY", "change-me-in-prod")
    DEBUG = os.getenv("FLASK_DEBUG", "false").lower() == "true"

    MONGODB_URI = os.getenv("MONGODB_URI", "")
    MONGODB_DB = os.getenv("MONGODB_DB", "sybrantbot")
    MONGODB_COLLECTION = os.getenv("MONGODB_COLLECTION", "appointments")

    MAIL_SERVER = os.getenv("MAIL_SERVER", "smtp.gmail.com")
    MAIL_PORT = int(os.getenv("MAIL_PORT", "587"))
    MAIL_USE_TLS = os.getenv("MAIL_USE_TLS", "true").lower() == "true"
    MAIL_USE_SSL = os.getenv("MAIL_USE_SSL", "false").lower() == "true"
    MAIL_USERNAME = os.getenv("MAIL_USERNAME", "")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD", "")
    MAIL_DEFAULT_SENDER = os.getenv("MAIL_DEFAULT_SENDER", os.getenv("MAIL_USERNAME", ""))

    PINECONE_API_KEY = os.getenv("PINECONE_API_KEY", "")
    PINECONE_INDEX = os.getenv("PINECONE_INDEX", "llama")
    PINECONE_CLOUD = os.getenv("PINECONE_CLOUD", "aws")
    PINECONE_REGION = os.getenv("PINECONE_REGION", "us-west-2")

    OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:3b")
    OLLAMA_TEMPERATURE = float(os.getenv("OLLAMA_TEMPERATURE", "0.1"))
    OLLAMA_NUM_CTX = int(os.getenv("OLLAMA_NUM_CTX", "1024"))
    OLLAMA_NUM_PREDICT = int(os.getenv("OLLAMA_NUM_PREDICT", "150"))
    OLLAMA_TOP_P = float(os.getenv("OLLAMA_TOP_P", "0.8"))
    OLLAMA_TOP_K = int(os.getenv("OLLAMA_TOP_K", "20"))
    OLLAMA_NUM_THREAD = int(os.getenv("OLLAMA_NUM_THREAD", "2"))
    OLLAMA_NUM_GPU = int(os.getenv("OLLAMA_NUM_GPU", "1"))
    USE_GPU = os.getenv("USE_GPU", "true").lower() == "true"

    # Cloud deployment flags
    CLOUD_MODE = os.getenv("CLOUD_MODE", "false").lower() == "true"

    # Groq (cloud LLM)
    GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
    GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-70b-versatile")


def init_app_config(app):
    app.config.from_object(BaseConfig)
    return app


