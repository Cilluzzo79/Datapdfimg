from PIL import Image, ImageEnhance, ImageFilter
import os
from typing import List, Dict, Any, Optional, Tuple
import uuid
from pathlib import Path

from app.config.settings import settings
from app.utils.logging_utils import get_logger
from app.services.ocr_service import OCRService
from app.services.mistral_vision import MistralVisionService

logger = get_logger(__name__)


class ImageProcessor:
    """Servizio per il processamento di immagini"""
    
    def __init__(self):
        """Inizializza il servizio di processamento immagini"""
        self.ocr_service = OCRService()
        self.mistral_vision_enabled = settings.ENABLE_MISTRAL_VISION
        if self.mistral_vision_enabled:
            self.mistral_vision = MistralVisionService()
            logger.info("Image Processor inizializzato con supporto Mistral Vision")
        else:
            logger.info("Image Processor inizializzato (Mistral Vision disabilitato)")
    
    def preprocess_image(self, image_path: str) -> str:
        """
        Preprocessa un'immagine per migliorare i risultati dell'OCR
        
        Args:
            image_path: Percorso dell'immagine
            
        Returns:
            Percorso dell'immagine preprocessata
        """
        try:
            logger.info(f"Preprocessamento immagine: {image_path}")
            
            # Carica l'immagine
            image = Image.open(image_path)
            
            # Converti in scala di grigi
            if image.mode != 'L':
                image = image.convert('L')
            
            # Aumenta il contrasto
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(2.0)
            
            # Applica filtro di nitidezza
            image = image.filter(ImageFilter.SHARPEN)
            
            # Applica soglia (binarizzazione)
            threshold_value = 200
            image = image.point(lambda p: 255 if p > threshold_value else 0)
            
            # Salva l'immagine preprocessata
            temp_dir = Path(settings.TEMP_FOLDER)
            temp_dir.mkdir(parents=True, exist_ok=True)
            
            preprocessed_path = temp_dir / f"preprocessed_{uuid.uuid4()}.png"
            image.save(preprocessed_path)
            
            logger.info(f"Immagine preprocessata salvata in: {preprocessed_path}")
            return str(preprocessed_path)
        except Exception as e:
            logger.error(f"Errore durante il preprocessamento dell'immagine {image_path}: {e}")
            return image_path  # Restituisci l'immagine originale in caso di errore
    
    def extract_text(self, image_path: str, preprocess: bool = True) -> str:
        """
        Estrae il testo da un'immagine
        
        Args:
            image_path: Percorso dell'immagine
            preprocess: Se True, preprocessa l'immagine prima dell'OCR
            
        Returns:
            Testo estratto dall'immagine
        """
        try:
            if preprocess:
                preprocessed_path = self.preprocess_image(image_path)
                text = self.ocr_service.extract_text_from_image(preprocessed_path)
                
                # Rimuovi l'immagine preprocessata
                if preprocessed_path != image_path:
                    os.remove(preprocessed_path)
            else:
                text = self.ocr_service.extract_text_from_image(image_path)
            
            return text
        except Exception as e:
            logger.error(f"Errore durante l'estrazione del testo dall'immagine {image_path}: {e}")
            return ""
    
    def analyze_image(self, image_path: str) -> Dict[str, Any]:
        """
        Analizza un'immagine ed estrae informazioni
        
        Args:
            image_path: Percorso dell'immagine
            
        Returns:
            Dizionario con informazioni sull'immagine
        """
        try:
            logger.info(f"Analisi immagine: {image_path}")
            
            # Carica l'immagine
            image = Image.open(image_path)
            
            # Ottieni informazioni di base
            width, height = image.size
            format_type = image.format
            mode = image.mode
            
            # Preprocessa l'immagine
            preprocessed_path = self.preprocess_image(image_path)
            
            # Esegui OCR sull'immagine preprocessata
            ocr_data = self.ocr_service.get_ocr_data(preprocessed_path)
            
            # Rimuovi l'immagine preprocessata
            if preprocessed_path != image_path:
                os.remove(preprocessed_path)
            
            # Raccogli i risultati
            analysis = {
                "image_info": {
                    "width": width,
                    "height": height,
                    "format": format_type,
                    "mode": mode,
                    "aspect_ratio": width / height if height != 0 else 0
                },
                "ocr_data": ocr_data
            }
            
            logger.info(f"Analisi immagine completata per {image_path}")
            return analysis
        except Exception as e:
            logger.error(f"Errore durante l'analisi dell'immagine {image_path}: {e}")
            return {
                "image_info": {},
                "ocr_data": {
                    "text": "",
                    "confidence": 0,
                    "words_count": 0,
                    "has_text": False,
                    "error": str(e)
                }
            }
    
    async def process_image(self, image_path: str) -> Tuple[str, Dict[str, Any]]:
        """
        Processa un'immagine ed estrae testo e informazioni
        
        Args:
            image_path: Percorso dell'immagine
            
        Returns:
            Tupla con testo estratto e informazioni sull'immagine
        """
        try:
            logger.info(f"Processamento immagine: {image_path}")
            
            # Analizza l'immagine
            analysis = self.analyze_image(image_path)
            
            # Estrai il testo
            text = analysis["ocr_data"]["text"]
            
            # Se Mistral Vision è abilitato, utilizza l'API per analisi avanzata
            if self.mistral_vision_enabled and settings.ENABLE_IMAGE_PROCESSING:
                try:
                    logger.info(f"Utilizzo Mistral Vision per analisi avanzata: {image_path}")
                    
                    # Rileva il tipo di documento
                    document_type_result = await self.mistral_vision.detect_document_type(image_path)
                    detected_type = document_type_result.get("document_type", "generico")
                    
                    # Estrai i dati strutturati dal documento
                    extracted_data = await self.mistral_vision.extract_document_data(image_path, detected_type)
                    
                    # Aggiungi i dati all'analisi
                    analysis["mistral_vision"] = {
                        "document_type": detected_type,
                        "confidence": document_type_result.get("confidence", 0.0),
                        "extracted_data": extracted_data.get("data", {}),
                        "language": document_type_result.get("language", "sconosciuto")
                    }
                    
                    # Se il testo OCR è scarso ma Mistral ha estratto del testo, utilizzalo
                    if len(text.strip()) < 100 and "raw_text" in extracted_data:
                        text = extracted_data.get("raw_text", text)
                        logger.info("Utilizzato testo estratto da Mistral Vision")
                    
                    logger.info(f"Analisi Mistral Vision completata per {image_path}")
                except Exception as e:
                    logger.error(f"Errore durante l'analisi Mistral Vision: {e}")
                    analysis["mistral_vision_error"] = str(e)
            
            logger.info(f"Processamento immagine completato per {image_path}")
            return text, analysis
        except Exception as e:
            logger.error(f"Errore durante il processamento dell'immagine {image_path}: {e}")
            return "", {
                "image_info": {},
                "ocr_data": {
                    "text": "",
                    "confidence": 0,
                    "words_count": 0,
                    "has_text": False,
                    "error": str(e)
                }
            }