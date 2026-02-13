"""
InsightForge - Configuration Module
Centralized configuration management for the application.
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Config:
    """Application configuration loaded from environment variables."""

    # ── OpenAI ──────────────────────────────────────────────
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    # ── Embeddings ──────────────────────────────────────────
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")

    # ── RAG Settings ────────────────────────────────────────
    CHUNK_SIZE: int = int(os.getenv("CHUNK_SIZE", "1000"))
    CHUNK_OVERLAP: int = int(os.getenv("CHUNK_OVERLAP", "200"))
    TOP_K_RESULTS: int = 5

    # ── File Upload ─────────────────────────────────────────
    MAX_UPLOAD_SIZE_MB: int = int(os.getenv("MAX_UPLOAD_SIZE_MB", "200"))
    ALLOWED_EXTENSIONS: list = ["csv", "xlsx", "xls", "pdf", "docx", "txt", "json", "png", "jpg", "jpeg"]

    # ── Paths ───────────────────────────────────────────────
    BASE_DIR: str = os.path.dirname(os.path.abspath(__file__))
    DATA_DIR: str = os.path.join(BASE_DIR, "data")
    UPLOAD_DIR: str = os.path.join(DATA_DIR, "uploads")
    VECTOR_STORE_DIR: str = os.path.join(DATA_DIR, "vector_store")
    SAMPLE_DATA_DIR: str = os.path.join(DATA_DIR, "sample")

    # ── Streamlit Page Config ───────────────────────────────
    PAGE_TITLE: str = "InsightForge BI Assistant"
    PAGE_ICON: str = "📊"
    LAYOUT: str = "wide"

    @classmethod
    def ensure_directories(cls):
        """Create necessary directories if they don't exist."""
        for directory in [cls.DATA_DIR, cls.UPLOAD_DIR, cls.VECTOR_STORE_DIR, cls.SAMPLE_DATA_DIR]:
            os.makedirs(directory, exist_ok=True)

    @classmethod
    def is_api_key_set(cls) -> bool:
        """Check if OpenAI API key is configured."""
        return bool(cls.OPENAI_API_KEY) and cls.OPENAI_API_KEY != "your-openai-api-key-here"


# Create directories on import
Config.ensure_directories()
