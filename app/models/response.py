from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class HealthResponse(BaseModel):
    """Risposta per l'endpoint /health"""
    status: str = "ok"
    timestamp: datetime = Field(default_factory=datetime.now)
    version: str
    environment: str
    api_connections: Dict[str, bool]
    uptime_seconds: int


class ErrorResponse(BaseModel):
    """Risposta di errore standard"""
    status: str = "error"
    error_code: str
    message: str
    timestamp: datetime = Field(default_factory=datetime.now)
    details: Optional[Dict[str, Any]] = None


class ProcessDocumentResponse(BaseModel):
    """Risposta per l'endpoint /process-document"""
    status: str = "success"
    timestamp: datetime = Field(default_factory=datetime.now)
    document_id: str
    document_type: str
    confidence_score: float
    processing_time_ms: int
    result_json: Dict[str, Any]
    processing_notes: List[str] = []


class WebhookTestResponse(BaseModel):
    """Risposta per l'endpoint /test-webhook"""
    status: str = "success"
    timestamp: datetime = Field(default_factory=datetime.now)
    webhook_received: bool
    payload_valid: bool
    simulated_processing_time_ms: int
    test_document_id: str
    message: str
