FROM python:3.11-slim

WORKDIR /app

# Installa solo le dipendenze necessarie
RUN pip install fastapi uvicorn

# Copia solo l'app minima
COPY app.py .

# Avvia l'app
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
