FROM python:3.11-slim

WORKDIR /app

# Installa dipendenze per Tesseract OCR e Poppler
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-ita \
    poppler-utils \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copia requirements e installa dipendenze Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia il codice dell'applicazione
COPY . .

# Copia e rende eseguibile lo script di entrypoint
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Espone la porta
EXPOSE 8000

# Comando per eseguire l'applicazione
ENTRYPOINT ["/entrypoint.sh"]
