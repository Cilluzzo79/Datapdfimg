"""
FastAPI app con supporto per CSV/Excel
"""
from fastapi import FastAPI, UploadFile, File, Form
from typing import Optional
import pandas as pd
import io
import json

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Tabular Data Processor"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.post("/process-csv")
async def process_csv(file: UploadFile = File(...)):
    """
    Processa un file CSV e restituisce i dati come JSON
    """
    # Leggi il contenuto del file
    content = await file.read()
    
    # Converti in DataFrame
    df = pd.read_csv(io.BytesIO(content))
    
    # Converti in JSON
    result = {
        "filename": file.filename,
        "rows": len(df),
        "columns": list(df.columns),
        "data": df.head(5).to_dict(orient="records")
    }
    
    return result

@app.post("/process-excel")
async def process_excel(file: UploadFile = File(...)):
    """
    Processa un file Excel e restituisce i dati come JSON
    """
    # Leggi il contenuto del file
    content = await file.read()
    
    # Converti in DataFrame
    df = pd.read_excel(io.BytesIO(content))
    
    # Converti in JSON
    result = {
        "filename": file.filename,
        "rows": len(df),
        "columns": list(df.columns),
        "data": df.head(5).to_dict(orient="records")
    }
    
    return result
