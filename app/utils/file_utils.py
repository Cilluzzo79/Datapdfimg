"""
Utility per la gestione dei file
"""
import os
from typing import List

from app.config.settings import settings
from app.utils.logging_utils import get_logger

logger = get_logger(__name__)


def get_file_extension(filename: str) -> str:
    """
    Estrae l'estensione da un nome di file
    
    Args:
        filename: Nome del file
        
    Returns:
        Estensione del file (senza il punto)
    """
    return os.path.splitext(filename)[1][1:].lower()


def is_allowed_file(filename: str) -> bool:
    """
    Verifica se il file ha un'estensione consentita
    
    Args:
        filename: Nome del file
        
    Returns:
        True se l'estensione è consentita, False altrimenti
    """
    return is_allowed_image(filename) or is_allowed_pdf(filename) or is_allowed_excel(filename) or is_allowed_csv(filename)


def is_allowed_image(filename: str) -> bool:
    """
    Verifica se il file è un'immagine con estensione consentita
    
    Args:
        filename: Nome del file
        
    Returns:
        True se è un'immagine consentita, False altrimenti
    """
    return '.' in filename and \
           get_file_extension(filename) in settings.ALLOWED_IMAGE_EXTENSIONS


def is_allowed_pdf(filename: str) -> bool:
    """
    Verifica se il file è un PDF
    
    Args:
        filename: Nome del file
        
    Returns:
        True se è un PDF, False altrimenti
    """
    return '.' in filename and \
           get_file_extension(filename) in settings.ALLOWED_PDF_EXTENSIONS


def is_allowed_excel(filename: str) -> bool:
    """
    Verifica se il file è un file Excel con estensione consentita
    
    Args:
        filename: Nome del file
        
    Returns:
        True se è un file Excel consentito, False altrimenti
    """
    return '.' in filename and \
           get_file_extension(filename) in settings.ALLOWED_EXCEL_EXTENSIONS


def is_allowed_csv(filename: str) -> bool:
    """
    Verifica se il file è un file CSV
    
    Args:
        filename: Nome del file
        
    Returns:
        True se è un file CSV, False altrimenti
    """
    return '.' in filename and \
           get_file_extension(filename) in settings.ALLOWED_CSV_EXTENSIONS


def is_file_size_allowed(file_size: int) -> bool:
    """
    Verifica se la dimensione del file è consentita
    
    Args:
        file_size: Dimensione del file in bytes
        
    Returns:
        True se la dimensione è consentita, False altrimenti
    """
    max_size_bytes = settings.MAX_FILE_SIZE_MB * 1024 * 1024
    return file_size <= max_size_bytes
