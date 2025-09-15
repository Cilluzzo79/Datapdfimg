# Datapdfimg
# Railway Document Worker

Microservizio per l'elaborazione di documenti business (immagini e PDF) con output JSON strutturato per LLM.

## Funzionalità

- Elaborazione di immagini (JPG, PNG, WEBP) e PDF
- Estrazione testo tramite OCR per immagini e PDF scannerizzati
- Classificazione automatica del tipo di documento
- Estrazione dati strutturati basata sul tipo di documento
- Integrazione con Mistral AI tramite OpenRouter per analisi avanzata
- API REST con FastAPI
- Deployment automatico su Railway

## Tipi di documenti supportati

- **Fatture**: Estrazione di numero fattura, data, importi, mittente, destinatario, ecc.
- **Bilanci**: Analisi di stato patrimoniale, conto economico, ecc.
- **Documenti di magazzino**: Inventari, movimentazioni, ecc.
- **Corrispettivi**: Scontrini, ricevute, ecc.
- **Analisi di mercato**: Report, grafici, tabelle, ecc.

## Architettura

Il worker è strutturato in modo modulare con i seguenti componenti:

- **API FastAPI**: Gestisce le richieste HTTP e coordina l'elaborazione
- **Document Processor**: Servizio principale che coordina l'elaborazione
- **Image Processor**: Elaborazione specifica per le immagini
- **PDF Processor**: Elaborazione specifica per i PDF
- **OCR Service**: Servizio OCR per estrazione testo
- **LLM Service**: Integrazione con Mistral AI per analisi avanzata

## Setup e Installazione

### Prerequisiti

- Python 3.11+
- Tesseract OCR
- Poppler (per la conversione PDF)

### Installazione locale

1. Clona il repository:
   ```bash
   git clone <repository-url>
   cd railway-document-worker
   ```

2. Crea un ambiente virtuale e installa le dipendenze:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # oppure
   venv\Scripts\activate  # Windows
   pip install -r requirements.txt
   ```

3. Crea un file `.env` con le variabili di ambiente necessarie:
   ```
   ENVIRONMENT=dev
   OPENROUTER_API_KEY=your_openrouter_api_key
   LOG_LEVEL=INFO
   MAX_FILE_SIZE_MB=10
   ```

4. Avvia il server:
   ```bash
   uvicorn app.main:app --reload
   ```

### Deployment su Railway

1. Assicurati di avere l'account Railway e CLI installata
2. Configura le variabili d'ambiente su Railway:
   - `ENVIRONMENT=production`
   - `OPENROUTER_API_KEY=your_openrouter_api_key`
   - `LOG_LEVEL=INFO`
   - `MAX_FILE_SIZE_MB=10`

3. Deploy su Railway:
   ```bash
   railway link
   railway up
   ```

## Utilizzo API

### Elaborazione documento

```bash
curl -X POST http://localhost:8000/process-document \
  -F "file=@path/to/your/document.pdf" \
  -F "document_type=fattura"  # Opzionale
```

### Risposta

```json
{
  "status": "success",
  "timestamp": "2023-10-01T12:34:56.789Z",
  "document_id": "123e4567-e89b-12d3-a456-426614174000",
  "document_type": "fattura",
  "confidence_score": 0.95,
  "processing_time_ms": 1234,
  "result_json": {
    "document_id": "123e4567-e89b-12d3-a456-426614174000",
    "processing_timestamp": "2023-10-01T12:34:56.789Z",
    "document_type": "fattura",
    "confidence_score": 0.95,
    "metadata": {
      "original_filename": "fattura_esempio.pdf",
      "file_type": "pdf",
      "file_size": 123456,
      "pages_processed": 1,
      "processing_time_ms": 1234,
      "md5_hash": "a1b2c3d4e5f6g7h8i9j0"
    },
    "extracted_data": {
      "numero_fattura": "F12345",
      "data_fattura": "2023-09-30",
      "importo_totale": 1000.00,
      "iva": 220.00,
      "mittente": {
        "nome": "Azienda SRL",
        "indirizzo": "Via Roma 123",
        "partita_iva": "IT12345678901"
      },
      "destinatario": {
        "nome": "Cliente SpA",
        "indirizzo": "Via Milano 456",
        "partita_iva": "IT98765432101"
      }
    },
    "raw_text": "Testo estratto dal documento...",
    "processing_notes": []
  },
  "processing_notes": []
}
```

## Test webhook N8N

Per testare l'integrazione con N8N, puoi utilizzare l'endpoint `/test-webhook`:

```bash
curl -X POST http://localhost:8000/test-webhook \
  -H "Content-Type: application/json" \
  -d '{"test": "payload"}'
```

## Integrazione con N8N

1. In N8N, crea un nuovo workflow
2. Aggiungi un nodo HTTP Request (POST) che invia il file al worker
3. Configura il nodo con:
   - URL: `https://tuo-worker-railway.app/process-document`
   - Metodo: POST
   - Modalità binaria: ON
   - Form data con:
     - `file`: Il file binario da elaborare
     - `document_type` (opzionale): Tipo di documento
4. Collega l'output al resto del tuo workflow

## Sviluppo

### Struttura progetto

```
railway-document-worker/
├── app/
│   ├── __init__.py
│   ├── main.py                # FastAPI app principale
│   ├── models/
│   │   ├── __init__.py
│   │   ├── document.py        # Modelli Pydantic per documenti
│   │   └── response.py        # Modelli per risposte API
│   ├── services/
│   │   ├── __init__.py
│   │   ├── document_processor.py  # Service per processare documenti
│   │   ├── image_processor.py     # Elaborazione immagini
│   │   ├── pdf_processor.py       # Elaborazione PDF
│   │   ├── ocr_service.py         # Servizio OCR
│   │   └── llm_service.py         # Integrazione con Mistral
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── file_utils.py       # Utility per file
│   │   ├── logging_utils.py    # Configurazione logging
│   │   └── validators.py       # Validatori input
│   └── config/
│       ├── __init__.py
│       └── settings.py         # Configurazioni app
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_main.py
│   ├── test_document_processor.py
│   ├── test_image_processor.py
│   └── test_pdf_processor.py
├── requirements.txt
├── Dockerfile
├── railway.toml
└── README.md
```

### Esecuzione test

```bash
pytest
```

## Licenza

MIT
