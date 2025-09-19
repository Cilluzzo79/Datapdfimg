"""
Configurazioni dell'applicazione
"""
import os
from typing import List
from pydantic import BaseSettings


class Settings(BaseSettings):
    """
    Impostazioni dell'applicazione
    """
    # Ambiente di esecuzione
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "dev")
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    # Limiti file
    MAX_FILE_SIZE_MB: int = int(os.getenv("MAX_FILE_SIZE_MB", "10"))
    
    # Estensioni consentite
    ALLOWED_IMAGE_EXTENSIONS: List[str] = ["jpg", "jpeg", "png", "webp"]
    ALLOWED_PDF_EXTENSIONS: List[str] = ["pdf"]
    ALLOWED_EXCEL_EXTENSIONS: List[str] = ["xls", "xlsx", "xlsm", "xlsb"]
    ALLOWED_CSV_EXTENSIONS: List[str] = ["csv"]
    
    # OpenRouter API
    OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "")
    OPENROUTER_API_URL: str = "https://openrouter.ai/api/v1"
    
    class Config:
        env_file = ".env"


# Istanza singleton delle impostazioni
settings = Settings()
