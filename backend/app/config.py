"""
SecureFlow AI - Configuration Management
Centralizes all application settings with environment variable support.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from project root
env_path = Path(__file__).resolve().parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)


class Settings:
    """Application settings loaded from environment variables."""

    # Project
    APP_NAME: str = "SecureFlow AI"
    APP_VERSION: str = "1.0.0"
    APP_DESCRIPTION: str = "Autonomous Security & IT Operations Agent"
    DEBUG: bool = os.getenv("DEBUG", "true").lower() == "true"

    # AI Provider
    AI_PROVIDER: str = os.getenv("AI_PROVIDER", "multi")
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GROK_API_KEY: str = os.getenv("GROK_API_KEY", "")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")

    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./data/secureflow.db")

    # JWT Auth
    JWT_SECRET: str = os.getenv("JWT_SECRET", "secureflow-dev-secret-change-me")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    JWT_EXPIRY_MINUTES: int = int(os.getenv("JWT_EXPIRY_MINUTES", "1440"))

    # Server
    BACKEND_HOST: str = os.getenv("BACKEND_HOST", "0.0.0.0")
    BACKEND_PORT: int = int(os.getenv("BACKEND_PORT", "8000"))
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:3000")

    # Demo
    DEMO_MODE: bool = os.getenv("DEMO_MODE", "true").lower() == "true"

    # Security
    MAX_INPUT_LENGTH: int = 10000
    RATE_LIMIT_PER_MINUTE: int = 60

    # Detection
    SSH_BRUTE_FORCE_THRESHOLD: int = 5
    SSH_BRUTE_FORCE_WINDOW_SECONDS: int = 300
    PORT_SCAN_THRESHOLD: int = 10
    PORT_SCAN_WINDOW_SECONDS: int = 60
    FAILED_LOGIN_THRESHOLD: int = 10
    FAILED_LOGIN_WINDOW_SECONDS: int = 120

    # Log Ingestion
    LOG_WATCH_DIR: str = os.getenv("LOG_WATCH_DIR", "./data/logs")
    ENABLE_LOG_SIMULATOR: bool = os.getenv("ENABLE_LOG_SIMULATOR", "true").lower() == "true"
    INGESTION_INTERVAL_SECONDS: int = int(os.getenv("INGESTION_INTERVAL_SECONDS", "5"))
    ENABLE_INGESTION: bool = os.getenv("ENABLE_INGESTION", "true").lower() == "true"

    # Knowledge Base
    KNOWLEDGE_DIR: str = os.getenv("KNOWLEDGE_DIR", "./data/knowledge")
    RAG_TOP_K: int = int(os.getenv("RAG_TOP_K", "3"))

    # Security Hardening
    MAX_MESSAGES_PER_MINUTE: int = int(os.getenv("MAX_MESSAGES_PER_MINUTE", "20"))
    MAX_CONTEXT_MESSAGES: int = int(os.getenv("MAX_CONTEXT_MESSAGES", "20"))


settings = Settings()
