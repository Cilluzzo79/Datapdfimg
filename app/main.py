"""
FastAPI app che utilizza pandas per elaborare un file CSV/Excel
"""
from fastapi import FastAPI, UploadFile, File
import pandas as pd
import io

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Pandas Test - File Processing"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.post("/process-file")
async def process_file(file: UploadFile = File(...)):
    """
    Processa un file CSV o Excel molto semplicemente
    """
    try:
        # Leggi il contenuto del file
        content = await file.read()
        
        # Crea un BytesIO object
        file_obj = io.BytesIO(content)
        
        # Determina il tipo di file dall'estensione
        if file.filename.endswith(('.xlsx', '.xls')):
            # Leggi Excel
            df = pd.read_excel(file_obj)
        elif file.filename.endswith('.csv'):
            # Leggi CSV
            df = pd.read_csv(file_obj)
        else:
            return {"error": "Formato file non supportato"}
        
        # Restituisci informazioni di base sul dataframe
        result = {
            "filename": file.filename,
            "rows": len(df),
            "columns": df.columns.tolist(),
            "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
            "head": df.head(2).to_dict(orient='records')  # Prime 2 righe come esempio
        }
        
        return result
    except Exception as e:
        # Log dettagliato dell'errore
        error_details = {
            "error_type": str(type(e).__name__),
            "error_message": str(e),
            "filename": file.filename,
        }
        return {"error": "Errore durante l'elaborazione del file", "details": error_details}
