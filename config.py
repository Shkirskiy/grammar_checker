# config.py - Configuration settings
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Bot API tokens and IDs
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_BASE_URL = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1/chat/completions")
ADMIN_ID = os.getenv("ADMIN_ID")

# User Management
MAX_USERS = int(os.getenv("MAX_USERS", "10"))

# GitHub Repository
GITHUB_REPO_URL = os.getenv("GITHUB_REPO_URL", "https://github.com/yourusername/grammar_check_bot_v2")

# LLM model settings
MODEL_NAME = os.getenv("MODEL_NAME", "openai/chatgpt-4o-latest")

# Bot behavior settings
MESSAGE_COMBINE_DELAY = float(os.getenv("MESSAGE_COMBINE_DELAY", "0.2"))
MAX_MESSAGE_LENGTH = int(os.getenv("MAX_MESSAGE_LENGTH", "4000"))

# Validate required environment variables
if not TELEGRAM_TOKEN:
    raise ValueError("TELEGRAM_TOKEN is required in .env file")
if not OPENROUTER_API_KEY:
    raise ValueError("OPENROUTER_API_KEY is required in .env file")
if not ADMIN_ID:
    raise ValueError("ADMIN_ID is required in .env file")
