import json
import os
import time
import uuid
from datetime import datetime
from typing import Dict, Any, Optional
from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks, Request, Depends, Form
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import psutil

from app.config.settings import settings
from app.models.document import ProcessingRequest, DocumentType
from app.models.response import (
    HealthResponse, 
    ErrorResponse, 
    ProcessDocumentResponse,
    WebhookTestResponse
)
from app.services.document_processor import DocumentProcessor
from app.utils.file_utils import save_upload_file, cleanup_temp_directory
from app.utils.validators import validate_file
from app.utils.logging_utils import get_logger, log_request, log_response, log_error

logger = get_logger(__name__)

# Crea l'app FastAPI
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="API per il processamento di documenti business (immagini e PDF)"
)

# Aggiungi middleware CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In produzione, specificare le origini consentite
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Variabili globali per monitorare lo stato del servizio
start_time = time.time()
document_processor = DocumentProcessor()


# Middleware per catturare errori globali
@app.middleware("http")
async def error_handling_middleware(request: Request, call_next):
    request_id = str(uuid.uuid4())
    
    try:
        response = await call_next(request)
        return response
    except Exception as e:
        logger.exception(f"Errore non gestito: {e}")
        
        error_response = ErrorResponse(
            error_code="server_error",
            message="Si è verificato un errore interno del server",
            details={"error": str(e)}
        )
        
        return JSONResponse(
            status_code=500,
            content=error_response.dict()
        )


# Endpoint di health check
@app.get("/health", response_model=HealthResponse, tags=["System"])
async def health_check():
    """
    Verifica lo stato del servizio
    """
    # Calcola l'uptime
    uptime_seconds = int(time.time() - start_time)
    
    # Verifica connessioni API esterne
    api_connections = {
        "openrouter": True  # Semplificato per il health check
    }
    
    return HealthResponse(
        status="ok",
        version=settings.APP_VERSION,
        environment=settings.ENVIRONMENT,
        api_connections=api_connections,
        uptime_seconds=uptime_seconds
    )
    
    # Informazioni di sistema
    cpu_percent = psutil.cpu_percent()
    memory_info = psutil.virtual_memory()
    
    return HealthResponse(
        status="ok",
        version=settings.APP_VERSION,
        environment=settings.ENVIRONMENT,
        api_connections=api_connections,
        uptime_seconds=uptime_seconds,
        system_info={
            "cpu_percent": cpu_percent,
            "memory_percent": memory_info.percent,
            "available_memory_mb": memory_info.available / (1024 * 1024)
        }
    )


# Endpoint per il processamento di documenti
@app.post("/process-document", response_model=ProcessDocumentResponse, tags=["Document"])
async def process_document(
    file: UploadFile = File(...),
    document_type: Optional[str] = Form(None),
    custom_metadata: Optional[str] = Form(None),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """
    Processa un documento (immagine o PDF) ed estrae informazioni strutturate
    """
    request_id = str(uuid.uuid4())
    start_time = time.time()
    
    try:
        # Log della richiesta
        log_request(
            request_id=request_id,
            endpoint="/process-document",
            metadata={"filename": file.filename, "document_type": document_type}
        )
        
        # Valida il file
        file_type, original_filename = await validate_file(file)
        
        # Crea la richiesta di processamento
        processing_request = ProcessingRequest(
            document_id=str(uuid.uuid4()),
            document_type_hint=DocumentType(document_type) if document_type else None,
            custom_metadata=json.loads(custom_metadata) if custom_metadata else None
        )
        
        # Salva il file
        file_path, md5_hash, file_size = await save_upload_file(file)
        
        # Processa il documento
        result = await document_processor.process_document(
            file_path=file_path,
            original_filename=original_filename,
            file_size=file_size,
            md5_hash=md5_hash,
            request=processing_request
        )
        
        # Calcola il tempo di elaborazione
        processing_time_ms = int((time.time() - start_time) * 1000)
        
        # Preparazione della risposta
        response = ProcessDocumentResponse(
            document_id=result.document_id,
            document_type=result.document_type.value,
            confidence_score=result.confidence_score,
            processing_time_ms=processing_time_ms,
            result_json=result.dict(),
            processing_notes=result.processing_notes
        )
        
        # Log della risposta
        log_response(
            request_id=request_id,
            endpoint="/process-document",
            status_code=200,
            processing_time_ms=processing_time_ms
        )
        
        # Aggiungi task in background per la pulizia periodica
        background_tasks.add_task(cleanup_temp_directory)
        
        return response
    except HTTPException as e:
        # Rilancia le eccezioni HTTP già gestite
        log_error(
            request_id=request_id,
            endpoint="/process-document",
            error_msg=e.detail,
            error_details={"status_code": e.status_code}
        )
        raise
    except Exception as e:
        # Gestione errori generici
        log_error(
            request_id=request_id,
            endpoint="/process-document",
            error_msg=str(e),
            error_details={"exception": str(type(e).__name__)}
        )
        
        raise HTTPException(
            status_code=500,
            detail=f"Errore durante il processamento del documento: {str(e)}"
        )


# Endpoint per il test del webhook
@app.post("/test-webhook", response_model=WebhookTestResponse, tags=["System"])
async def test_webhook(
    request: Request
):
    """
    Endpoint per testare l'integrazione webhook con N8N
    """
    request_id = str(uuid.uuid4())
    start_time = time.time()
    
    try:
        # Log della richiesta
        log_request(
            request_id=request_id,
            endpoint="/test-webhook",
            metadata={}
        )
        
        # Ottieni il body della richiesta
        body = await request.json()
        
        # Simula un tempo di elaborazione
        time.sleep(0.5)
        
        # Calcola il tempo di elaborazione
        processing_time_ms = int((time.time() - start_time) * 1000)
        
        # Preparazione della risposta
        response = WebhookTestResponse(
            webhook_received=True,
            payload_valid=True,
            simulated_processing_time_ms=processing_time_ms,
            test_document_id=str(uuid.uuid4()),
            message="Webhook ricevuto e testato con successo"
        )
        
        # Log della risposta
        log_response(
            request_id=request_id,
            endpoint="/test-webhook",
            status_code=200,
            processing_time_ms=processing_time_ms
        )
        
        return response
    except Exception as e:
        # Gestione errori
        log_error(
            request_id=request_id,
            endpoint="/test-webhook",
            error_msg=str(e),
            error_details={"exception": str(type(e).__name__)}
        )
        
        # Preparazione della risposta di errore
        response = WebhookTestResponse(
            webhook_received=True,
            payload_valid=False,
            simulated_processing_time_ms=int((time.time() - start_time) * 1000),
            test_document_id=str(uuid.uuid4()),
            message=f"Errore durante il test del webhook: {str(e)}"
        )
        
        return response


# Eventi di startup e shutdown dell'applicazione
@app.on_event("startup")
async def startup_event():
    """
    Eventi da eseguire all'avvio dell'applicazione
    """
    logger.info(f"Avvio del servizio {settings.APP_NAME} v{settings.APP_VERSION} in ambiente {settings.ENVIRONMENT}")
    
    # Verifica la presenza della cartella temporanea
    os.makedirs(settings.TEMP_FOLDER, exist_ok=True)
    logger.info(f"Cartella temporanea creata: {settings.TEMP_FOLDER}")
    
    # Pulisci eventuali file temporanei residui
    cleanup_temp_directory()


@app.on_event("shutdown")
async def shutdown_event():
    """
    Eventi da eseguire alla chiusura dell'applicazione
    """
    logger.info(f"Arresto del servizio {settings.APP_NAME}")
    
    # Pulisci la cartella temporanea
    cleanup_temp_directory()


# Punto di ingresso per il server uvicorn
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
