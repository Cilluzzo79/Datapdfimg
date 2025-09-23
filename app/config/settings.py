"""
Configurazione dell'applicazione
"""
import os
from pathlib import Path

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
ALLOWED_EXCEL_EXTENSIONS = ['xls', 'xlsx', 'xlsm', 'xlsb']
ALLOWED_CSV_EXTENSIONS = ['csv']

class Settings:
    """Classe che contiene tutte le impostazioni dell'applicazione"""
    DEBUG = DEBUG
    LOG_LEVEL = LOG_LEVEL
    MAX_FILE_SIZE_MB = MAX_FILE_SIZE_MB
    TEMP_FOLDER = TEMP_FOLDER
    
    # Feature flags
    ENABLE_TABULAR_PROCESSING = ENABLE_TABULAR_PROCESSING
    ENABLE_PDF_PROCESSING = ENABLE_PDF_PROCESSING
    ENABLE_ADVANCED_PDF = ENABLE_ADVANCED_PDF
    ENABLE_OCR = ENABLE_OCR
    ENABLE_IMAGE_PROCESSING = ENABLE_IMAGE_PROCESSING
    ENABLE_MISTRAL_VISION = ENABLE_MISTRAL_VISION
    
    # Supporto per Claude
    ENABLE_CLAUDE_FORMAT = ENABLE_CLAUDE_FORMAT
    CLAUDE_INCLUDE_RAW_TEXT = CLAUDE_INCLUDE_RAW_TEXT
    CLAUDE_MAX_RAW_TEXT_LENGTH = CLAUDE_MAX_RAW_TEXT_LENGTH
    
    # Configurazione LLM
    OPENROUTER_API_KEY = OPENROUTER_API_KEY
    OPENROUTER_API_URL = OPENROUTER_API_URL
    LLM_MODEL = LLM_MODEL
    LLM_TIMEOUT = LLM_TIMEOUT
    
    # Configurazione Mistral
    MISTRAL_API_KEY = MISTRAL_API_KEY
    
    # Configurazione OCR
    OCR_LANGUAGE = OCR_LANGUAGE
    
    # Estensioni di file supportate
    ALLOWED_IMAGE_EXTENSIONS = ALLOWED_IMAGE_EXTENSIONS
    ALLOWED_PDF_EXTENSIONS = ALLOWED_PDF_EXTENSIONS
    ALLOWED_TABULAR_EXTENSIONS = ALLOWED_TABULAR_EXTENSIONS
    ALLOWED_EXCEL_EXTENSIONS = ALLOWED_EXCEL_EXTENSIONS
    ALLOWED_CSV_EXTENSIONS = ALLOWED_CSV_EXTENSIONS

    def is_allowed_extension(self, filename: str, extensions: list) -> bool:
        """Verifica se un file ha un'estensione consentita"""
        ext = Path(filename).suffix.lstrip('.').lower()
        return ext in extensions

    def is_allowed_file(self, filename: str) -> bool:
        """Verifica se il file ha un'estensione consentita"""
        return (self.is_allowed_extension(filename, self.ALLOWED_IMAGE_EXTENSIONS) or 
                self.is_allowed_extension(filename, self.ALLOWED_PDF_EXTENSIONS) or
                self.is_allowed_extension(filename, self.ALLOWED_TABULAR_EXTENSIONS))

    def is_allowed_image(self, filename: str) -> bool:
        """Verifica se il file è un'immagine supportata"""
        return self.is_allowed_extension(filename, self.ALLOWED_IMAGE_EXTENSIONS)

    def is_allowed_pdf(self, filename: str) -> bool:
        """Verifica se il file è un PDF"""
        return self.is_allowed_extension(filename, self.ALLOWED_PDF_EXTENSIONS)

    def is_allowed_tabular(self, filename: str) -> bool:
        """Verifica se il file è un file tabellare supportato"""
        return self.is_allowed_extension(filename, self.ALLOWED_TABULAR_EXTENSIONS)
    
    def get_file_extension(self, filename: str) -> str:
        """Ottiene l'estensione di un file"""
        return Path(filename).suffix.lstrip('.').lower()

# Crea un'istanza della classe Settings
settings = Settings()
