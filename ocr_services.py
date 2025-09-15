import pytesseract
from PIL import Image
import os
from typing import List, Dict, Any, Optional
import tempfile

from app.config.settings import settings
from app.utils.logging_utils import get_logger

logger = get_logger(__name__)


class OCRService:
    """Servizio per l'OCR di immagini"""
    
    def __init__(self, language: Optional[str] = None):
        """
        Inizializza il servizio OCR
        
        Args:
            language: Lingua da utilizzare per l'OCR (formato ISO 639-2)
                     Default: impostazione da config (ita+eng)
        """
        self.language = language or settings.OCR_LANGUAGE
        logger.info(f"OCR Service inizializzato con lingua: {self.language}")
    
    def extract_text_from_image(self, image_path: str) -> str:
        """
        Estrae il testo da un'immagine usando pytesseract
        
        Args:
            image_path: Percorso dell'immagine
            
        Returns:
            Testo estratto dall'immagine
        """
        try:
            logger.info(f"Esecuzione OCR su: {image_path}")
            
            # Carica l'immagine
            image = Image.open(image_path)
            
            # Esegui OCR con pytesseract
            ocr_config = f'--oem 3 --psm 6 -l {self.language}'
            text = pytesseract.image_to_string(image, config=ocr_config)
            
            logger.info(f"OCR completato per {image_path}, estratti {len(text)} caratteri")
            return text
        except Exception as e:
            logger.error(f"Errore durante l'OCR dell'immagine {image_path}: {e}")
            return ""
    
    def extract_text_from_images(self, image_paths: List[str]) -> str:
        """
        Estrae il testo da più immagini
        
        Args:
            image_paths: Lista di percorsi delle immagini
            
        Returns:
            Testo estratto dalle immagini concatenato
        """
        all_text = []
        
        for idx, image_path in enumerate(image_paths):
            logger.info(f"Elaborazione immagine {idx+1}/{len(image_paths)}: {image_path}")
            text = self.extract_text_from_image(image_path)
            all_text.append(text)
        
        combined_text = "\n\n".join(all_text)
        logger.info(f"OCR completato per {len(image_paths)} immagini, estratti {len(combined_text)} caratteri totali")
        return combined_text
    
    def get_ocr_data(self, image_path: str) -> Dict[str, Any]:
        """
        Ottiene dati OCR strutturati da un'immagine
        
        Args:
            image_path: Percorso dell'immagine
            
        Returns:
            Dizionario con testo e dati OCR
        """
        try:
            logger.info(f"Recupero dati OCR da: {image_path}")
            
            # Carica l'immagine
            image = Image.open(image_path)
            
            # Esegui OCR con pytesseract per il testo
            ocr_config = f'--oem 3 --psm 6 -l {self.language}'
            text = pytesseract.image_to_string(image, config=ocr_config)
            
            # Ottieni dati sulle caselle di testo
            boxes = pytesseract.image_to_data(image, config=ocr_config, output_type=pytesseract.Output.DICT)
            
            # Ottieni informazioni sulla struttura della pagina
            hocr_data = pytesseract.image_to_pdf_or_hocr(
                image, 
                extension='hocr', 
                config=ocr_config
            )
            
            ocr_data = {
                "text": text,
                "boxes": boxes,
                "confidence": sum(boxes['conf']) / len(boxes['conf']) if boxes['conf'] else 0,
                "words_count": len([w for w in boxes['text'] if w.strip()]),
                "has_text": bool(text.strip())
            }
            
            logger.info(f"Dati OCR recuperati per {image_path}, confidence: {ocr_data['confidence']:.2f}%")
            return ocr_data
        except Exception as e:
            logger.error(f"Errore durante il recupero dei dati OCR da {image_path}: {e}")
            return {
                "text": "",
                "boxes": {},
                "confidence": 0,
                "words_count": 0,
                "has_text": False,
                "error": str(e)
            }
