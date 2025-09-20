import base64
import json
import aiohttp
import os
from typing import Dict, Any, Optional, List
from PIL import Image
import io
from pathlib import Path

from app.config.settings import settings
from app.utils.logging_utils import get_logger

logger = get_logger(__name__)

class MistralVisionService:
    """Servizio per l'integrazione con Mistral Vision API"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Inizializza il servizio Mistral Vision
        
        Args:
            api_key: Chiave API per Mistral (opzionale, altrimenti usa quella in settings)
        """
        self.api_key = api_key or settings.MISTRAL_API_KEY
        self.api_url = "https://api.mistral.ai/v1/chat/completions"
        
        if not self.api_key:
            logger.warning("Nessuna API key Mistral configurata. Il servizio non sarà disponibile.")
            
        logger.info("Mistral Vision Service inizializzato")
    
    def _encode_image(self, image_path: str) -> str:
        """
        Codifica un'immagine in base64
        
        Args:
            image_path: Percorso dell'immagine
            
        Returns:
            Stringa base64 dell'immagine
        """
        try:
            with open(image_path, "rb") as image_file:
                return base64.b64encode(image_file.read()).decode('utf-8')
        except Exception as e:
            logger.error(f"Errore durante la codifica dell'immagine {image_path}: {e}")
            raise
    
    async def analyze_image(self, 
                           image_path: str, 
                           prompt: str = "Analizza questa immagine e estrai tutte le informazioni rilevanti in formato JSON") -> Dict[str, Any]:
        """
        Analizza un'immagine usando Mistral Vision API
        
        Args:
            image_path: Percorso dell'immagine
            prompt: Prompt da utilizzare per l'analisi dell'immagine
            
        Returns:
            Risposta dell'API Mistral Vision
        """
        if not self.api_key:
            logger.error("Impossibile analizzare l'immagine: API key Mistral non configurata")
            return {
                "error": "API key Mistral non configurata",
                "success": False,
                "raw_text": ""
            }
        
        try:
            logger.info(f"Analisi immagine con Mistral Vision: {image_path}")
            
            # Codifica l'immagine in base64
            image_base64 = self._encode_image(image_path)
            
            # Costruisci il prompt per Mistral Vision
            messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_base64}"
                            }
                        }
                    ]
                }
            ]
            
            # Prepara la richiesta
            payload = {
                "model": "mistral-large-latest",  # modello che supporta visione
                "messages": messages,
                "temperature": 0.2,  # bassa temperatura per risposta più deterministica
                "max_tokens": 2048,
                "response_format": {"type": "json_object"}  # richiedi risposta in formato JSON
            }
            
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
            
            # Effettua la chiamata API
            async with aiohttp.ClientSession() as session:
                async with session.post(self.api_url, json=payload, headers=headers) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"Errore nella chiamata API Mistral: {response.status} - {error_text}")
                        return {
                            "error": f"Errore API: {response.status}",
                            "details": error_text,
                            "success": False,
                            "raw_text": ""
                        }
                    
                    # Estrai il risultato
                    result = await response.json()
                    
                    # Estrai il testo dalla risposta
                    raw_text = result.get("choices", [{}])[0].get("message", {}).get("content", "")
                    
                    # Prova a parsare il JSON dalla risposta
                    try:
                        # La risposta dovrebbe essere già in formato JSON
                        parsed_data = json.loads(raw_text)
                        
                        return {
                            "success": True,
                            "raw_text": raw_text,
                            "parsed_data": parsed_data
                        }
                    except json.JSONDecodeError as e:
                        logger.warning(f"Impossibile parsare la risposta JSON da Mistral: {e}")
                        return {
                            "success": True,
                            "raw_text": raw_text,
                            "error": "Formato risposta non valido",
                            "parsed_data": {}
                        }
                    
        except Exception as e:
            logger.error(f"Errore durante l'analisi dell'immagine con Mistral Vision: {e}")
            return {
                "error": str(e),
                "success": False,
                "raw_text": ""
            }
    
    async def detect_document_type(self, image_path: str) -> Dict[str, Any]:
        """
        Rileva il tipo di documento da un'immagine
        
        Args:
            image_path: Percorso dell'immagine
            
        Returns:
            Tipo di documento rilevato e confidenza
        """
        prompt = """
        Analizza questa immagine e identifica il tipo di documento business. 
        Restituisci la risposta in formato JSON con i seguenti campi:
        - document_type: tipo di documento (fattura, scontrino, documento identità, bilancio, documento generico, altro)
        - confidence: confidenza della classificazione da 0.0 a 1.0
        - details: dettagli aggiuntivi sul documento
        - language: lingua del documento
        """
        
        result = await self.analyze_image(image_path, prompt)
        
        if not result.get("success"):
            return {
                "document_type": "sconosciuto",
                "confidence": 0.0,
                "error": result.get("error", "Errore sconosciuto")
            }
        
        try:
            data = result.get("parsed_data", {})
            return {
                "document_type": data.get("document_type", "sconosciuto").lower(),
                "confidence": data.get("confidence", 0.0),
                "details": data.get("details", ""),
                "language": data.get("language", "sconosciuto")
            }
        except Exception as e:
            logger.error(f"Errore durante l'elaborazione dei risultati: {e}")
            return {
                "document_type": "sconosciuto",
                "confidence": 0.0,
                "error": str(e)
            }
    
    async def extract_document_data(self, image_path: str, document_type: str = "generico") -> Dict[str, Any]:
        """
        Estrae dati strutturati da un'immagine di documento
        
        Args:
            image_path: Percorso dell'immagine
            document_type: Tipo di documento per ottimizzare l'estrazione
            
        Returns:
            Dati estratti dal documento
        """
        # Costruisci prompt in base al tipo di documento
        if document_type.lower() == "fattura":
            prompt = """
            Analizza questa fattura ed estrai tutti i dati rilevanti.
            Restituisci la risposta in formato JSON con i seguenti campi:
            - numero_fattura: il numero della fattura
            - data_emissione: la data di emissione della fattura
            - fornitore: nome e dettagli del fornitore
            - cliente: nome e dettagli del cliente
            - importo_totale: importo totale della fattura
            - importo_netto: importo netto (senza IVA)
            - iva: importo IVA
            - voci: array di elementi della fattura con quantità, descrizione e prezzo
            - metodo_pagamento: metodo di pagamento se presente
            - scadenza_pagamento: scadenza del pagamento se presente
            """
        elif document_type.lower() == "scontrino":
            prompt = """
            Analizza questo scontrino ed estrai tutti i dati rilevanti.
            Restituisci la risposta in formato JSON con i seguenti campi:
            - negozio: nome del negozio o esercente
            - data: data dello scontrino
            - ora: ora dello scontrino
            - prodotti: array di prodotti acquistati con quantità, descrizione e prezzo
            - totale: importo totale dello scontrino
            - pagamento: metodo di pagamento se presente
            - iva: dettagli IVA se presenti
            """
        elif document_type.lower() == "bilancio":
            prompt = """
            Analizza questo documento di bilancio ed estrai tutti i dati rilevanti.
            Restituisci la risposta in formato JSON con i seguenti campi:
            - azienda: nome dell'azienda
            - anno: anno di riferimento
            - tipo_bilancio: tipo di bilancio (es. stato patrimoniale, conto economico)
            - totale_attivo: totale attivo se presente
            - totale_passivo: totale passivo se presente
            - ricavi: ricavi se presenti
            - costi: costi se presenti
            - utile_perdita: utile o perdita se presente
            - voci_principali: array delle voci principali con descrizione e valore
            """
        else:
            prompt = f"""
            Analizza questa immagine di documento "{document_type}" ed estrai tutti i dati rilevanti.
            Restituisci la risposta in formato JSON con campi appropriati per questo tipo di documento.
            Include almeno:
            - tipo_documento: tipo di documento rilevato
            - data: data del documento se presente
            - mittente: mittente/emittente del documento se presente
            - destinatario: destinatario del documento se presente
            - oggetto: oggetto/titolo del documento se presente
            - importi: eventuali importi monetari rilevanti
            - dati_chiave: array di altre informazioni chiave nel formato {"chiave": "valore"}
            """
        
        result = await self.analyze_image(image_path, prompt)
        
        if not result.get("success"):
            return {
                "error": result.get("error", "Errore sconosciuto"),
                "raw_text": result.get("raw_text", "")
            }
        
        try:
            return {
                "success": True,
                "data": result.get("parsed_data", {}),
                "raw_text": result.get("raw_text", "")
            }
        except Exception as e:
            logger.error(f"Errore durante l'elaborazione dei dati estratti: {e}")
            return {
                "error": str(e),
                "raw_text": result.get("raw_text", "")
            }
