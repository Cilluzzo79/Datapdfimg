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
    cleanup_temp_file
)
from app.services.image_processor import ImageProcessor
from app.services.pdf_processor import PDFProcessor
from app.services.llm_service import LLMService
from app.models.document import (
    DocumentType, 
    FileType, 
    DocumentMetadata, 
    DocumentProcessingResult,
    ProcessingRequest
)

logger = get_logger(__name__)


class DocumentProcessor:
    """Service principale per il processamento dei documenti"""
    
    def __init__(self):
        """Inizializza il servizio di processamento documenti"""
        self.image_processor = ImageProcessor()
        self.pdf_processor = PDFProcessor()
        self.llm_service = LLMService()
        logger.info("Document Processor inizializzato")
    
    async def process_document(
        self, 
        file_path: str, 
        original_filename: str, 
        file_size: int,
        md5_hash: str,
        request: Optional[ProcessingRequest] = None
    ) -> DocumentProcessingResult:
        """
        Processa un documento e restituisce i risultati
        
        Args:
            file_path: Percorso del file
            original_filename: Nome originale del file
            file_size: Dimensione del file in byte
            md5_hash: Hash MD5 del file
            request: Richiesta di processamento (opzionale)
            
        Returns:
            Risultato del processamento del documento
        """
        start_time = time.time()
        
        try:
            logger.info(f"Inizio processamento documento: {original_filename}")
            
            # Crea richiesta se non fornita
            if not request:
                request = ProcessingRequest()
            
            # Determina il tipo di file
            file_extension = get_file_extension(original_filename)
            if is_allowed_image(original_filename):
                file_type = FileType(file_extension.lower())
                result = await self._process_image(file_path, request.document_type_hint)
            elif is_allowed_pdf(original_filename):
                file_type = FileType.PDF
                result = await self._process_pdf(file_path, request.document_type_hint)
            else:
                raise ValueError(f"Tipo di file non supportato: {file_extension}")
            
            # Calcola il tempo di processamento
            processing_time_ms = int((time.time() - start_time) * 1000)
            
            # Crea i metadati
            metadata = DocumentMetadata(
                original_filename=original_filename,
                file_type=file_type,
                file_size=file_size,
                pages_processed=result.get("metadata", {}).get("page_count", 1) if "metadata" in result else 1,
                processing_time_ms=processing_time_ms,
                md5_hash=md5_hash
            )
            
            # Crea il risultato
            document_result = DocumentProcessingResult(
                document_id=request.document_id,
                document_type=DocumentType(result.get("document_type", "sconosciuto")),
                confidence_score=result.get("confidence_score", 0.0),
                metadata=metadata,
                extracted_data=result.get("extracted_data", {}),
                raw_text=result.get("raw_text", ""),
                processing_notes=result.get("processing_notes", []),
                llm_ready=True
            )
            
            logger.info(f"Processamento documento completato: {original_filename}, "
                        f"tipo: {document_result.document_type}, "
                        f"confidence: {document_result.confidence_score:.2f}, "
                        f"tempo: {processing_time_ms}ms")
            
            return document_result
        except Exception as e:
            logger.error(f"Errore durante il processamento del documento {original_filename}: {e}")
            
            # Calcola il tempo di processamento anche in caso di errore
            processing_time_ms = int((time.time() - start_time) * 1000)
            
            # Crea metadati minimi
            metadata = DocumentMetadata(
                original_filename=original_filename,
                file_type=FileType(get_file_extension(original_filename).lower()),
                file_size=file_size,
                pages_processed=0,
                processing_time_ms=processing_time_ms,
                md5_hash=md5_hash
            )
            
            # Crea risultato di errore
            document_result = DocumentProcessingResult(
                document_id=request.document_id if request else str(uuid.uuid4()),
                document_type=DocumentType.SCONOSCIUTO,
                confidence_score=0.0,
                metadata=metadata,
                extracted_data={},
                raw_text="",
                processing_notes=[f"Errore durante il processamento: {str(e)}"],
                llm_ready=False
            )
            
            return document_result
        finally:
            # Pulisci il file temporaneo
            cleanup_temp_file(file_path)
    
    async def _process_image(
        self, 
        image_path: str, 
        document_type_hint: Optional[DocumentType] = None
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
            if len(text.strip()) < 200 and settings.ENABLE_MISTRAL_VISION:
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
            
            # Se disponibile, aggiungi i dati di Mistral Vision
            if "mistral_vision" in image_analysis:
                analysis["mistral_vision"] = image_analysis["mistral_vision"]
                
                # Se Mistral Vision ha rilevato un tipo di documento, usalo
                if "document_type" in image_analysis["mistral_vision"]:
                    detected_type = image_analysis["mistral_vision"]["document_type"]
                    confidence = image_analysis["mistral_vision"]["confidence"]
                    
                    if confidence > 0.7:  # Usa solo se abbastanza confidenza
                        analysis["document_type"] = detected_type
                        analysis["confidence_score"] = confidence
                        logger.info(f"Utilizzato tipo documento da Mistral Vision: {detected_type} ({confidence:.2f})")
                
                # Se Mistral Vision ha estratto dati, aggiungili
                if "extracted_data" in image_analysis["mistral_vision"]:
                    analysis["extracted_data"] = image_analysis["mistral_vision"]["extracted_data"]
                    logger.info("Aggiunti dati estratti da Mistral Vision")
            
            # Aggiungi note sul processamento
            processing_notes = []
            
            if analysis.get("error"):
                processing_notes.append(f"Errore nell'analisi: {analysis['error']}")
            
            if image_analysis.get("ocr_data", {}).get("confidence", 0) < 70:
                processing_notes.append("Bassa confidenza OCR, i risultati potrebbero non essere accurati")
            
            if "mistral_vision_error" in image_analysis:
                processing_notes.append(f"Errore nell'analisi Mistral Vision: {image_analysis['mistral_vision_error']}")
                
            if settings.ENABLE_MISTRAL_VISION and "mistral_vision" in image_analysis:
                processing_notes.append(f"Analisi avanzata con Mistral Vision completata")
            
            analysis["processing_notes"] = processing_notes
            
            logger.info(f"Processamento immagine completato: {image_path}")
            return analysis
        except Exception as e:
            logger.error(f"Errore durante il processamento dell'immagine {image_path}: {e}")
            raise
    
    async def _process_pdf(
        self, 
        pdf_path: str, 
        document_type_hint: Optional[DocumentType] = None
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
            text, pdf_info = self.pdf_processor.process_pdf(pdf_path)
            
            # Analizza il testo con l'LLM
            analysis = await self.llm_service.analyze_document_text(text, document_type_hint)
            
            # Aggiungi informazioni dal PDF
            analysis["metadata"] = pdf_info.get("metadata", {})
            analysis["raw_text"] = text
            
            # Aggiungi note sul processamento
            processing_notes = []
            
            if analysis.get("error"):
                processing_notes.append(f"Errore nell'analisi: {analysis['error']}")
            
            if pdf_info.get("error"):
                processing_notes.append(f"Errore nell'estrazione PDF: {pdf_info['error']}")
            
            if pdf_info.get("is_searchable") is False:
                processing_notes.append("PDF non ricercabile, testo estratto tramite OCR")
                
                # Aggiungi informazioni OCR
                if pdf_info.get("ocr_results"):
                    avg_confidence = sum(r.get("confidence", 0) for r in pdf_info["ocr_results"]) / len(pdf_info["ocr_results"])
                    if avg_confidence < 70:
                        processing_notes.append(f"Bassa confidenza OCR ({avg_confidence:.2f}%), i risultati potrebbero non essere accurati")
            
            analysis["processing_notes"] = processing_notes
            
            logger.info(f"Processamento PDF completato: {pdf_path}")
            return analysis
        except Exception as e:
            logger.error(f"Errore durante il processamento del PDF {pdf_path}: {e}")
            raise