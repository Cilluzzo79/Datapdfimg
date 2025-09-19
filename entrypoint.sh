#!/bin/bash
# entrypoint.sh

# Imposta la porta di default se non è definita
PORT=${PORT:-8000}

# Esegui uvicorn con la porta corretta
exec uvicorn app.main:app --host 0.0.0.0 --port $PORT
