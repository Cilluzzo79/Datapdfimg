# Report Sviluppo Railway Document Worker

## Riassunto Operativo

Questo report documenta il processo di sviluppo e debug del microservizio Railway Document Worker, progettato per l'elaborazione di documenti business (immagini, PDF, Excel, CSV) con output JSON strutturato per integrazione con LLM e flussi di lavoro N8N.

**Stato attuale**: Implementazione funzionante dell'elaborazione di file CSV, Excel e PDF.

## Problema Iniziale

Il deployment su Railway presentava errori durante l'health check, impedendo il corretto funzionamento del microservizio. Attraverso un approccio di debug sistematico, abbiamo identificato e risolto i problemi, implementando con successo la funzionalità di elaborazione dei file tabulari (CSV ed Excel) e ripristinando il supporto per i file PDF.

## Cronologia del Debug

### 1. Analisi del Problema

L'healthcheck del servizio falliva costantemente su Railway, con il seguente errore:
```
Error: Invalid value for '--port': '$PORT' is not a valid integer.
```

Questo indicava un problema con la gestione delle variabili d'ambiente nel container Docker.

### 2. Approccio Incrementale

Abbiamo adottato un approccio incrementale per isolare il problema:

1. **Versione Ultra-Minimale**: Implementata una versione con sola FastAPI e Uvicorn
   - Risultato: ✅ Funzionante

2. **Test con Pandas Installato**: Aggiunta dipendenza pandas senza importarla
   - Risultato: ✅ Funzionante

3. **Test con Pandas Importato**: Importazione di pandas senza utilizzo attivo
   - Risultato: ✅ Funzionante

4. **Test con DataFrame Semplice**: Creazione di DataFrame in memoria
   - Risultato: ✅ Funzionante

5. **Test di Elaborazione File**: Implementazione di elaborazione file minimale
   - Risultato: ✅ Funzionante

6. **Implementazione Completa**: Struttura modulare con modelli e servizi
   - Risultato: ✅ Funzionante

## Soluzioni Implementate

### 1. Correzioni di Base

1. **Gestione PORT**: Risolto problema con la variabile d'ambiente PORT
   ```dockerfile
   CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT} --log-level debug"]
   ```

2. **Health Endpoint Semplificato**: Endpoint di health check minimo
   ```python
   @app.get("/health")
   async def health_check():
       return {"status": "healthy"}
   ```

3. **Timeout Aumentato**: Modificato `railway.toml` per aumentare il timeout dell'healthcheck
   ```toml
   healthcheckTimeout = 60  # Aumentato il timeout
   restartPolicyMaxRetries = 5  # Aumentati i tentativi di riavvio
   ```

### 2. Architettura Implementata

Abbiamo implementato un'architettura modulare con:

1. **TabularProcessor**: Servizio per l'elaborazione di file Excel e CSV
   - Rilevamento automatico dei separatori CSV
   - Supporto per file Excel multi-foglio
   - Rilevamento del tipo di documento
   - Conversione in formato JSON strutturato

2. **PDFProcessor**: Servizio per l'elaborazione di file PDF
   - Rilevamento automatico di PDF nativi vs scansionati
   - Estrazione di testo da PDF nativi
   - OCR per PDF scansionati
   - Estrazione di metadati e immagini

3. **Modelli Pydantic**: Per validazione e tipizzazione
   - `DocumentResponse`: Per strutturare le risposte API
   - `SheetInfo`: Per informazioni sui fogli di lavoro
   - `TabularMetadata`: Per metadati dei file
   - `TabularDocument`: Per il documento elaborato

4. **Endpoint API**: 
   - `/health`: Per il controllo dello stato
   - `/process-document`: Per l'elaborazione dei file
   - `/test-webhook`: Per l'integrazione con N8N

## Struttura Attuale del Progetto

```
railway-document-worker/
├── app/
│   ├── main.py                 # FastAPI app principale
│   ├── models/
│   │   ├── document.py         # Modelli Pydantic per documenti
│   │   ├── response.py         # Modelli per risposte API
│   │   └── __init__.py
│   ├── services/
│   │   ├── tabular_processor.py # Elaborazione CSV/Excel
│   │   ├── pdf_processor.py     # Elaborazione PDF
│   │   └── __init__.py
│   └── __init__.py
├── Dockerfile.complete         # Dockerfile per la versione attuale
├── Dockerfile.ultra            # Dockerfile minimale (per debug)
├── Dockerfile.pandas_test      # Dockerfile intermedio (per debug)
├── minimal_app.py              # App minimale (per debug)
├── railway.toml                # Configurazione Railway
└── README.md                   # Documentazione
```

## Funzionalità Implementate

### 1. Elaborazione di File Tabulari (CSV/Excel)

Il sistema attualmente supporta:

1. **Caricamento di file Excel**:
   - Supporto per tutti i formati (.xls, .xlsx, .xlsm, .xlsb)
   - Estrazione di tutti i fogli di lavoro
   - Metadati dettagliati per ogni foglio

2. **Caricamento di file CSV**:
   - Rilevamento automatico del separatore (,|;|tab|pipe)
   - Gestione di diversi encoding (UTF-8, ISO-8859-1, etc.)
   - Gestione di errori e righe malformate

3. **Classificazione del documento**:
   - Rilevamento automatico del tipo di documento (fattura, bilancio, etc.)
   - Basato su nome file e contenuto delle colonne

4. **Output JSON strutturato**:
   - Formato standardizzato per integrazione con LLM e N8N
   - Metadati completi e dati estratti

### 2. Elaborazione di File PDF

Il sistema ora supporta:

1. **Rilevamento del tipo di PDF**:
   - Distinzione tra PDF nativi (con testo) e PDF scansionati (immagini)
   - Analisi del contenuto per determinare il tipo

2. **Estrazione da PDF nativi**:
   - Estrazione di testo con formattazione
   - Estrazione di immagini incorporate
   - Estrazione di metadati (autore, titolo, etc.)

3. **OCR per PDF scansionati**:
   - Conversione di pagine in immagini
   - Applicazione di OCR con supporto multilingua (italiano e inglese)
   - Gestione delle eccezioni e fallback

4. **Classificazione del documento**:
   - Analisi del testo estratto per determinare il tipo
   - Basato su contenuto e nome del file

## Prossimi Passi

### 1. Integrazione Immagini

Per aggiungere il supporto per le immagini, sarà necessario:

1. Creare un `ImageProcessor` in `app/services/`
2. Implementare OCR per l'estrazione del testo
3. Implementare l'analisi delle immagini per la classificazione

### 2. Integrazione LLM

Per arricchire l'analisi con modelli di linguaggio:

1. Creare un `LLMService` in `app/services/`
2. Aggiungere l'integrazione con Mistral AI tramite OpenRouter
3. Implementare prompt specializzati per ogni tipo di documento

### 3. Miglioramenti Generali

1. Aggiungere test automatici
2. Migliorare la gestione degli errori e il logging
3. Implementare caching e ottimizzazioni delle prestazioni
4. Documentazione API completa con Swagger

## Conclusioni

Il microservizio Railway Document Worker è ora in grado di elaborare file tabulari (Excel e CSV) e PDF, convertendoli in formato JSON strutturato. L'approccio di debug incrementale ha permesso di identificare e risolvere i problemi di deployment, e l'architettura modulare faciliterà l'aggiunta di nuove funzionalità come il supporto per le immagini.

## Note Tecniche

- Railway richiede particolare attenzione alla gestione delle variabili d'ambiente, in particolare `PORT`
- L'utilizzo di dipendenze native (come pandas, pymupdf, pytesseract) richiede attenzione durante il deployment
- L'architettura modulare facilita l'estensione del sistema e il debug

---

Report aggiornato il: 20 settembre 2025