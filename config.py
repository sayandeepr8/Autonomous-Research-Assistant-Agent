"""
Configuration module for the Autonomous Research Assistant.
Loads environment variables and provides application-wide settings.
"""
import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Application configuration."""
    SECRET_KEY = os.getenv("SECRET_KEY", "research-assistant-secret-key-2026")
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL = "gemini-2.0-flash"

    # arXiv API settings
    ARXIV_API_URL = "http://export.arxiv.org/api/query"
    ARXIV_MAX_RESULTS = 15
    ARXIV_SORT_BY = "relevance"

    # Agent settings
    MAX_ITERATIONS = 3  # Max critic loop iterations
    MIN_COVERAGE_SCORE = 7  # Minimum coverage score (out of 10) to stop iterating
    MAX_PAPERS_PER_QUERY = 10

    # Report settings
    REPORT_OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "reports")
