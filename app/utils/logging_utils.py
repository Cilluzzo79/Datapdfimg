import sys
import json
from datetime import datetime
from pathlib import Path
from loguru import logger
import logging
from typing import Dict, Any

from app.config.settings import settings


class InterceptHandler(logging.Handler):
    """
    Intercetta i log standard e li redirige a Loguru
    """
    def emit(self, record):
        # Get corresponding Loguru level if it exists
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Find caller from where originated the logged message
        frame, depth = logging.currentframe(), 2
        while frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())


def setup_logging():
    """
    Configura il logging per l'applicazione.
    Intercetta i log standard e li redirige a Loguru.
    """
    # Rimuove il gestore predefinito di loguru
    logger.remove()
    
    # Aggiunge un gestore per l'output in console con il formato JSON in produzione
    log_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
        "<level>{message}</level>"
    )
    
    # In produzione, usa il formato JSON
    if settings.ENVIRONMENT == "production":
        logger.add(
            sys.stdout,
            serialize=True,  # Serializza come JSON
            format="{message}",
            level=settings.LOG_LEVEL,
            enqueue=True,
            backtrace=True,
            diagnose=True,
        )
    else:
        # In sviluppo, usa un formato più leggibile
        logger.add(
            sys.stdout,
            format=log_format,
            level=settings.LOG_LEVEL,
            colorize=True,
            enqueue=True,
            backtrace=True,
            diagnose=True,
        )
    
    # Intercetta i log standard e li redirige a Loguru
    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)
    
    # Imposta anche i logger per le librerie utilizzate
    for logger_name in ["uvicorn", "uvicorn.error", "fastapi"]:
        logging_logger = logging.getLogger(logger_name)
        logging_logger.handlers = [InterceptHandler()]
        
    return logger


def get_logger(name: str):
    """
    Ottiene un logger configurato per il modulo specificato
    """
    return logger.bind(module=name)


def log_request(request_id: str, endpoint: str, metadata: Dict[str, Any]):
    """
    Registra informazioni sulla richiesta
    """
    logger.info(
        f"Richiesta ricevuta: {endpoint}", 
        request_id=request_id,
        endpoint=endpoint,
        metadata=metadata,
        timestamp=datetime.now().isoformat()
    )


def log_response(request_id: str, endpoint: str, status_code: int, processing_time_ms: int):
    """
    Registra informazioni sulla risposta
    """
    logger.info(
        f"Risposta inviata: {endpoint}", 
        request_id=request_id,
        endpoint=endpoint,
        status_code=status_code,
        processing_time_ms=processing_time_ms,
        timestamp=datetime.now().isoformat()
    )


def log_error(request_id: str, endpoint: str, error_msg: str, error_details: Dict[str, Any] = None):
    """
    Registra informazioni sugli errori
    """
    logger.error(
        f"Errore in {endpoint}: {error_msg}", 
        request_id=request_id,
        endpoint=endpoint,
        error_msg=error_msg,
        error_details=error_details,
        timestamp=datetime.now().isoformat()
    )


# Configura il logger all'importazione del modulo
setup_logging()
