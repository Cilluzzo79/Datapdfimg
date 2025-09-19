"""
FastAPI app principale
"""
import time
from typing import Optional
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.models.document import DocumentRequest
from app.models.response import DocumentResponse
from app.utils.validators import validate_file
from app.utils.logging_utils import get_logger
from app.services.tabular_processor import TabularProcessor
# Importare gli altri processor quando saranno implementati
# from app.services.image_processor import ImageProcessor
# from app.services.pdf_processor import PdfProcessor

logger = get_logger(__name__)

app = FastAPI(
    title="Document Processing API",
    description="API per l'elaborazione di documenti business",
    version="1.0.0"
)

# Configurazione CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In produzione, limitare alle origini autorizzate
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    """
    Endpoint per verificare lo stato dell'API
    """
    return {"status": "healthy", "message": "API operativa"}


@app.post("/process-document", response_model=DocumentResponse)
async def process_document(
    file: UploadFile = File(...),
    document_type: Optional[str] = Form(None)
):
    """
    Elabora un documento caricato (immagine, PDF o Excel)
    
    Args:
        file: File da elaborare
        document_type: Tipo di documento (opzionale)
        
    Returns:
        Risposta con i dati estratti dal documento
    """
    start_time = time.time()
    
    try:
        # Valida il file
        file_type, filename = await validate_file(file)
        
        # Elabora il file in base al tipo
        if file_type == "excel" or file_type == "csv":
            result = await TabularProcessor.process_tabular(file, file_type, document_type)
        elif file_type == "image":
            # Implementare quando sarà disponibile
            # result = await ImageProcessor.process_image(file, document_type)
            raise HTTPException(status_code=501, detail="Elaborazione immagini non ancora implementata")
        elif file_type == "pdf":
            # Implementare quando sarà disponibile
            # result = await PdfProcessor.process_pdf(file, document_type)
            raise HTTPException(status_code=501, detail="Elaborazione PDF non ancora implementata")
        else:
            raise HTTPException(status_code=400, detail=f"Tipo di file non supportato: {file_type}")
        
        # Calcola il tempo di elaborazione
        processing_time_ms = int((time.time() - start_time) * 1000)
        
        # Crea la risposta
        response = DocumentResponse(
            document_type=result["document_type"],
            processing_time_ms=processing_time_ms,
            result_json=result,
            processing_notes=result.get("processing_notes", [])
        )
        
        logger.info(f"Documento elaborato con successo: {filename}, tipo: {result['document_type']}")
        return response
    
    except Exception as e:
        logger.error(f"Errore durante l'elaborazione del documento: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Errore durante l'elaborazione del documento: {str(e)}")


@app.post("/test-webhook")
async def test_webhook(request: dict):
    """
    Endpoint per testare l'integrazione webhook con N8N
    
    Args:
        request: Payload di test
        
    Returns:
        Echo del payload ricevuto con timestamp
    """
    logger.info(f"Ricevuto test webhook: {request}")
    return {
        "status": "success",
        "timestamp": time.time(),
        "received_payload": request
    }
