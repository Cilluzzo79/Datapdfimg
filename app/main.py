"""
FastAPI app che utilizza pandas per creare un semplice DataFrame
"""
from fastapi import FastAPI
import pandas as pd

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Pandas Test - Simple DataFrame"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/pandas-version")
async def pandas_version():
    return {"pandas_version": pd.__version__}

@app.get("/simple-dataframe")
async def simple_dataframe():
    # Creiamo un semplice DataFrame in memoria
    df = pd.DataFrame({
        'A': [1, 2, 3],
        'B': ['a', 'b', 'c']
    })
    
    # Convertiamo in dict e restituiamo
    return {"dataframe": df.to_dict()}
