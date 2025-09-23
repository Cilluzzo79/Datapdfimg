from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks, Form, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import os
import uuid
import time
from datetime import datetime
from typing import Optional, Dict, Any

# Importazioni dalle utilities e configurazioni
from app.utils.validators import validate_file
from app.utils.file_utils import save_upload_file, cleanup_temp_file, cleanup_temp_directory
from app.utils.logging_utils import get_logger, log_request, log_response, log_error
from app.config.settings import settings

# Importazioni dai modelli
from app.models.response import ClaudeFormatResponse

# Importazione del servizio di elaborazione documenti
from app.services.document_processor import DocumentProcessor

logger = get_logger(__name__)

# Crea l'app FastAPI
app = FastAPI(
    title="Railway Document Worker",
    version="1.1.0",
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
        
        error_response = {
            "error_code": "server_error",
            "message": "Si è verificato un errore interno del server",
            "details": {"error": str(e)}
        }
        
        return JSONResponse(
            status_code=500,
            content=error_response
        )

@app.get("/")
def root():
    return {"status": "ok", "message": "Railway Document Worker is running"}

@app.get("/health")
def health_check():
    """
    Verifica lo stato del servizio
    """
    # Calcola l'uptime
    uptime_seconds = int(time.time() - start_time)
    
    # Verifica connessioni API esterne
    api_connections = {
        "openrouter": bool(settings.OPENROUTER_API_KEY),
        "mistral": bool(settings.MISTRAL_API_KEY)
    }
    
    # Verifica feature flags
    features = {
        "tabular_processing": settings.ENABLE_TABULAR_PROCESSING,
        "pdf_processing": settings.ENABLE_PDF_PROCESSING,
        "advanced_pdf": settings.ENABLE_ADVANCED_PDF,
        "ocr": settings.ENABLE_OCR,
        "image_processing": settings.ENABLE_IMAGE_PROCESSING,
        "mistral_vision": settings.ENABLE_MISTRAL_VISION,
        "claude_format": settings.ENABLE_CLAUDE_FORMAT
    }
    
    return {
        "status": "ok",
        "version": "1.1.0",
        "environment": os.getenv("ENVIRONMENT", "development"),
        "api_connections": api_connections,
        "features": features,
        "uptime_seconds": uptime_seconds
    }

@app.get("/features")
async def feature_flags():
    """
    Mostra lo stato corrente dei feature flags
    """
    return {
        "features": {
            "tabular_processing": settings.ENABLE_TABULAR_PROCESSING,
            "pdf_processing": settings.ENABLE_PDF_PROCESSING,
            "advanced_pdf": settings.ENABLE_ADVANCED_PDF,
            "ocr": settings.ENABLE_OCR,
            "image_processing": settings.ENABLE_IMAGE_PROCESSING,
            "mistral_vision": settings.ENABLE_MISTRAL_VISION,
            "claude_format": settings.ENABLE_CLAUDE_FORMAT
        }
    }

@app.post("/process-document")
async def process_document(
    file: UploadFile = File(...),
    document_type: Optional[str] = Form(None),
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
        file_type, filename = await validate_file(file)
        
        # Salva il file
        file_path, md5_hash, file_size = await save_upload_file(file)
        
        # Processa il documento
        result = await document_processor.process_document(
            file_path=file_path,
            original_filename=filename,
            file_size=file_size,
            md5_hash=md5_hash,
            document_type_hint=document_type
        )
        
        # Calcola il tempo di elaborazione
        processing_time_ms = int((time.time() - start_process_time) * 1000)
        
        # Preparazione della risposta
        response = {
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "document_id": request_id,
            "document_type": result.get("document_type", "sconosciuto"),
            "confidence_score": result.get("confidence_score", 0.0),
            "processing_time_ms": processing_time_ms,
            "result_json": result,
            "processing_notes": result.get("processing_notes", [])
        }
        
        # Log della risposta
        log_response(
            request_id=request_id,
            endpoint="/process-document",
            status_code=200,
            processing_time_ms=processing_time_ms
        )
        
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

@app.post("/process-for-claude", response_model=ClaudeFormatResponse)
async def process_for_claude(
    file: UploadFile = File(...),
    document_type: Optional[str] = Form(None),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """
    Elabora un documento ed emette un output ottimizzato per Claude Sonnet
    """
    try:
        # Validazione del file
        file_type, filename = await validate_file(file)
        logger.info(f"File validato: {filename}, tipo: {file_type}")
        
        # Genera un ID documento
        document_id = str(uuid.uuid4())
        
        # Salva il file temporaneamente
        file_path, md5_hash, file_size = await save_upload_file(file)
        logger.info(f"File salvato: {file_path}, hash: {md5_hash}, dimensione: {file_size} bytes")
        
        # Registra la richiesta in background
        log_request(document_id, "/process-for-claude", {
            "filename": filename,
            "file_type": file_type,
            "document_type": document_type,
            "file_size": file_size,
            "md5_hash": md5_hash
        })
        
        # Elabora il documento
        start_time = datetime.now()
        
        document_processor = DocumentProcessor()
        claude_format = await document_processor.process_for_claude(
            file_path=file_path,
            original_filename=filename,
            document_type_hint=document_type
        )
        
        end_time = datetime.now()
        processing_time_ms = int((end_time - start_time).total_seconds() * 1000)
        
        # Pulizia del file temporaneo in background
        background_tasks.add_task(cleanup_temp_file, file_path)
        
        # Registra la risposta in background
        log_response(
            document_id, 
            "/process-for-claude", 
            200, 
            processing_time_ms
        )
        
        # Restituisci il risultato
        return ClaudeFormatResponse(
            status="success",
            timestamp=datetime.now(),
            document_id=document_id,
            document_type=claude_format["metadata"]["document_type"],
            confidence_score=claude_format["metadata"]["confidence_score"],
            claude_format=claude_format,
            processing_notes=[]
        )
    
    except HTTPException as e:
        # Rilancia le eccezioni HTTP
        raise
    
    except Exception as e:
        logger.error(f"Errore durante l'elaborazione: {e}")
        # Registra l'errore
        if 'document_id' in locals():
            log_error(
                document_id,
                "/process-for-claude",
                str(e),
                {"exception": str(type(e).__name__)}
            )
        
        # Cleanup del file temporaneo se esistente
        if 'file_path' in locals():
            background_tasks.add_task(cleanup_temp_file, file_path)
        
        # Restituisci errore
        raise HTTPException(
            status_code=500,
            detail=f"Errore durante l'elaborazione del documento: {str(e)}"
        )

@app.post("/test-webhook")
async def test_webhook():
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
    logger.info(f"Avvio del servizio Railway Document Worker v1.1.0 con supporto Claude")
    
    # Verifica la presenza della cartella temporanea
    os.makedirs(settings.TEMP_FOLDER, exist_ok=True)
    logger.info(f"Cartella temporanea creata: {settings.TEMP_FOLDER}")
    
    # Verifica le caratteristiche abilitate
    features_enabled = []
    if settings.ENABLE_PDF_PROCESSING:
        features_enabled.append("PDF Processing")
    if settings.ENABLE_ADVANCED_PDF:
        features_enabled.append("Advanced PDF")
    if settings.ENABLE_OCR:
        features_enabled.append("OCR")
    if settings.ENABLE_IMAGE_PROCESSING:
        features_enabled.append("Image Processing")
    if settings.ENABLE_MISTRAL_VISION:
        features_enabled.append("Mistral Vision")
    if settings.ENABLE_CLAUDE_FORMAT:
        features_enabled.append("Claude Format")
    
    logger.info(f"Caratteristiche abilitate: {', '.join(features_enabled)}")

@app.on_event("shutdown")
async def shutdown_event():
    """
    Eventi da eseguire alla chiusura dell'applicazione
    """
    logger.info("Arresto del servizio Railway Document Worker")
    
    # Pulizia della cartella temporanea
    cleanup_temp_directory()

# Punto di ingresso per il server uvicorn
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)
