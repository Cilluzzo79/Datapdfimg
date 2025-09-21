FROM python:3.11-slim

# Installa dipendenze di sistema
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-ita \
    tesseract-ocr-eng \
    poppler-utils \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copia requirements e installa dipendenze
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia solo i file essenziali inizialmente
COPY main.py .
COPY app ./app

# Crea la directory temporanea
RUN mkdir -p /tmp/railway-document-worker

# Configurazione feature flags (on/off)
ENV ENABLE_TABULAR_PROCESSING=true
ENV ENABLE_PDF_PROCESSING=true
ENV ENABLE_ADVANCED_PDF=false
ENV ENABLE_OCR=false
ENV ENABLE_IMAGE_PROCESSING=true
ENV ENABLE_MISTRAL_VISION=true

# Configurazione logging
ENV LOG_LEVEL=INFO

# Avvia l'app utilizzando la variabile d'ambiente PORT
CMD uvicorn main:app --host 0.0.0.0 --port $PORT