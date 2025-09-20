"""
FastAPI app principale
"""
import time
from typing import Optional
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.models.document import DocumentRequest
from app.models.response import DocumentResponse
from app.services.tabular_processor import TabularProcessor
from app.services.pdf_processor import PDFProcessor

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

@app.get("/")
async def root():
    return {"message": "Tabular Data Processor - Versione 1.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.post("/process-document", response_model=DocumentResponse)
async def process_document(
    file: UploadFile = File(...),
    document_type: Optional[str] = Form(None)
):
    """
    Elabora un documento caricato (CSV o Excel)
    
    Args:
        file: File da elaborare
        document_type: Tipo di documento (opzionale)
        
    Returns:
        Risposta con i dati estratti dal documento
    """
    start_time = time.time()
    
    try:
        # Determina il tipo di file dall'estensione
        file_type = None
        if file.filename.endswith(('.xlsx', '.xls', '.xlsm', '.xlsb')):
            file_type = "excel"
        elif file.filename.endswith('.csv'):
            file_type = "csv"
        elif file.filename.endswith('.pdf'):
            file_type = "pdf"
        else:
            raise HTTPException(status_code=400, detail=f"Tipo di file non supportato: {file.filename}")
        
        # Elabora il file in base al tipo
        if file_type == "excel" or file_type == "csv":
            result = await TabularProcessor.process_tabular(file, file_type, document_type)
        elif file_type == "pdf":
            result = await PDFProcessor.process_pdf(file, document_type)
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
        
        return response
    
    except Exception as e:
        # Calcola il tempo di elaborazione anche in caso di errore
        processing_time_ms = int((time.time() - start_time) * 1000)
        
        # Log dell'errore
        error_details = {
            "error_type": str(type(e).__name__),
            "error_message": str(e),
            "filename": file.filename if file else "unknown",
        }
        
        # Crea una risposta di errore
        response = DocumentResponse(
            status="error",
            document_type="error",
            processing_time_ms=processing_time_ms,
            result_json={
                "error": str(e),
                "error_details": error_details
            },
            processing_notes=[f"Errore durante l'elaborazione: {str(e)}"]
        )
        
        return response

@app.post("/test-webhook")
async def test_webhook(request: dict):
    """
    Endpoint per testare l'integrazione webhook con N8N
    
    Args:
        request: Payload di test
        
    Returns:
        Echo del payload ricevuto con timestamp
    """
    return {
        "status": "success",
        "timestamp": time.time(),
        "received_payload": request
    }