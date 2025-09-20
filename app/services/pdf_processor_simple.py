"""
Servizio per l'elaborazione di file PDF (versione semplificata)
"""
import io
from typing import Dict, Any, List, Optional, Tuple
from fastapi import UploadFile
from pypdf import PdfReader

from app.config import settings

class PDFProcessor:
    """
    Classe per l'elaborazione di file PDF
    """
    
    @staticmethod
    async def process_pdf(
        file: UploadFile,
        document_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Elabora un file PDF e lo converte in formato JSON
        
        Args:
            file: File PDF caricato
            document_type: Tipo di documento (opzionale)
            
        Returns:
            Dizionario con i dati estratti dal file PDF
        """
        try:
            # Leggi il contenuto del file
            content = await file.read()
            file_obj = io.BytesIO(content)
            
            # Verifica se è un PDF nativo o scansionato
            is_native, page_count = PDFProcessor._check_pdf_type(file_obj)
            
            # Riposiziona il cursore all'inizio
            file_obj.seek(0)
            
            # Estrai testo e metadati (versione base senza PyMuPDF o OCR)
            text, metadata = PDFProcessor._extract_from_pdf_base(file_obj)
            
            # Analisi del tipo di documento
            detected_type = document_type or PDFProcessor._detect_document_type(text, file.filename)
            
            # Crea il risultato
            result = {
                "document_type": detected_type,
                "metadata": {
                    "original_filename": file.filename,
                    "file_type": "pdf",
                    "is_native": is_native,
                    "page_count": page_count,
                    "pdf_metadata": metadata
                },
                "extracted_data": {
                    "text": text
                },
                "processing_notes": ["Estrazione PDF base senza OCR"]
            }
            
            # Riposiziona il cursore all'inizio del file
            await file.seek(0)
            
            return result
        except Exception as e:
            # Gestione degli errori
            error_details = {
                "error_type": str(type(e).__name__),
                "error_message": str(e),
                "filename": file.filename,
            }
            return {
                "document_type": "error",
                "metadata": {
                    "original_filename": file.filename,
                    "file_type": "pdf",
                    "error": str(e)
                },
                "processing_notes": [f"Errore durante l'elaborazione del PDF: {str(e)}"],
                "error_details": error_details
            }
    
    @staticmethod
    def _check_pdf_type(pdf_file: io.BytesIO) -> Tuple[bool, int]:
        """
        Verifica se un PDF è nativo (con testo) o scansionato (immagini)
        
        Args:
            pdf_file: File PDF come BytesIO
            
        Returns:
            Tuple con (is_native, page_count)
        """
        # Usa PyPDF per verificare il contenuto
        reader = PdfReader(pdf_file)
        page_count = len(reader.pages)
        
        # Un PDF è considerato nativo se ha almeno un minimo di testo
        # in almeno una pagina
        min_text_length = 50  # Caratteri minimi per considerarlo nativo
        is_native = False
        
        for page in reader.pages:
            text = page.extract_text()
            if text and len(text.strip()) > min_text_length:
                is_native = True
                break
        
        # Riposiziona il cursore all'inizio
        pdf_file.seek(0)
        
        return is_native, page_count
    
    @staticmethod
    def _extract_from_pdf_base(pdf_file: io.BytesIO) -> Tuple[Dict[int, str], Dict[str, Any]]:
        """
        Estrae testo e metadati da un PDF usando solo PyPDF
        
        Args:
            pdf_file: File PDF come BytesIO
            
        Returns:
            Tuple con (text_by_page, metadata)
        """
        # Usa PyPDF per estrarre testo e metadati
        reader = PdfReader(pdf_file)
        metadata = {}
        
        # Estrai i metadati
        if reader.metadata:
            for key, value in reader.metadata.items():
                if key and value and key.startswith('/'):
                    metadata[key[1:]] = str(value)
        
        # Estrai il testo pagina per pagina
        text_by_page = {}
        for i, page in enumerate(reader.pages):
            text = page.extract_text()
            text_by_page[i] = text if text else ""
        
        return text_by_page, metadata
    
    @staticmethod
    def _detect_document_type(text_content: Dict[int, str], filename: str) -> str:
        """
        Rileva il tipo di documento in base al contenuto
        
        Args:
            text_content: Testo estratto dal PDF
            filename: Nome del file
            
        Returns:
            Tipo di documento rilevato
        """
        # Combina tutto il testo
        all_text = " ".join(text_content.values()).lower()
        filename_lower = filename.lower()
        
        # Cerca parole chiave nel testo e nel nome del file
        if any(keyword in filename_lower for keyword in ["fattura", "invoice"]) or any(keyword in all_text for keyword in ["fattura", "invoice", "partita iva", "codice fiscale", "imponibile", "iva"]):
            return "fattura"
        elif any(keyword in filename_lower for keyword in ["bilancio", "balance"]) or any(keyword in all_text for keyword in ["bilancio", "stato patrimoniale", "conto economico", "balance sheet", "income statement"]):
            return "bilancio"
        elif any(keyword in filename_lower for keyword in ["magazzino", "inventory", "stock"]) or any(keyword in all_text for keyword in ["magazzino", "inventario", "stock", "quantità", "giacenza"]):
            return "magazzino"
        elif any(keyword in filename_lower for keyword in ["corrispettivo", "receipt", "scontrino"]) or any(keyword in all_text for keyword in ["corrispettivo", "scontrino", "ricevuta", "receipt"]):
            return "corrispettivo"
        elif any(keyword in filename_lower for keyword in ["analisi", "report", "analysis", "market"]) or any(keyword in all_text for keyword in ["analisi", "report", "mercato", "trend", "previsioni", "forecast"]):
            return "analisi_mercato"
        
        # Default
        return "documento_generico"