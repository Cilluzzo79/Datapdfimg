"""
FastAPI app ultra-semplificata
"""
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello Railway"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
