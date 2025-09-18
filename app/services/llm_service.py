import json
import httpx
import base64
from typing import Dict, Any, List, Optional
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from app.config.settings import settings
from app.utils.logging_utils import get_logger
from app.models.document import DocumentType

logger = get_logger(__name__)


class LLMService:
    """Servizio per l'integrazione con Mistral tramite OpenRouter"""
    
    def __init__(self):
        """Inizializza il servizio LLM"""
        self.api_key = settings.OPENROUTER_API_KEY
        self.api_url = settings.OPENROUTER_API_URL
        self.model = settings.LLM_MODEL
        self.timeout = settings.LLM_TIMEOUT
        
        logger.info(f"LLM Service inizializzato con modello: {self.model}")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((httpx.RequestError, httpx.TimeoutException))
    )
    async def call_llm_api(self, prompt: str) -> Dict[str, Any]:
        """
        Chiama l'API LLM con il prompt specificato
        
        Args:
            prompt: Prompt da inviare all'LLM
            
        Returns:
            Risposta dell'LLM come dizionario
        """
        try:
            logger.info(f"Chiamata API LLM con prompt di {len(prompt)} caratteri")
            
            headers = {
                "Authorization": f"Bearer {self.api_key.strip()}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": self.model,
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": 1024,
                "temperature": 0.1,  # Bassa temperatura per output più deterministici
                "response_format": {"type": "json_object"}  # Richiedi output in formato JSON
            }
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.api_url}/chat/completions",
                    headers=headers,
                    json=payload
                )
                
                response.raise_for_status()
                result = response.json()
                
                logger.info(f"Risposta API LLM ricevuta, {len(result['choices'][0]['message']['content'])} caratteri")
                return result
        except httpx.RequestError as e:
            logger.error(f"Errore di richiesta API LLM: {e}")
            raise
        except httpx.HTTPStatusError as e:
            logger.error(f"Errore HTTP API LLM: {e}, Status Code: {e.response.status_code}")
            logger.error(f"Risposta errore: {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Errore generico API LLM: {e}")
            raise
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((httpx.RequestError, httpx.TimeoutException))
    )
    async def analyze_image(self, image_path: str, prompt: str) -> Dict[str, Any]:
        """
        Analizza un'immagine usando l'API di visione di Mistral
        
        Args:
            image_path: Percorso dell'immagine
            prompt: Prompt da inviare all'LLM
            
        Returns:
            Risposta dell'LLM come dizionario
        """
        try:
            logger.info(f"Analisi immagine con Mistral Vision: {image_path}")
            
            # Leggi l'immagine e convertila in base64
            with open(image_path, "rb") as image_file:
                base64_image = base64.b64encode(image_file.read()).decode("utf-8")
            
            headers = {
                "Authorization": f"Bearer {self.api_key.strip()}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": self.model,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                }
                            },
                            {
                                "type": "text",
                                "text": prompt
                            }
                        ]
                    }
                ],
                "max_tokens": 1024,
                "temperature": 0.1,  # Bassa temperatura per output più deterministici
                "response_format": {"type": "json_object"}  # Richiedi output in formato JSON
            }
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.api_url}/chat/completions",
                    headers=headers,
                    json=payload
                )
                
                response.raise_for_status()
                result = response.json()
                
                logger.info(f"Risposta analisi immagine ricevuta, {len(result['choices'][0]['message']['content'])} caratteri")
                return result
        except httpx.RequestError as e:
            logger.error(f"Errore di richiesta analisi immagine: {e}")
            raise
        except httpx.HTTPStatusError as e:
            logger.error(f"Errore HTTP analisi immagine: {e}, Status Code: {e.response.status_code}")
            logger.error(f"Risposta errore: {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Errore generico analisi immagine: {e}")
            raise
    
    async def analyze_document_text(self, text: str, document_type_hint: Optional[DocumentType] = None) -> Dict[str, Any]:
        """
        Analizza il testo di un documento usando l'LLM
        
        Args:
            text: Testo del documento
            document_type_hint: Suggerimento sul tipo di documento
            
        Returns:
            Risultati dell'analisi
        """
        try:
            logger.info(f"Analisi testo documento con LLM, {len(text)} caratteri")
            
            # Costruisci il prompt
            prompt = """
            Analizza il seguente documento di business e crea un riassunto strutturato in formato JSON.
            
            Identifica il tipo di documento tra: fattura, bilancio, magazzino, corrispettivo, analisi_mercato.
            
            Estrai tutti i dettagli rilevanti in base al tipo di documento.
            
            Documento:
            """
            
            # Aggiungi suggerimento sul tipo di documento se fornito
            if document_type_hint:
                prompt += f"\n\nSuggerimento: Questo documento potrebbe essere di tipo {document_type_hint.value}."
                
            # Aggiungi il testo del documento
            prompt += f"\n\n{text[:8000]}"  # Limita a 8000 caratteri per evitare token eccessivi
            
            # Aggiungi istruzioni sul formato di output
            prompt += """
            
            Restituisci la risposta in formato JSON con la seguente struttura:
            {
                "document_type": "fattura|bilancio|magazzino|corrispettivo|analisi_mercato",
                "confidence_score": 0.95, // Livello di confidenza nell'identificazione del tipo
                "extracted_data": {
                    // Campi specifici in base al tipo di documento
                },
                "summary": "Breve riassunto del documento"
            }
            
            Se il documento è una fattura, includi: numero_fattura, data_fattura, importo_totale, iva, mittente, destinatario, righe_fattura, valuta.
            Se è un bilancio, includi: tipo_bilancio, periodo, attivita, passivita, patrimonio_netto, ricavi, costi, utile_perdita.
            Se è un documento di magazzino, includi: tipo_documento, data, articoli, totale_quantita, totale_valore, magazzino_codice.
            Se è un corrispettivo, includi: numero_documento, data, importo_totale, iva, esercente, prodotti.
            Se è un'analisi di mercato, includi: titolo, periodo, settore, dati_analitici, grafici_descrizioni, conclusioni.
            
            Assicurati che il JSON sia ben formato e valido.
            """
            
            # Chiama l'API LLM
            result = await self.call_llm_api(prompt)
            
            # Estrai il contenuto JSON dalla risposta
            try:
                content = result["choices"][0]["message"]["content"]
                analysis = json.loads(content)
                logger.info(f"Analisi documento completata, tipo: {analysis.get('document_type', 'sconosciuto')}")
                return analysis
            except json.JSONDecodeError as e:
                logger.error(f"Errore nel parsing JSON dalla risposta LLM: {e}")
                logger.error(f"Contenuto risposta: {content}")
                return {
                    "document_type": "sconosciuto",
                    "confidence_score": 0.0,
                    "extracted_data": {},
                    "summary": "Impossibile analizzare il documento",
                    "error": "Errore nel parsing JSON"
                }
        except Exception as e:
            logger.error(f"Errore durante l'analisi del documento: {e}")
            return {
                "document_type": "sconosciuto",
                "confidence_score": 0.0,
                "extracted_data": {},
                "summary": "Errore durante l'analisi del documento",
                "error": str(e)
            }
    
    async def analyze_document_image(self, image_path: str, document_type_hint: Optional[DocumentType] = None) -> Dict[str, Any]:
        """
        Analizza un'immagine di un documento usando Mistral Vision
        
        Args:
            image_path: Percorso dell'immagine
            document_type_hint: Suggerimento sul tipo di documento
            
        Returns:
            Risultati dell'analisi
        """
        try:
            logger.info(f"Analisi immagine documento con Mistral Vision: {image_path}")
            
            # Costruisci il prompt
            prompt = """
            Analizza questa immagine di un documento di business e crea un riassunto strutturato in formato JSON.
            
            Identifica il tipo di documento tra: fattura, bilancio, magazzino, corrispettivo, analisi_mercato.
            
            Estrai tutti i dettagli rilevanti in base al tipo di documento.
            """
            
            # Aggiungi suggerimento sul tipo di documento se fornito
            if document_type_hint:
                prompt += f"\n\nSuggerimento: Questo documento potrebbe essere di tipo {document_type_hint.value}."
            
            # Aggiungi istruzioni sul formato di output
            prompt += """
            
            Restituisci la risposta in formato JSON con la seguente struttura:
            {
                "document_type": "fattura|bilancio|magazzino|corrispettivo|analisi_mercato",
                "confidence_score": 0.95, // Livello di confidenza nell'identificazione del tipo
                "extracted_data": {
                    // Campi specifici in base al tipo di documento
                },
                "raw_text": "Testo estratto dall'immagine",
                "summary": "Breve riassunto del documento"
            }
            
            Se il documento è una fattura, includi: numero_fattura, data_fattura, importo_totale, iva, mittente, destinatario, righe_fattura, valuta.
            Se è un bilancio, includi: tipo_bilancio, periodo, attivita, passivita, patrimonio_netto, ricavi, costi, utile_perdita.
            Se è un documento di magazzino, includi: tipo_documento, data, articoli, totale_quantita, totale_valore, magazzino_codice.
            Se è un corrispettivo, includi: numero_documento, data, importo_totale, iva, esercente, prodotti.
            Se è un'analisi di mercato, includi: titolo, periodo, settore, dati_analitici, grafici_descrizioni, conclusioni.
            
            Assicurati che il JSON sia ben formato e valido.
            """
            
            # Chiama l'API di analisi immagine
            result = await self.analyze_image(image_path, prompt)
            
            # Estrai il contenuto JSON dalla risposta
            try:
                content = result["choices"][0]["message"]["content"]
                analysis = json.loads(content)
                logger.info(f"Analisi immagine documento completata, tipo: {analysis.get('document_type', 'sconosciuto')}")
                return analysis
            except json.JSONDecodeError as e:
                logger.error(f"Errore nel parsing JSON dalla risposta Mistral Vision: {e}")
                logger.error(f"Contenuto risposta: {content}")
                return {
                    "document_type": "sconosciuto",
                    "confidence_score": 0.0,
                    "extracted_data": {},
                    "raw_text": "",
                    "summary": "Impossibile analizzare il documento",
                    "error": "Errore nel parsing JSON"
                }
        except Exception as e:
            logger.error(f"Errore durante l'analisi dell'immagine documento: {e}")
            return {
                "document_type": "sconosciuto",
                "confidence_score": 0.0,
                "extracted_data": {},
                "raw_text": "",
                "summary": "Errore durante l'analisi dell'immagine documento",
                "error": str(e)
            }
