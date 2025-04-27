# app/__init__.py
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Ensure required directories exist
os.makedirs("app/static/css", exist_ok=True)
os.makedirs("app/static/js", exist_ok=True)
os.makedirs("templates", exist_ok=True)

# Create ChromaDB persist directory if it doesn't exist
chroma_dir = os.getenv("CHROMA_PERSIST_DIRECTORY", "./chroma_db")
os.makedirs(chroma_dir, exist_ok=True)