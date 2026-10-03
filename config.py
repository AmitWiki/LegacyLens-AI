import os
from dotenv import load_dotenv

load_dotenv()

# OpenRouter Configuration
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

# Primary & Fallback Free Models on OpenRouter
FREE_MODELS = [
    "meta-llama/llama-3.3-70b-instruct:free",
    "google/gemini-2.0-flash-exp:free",
    "qwen/qwen-2.5-coder-32b-instruct:free",
    "deepseek/deepseek-r1:free"
]

DEFAULT_MODEL = FREE_MODELS[0]

# Large Codebase Processing Controls
MAX_CHUNK_TOKENS = 6000
BATCH_SIZE = 15
MAX_FILE_SIZE_MB = 2.0

# Archive Formats to Recursively Unpack
ARCHIVE_EXTENSIONS = {
    ".rar", ".zip", ".jar", ".war", ".ear", ".tar", ".gz", ".tgz"
}

# Target Code File Extensions
ALLOWED_EXTENSIONS = {
    ".java", ".jsp", ".jspf", ".xml", ".properties", 
    ".tag", ".tld", ".sql", ".htm", ".html", ".css", ".js", ".class"
}

# Decompiler Tool Settings
JAVA_DECOMPILER_CMD = "cfr"  # Standard CFR decompiler command (or "java -jar cfr.jar")
