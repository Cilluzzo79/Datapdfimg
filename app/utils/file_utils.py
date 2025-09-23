"""
Utility per la gestione dei file
"""
import os
import io
import hashlib
import shutil
from typing import List, Tuple
from fastapi import UploadFile

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


async def save_upload_file(file: UploadFile) -> Tuple[str, str, int]:
    """
    Salva un file caricato in una directory temporanea
    
    Args:
        file: File caricato
        
    Returns:
        Tuple con percorso del file salvato, hash MD5 e dimensione in bytes
    """
    # Crea la directory temporanea se non esiste
    os.makedirs(settings.TEMP_FOLDER, exist_ok=True)
    
    # Crea un nome di file univoco
    file_extension = get_file_extension(file.filename)
    temp_filename = f"{os.path.splitext(os.path.basename(file.filename))[0]}_{hashlib.md5(os.urandom(32)).hexdigest()[:8]}.{file_extension}"
    file_path = os.path.join(settings.TEMP_FOLDER, temp_filename)
    
    # Leggi il contenuto del file
    contents = await file.read()
    file_size = len(contents)
    
    # Calcola l'hash MD5
    md5_hash = hashlib.md5(contents).hexdigest()
    
    # Scrivi il file
    with open(file_path, "wb") as f:
        f.write(contents)
    
    # Riposiziona il cursore all'inizio del file per eventuali letture successive
    await file.seek(0)
    
    logger.info(f"File salvato: {file_path}, dimensione: {file_size} bytes, hash: {md5_hash}")
    return file_path, md5_hash, file_size


def cleanup_temp_file(file_path: str) -> None:
    """
    Rimuove un file temporaneo
    
    Args:
        file_path: Percorso del file da rimuovere
    """
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"File temporaneo rimosso: {file_path}")
    except Exception as e:
        logger.error(f"Errore durante la rimozione del file temporaneo {file_path}: {e}")


def cleanup_temp_directory() -> None:
    """
    Rimuove tutti i file dalla directory temporanea
    """
    try:
        if os.path.exists(settings.TEMP_FOLDER):
            for filename in os.listdir(settings.TEMP_FOLDER):
                file_path = os.path.join(settings.TEMP_FOLDER, filename)
                if os.path.isfile(file_path):
                    os.remove(file_path)
            logger.info(f"Directory temporanea pulita: {settings.TEMP_FOLDER}")
    except Exception as e:
        logger.error(f"Errore durante la pulizia della directory temporanea {settings.TEMP_FOLDER}: {e}")
