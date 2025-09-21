from pydantic_settings import BaseSettings
from typing import Optional
import os
from enum import Enum


class Environment(str, Enum):
    DEVELOPMENT = "dev"
    STAGING = "staging"
    PRODUCTION = "production"


class Settings(BaseSettings):
    # Ambiente
    ENVIRONMENT: Environment = Environment.DEVELOPMENT
    
    # Chiavi API
    OPENROUTER_API_KEY: Optional[str] = None
    OPENROUTER_API_URL: str = "https://openrouter.ai/api/v1"
    MISTRAL_API_KEY: Optional[str] = None
    
    # Configurazione app
    APP_NAME: str = "Railway Document Worker"
    APP_VERSION: str = "0.1.0"
    
    # Limiti file
    MAX_FILE_SIZE_MB: int = 10
    ALLOWED_IMAGE_EXTENSIONS: list[str] = ["jpg", "jpeg", "png", "webp"]
    ALLOWED_PDF_EXTENSIONS: list[str] = ["pdf"]
    ALLOWED_TABULAR_EXTENSIONS: list[str] = ["xls", "xlsx", "csv"]
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    # Cartella temporanea per file
    TEMP_FOLDER: str = "/tmp/railway-document-worker"
    
    # Configurazione OCR
    OCR_LANGUAGE: str = "ita+eng"  # Default italiano + inglese
    
    # Configurazione LLM
    LLM_MODEL: str = "mistralai/mistral-large-latest"  # Modello Mistral per analisi
    LLM_TIMEOUT: int = 60  # Timeout in secondi
    
    # Parametri JSON
    JSON_OUTPUT_INDENT: int = 2
    
    # Feature flags
    ENABLE_TABULAR_PROCESSING: bool = os.getenv("ENABLE_TABULAR_PROCESSING", "true").lower() == "true"
    ENABLE_PDF_PROCESSING: bool = os.getenv("ENABLE_PDF_PROCESSING", "true").lower() == "true"
    ENABLE_ADVANCED_PDF: bool = os.getenv("ENABLE_ADVANCED_PDF", "false").lower() == "true"
    ENABLE_OCR: bool = os.getenv("ENABLE_OCR", "false").lower() == "true"
    ENABLE_IMAGE_PROCESSING: bool = os.getenv("ENABLE_IMAGE_PROCESSING", "false").lower() == "true"
    ENABLE_MISTRAL_VISION: bool = os.getenv("ENABLE_MISTRAL_VISION", "false").lower() == "true"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# Carica le impostazioni
settings = Settings()

# Crea cartella temporanea se non esiste
os.makedirs(settings.TEMP_FOLDER, exist_ok=True)
