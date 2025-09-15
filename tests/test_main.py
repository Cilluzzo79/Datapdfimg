import os
import json
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from app.main import app
from app.models.document import DocumentType, DocumentProcessingResult, DocumentMetadata, FileType


# Client di test
client = TestClient(app)


def test_health_check():
    """Test dell'endpoint di health check"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "uptime_seconds" in data
    assert "version" in data
    assert "environment" in data


@pytest.fixture
def mock_document_processor():
    """Mock del document processor"""
    with patch("app.main.document_processor") as mock:
        # Crea un risultato di esempio
        result = DocumentProcessingResult(
            document_id="test-123",
            document_type=DocumentType.FATTURA,
            confidence_score=0.95,
            metadata=DocumentMetadata(
                original_filename="test.pdf",
                file_type=FileType.PDF,
                file_size=1024,
                pages_processed=1,
                processing_time_ms=500,
                md5_hash="abc123"
            ),
            extracted_data={
                "numero_fattura": "F12345",
                "data_fattura": "2023-09-30",
                "importo_totale": 1000.00
            },
            raw_text="Esempio di testo estratto",
            processing_notes=["Nota di test"],
            llm_ready=True
        )
        
        # Configura il mock
        mock.process_document.return_value = result
        yield mock


@pytest.fixture
def test_pdf_file():
    """Crea un file PDF di test"""
    # Percorso del file di test
    file_path = "tests/test_files/test.pdf"
    
    # Verifica se la directory esiste, altrimenti creala
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    
    # Crea un file PDF di test se non esiste
    if not os.path.exists(file_path):
        with open(file_path, "wb") as f:
            # PDF minimo valido
            f.write(b"%PDF-1.4\n%¥±ë\n\n1 0 obj\n  << /Type /Catalog\n     /Pages 2 0 R\n  >>\nendobj\n\n2 0 obj\n  << /Type /Pages\n     /Kids [3 0 R]\n     /Count 1\n  >>\nendobj\n\n3 0 obj\n  << /Type /Page\n  >>\nendobj\n\nxref\n0 4\n0000000000 65535 f\n0000000018 00000 n\n0000000077 00000 n\n0000000178 00000 n\n\ntrailer\n  << /Root 1 0 R\n     /Size 4\n  >>\nstartxref\n216\n%%EOF")
    
    return file_path


@pytest.mark.asyncio
async def test_process_document(mock_document_processor, test_pdf_file):
    """Test dell'endpoint di processamento documenti"""
    
    # Patch della funzione save_upload_file
    with patch("app.main.save_upload_file") as mock_save:
        # Configura il mock di save_upload_file
        mock_save.return_value = (test_pdf_file, "abc123", 1024)
        
        # Patch della funzione validate_file
        with patch("app.main.validate_file") as mock_validate:
            # Configura il mock di validate_file
            mock_validate.return_value = ("pdf", "test.pdf")
            
            # Esegui la richiesta
            with open(test_pdf_file, "rb") as f:
                response = client.post(
                    "/process-document",
                    files={"file": ("test.pdf", f, "application/pdf")},
                    data={"document_type": "fattura"}
                )
            
            # Verifica la risposta
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert data["document_id"] == "test-123"
            assert data["document_type"] == "fattura"
            assert data["confidence_score"] == 0.95
            assert "processing_time_ms" in data
            
            # Verifica che il processor sia stato chiamato
            mock_document_processor.process_document.assert_called_once()


@pytest.mark.asyncio
async def test_test_webhook():
    """Test dell'endpoint di test webhook"""
    
    # Crea un payload di test
    payload = {"test": "data"}
    
    # Esegui la richiesta
    response = client.post(
        "/test-webhook",
        json=payload
    )
    
    # Verifica la risposta
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["webhook_received"] == True
    assert data["payload_valid"] == True
    assert "test_document_id" in data
    assert "simulated_processing_time_ms" in data
