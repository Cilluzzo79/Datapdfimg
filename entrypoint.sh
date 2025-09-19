#!/bin/bash
# entrypoint.sh

# Debug: mostra variabili d'ambiente
echo "DEBUG: PORT=${PORT:-8000}"
echo "DEBUG: Environment=${ENVIRONMENT:-development}"

# Piccolo ritardo per sicurezza
echo "Attendi 5 secondi prima dell'avvio..."
sleep 5
echo "Avvio dell'applicazione..."

# Imposta la porta di default se non è definita
PORT=${PORT:-8000}

# Esegui uvicorn con la porta corretta e log verbose
exec uvicorn app.main:app --host 0.0.0.0 --port $PORT --log-level debug
