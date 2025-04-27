# app/config.py
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API Keys
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Model Configuration
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")

# Vector Database Configuration
CHROMA_PERSIST_DIRECTORY = os.getenv("CHROMA_PERSIST_DIRECTORY", "./chroma_db")

# Crawler Configuration
MAX_WEBSITES_TO_CRAWL = int(os.getenv("MAX_WEBSITES_TO_CRAWL", 10))
MAX_DEPTH = int(os.getenv("MAX_DEPTH", 2))
USER_AGENT = "SemanticSearchBot/1.0"

# Search Configuration
TOP_K_RESULTS = 10
SIMILARITY_THRESHOLD = 0.6