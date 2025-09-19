"""
FastAPI app minimale senza importare pandas
"""
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Pandas Test - No Import"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
