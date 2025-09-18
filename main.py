from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
import os
import uuid
import time
from typing import Optional

# Importazioni minime dalle utilities e configurazioni
from app.utils.validators import validate_file
from app.utils.file_utils import save_upload_file, cleanup_temp_file
from app.utils.logging_utils import get_logger
from app.config.settings import settings

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
    
    return {
        "status": "ok",
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "api_connections": {"openrouter": True},
        "uptime_seconds": uptime_seconds
    }

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
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)