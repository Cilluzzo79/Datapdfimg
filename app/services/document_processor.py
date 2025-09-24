import os
import time
import json
from typing import Dict, Any, Optional, Tuple
import uuid

from app.config.settings import settings
from app.utils.logging_utils import get_logger
from app.utils.file_utils import (
    get_file_extension, 
    is_allowed_image, 
    is_allowed_pdf,
    is_allowed_excel,
    is_allowed_csv,
    cleanup_temp_file
)
from app.services.image_processor import ImageProcessor
from app.services.pdf_processor import PDFProcessor
from app.services.tabular_processor import TabularProcessor
from app.services.llm_service import LLMService
from app.services.claude_formatter import ClaudeFormatter
from app.models.document import DocumentType
from app.models.response import ClaudeFormatResponse

logger = get_logger(__name__)


class DocumentProcessor:
    """Service principale per il processamento dei documenti"""
    
    def __init__(self):
        """Inizializza il servizio di processamento documenti"""
        self.image_processor = ImageProcessor()
        self.pdf_processor = PDFProcessor()
        self.tabular_processor = TabularProcessor()
        self.llm_service = LLMService()
        logger.info("Document Processor inizializzato")
    
    async def process_document(
        self, 
        file_path: str, 
        original_filename: str, 
        file_size: int,
        md5_hash: str,
        document_type_hint: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Processa un documento e restituisce i risultati
        
        Args:
            file_path: Percorso del file
            original_filename: Nome originale del file
            file_size: Dimensione del file in byte
            md5_hash: Hash MD5 del file
            document_type_hint: Suggerimento sul tipo di documento (opzionale)
            
        Returns:
            Risultato del processamento del documento
        """
        start_time = time.time()
        
        try:
            logger.info(f"Inizio processamento documento: {original_filename}")
            
            # Determina il tipo di file
            file_extension = get_file_extension(original_filename)
            
            # Processa in base al tipo di file
            if is_allowed_image(original_filename):
                file_type = file_extension.lower()
                result = await self._process_image(file_path, document_type_hint)
            elif is_allowed_pdf(original_filename):
                file_type = "pdf"
                result = await self._process_pdf(file_path, document_type_hint)
            elif is_allowed_excel(original_filename):
                file_type = "excel"
                # Crea un UploadFile simulato per tabular_processor
                class MockUploadFile:
                    def __init__(self, path, filename):
                        self.path = path
                        self.filename = filename
                        self._file = open(path, 'rb')
                    
                    async def read(self):
                        self._file.seek(0)
                        return self._file.read()
                    
                    async def seek(self, offset):
                        self._file.seek(offset)
                        
                    def close(self):
                        self._file.close()
                
                mock_file = MockUploadFile(file_path, original_filename)
                result = await self.tabular_processor.process_tabular(mock_file, "excel", document_type_hint)
                mock_file.close()
            elif is_allowed_csv(original_filename):
                file_type = "csv"
                # Crea un UploadFile simulato per tabular_processor
                class MockUploadFile:
                    def __init__(self, path, filename):
                        self.path = path
                        self.filename = filename
                        self._file = open(path, 'rb')
                    
                    async def read(self):
                        self._file.seek(0)
                        return self._file.read()
                    
                    async def seek(self, offset):
                        self._file.seek(offset)
                        
                    def close(self):
                        self._file.close()
                
                mock_file = MockUploadFile(file_path, original_filename)
                result = await self.tabular_processor.process_tabular(mock_file, "csv", document_type_hint)
                mock_file.close()
            else:
                raise ValueError(f"Tipo di file non supportato: {file_extension}")
            
            # Calcola il tempo di processamento
            processing_time_ms = int((time.time() - start_time) * 1000)
            
            # Crea i metadati
            metadata = {
                "original_filename": original_filename,
                "file_type": file_type,
                "file_size": file_size,
                "pages_processed": result.get("metadata", {}).get("page_count", 1) if "metadata" in result else 1,
                "processing_time_ms": processing_time_ms,
                "md5_hash": md5_hash
            }
            
            # Aggiungi i metadati al risultato
            result["metadata"] = {**result.get("metadata", {}), **metadata}
            
            logger.info(f"Processamento documento completato: {original_filename}, "
                        f"tipo: {result.get('document_type', 'sconosciuto')}, "
                        f"confidence: {result.get('confidence_score', 0.0):.2f}, "
                        f"tempo: {processing_time_ms}ms")
            
            return result
        except Exception as e:
            logger.error(f"Errore durante il processamento del documento {original_filename}: {e}")
            
            # Calcola il tempo di processamento anche in caso di errore
            processing_time_ms = int((time.time() - start_time) * 1000)
            
            # Crea risultato di errore
            return {
                "document_type": "documento_generico",
                "confidence_score": 0.0,
                "metadata": {
                    "original_filename": original_filename,
                    "file_type": file_extension.lower(),
                    "file_size": file_size,
                    "pages_processed": 0,
                    "processing_time_ms": processing_time_ms,
                    "md5_hash": md5_hash,
                    "error": str(e)
                },
                "extracted_data": {},
                "raw_text": "",
                "processing_notes": [f"Errore durante il processamento: {str(e)}"]
            }
        finally:
            # Pulisci il file temporaneo
            cleanup_temp_file(file_path)
    
    async def process_for_claude(
        self, 
        file_path: str, 
        original_filename: str, 
        document_type_hint: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Elabora un documento e formatta il risultato per Claude
        
        Args:
            file_path: Percorso del file
            original_filename: Nome originale del file
            document_type_hint: Suggerimento sul tipo di documento (opzionale)
            
        Returns:
            Risultato dell'elaborazione formattato per Claude
        """
        try:
            # Genera ID documento
            document_id = str(uuid.uuid4())
            logger.info(f"Inizio processamento per Claude: {original_filename} (ID: {document_id})")
            
            # Determina il tipo di file
            file_extension = get_file_extension(original_filename)
            
            # Processa in base al tipo di file
            if is_allowed_image(original_filename):
                file_type = file_extension.lower()
                result = await self._process_image(file_path, document_type_hint)
            elif is_allowed_pdf(original_filename):
                file_type = "pdf"
                result = await self._process_pdf(file_path, document_type_hint)
            elif is_allowed_excel(original_filename):
                file_type = "excel"
                # Crea un UploadFile simulato per tabular_processor
                class MockUploadFile:
                    def __init__(self, path, filename):
                        self.path = path
                        self.filename = filename
                        self._file = open(path, 'rb')
                    
                    async def read(self):
                        self._file.seek(0)
                        return self._file.read()
                    
                    async def seek(self, offset):
                        self._file.seek(offset)
                        
                    def close(self):
                        self._file.close()
                
                mock_file = MockUploadFile(file_path, original_filename)
                result = await self.tabular_processor.process_tabular(mock_file, "excel", document_type_hint)
                mock_file.close()
            elif is_allowed_csv(original_filename):
                file_type = "csv"
                # Crea un UploadFile simulato per tabular_processor
                class MockUploadFile:
                    def __init__(self, path, filename):
                        self.path = path
                        self.filename = filename
                        self._file = open(path, 'rb')
                    
                    async def read(self):
                        self._file.seek(0)
                        return self._file.read()
                    
                    async def seek(self, offset):
                        self._file.seek(offset)
                        
                    def close(self):
                        self._file.close()
                
                mock_file = MockUploadFile(file_path, original_filename)
                result = await self.tabular_processor.process_tabular(mock_file, "csv", document_type_hint)
                mock_file.close()
            else:
                raise ValueError(f"Tipo di file non supportato: {file_extension}")
            
            # Aggiungi metadati di base
            metadata = {
                "original_filename": original_filename,
                "file_type": file_type
            }
            
            # Formatta il risultato per Claude
            claude_format = ClaudeFormatter.format_for_claude(
                document_type=result.get("document_type", "documento_generico"),
                metadata=result.get("metadata", metadata),
                extracted_data=result.get("extracted_data", {}),
                confidence_score=result.get("confidence_score", 0.8),
                raw_text=result.get("raw_text", ""),
                processing_notes=result.get("processing_notes", [])
            )
            
            logger.info(f"Processamento per Claude completato: {original_filename}, tipo: {claude_format['metadata']['document_type']}")
            
            return claude_format
        except Exception as e:
            logger.error(f"Errore durante l'elaborazione per Claude: {e}")
            # Formato di fallback
            return {
                "metadata": {
                    "document_type": "error",
                    "file_name": original_filename,
                    "error": str(e),
                    "confidence_score": 0.0
                },
                "content": {},
                "summary": f"Si è verificato un errore durante l'elaborazione del documento: {str(e)}",
                "suggested_prompts": [
                    "Come posso risolvere l'errore di elaborazione?",
                    "Quali formati di file sono supportati da questo servizio?"
                ]
            }
        finally:
            # Pulisci il file temporaneo
            cleanup_temp_file(file_path)
    
    async def _process_image(
        self, 
        image_path: str, 
        document_type_hint: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Processa un'immagine
        
        Args:
            image_path: Percorso dell'immagine
            document_type_hint: Suggerimento sul tipo di documento
            
        Returns:
            Risultati del processamento
        """
        try:
            logger.info(f"Processamento immagine: {image_path}")
            
            # Estrai testo e analisi dall'immagine
            text, image_analysis = await self.image_processor.process_image(image_path)
            
            # Se il testo è troppo corto, usa direttamente Mistral Vision
            if len(text.strip()) < 200:
                logger.info(f"Testo OCR insufficiente ({len(text)} caratteri), uso diretto di Mistral Vision")
                analysis = await self.llm_service.analyze_document_image(image_path, document_type_hint)
                
                # Usa il testo estratto da Mistral Vision
                if "raw_text" in analysis and analysis["raw_text"]:
                    text = analysis["raw_text"]
            else:
                # Analizza il testo con l'LLM
                analysis = await self.llm_service.analyze_document_text(text, document_type_hint)
                analysis["raw_text"] = text
            
            # Aggiungi informazioni dall'analisi dell'immagine
            analysis["image_info"] = image_analysis.get("image_info", {})
            analysis["ocr_info"] = image_analysis.get("ocr_data", {})
            
            # Aggiungi note sul processamento
            processing_notes = []
            
            if analysis.get("error"):
                processing_notes.append(f"Errore nell'analisi: {analysis['error']}")
            
            if image_analysis.get("ocr_data", {}).get("confidence", 0) < 70:
                processing_notes.append("Bassa confidenza OCR, i risultati potrebbero non essere accurati")
            
            analysis["processing_notes"] = processing_notes
            
            logger.info(f"Processamento immagine completato: {image_path}")
            return analysis
        except Exception as e:
            logger.error(f"Errore durante il processamento dell'immagine {image_path}: {e}")
            raise
    
    async def _process_pdf(
        self, 
        pdf_path: str, 
        document_type_hint: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Processa un PDF
        
        Args:
            pdf_path: Percorso del PDF
            document_type_hint: Suggerimento sul tipo di documento
            
        Returns:
            Risultati del processamento
        """
        try:
            logger.info(f"Processamento PDF: {pdf_path}")
            
            # Estrai testo e metadati dal PDF
            result = await self.pdf_processor.process_pdf(pdf_path, document_type_hint)
            text = result.get("raw_text", "")
            
            # Se non abbiamo già un'analisi dal PDF processor, usa l'LLM
            if not result.get("extracted_data"):
                # Analizza il testo con l'LLM
                analysis = await self.llm_service.analyze_document_text(text, document_type_hint)
                
                # Aggiorna il risultato con l'analisi
                result.update(analysis)
                result["raw_text"] = text
            
            logger.info(f"Processamento PDF completato: {pdf_path}")
            return result
        except Exception as e:
            logger.error(f"Errore durante il processamento del PDF {pdf_path}: {e}")
            raise
