"""
Utility per il logging
"""
import logging
import sys
from app.config.settings import settings

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
    log_level = getattr(logging, settings.LOG_LEVEL)
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
