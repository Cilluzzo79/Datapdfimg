"""
Modelli per le risposte API
"""
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime
import uuid

class DocumentResponse(BaseModel):
    """
    Modello per la risposta dell'elaborazione del documento
    """
    status: str = "success"
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    document_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    document_type: str
    confidence_score: float = 0.95
    processing_time_ms: int
    result_json: Dict[str, Any]
    processing_notes: List[str] = []
