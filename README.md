# Railway Document Worker

## Panoramica

Railway Document Worker è un microservizio per l'elaborazione di documenti business (Excel, CSV, PDF, immagini) che produce output JSON strutturato per integrazione con LLM e flussi di lavoro N8N.

## Funzionalità

- **Elaborazione di file Excel**: Estrazione di dati da tutti i fogli di lavoro
- **Elaborazione di file CSV**: Rilevamento automatico del separatore e conversione in JSON
- **Elaborazione di file PDF**: Estrazione di testo e metadati
- **Classificazione automatica dei documenti**: Riconoscimento automatico del tipo di documento
- **Architettura modulare con feature flags**: Attivazione/disattivazione selettiva delle funzionalità

## Requisiti

- Python 3.11 o superiore
- FastAPI
- Pandas (per elaborazione Excel/CSV)
- PyPDF (per elaborazione PDF base)
- Poppler (per funzionalità PDF avanzate)
- Tesseract OCR (per OCR su PDF scansionati e immagini)

## Installazione

1. Clona il repository:
```bash
git clone https://github.com/yourusername/railway-document-worker.git
cd railway-document-worker
```

2. Installa le dipendenze:
```bash
pip install -r requirements.unified.txt
```

3. Per funzionalità avanzate, installa le dipendenze di sistema:
```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install -y poppler-utils tesseract-ocr tesseract-ocr-ita

# MacOS
brew install poppler tesseract
```

## Utilizzo locale

### Script di avvio con feature flags

Utilizza gli script `run-app.sh` (Linux/Mac) o `run-app.ps1` (Windows) per avviare l'applicazione con diverse configurazioni:

```bash
# Avvio con tutte le funzionalità abilitate
./run-app.sh --all

# Avvio solo con elaborazione Excel/CSV
./run-app.sh --minimal

# Avvio senza elaborazione PDF
./run-app.sh --no-pdf

# Avvio con configurazione personalizzata
./run-app.sh --tabular=true --pdf=true --advanced-pdf=false --ocr=false --image=false
```

### Chiamata API

Una volta avviato il server, puoi elaborare documenti inviando richieste POST all'endpoint `/process-document`:

```bash
curl -X POST -F "file=@/path/to/your/document.xlsx" -F "document_type=optional_type" http://localhost:8080/process-document
```

## Deployment su Railway

### Script di deployment con feature flags

Utilizza gli script `deploy-railway.sh` (Linux/Mac) o `deploy-railway.ps1` (Windows) per deployare su Railway con diverse configurazioni:

```bash
# Deploy con configurazione standard (Excel/CSV + PDF base)
./deploy-railway.sh --standard

# Deploy con tutte le funzionalità abilitate
./deploy-railway.sh --all

# Deploy solo con elaborazione Excel/CSV
./deploy-railway.sh --minimal

# Deploy solo con elaborazione PDF
./deploy-railway.sh --pdf-only

# Deploy con funzionalità avanzate
./deploy-railway.sh --advanced
```

### Configurazione manuale

Puoi anche configurare manualmente le variabili d'ambiente su Railway:

- `ENABLE_TABULAR_PROCESSING`: Abilita/disabilita elaborazione Excel/CSV (true/false)
- `ENABLE_PDF_PROCESSING`: Abilita/disabilita elaborazione PDF (true/false)
- `ENABLE_ADVANCED_PDF`: Abilita/disabilita funzionalità PDF avanzate (true/false)
- `ENABLE_OCR`: Abilita/disabilita OCR per PDF scansionati (true/false)
- `ENABLE_IMAGE_PROCESSING`: Abilita/disabilita elaborazione immagini (true/false)

## Struttura del progetto

```
railway-document-worker/
├── app/
│   ├── main.py                   # FastAPI app principale
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
├── railway.toml                  # Configurazione Railway
├── run-app.sh                    # Script per avvio locale (Linux/Mac)
├── run-app.ps1                   # Script per avvio locale (Windows)
├── deploy-railway.sh             # Script per deployment su Railway (Linux/Mac)
└── deploy-railway.ps1            # Script per deployment su Railway (Windows)
```

## Troubleshooting

### Problemi con PDF avanzati o OCR

Se riscontri problemi con le funzionalità PDF avanzate o OCR, prova a disabilitarle:

```bash
# Avvio con solo PDF base
./run-app.sh --pdf=true --advanced-pdf=false --ocr=false
```

### Problemi di memoria su Railway

Se riscontri problemi di memoria su Railway, prova con una configurazione minimale:

```bash
./deploy-railway.sh --minimal
```

## Sviluppo futuro

- Supporto per elaborazione immagini con OCR
- Integrazione con Mistral AI per analisi avanzata
- Miglioramento della classificazione automatica dei documenti
- Supporto per estrazione di tabelle da PDF

## Licenza

[MIT License](LICENSE)
