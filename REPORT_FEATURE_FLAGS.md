# Report Implementazione Architecture Unificata con Feature Flags

## Riassunto Operativo

Questo report documenta l'implementazione di un'architettura unificata con feature flags per il Railway Document Worker. L'approccio risolutivo permette di mantenere tutte le funzionalità sviluppate finora (elaborazione di Excel/CSV e PDF) in un'unica applicazione, con la possibilità di abilitare/disabilitare selettivamente le varie componenti.

**Stato attuale**: Implementazione di un'architettura unificata che supporta l'elaborazione di file CSV, Excel e PDF con feature flags.

## Problema Risolto

Il progetto soffriva di un ciclo di sviluppo in cui ogni nuova funzionalità implementata (prima Excel/CSV, poi PDF) causava la perdita di funzionalità precedenti. Questo creava una situazione "ping-pong" in cui non era possibile avere tutte le funzionalità attive contemporaneamente.

## Soluzione Implementata

Abbiamo adottato un'architettura basata su feature flags che permette di:

1. **Mantenere tutte le funzionalità in un unico codebase**
2. **Attivare/disattivare selettivamente le varie componenti**
3. **Gestire le dipendenze in modo modulare**
4. **Facilitare il debugging in caso di problemi**

## Implementazione Dettagliata

### 1. Feature Flags

Abbiamo creato un modulo di configurazione (`app/config/settings.py`) che definisce i feature flags:

```python
# Feature flags
ENABLE_TABULAR_PROCESSING = os.getenv("ENABLE_TABULAR_PROCESSING", "true").lower() == "true"
ENABLE_PDF_PROCESSING = os.getenv("ENABLE_PDF_PROCESSING", "true").lower() == "true"
ENABLE_ADVANCED_PDF = os.getenv("ENABLE_ADVANCED_PDF", "false").lower() == "true"
ENABLE_OCR = os.getenv("ENABLE_OCR", "false").lower() == "true"
ENABLE_IMAGE_PROCESSING = os.getenv("ENABLE_IMAGE_PROCESSING", "false").lower() == "true"
```

Questi flag possono essere controllati tramite variabili d'ambiente nel Dockerfile o nel deployment su Railway.

### 2. PDFProcessor Semplificato

Abbiamo creato una versione semplificata del `PDFProcessor` che utilizza solo `pypdf` (senza PyMuPDF e OCR):

```python
@staticmethod
def _extract_from_pdf_base(pdf_file: io.BytesIO) -> Tuple[Dict[int, str], Dict[str, Any]]:
    """
    Estrae testo e metadati da un PDF usando solo PyPDF
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
```

### 3. Endpoint API Unificato

L'endpoint `/process-document` è stato aggiornato per supportare tutti i tipi di file e verificare i feature flags:

```python
@app.post("/process-document", response_model=DocumentResponse)
async def process_document(
    file: UploadFile = File(...),
    document_type: Optional[str] = Form(None)
):
    # Determina il tipo di file dall'estensione
    file_type = None
    if file.filename.endswith(tuple(settings.ALLOWED_EXCEL_EXTENSIONS)):
        if not settings.ENABLE_TABULAR_PROCESSING:
            raise HTTPException(status_code=400, detail="Elaborazione file Excel disabilitata")
        file_type = "excel"
    elif file.filename.endswith(tuple(settings.ALLOWED_CSV_EXTENSIONS)):
        if not settings.ENABLE_TABULAR_PROCESSING:
            raise HTTPException(status_code=400, detail="Elaborazione file CSV disabilitata")
        file_type = "csv"
    elif file.filename.endswith(tuple(settings.ALLOWED_PDF_EXTENSIONS)):
        if not settings.ENABLE_PDF_PROCESSING:
            raise HTTPException(status_code=400, detail="Elaborazione PDF disabilitata")
        file_type = "pdf"
    # ...
```

### 4. Dockerfile Unificato

Abbiamo creato un Dockerfile unificato che include tutte le dipendenze necessarie e imposta i feature flags:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Installiamo dipendenze di sistema minime
RUN apt-get update && apt-get install -y \
    poppler-utils \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copiamo prima i file di requirements per migliore caching
COPY requirements.unified.txt .
RUN pip install --no-cache-dir -r requirements.unified.txt

# Copiamo il codice dell'applicazione
COPY app ./app

# Configurazione feature flags
ENV ENABLE_TABULAR_PROCESSING=true
ENV ENABLE_PDF_PROCESSING=true
ENV ENABLE_ADVANCED_PDF=false
ENV ENABLE_OCR=false
ENV ENABLE_IMAGE_PROCESSING=false
```

### 5. Backup della Versione Funzionante

Abbiamo creato una sottocartella `version_backup` che contiene la versione funzionante precedente:

```
version_backup/
├── Dockerfile.tabular_complete
├── main.py
├── railway.toml
└── tabular_processor.py
```

## Architettura Attuale

```
railway-document-worker/
├── app/
│   ├── main.py                   # FastAPI app principale unificata
│   ├── config/
│   │   └── settings.py           # Configurazioni e feature flags
│   ├── models/
│   │   ├── document.py           # Modelli Pydantic per documenti
│   │   ├── response.py           # Modelli per risposte API
│   │   └── __init__.py
│   ├── services/
│   │   ├── tabular_processor.py  # Elaborazione CSV/Excel
│   │   ├── pdf_processor.py      # Elaborazione PDF completa
│   │   ├── pdf_processor_simple.py # Elaborazione PDF semplificata
│   │   └── __init__.py
│   └── __init__.py
├── Dockerfile.unified            # Dockerfile con supporto per tutte le funzionalità
├── requirements.unified.txt      # Dipendenze unificate
├── railway.toml                  # Configurazione Railway aggiornata
├── version_backup/               # Backup della versione funzionante
└── README.md                     # Documentazione
```

## Vantaggi dell'Approccio

1. **Flessibilità**: Possibilità di attivare/disattivare funzionalità a runtime
2. **Debugging facilitato**: Se una componente causa problemi, può essere disabilitata senza rimuovere il codice
3. **Sviluppo incrementale**: Possibilità di sviluppare nuove funzionalità senza interferire con quelle esistenti
4. **Deployment controllato**: Attivazione graduale delle funzionalità in produzione

## Prossimi Passi

1. **Test dell'architettura unificata**: Verificare il corretto funzionamento con Excel/CSV e PDF base
2. **Abilitazione graduale delle funzionalità avanzate**: Testare l'attivazione di ADVANCED_PDF e OCR
3. **Implementazione di supporto per immagini**: Aggiungere un `ImageProcessor` con OCR
4. **Integrazione LLM**: Aggiungere il supporto per Mistral AI

## Note Tecniche

- I feature flags sono controllati tramite variabili d'ambiente
- Il timeout di healthcheck è stato aumentato a 120 secondi per dare più tempo all'avvio
- Le dipendenze sono state semplificate al minimo necessario per garantire la stabilità
- L'applicazione espone un endpoint `/features` per verificare lo stato dei feature flags

## Conclusioni

L'implementazione di un'architettura unificata con feature flags permette di mantenere tutte le funzionalità sviluppate finora in un'unica applicazione, evitando il ciclo di sviluppo "ping-pong". Questo approccio facilita anche il debugging e il deployment controllato delle funzionalità.

---

Report generato il: 20 settembre 2025