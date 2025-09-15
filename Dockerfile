FROM python:3.11-slim

# Imposta la directory di lavoro
WORKDIR /app

# Installa le dipendenze di sistema
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-ita \
    tesseract-ocr-eng \
    poppler-utils \
    libpoppler-cpp-dev \
    pkg-config \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copia i file necessari
COPY requirements.txt .

# Installa le dipendenze Python
RUN pip install --no-cache-dir -r requirements.txt

# Copia il resto dell'applicazione
COPY . .

# Crea directory temporanea per i file
RUN mkdir -p /tmp/railway-document-worker && chmod 777 /tmp/railway-document-worker

# Esegui come utente non root
RUN useradd -m appuser
USER appuser

# Esponi la porta
EXPOSE 8000

# Comando per avviare l'applicazione
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
