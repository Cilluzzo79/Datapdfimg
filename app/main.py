"""
FastAPI app che importa pandas ma non lo utilizza
"""
from fastapi import FastAPI
import pandas as pd  # Importiamo pandas ma non lo usiamo

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Pandas Test - Import Only"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/pandas-version")
async def pandas_version():
    # Usiamo pandas solo per ottenere la versione, non per elaborare dati
    return {"pandas_version": pd.__version__}
