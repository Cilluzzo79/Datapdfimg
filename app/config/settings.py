"""
Configurazione dell'applicazione
"""
import os

# Configurazione generale
DEBUG = os.getenv("DEBUG", "false").lower() == "true"
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", "10"))
TEMP_FOLDER = os.getenv("TEMP_FOLDER", "/tmp/railway-document-worker")

# Feature flags
ENABLE_TABULAR_PROCESSING = os.getenv("ENABLE_TABULAR_PROCESSING", "true").lower() == "true"
ENABLE_PDF_PROCESSING = os.getenv("ENABLE_PDF_PROCESSING", "true").lower() == "true"
ENABLE_ADVANCED_PDF = os.getenv("ENABLE_ADVANCED_PDF", "false").lower() == "true"
ENABLE_OCR = os.getenv("ENABLE_OCR", "false").lower() == "true"
ENABLE_IMAGE_PROCESSING = os.getenv("ENABLE_IMAGE_PROCESSING", "false").lower() == "true"
ENABLE_MISTRAL_VISION = os.getenv("ENABLE_MISTRAL_VISION", "true").lower() == "true"

# Supporto per Claude
ENABLE_CLAUDE_FORMAT = os.getenv("ENABLE_CLAUDE_FORMAT", "true").lower() == "true"
CLAUDE_INCLUDE_RAW_TEXT = os.getenv("CLAUDE_INCLUDE_RAW_TEXT", "true").lower() == "true"
CLAUDE_MAX_RAW_TEXT_LENGTH = int(os.getenv("CLAUDE_MAX_RAW_TEXT_LENGTH", "8000"))

# Configurazione LLM
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_API_URL = os.getenv("OPENROUTER_API_URL", "https://openrouter.ai/api/v1")
LLM_MODEL = os.getenv("LLM_MODEL", "anthropic/claude-3-opus:beta")
LLM_TIMEOUT = int(os.getenv("LLM_TIMEOUT", "60"))

# Configurazione Mistral
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY", "")

# Configurazione OCR
OCR_LANGUAGE = os.getenv("OCR_LANGUAGE", "ita+eng")

# Estensioni di file supportate
ALLOWED_IMAGE_EXTENSIONS = ['jpg', 'jpeg', 'png', 'webp']
ALLOWED_PDF_EXTENSIONS = ['pdf']
ALLOWED_TABULAR_EXTENSIONS = ['xls', 'xlsx', 'xlsm', 'xlsb', 'csv']
