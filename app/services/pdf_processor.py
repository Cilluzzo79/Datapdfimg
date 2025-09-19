import os
import uuid
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
import pypdf
from pdf2image import convert_from_path
import tempfile

from app.config.settings import settings
from app.utils.logging_utils import get_logger
from app.services.ocr_service import OCRService
from app.services.image_processor import ImageProcessor

logger = get_logger(__name__)


class PDFProcessor:
    """Servizio per il processamento di file PDF"""
    
    def __init__(self):
        """Inizializza il servizio di processamento PDF"""
        self.ocr_service = OCRService()
        self.image_processor = ImageProcessor()
        logger.info("PDF Processor inizializzato")
    
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """
        Estrae il testo da un PDF nativo (con testo selezionabile)
        
        Args:
            pdf_path: Percorso del file PDF
            
        Returns:
            Testo estratto dal PDF
        """
        try:
            logger.info(f"Estrazione testo da PDF nativo: {pdf_path}")
            
            # Apri il PDF
            with open(pdf_path, 'rb') as file:
                pdf_reader = pypdf.PdfReader(file)
                
                # Estrai il testo da ogni pagina
                text = ""
                for page_num in range(len(pdf_reader.pages)):
                    page = pdf_reader.pages[page_num]
                    text += page.extract_text() + "\n\n"
            
            logger.info(f"Testo estratto da PDF nativo: {pdf_path}, {len(text)} caratteri")
            return text
        except Exception as e:
            logger.error(f"Errore durante l'estrazione del testo dal PDF nativo {pdf_path}: {e}")
            return ""
    
    def convert_pdf_to_images(self, pdf_path: str) -> List[str]:
        """
        Converte un PDF in una lista di immagini
        
        Args:
            pdf_path: Percorso del file PDF
            
        Returns:
            Lista di percorsi delle immagini generate
        """
        try:
            logger.info(f"Conversione PDF in immagini: {pdf_path}")
            
            # Crea directory temporanea
            temp_dir = Path(settings.TEMP_FOLDER)
            temp_dir.mkdir(parents=True, exist_ok=True)
            
            # Genera un prefisso unico per i file
            prefix = f"pdf_img_{uuid.uuid4()}"
            
            # Converti PDF in immagini
            images = convert_from_path(
                pdf_path,
                dpi=300,
                fmt="png",
                output_folder=str(temp_dir),
                output_file=prefix,
                paths_only=True
            )
            
            logger.info(f"PDF convertito in {len(images)} immagini: {pdf_path}")
            return images
        except Exception as e:
            logger.error(f"Errore durante la conversione del PDF in immagini {pdf_path}: {e}")
            return []
    
    def is_searchable_pdf(self, pdf_path: str) -> bool:
        """
        Verifica se un PDF contiene testo selezionabile
        
        Args:
            pdf_path: Percorso del file PDF
            
        Returns:
            True se il PDF contiene testo selezionabile, False altrimenti
        """
        try:
            logger.info(f"Verifica se il PDF è ricercabile: {pdf_path}")
            
            # Apri il PDF
            with open(pdf_path, 'rb') as file:
                pdf_reader = pypdf.PdfReader(file)
                
                # Verifica se c'è testo nelle prime pagine
                for page_num in range(min(3, len(pdf_reader.pages))):
                    page = pdf_reader.pages[page_num]
                    text = page.extract_text()
                    
                    # Se c'è almeno 100 caratteri di testo, considera il PDF ricercabile
                    if len(text.strip()) > 100:
                        logger.info(f"PDF ricercabile: {pdf_path}")
                        return True
            
            logger.info(f"PDF non ricercabile: {pdf_path}")
            return False
        except Exception as e:
            logger.error(f"Errore durante la verifica se il PDF è ricercabile {pdf_path}: {e}")
            return False
    
    def get_pdf_metadata(self, pdf_path: str) -> Dict[str, Any]:
        """
        Ottiene i metadati da un PDF
        
        Args:
            pdf_path: Percorso del file PDF
            
        Returns:
            Dizionario con metadati del PDF
        """
        try:
            logger.info(f"Recupero metadati PDF: {pdf_path}")
            
            # Apri il PDF
            with open(pdf_path, 'rb') as file:
                pdf_reader = pypdf.PdfReader(file)
                
                # Ottieni metadati
                metadata = pdf_reader.metadata
                
                # Converti in dizionario
                if metadata:
                    metadata_dict = {
                        "title": metadata.get("/Title", ""),
                        "author": metadata.get("/Author", ""),
                        "subject": metadata.get("/Subject", ""),
                        "creator": metadata.get("/Creator", ""),
                        "producer": metadata.get("/Producer", ""),
                        "creation_date": metadata.get("/CreationDate", ""),
                        "modification_date": metadata.get("/ModDate", "")
                    }
                else:
                    metadata_dict = {}
                
                # Aggiungi informazioni sulle pagine
                metadata_dict["page_count"] = len(pdf_reader.pages)
                
                # Aggiungi dimensioni delle pagine
                page_sizes = []
                for page_num in range(min(3, len(pdf_reader.pages))):
                    page = pdf_reader.pages[page_num]
                    width = page.mediabox.width
                    height = page.mediabox.height
                    page_sizes.append({"width": width, "height": height})
                
                metadata_dict["page_sizes"] = page_sizes
                
                logger.info(f"Metadati PDF recuperati: {pdf_path}")
                return metadata_dict
        except Exception as e:
            logger.error(f"Errore durante il recupero dei metadati del PDF {pdf_path}: {e}")
            return {"error": str(e)}
    
    def process_pdf(self, pdf_path: str) -> Tuple[str, Dict[str, Any]]:
        """
        Processa un PDF ed estrae testo e informazioni
        
        Args:
            pdf_path: Percorso del file PDF
            
        Returns:
            Tupla con testo estratto e informazioni sul PDF
        """
        try:
            logger.info(f"Processamento PDF: {pdf_path}")
            
            # Ottieni metadati
            metadata = self.get_pdf_metadata(pdf_path)
            
            # Verifica se il PDF è ricercabile
            is_searchable = self.is_searchable_pdf(pdf_path)
            
            text = ""
            ocr_results = []
            
            if is_searchable:
                # Estrai testo direttamente dal PDF
                text = self.extract_text_from_pdf(pdf_path)
            else:
                # Converti PDF in immagini e esegui OCR
                images = self.convert_pdf_to_images(pdf_path)
                
                # Processa ogni immagine
                page_texts = []
                for idx, image_path in enumerate(images):
                    logger.info(f"OCR sulla pagina {idx+1}/{len(images)}: {image_path}")
                    
                    # Processa l'immagine
                    page_text, page_analysis = self.image_processor.process_image(image_path)
                    page_texts.append(page_text)
                    
                    # Aggiungi risultati OCR
                    ocr_results.append({
                        "page": idx + 1,
                        "confidence": page_analysis["ocr_data"]["confidence"],
                        "words_count": page_analysis["ocr_data"]["words_count"]
                    })
                    
                    # Elimina l'immagine temporanea
                    os.remove(image_path)
                
                # Combina il testo di tutte le pagine
                text = "\n\n".join(page_texts)
            
            # Prepara i risultati
            results = {
                "metadata": metadata,
                "is_searchable": is_searchable,
                "page_count": metadata["page_count"],
                "text_length": len(text),
                "ocr_results": ocr_results if ocr_results else None
            }
            
            logger.info(f"Processamento PDF completato: {pdf_path}, {len(text)} caratteri estratti")
            return text, results
        except Exception as e:
            logger.error(f"Errore durante il processamento del PDF {pdf_path}: {e}")
            return "", {"error": str(e)}
