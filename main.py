from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks, Form, Request, Depends
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import os
import uuid
import time
import json
from datetime import datetime
from typing import Optional, Dict, Any

# Importazioni dalle utilities e configurazioni
from app.utils.validators import validate_file
from app.utils.file_utils import save_upload_file, cleanup_temp_file, cleanup_temp_directory
from app.utils.logging_utils import get_logger, log_request, log_response, log_error
from app.config.settings import settings

# Importazioni dai modelli
from app.models.document import ProcessingRequest, DocumentType
from app.models.response import (
    HealthResponse, 
    ErrorResponse, 
    ProcessDocumentResponse,
    WebhookTestResponse
)

# Importazione del servizio di elaborazione documenti
from app.services.document_processor import DocumentProcessor

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
    allow_origins=["*"],
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
            content=error_response.model_dump()
        )

@app.get("/")
def root():
    return {"status": "ok", "message": "Railway Document Worker is running"}

@app.get("/health", response_model=HealthResponse)
def health_check():
    """
    Verifica lo stato del servizio
    """
    # Calcola l'uptime
    uptime_seconds = int(time.time() - start_time)
    
    # Verifica connessioni API esterne
    api_connections = {
        "openrouter": True  # Da implementare controllo effettivo
    }
    
    return HealthResponse(
        status="ok",
        version=settings.APP_VERSION,
        environment=settings.ENVIRONMENT,
        api_connections=api_connections,
        uptime_seconds=uptime_seconds
    )

@app.post("/process-document", response_model=ProcessDocumentResponse)
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
    start_process_time = time.time()
    
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
        processing_time_ms = int((time.time() - start_process_time) * 1000)
        
        # Preparazione della risposta
        response = ProcessDocumentResponse(
            document_id=result.document_id,
            document_type=result.document_type.value,
            confidence_score=result.confidence_score,
            processing_time_ms=processing_time_ms,
            result_json=result.model_dump(),
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

@app.post("/process-document-simple")
async def process_document_simple(
    file: UploadFile = File(...),
    document_type: Optional[str] = None,
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """
    Versione semplificata dell'endpoint di processamento documenti
    """
    request_id = str(uuid.uuid4())
    start_processing_time = time.time()
    
    try:
        logger.info(f"Richiesta ricevuta: process-document-simple, filename: {file.filename}")
        
        # Valida il file
        file_type, original_filename = await validate_file(file)
        
        # Salva il file
        file_path, md5_hash, file_size = await save_upload_file(file)
        
        # Aggiungi task in background per la pulizia periodica
        background_tasks.add_task(cleanup_temp_file, file_path)
        
        # Calcola il tempo di elaborazione
        processing_time_ms = int((time.time() - start_processing_time) * 1000)
        
        # Prepara la risposta
        response = {
            "status": "success",
            "timestamp": time.time(),
            "document_id": request_id,
            "file_info": {
                "file_type": file_type,
                "original_filename": original_filename,
                "file_size": file_size,
                "md5_hash": md5_hash
            },
            "processing_time_ms": processing_time_ms,
            "message": "File elaborato con successo (versione semplificata)"
        }
        
        logger.info(f"Elaborazione completata: {original_filename}, tempo: {processing_time_ms}ms")
        return response
    except HTTPException as e:
        logger.error(f"Errore HTTP durante l'elaborazione: {e.detail}")
        raise
    except Exception as e:
        logger.error(f"Errore durante l'elaborazione: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Errore durante il processamento del documento: {str(e)}"
        )

@app.post("/test-webhook")
async def test_webhook(background_tasks: BackgroundTasks):
    """
    Endpoint per testare l'integrazione webhook con N8N
    """
    request_id = str(uuid.uuid4())
    start_time_webhook = time.time()
    
    try:
        # Simula un tempo di elaborazione
        time.sleep(0.5)
        
        # Calcola il tempo di elaborazione
        processing_time_ms = int((time.time() - start_time_webhook) * 1000)
        
        # Preparazione della risposta
        response = {
            "status": "success",
            "timestamp": time.time(),
            "webhook_received": True,
            "payload_valid": True,
            "simulated_processing_time_ms": processing_time_ms,
            "test_document_id": request_id,
            "message": "Webhook ricevuto e testato con successo"
        }
        
        logger.info(f"Test webhook completato, tempo: {processing_time_ms}ms")
        return response
    except Exception as e:
        logger.error(f"Errore durante il test webhook: {str(e)}")
        return {
            "status": "error",
            "webhook_received": True,
            "payload_valid": False,
            "simulated_processing_time_ms": int((time.time() - start_time_webhook) * 1000),
            "test_document_id": request_id,
            "message": f"Errore durante il test del webhook: {str(e)}"
        }

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

@app.on_event("shutdown")
async def shutdown_event():
    """
    Eventi da eseguire alla chiusura dell'applicazione
    """
    logger.info(f"Arresto del servizio {settings.APP_NAME}")

# Punto di ingresso per il server uvicorn
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
