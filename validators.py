from fastapi import HTTPException, UploadFile, File
from typing import Tuple

from app.utils.file_utils import (
    is_allowed_file, 
    is_allowed_image, 
    is_allowed_pdf, 
    is_file_size_allowed, 
    get_file_extension
)
from app.utils.logging_utils import get_logger
from app.config.settings import settings

logger = get_logger(__name__)


async def validate_file(file: UploadFile) -> Tuple[str, str]:
    """
    Valida un file caricato
    
    Args:
        file: File caricato
        
    Returns:
        Tuple con tipo di file e nome originale
    
    Raises:
        HTTPException: Se il file non è valido
    """
    if not file:
        logger.error("Nessun file caricato")
        raise HTTPException(status_code=400, detail="Nessun file caricato")
    
    filename = file.filename
    if not filename:
        logger.error("Nome file mancante")
        raise HTTPException(status_code=400, detail="Nome file mancante")
    
    # Verifica l'estensione del file
    if not is_allowed_file(filename):
        logger.error(f"Tipo di file non supportato: {filename}")
        raise HTTPException(
            status_code=400, 
            detail=f"Tipo di file non supportato. Tipi supportati: {settings.ALLOWED_IMAGE_EXTENSIONS + settings.ALLOWED_PDF_EXTENSIONS}"
        )
    
    # Leggi il contenuto del file per verificare la dimensione
    file_content = await file.read()
    file_size = len(file_content)
    
    # Riposiziona il cursore all'inizio del file per le successive letture
    await file.seek(0)
    
    if not is_file_size_allowed(file_size):
        logger.error(f"File troppo grande: {file_size} bytes")
        raise HTTPException(
            status_code=400, 
            detail=f"Il file supera la dimensione massima consentita di {settings.MAX_FILE_SIZE_MB}MB"
        )
    
    # Classifica il tipo di file
    file_extension = get_file_extension(filename)
    if is_allowed_image(filename):
        file_type = "image"
    elif is_allowed_pdf(filename):
        file_type = "pdf"
    else:
        logger.error(f"Tipo di file non classificato: {filename}")
        raise HTTPException(status_code=400, detail="Tipo di file non classificato")
    
    logger.info(f"File validato: {filename}, tipo: {file_type}, dimensione: {file_size} bytes")
    return file_type, filename
