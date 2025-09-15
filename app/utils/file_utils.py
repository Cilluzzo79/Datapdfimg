import os
import uuid
import hashlib
import aiofiles
import shutil
from typing import Tuple, Optional, List
from fastapi import UploadFile
from pathlib import Path
import tempfile

from app.config.settings import settings
from app.utils.logging_utils import get_logger

logger = get_logger(__name__)


def get_file_extension(filename: str) -> str:
    """Ottiene l'estensione del file"""
    return Path(filename).suffix.lstrip(".").lower()


def is_allowed_image(filename: str) -> bool:
    """Verifica se il file è un'immagine supportata"""
    ext = get_file_extension(filename)
    return ext in settings.ALLOWED_IMAGE_EXTENSIONS


def is_allowed_pdf(filename: str) -> bool:
    """Verifica se il file è un PDF"""
    ext = get_file_extension(filename)
    return ext in settings.ALLOWED_PDF_EXTENSIONS


def is_allowed_file(filename: str) -> bool:
    """Verifica se il file è supportato"""
    return is_allowed_image(filename) or is_allowed_pdf(filename)


def get_file_type(filename: str) -> str:
    """Ottiene il tipo di file"""
    ext = get_file_extension(filename)
    if ext in settings.ALLOWED_IMAGE_EXTENSIONS:
        return ext
    elif ext in settings.ALLOWED_PDF_EXTENSIONS:
        return ext
    else:
        return "unknown"


def get_file_size_mb(file_size_bytes: int) -> float:
    """Converte la dimensione del file da byte a MB"""
    return file_size_bytes / (1024 * 1024)


def is_file_size_allowed(file_size_bytes: int) -> bool:
    """Verifica se la dimensione del file rientra nei limiti"""
    file_size_mb = get_file_size_mb(file_size_bytes)
    return file_size_mb <= settings.MAX_FILE_SIZE_MB


async def save_upload_file(upload_file: UploadFile) -> Tuple[str, str, int]:
    """
    Salva un file caricato e restituisce il percorso, l'hash MD5 e la dimensione
    
    Args:
        upload_file: File caricato
        
    Returns:
        Tuple con percorso file, hash MD5 e dimensione in byte
    """
    temp_dir = Path(settings.TEMP_FOLDER)
    temp_dir.mkdir(parents=True, exist_ok=True)
    
    # Genera un nome file unico
    file_extension = get_file_extension(upload_file.filename)
    unique_filename = f"{uuid.uuid4()}.{file_extension}"
    file_path = temp_dir / unique_filename
    
    # Calcola l'hash MD5 mentre salva il file
    md5_hash = hashlib.md5()
    file_size = 0
    
    try:
        async with aiofiles.open(file_path, 'wb') as out_file:
            # Leggi il file a chunk
            while content := await upload_file.read(1024 * 1024):  # 1MB chunks
                file_size += len(content)
                md5_hash.update(content)
                await out_file.write(content)
                
        logger.info(f"File salvato: {file_path}, dimensione: {file_size} bytes")
        return str(file_path), md5_hash.hexdigest(), file_size
    except Exception as e:
        logger.error(f"Errore durante il salvataggio del file: {e}")
        # Cancella il file se esiste
        if file_path.exists():
            file_path.unlink()
        raise


def cleanup_temp_file(file_path: str) -> None:
    """Elimina un file temporaneo"""
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"File temporaneo eliminato: {file_path}")
    except Exception as e:
        logger.error(f"Errore durante l'eliminazione del file temporaneo {file_path}: {e}")


def cleanup_temp_files(file_paths: List[str]) -> None:
    """Elimina più file temporanei"""
    for file_path in file_paths:
        cleanup_temp_file(file_path)


def cleanup_temp_directory() -> None:
    """Pulisce la directory temporanea"""
    try:
        temp_dir = Path(settings.TEMP_FOLDER)
        if temp_dir.exists():
            shutil.rmtree(temp_dir)
            logger.info(f"Directory temporanea eliminata: {temp_dir}")
            temp_dir.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        logger.error(f"Errore durante la pulizia della directory temporanea: {e}")
