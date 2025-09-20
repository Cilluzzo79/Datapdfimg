"""
Configurazione dell'applicazione
"""
import os

# Configurazione generale
DEBUG = os.getenv("DEBUG", "false").lower() == "true"
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", "10"))

# Feature flags
ENABLE_TABULAR_PROCESSING = os.getenv("ENABLE_TABULAR_PROCESSING", "true").lower() == "true"
ENABLE_PDF_PROCESSING = os.getenv("ENABLE_PDF_PROCESSING", "true").lower() == "true"
ENABLE_ADVANCED_PDF = os.getenv("ENABLE_ADVANCED_PDF", "false").lower() == "true"
ENABLE_OCR = os.getenv("ENABLE_OCR", "false").lower() == "true"
ENABLE_IMAGE_PROCESSING = os.getenv("ENABLE_IMAGE_PROCESSING", "false").lower() == "true"

# Estensioni di file supportate
ALLOWED_IMAGE_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.webp']
ALLOWED_PDF_EXTENSIONS = ['.pdf']
ALLOWED_EXCEL_EXTENSIONS = ['.xls', '.xlsx', '.xlsm', '.xlsb']
ALLOWED_CSV_EXTENSIONS = ['.csv']

def is_allowed_extension(filename: str, extensions: list) -> bool:
    """Verifica se un file ha un'estensione consentita"""
    return any(filename.lower().endswith(ext) for ext in extensions)

def is_allowed_file(filename: str) -> bool:
    """Verifica se un file ha un'estensione consentita"""
    return (
        is_allowed_extension(filename, ALLOWED_IMAGE_EXTENSIONS) or 
        is_allowed_extension(filename, ALLOWED_PDF_EXTENSIONS) or 
        is_allowed_extension(filename, ALLOWED_EXCEL_EXTENSIONS) or
        is_allowed_extension(filename, ALLOWED_CSV_EXTENSIONS)
    )

def is_allowed_image(filename: str) -> bool:
    """Verifica se un file è un'immagine consentita"""
    return is_allowed_extension(filename, ALLOWED_IMAGE_EXTENSIONS)

def is_allowed_pdf(filename: str) -> bool:
    """Verifica se un file è un PDF"""
    return is_allowed_extension(filename, ALLOWED_PDF_EXTENSIONS)

def is_allowed_excel(filename: str) -> bool:
    """Verifica se un file è un Excel"""
    return is_allowed_extension(filename, ALLOWED_EXCEL_EXTENSIONS)

def is_allowed_csv(filename: str) -> bool:
    """Verifica se un file è un CSV"""
    return is_allowed_extension(filename, ALLOWED_CSV_EXTENSIONS)

def get_file_extension(filename: str) -> str:
    """Ottiene l'estensione di un file"""
    return os.path.splitext(filename)[1].lower()

def is_file_size_allowed(file_size: int) -> bool:
    """Verifica se la dimensione del file è consentita"""
    max_size_bytes = MAX_FILE_SIZE_MB * 1024 * 1024
    return file_size <= max_size_bytes