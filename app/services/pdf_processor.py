"""
Servizio per l'elaborazione di file PDF
"""
import io
import os
import tempfile
from typing import Dict, Any, List, Optional, Tuple
from fastapi import UploadFile
import fitz  # PyMuPDF
from pypdf import PdfReader
import base64
from PIL import Image

# Importazione condizionale per evitare errori se manca pytesseract
try:
    import pytesseract
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False


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
            
            # Estrai il testo in base al tipo di PDF
            if is_native:
                # PDF nativo con testo
                text, images, metadata = PDFProcessor._extract_from_native_pdf(file_obj)
            else:
                # PDF scansionato (immagini)
                text, images, metadata = PDFProcessor._extract_from_scanned_pdf(file_obj)
            
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
                    "text": text,
                    "images_count": len(images)
                },
                "processing_notes": []
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
    def _extract_from_native_pdf(pdf_file: io.BytesIO) -> Tuple[Dict[int, str], List[Dict[str, Any]], Dict[str, Any]]:
        """
        Estrae testo e metadati da un PDF nativo
        
        Args:
            pdf_file: File PDF come BytesIO
            
        Returns:
            Tuple con (text_by_page, images, metadata)
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
        images = []
        
        # Usa PyMuPDF per estrarre immagini e testo formattato
        pdf_file.seek(0)
        try:
            with fitz.open(stream=pdf_file.read(), filetype="pdf") as doc:
                for page_num, page in enumerate(doc):
                    # Estrai il testo
                    text_by_page[page_num] = page.get_text()
                    
                    # Estrai le immagini
                    image_list = page.get_images(full=True)
                    for img_index, img in enumerate(image_list):
                        xref = img[0]
                        base_image = doc.extract_image(xref)
                        image_data = base_image["image"]
                        image_ext = base_image["ext"]
                        
                        # Salva l'immagine come base64
                        image_base64 = base64.b64encode(image_data).decode('utf-8')
                        
                        images.append({
                            "page": page_num,
                            "index": img_index,
                            "extension": image_ext,
                            "size": len(image_data),
                            "base64": image_base64[:100] + "..." if len(image_base64) > 100 else image_base64
                        })
        except Exception as e:
            # Fallback a PyPDF se PyMuPDF fallisce
            pdf_file.seek(0)
            for i, page in enumerate(reader.pages):
                text = page.extract_text()
                text_by_page[i] = text if text else ""
        
        return text_by_page, images, metadata
    
    @staticmethod
    def _extract_from_scanned_pdf(pdf_file: io.BytesIO) -> Tuple[Dict[int, str], List[Dict[str, Any]], Dict[str, Any]]:
        """
        Estrae testo e immagini da un PDF scansionato usando OCR
        
        Args:
            pdf_file: File PDF come BytesIO
            
        Returns:
            Tuple con (text_by_page, images, metadata)
        """
        # Verifica se tesseract è disponibile
        if not TESSERACT_AVAILABLE:
            return (
                {0: "OCR non disponibile: pytesseract non installato"},
                [],
                {"error": "OCR non disponibile"}
            )
        
        text_by_page = {}
        images = []
        metadata = {}
        
        # Estrai i metadati base con PyPDF
        reader = PdfReader(pdf_file)
        if reader.metadata:
            for key, value in reader.metadata.items():
                if key and value and key.startswith('/'):
                    metadata[key[1:]] = str(value)
        
        # Usa PyMuPDF per convertire le pagine in immagini
        pdf_file.seek(0)
        
        try:
            with fitz.open(stream=pdf_file.read(), filetype="pdf") as doc:
                for page_num, page in enumerate(doc):
                    # Renderizza la pagina come immagine
                    pix = page.get_pixmap(matrix=fitz.Matrix(300/72, 300/72))
                    
                    # Converti in immagine PIL
                    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                    
                    # Esegui OCR
                    text = pytesseract.image_to_string(img, lang='ita+eng')
                    text_by_page[page_num] = text
                    
                    # Salva l'immagine
                    img_byte_arr = io.BytesIO()
                    img.save(img_byte_arr, format='JPEG')
                    img_byte_arr = img_byte_arr.getvalue()
                    
                    # Converti in base64
                    image_base64 = base64.b64encode(img_byte_arr).decode('utf-8')
                    
                    images.append({
                        "page": page_num,
                        "extension": "jpeg",
                        "size": len(img_byte_arr),
                        "base64": image_base64[:100] + "..." if len(image_base64) > 100 else image_base64
                    })
        except Exception as e:
            text_by_page[0] = f"Errore nell'OCR: {str(e)}"
            metadata["error"] = str(e)
        
        return text_by_page, images, metadata
    
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
