FROM python:3.11-slim

WORKDIR /app

# Installa solo le dipendenze necessarie
RUN pip install fastapi uvicorn

# Copia solo l'app minima
COPY app.py .

# Avvia l'app utilizzando la variabile d'ambiente PORT
CMD uvicorn app:app --host 0.0.0.0 --port ${PORT:-8000}
