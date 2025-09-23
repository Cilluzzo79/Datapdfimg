"""
Utility per il logging
"""
import logging
import sys
import os
import json
from typing import Dict, Any, Optional
from datetime import datetime

# Leggi il livello di logging dall'ambiente
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

def get_logger(name: str) -> logging.Logger:
    """
    Configura e restituisce un logger
    
    Args:
        name: Nome del logger
        
    Returns:
        Logger configurato
    """
    logger = logging.getLogger(name)
    
    # Imposta il livello di logging in base alle impostazioni
    log_level = getattr(logging, LOG_LEVEL)
    logger.setLevel(log_level)
    
    # Se il logger non ha handler, aggiungine uno
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    
    return logger

# Logger globale per le operazioni API
api_logger = get_logger("api")

def log_request(request_id: str, endpoint: str, metadata: Optional[Dict[str, Any]] = None) -> None:
    """
    Logga una richiesta API
    
    Args:
        request_id: ID della richiesta
        endpoint: Endpoint chiamato
        metadata: Metadati aggiuntivi (opzionale)
    """
    log_data = {
        "timestamp": datetime.now().isoformat(),
        "request_id": request_id,
        "type": "request",
        "endpoint": endpoint
    }
    
    if metadata:
        log_data["metadata"] = metadata
    
    api_logger.info(f"API Request: {json.dumps(log_data)}")

def log_response(request_id: str, endpoint: str, status_code: int, processing_time_ms: int) -> None:
    """
    Logga una risposta API
    
    Args:
        request_id: ID della richiesta
        endpoint: Endpoint chiamato
        status_code: Codice di stato HTTP
        processing_time_ms: Tempo di elaborazione in millisecondi
    """
    log_data = {
        "timestamp": datetime.now().isoformat(),
        "request_id": request_id,
        "type": "response",
        "endpoint": endpoint,
        "status_code": status_code,
        "processing_time_ms": processing_time_ms
    }
    
    api_logger.info(f"API Response: {json.dumps(log_data)}")

def log_error(request_id: str, endpoint: str, error_msg: str, error_details: Optional[Dict[str, Any]] = None) -> None:
    """
    Logga un errore API
    
    Args:
        request_id: ID della richiesta
        endpoint: Endpoint chiamato
        error_msg: Messaggio di errore
        error_details: Dettagli aggiuntivi sull'errore (opzionale)
    """
    log_data = {
        "timestamp": datetime.now().isoformat(),
        "request_id": request_id,
        "type": "error",
        "endpoint": endpoint,
        "error_message": error_msg
    }
    
    if error_details:
        log_data["error_details"] = error_details
    
    api_logger.error(f"API Error: {json.dumps(log_data)}")
